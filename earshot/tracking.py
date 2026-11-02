"""Person tracking with hosted SAM 3.1.

The user taps each person once (a point on their face). We send those taps as
SAM 3.1 object prompts on the analysis video and get a mask per person per
frame, under the IDs we chose. Request and stream handling follow Meta's
cookbook (07_sam/01_api_basics), parsing uses Meta's `meta_sam_parser`.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .calls import BASE_URL, CallLog, api_key

SAM_MODEL = "sam-3.1"


@dataclass(frozen=True)
class Tap:
    """A person to follow: a point on their face, as fractions of width/height."""

    name: str
    x: float
    y: float
    frame: int = 0

    @staticmethod
    def parse(spec: str) -> "Tap":
        """`Ana@0.31,0.42` or `Ana@0.31,0.42#frame`."""
        name, _, rest = spec.partition("@")
        coords, _, frame = rest.partition("#")
        x, y = (float(v) for v in coords.split(","))
        return Tap(name=name.strip(), x=x, y=y, frame=int(frame or 0))


@dataclass
class Tracks:
    """Per-person mask regions, as returned by SAM (bounds + raster of the bounds)."""

    names: list[str]
    width: int
    height: int
    fps: float
    frames: int
    # regions[person][frame] = (left, top, w, h, packed raster bits)
    regions: list[dict[int, tuple[int, int, int, int, bytes]]]

    # ---------- masks ----------
    def mask(self, person: int, frame: int) -> np.ndarray:
        """Full-frame boolean mask (height, width); empty if the person isn't visible."""
        out = np.zeros((self.height, self.width), dtype=bool)
        region = self.regions[person].get(frame)
        if region is None:
            return out
        left, top, w, h, packed = region
        raster = np.unpackbits(np.frombuffer(packed, dtype=np.uint8), count=w * h).reshape(h, w).astype(bool)
        y1, x1 = min(top + h, self.height), min(left + w, self.width)
        out[top:y1, left:x1] = raster[: y1 - top, : x1 - left]
        return out

    def masks(self, person: int, frame0: int, frame1: int) -> np.ndarray:
        """Stack of full-frame masks for frames [frame0, frame1)."""
        return np.stack([self.mask(person, f) for f in range(frame0, frame1)])

    def bbox(self, person: int, frame: int) -> tuple[int, int, int, int] | None:
        region = self.regions[person].get(frame)
        if region is None:
            return None
        left, top, w, h, _ = region
        return left, top, left + w, top + h

    # ---------- bubble anchors ----------
    def anchors(self, person: int, step: int = 3) -> list[list[float]]:
        """[time, x, y_top] per sampled frame, as fractions of the frame.

        x is the centre of the top 20% of the silhouette (the head), y is its top.
        Frames where the person isn't visible are skipped.
        """
        out = []
        for f in range(0, self.frames, step):
            region = self.regions[person].get(f)
            if region is None:
                continue
            left, top, w, h, packed = region
            raster = np.unpackbits(np.frombuffer(packed, dtype=np.uint8), count=w * h).reshape(h, w)
            rows = np.flatnonzero(raster.any(axis=1))
            if rows.size == 0:
                continue
            head = raster[rows[0]: rows[0] + max(1, int(0.2 * (rows[-1] - rows[0] + 1)))]
            cols = np.flatnonzero(head.any(axis=0))
            x = left + (cols.mean() if cols.size else w / 2)
            y = top + rows[0]
            out.append([round(f / self.fps, 3), round(x / self.width, 4), round(y / self.height, 4)])
        return out

    # ---------- persistence ----------
    def save(self, path: Path) -> None:
        payload = {
            "names": self.names, "width": self.width, "height": self.height,
            "fps": self.fps, "frames": self.frames,
            "regions": [
                {str(f): [l, t, w, h, base64.b64encode(p).decode()] for f, (l, t, w, h, p) in r.items()}
                for r in self.regions
            ],
        }
        path.write_text(json.dumps(payload))

    @staticmethod
    def load(path: Path) -> "Tracks":
        d = json.loads(path.read_text())
        regions = [
            {int(f): (l, t, w, h, base64.b64decode(p)) for f, (l, t, w, h, p) in r.items()}
            for r in d["regions"]
        ]
        return Tracks(d["names"], d["width"], d["height"], d["fps"], d["frames"], regions)


# --------------------------------------------------------------------------- #
# SAM 3.1 API
# --------------------------------------------------------------------------- #
def object_prompt_text(taps: list[Tap], width: int, height: int) -> str:
    from meta_sam_parser import FramePrompt, PromptObject, PromptPoint, build_object_prompt

    objects = []
    for i, tap in enumerate(taps, start=1):
        px = max(0, min(width - 1, int(tap.x * width)))
        py = max(0, min(height - 1, int(tap.y * height)))
        objects.append(PromptObject(id=i, prompts=[FramePrompt(frame=tap.frame, points=[PromptPoint(px, py)])]))
    return build_object_prompt(size=(width, height), objects=objects)


def parse_raw_output(raw_output: str):
    """Re-parse SAM's raw output text (cached) into records with Meta's parser."""
    from meta_sam_parser import CompletedOutcome, video_segmentation_format

    parser = video_segmentation_format().create_parser()
    parser.push(raw_output)
    return parser.finish(CompletedOutcome()).result


def records_to_tracks(result, names: list[str], ids: list[str], width: int, height: int,
                      fps: float, frames: int) -> Tracks:
    from meta_sam_parser import decode_mask_to_raster

    errors = [d for d in result.diagnostics if d.severity == "error"]
    if errors:
        raise RuntimeError("SAM output rejected by parser: " + "; ".join(d.message for d in errors[:5]))
    index = {obj_id: i for i, obj_id in enumerate(ids)}
    latest: dict[tuple[int, int], object] = {}
    for rec in result.records:
        if rec.kind != "mask" or rec.frame is None or rec.object_id not in index:
            continue
        k = (index[rec.object_id], rec.frame.frame_index)
        if k not in latest or rec.revision >= latest[k].revision:
            latest[k] = rec
    regions: list[dict] = [dict() for _ in names]
    for (person, frame), rec in latest.items():
        raster = np.frombuffer(decode_mask_to_raster(rec.mask), dtype=np.uint8)
        if not raster.any():
            continue
        left, top = int(rec.bounds.left), int(rec.bounds.top)
        regions[person][frame] = (left, top, rec.mask.width, rec.mask.height, np.packbits(raster).tobytes())
    return Tracks(names, width, height, fps, frames, regions)


async def _sam_video_stream(file_id: str, text: str) -> str:
    from contextlib import aclosing

    from meta_sam_parser import parse_responses_stream, video_segmentation_format
    from openai import AsyncOpenAI

    async def normalized(stream):
        # The live API finalizes lanes with response.content_part.done only;
        # synthesize response.output_text.done for the parser (as in the cookbook).
        done = set()
        async for event in stream:
            data = event.model_dump() if hasattr(event, "model_dump") else dict(event)
            lane = (data.get("item_id"), data.get("output_index"), data.get("content_index"))
            if data.get("type") == "response.output_text.done":
                if lane not in done:
                    done.add(lane)
                    yield data
                continue
            yield data
            part = data.get("part")
            if (data.get("type") == "response.content_part.done" and lane not in done
                    and isinstance(part, dict) and part.get("type") == "output_text"):
                done.add(lane)
                yield {"type": "response.output_text.done", "item_id": lane[0], "output_index": lane[1],
                       "content_index": lane[2], "text": part["text"]}

    async with AsyncOpenAI(base_url=BASE_URL, api_key=api_key()) as api:
        stream = await api.responses.create(
            model=SAM_MODEL, stream=True,
            metadata={"mask_encoding": "one_bit", "propagation_direction": "both"},
            input=[{"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": text},
                {"type": "input_video", "file_id": file_id},
            ]}],
        )
        async with stream, aclosing(normalized(stream)) as events:
            parsed = parse_responses_stream(events, video_segmentation_format())
            async with parsed:
                async for _ in parsed:
                    pass
                result = await parsed.final_result()
    if result.outcome.status != "completed":
        raise RuntimeError(f"SAM segmentation incomplete: {result.outcome}")
    return result.raw_output


def _upload(video: Path) -> str:
    from openai import OpenAI

    with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
        uploaded = api.files.create(file=(video.name, video.read_bytes(), "video/mp4"), purpose="user_data")
    return uploaded.id


def track_people(video: Path, taps: list[Tap], info, calls: CallLog) -> Tracks:
    """Track each tapped person through `video` (the prepared analysis video)."""
    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    text = object_prompt_text(taps, info.width, info.height)

    def upload():
        return {"file_id": _upload(video)}, {}

    def segment():
        file_id = calls.cached(model="files", purpose="upload analysis video", where="hosted",
                               key_parts=(digest,), fn=upload)["file_id"]
        raw = asyncio.run(_sam_video_stream(file_id, text))
        return {"raw_output": raw}, {"prompt": text, "file_id": file_id}

    raw = calls.cached(model=SAM_MODEL, purpose="track tapped people", where="hosted",
                       key_parts=(digest, text), fn=segment)["raw_output"]
    result = parse_raw_output(raw)
    ids = [str(i) for i in range(1, len(taps) + 1)]
    return records_to_tracks(result, [t.name for t in taps], ids, info.width, info.height, info.fps, info.frames)
