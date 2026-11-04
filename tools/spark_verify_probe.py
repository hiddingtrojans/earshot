"""Muse Spark confirms flagged voice-to-face bindings from muted numbered clips (review/SPARK_VERIFY_PROTOCOL.md)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from earshot.bench import oracle_speaker_mapping
from earshot.calls import BASE_URL, CallLog, api_key
from earshot.lite import CONFIDENCE_THRESHOLD, attribute_with_confidence, gray_frames, head_motion
from earshot.media import SEPARATION_SR, TRANSCRIBE_SR, read_audio, resample
from earshot.spark import SPARK_MODEL
from earshot.tracking import Tracks, _upload
from earshot.transcribe import transcribe

from tools.lite_input_probe import REPEATS, WINDOWS, score_mapping

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
CLIPS_PER_LABEL = 3
MIN_TURN = 1.5
CLIP_SECONDS = 2.5
AGREE = 2
SCHEMA = {
    "type": "object",
    "properties": {"speaker": {"type": "string", "enum": ["1", "2", "3", "4", "unclear"]}},
    "required": ["speaker"], "additionalProperties": False,
}
INSTRUCTIONS = (
    "This video clip is muted. Large white numbers 1 to 4 label four people. Watch their mouths. "
    "Which numbered person is talking (lips and jaw moving as in speech) for most of the clip? "
    'Answer "unclear" if no one clearly is, or if you cannot tell. Do not guess.'
)
USER = "Which numbered person is talking in this muted clip?"


def numbered_clip(video: Path, start: float, seconds: float, taps: list[tuple[float, float]],
                  size: tuple[int, int], out: Path) -> Path:
    if out.exists():
        return out
    width, height = size
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(video),
         "-t", f"{seconds:.3f}", "-an", "-vf", "fps=25", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True).stdout
    frame_bytes = width * height * 3
    font = ImageFont.truetype(FONT, 34)
    frames = []
    for offset in range(0, len(raw) - frame_bytes + 1, frame_bytes):
        image = Image.frombytes("RGB", size, raw[offset:offset + frame_bytes])
        draw = ImageDraw.Draw(image)
        for number, (x, y) in enumerate(taps, start=1):
            cx, cy = x * width, max(22.0, y * height - 0.12 * height)
            draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill="black", outline="white", width=3)
            draw.text((cx, cy), str(number), fill="white", font=font, anchor="mm")
        frames.append(image.tobytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{width}x{height}", "-r", "25", "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
        input=b"".join(frames), check=True)
    return out


def ask_spark(calls: CallLog, clip: Path) -> str:
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()

    def call():
        from openai import OpenAI

        file_id = _upload(clip)
        with OpenAI(base_url=BASE_URL, api_key=api_key()) as api:
            resp = api.responses.create(
                model=SPARK_MODEL, instructions=INSTRUCTIONS,
                input=[{"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": USER}, {"type": "input_video", "file_id": file_id}]}],
                text={"format": {"type": "json_schema", "name": "speaking_person", "schema": SCHEMA, "strict": True}},
                reasoning={"effort": "low"}, max_output_tokens=4000,
            )
        if not resp.output_text:
            raise RuntimeError(f"Spark returned no JSON (status={getattr(resp, 'status', None)})")
        usage = getattr(resp, "usage", None)
        return json.loads(resp.output_text), {
            "request_id": resp.id, "usage": usage.model_dump() if hasattr(usage, "model_dump") else None}

    result = calls.cached(model=SPARK_MODEL, purpose="verify a flagged binding: which numbered person is talking",
                          where="hosted", key_parts=(digest, INSTRUCTIONS, USER, SCHEMA), fn=call)
    return result.get("speaker", "unclear")


def clip_spans(turns, label: str) -> list[tuple[float, float]]:
    others = [t for t in turns if t.speaker != label]
    solo = [t for t in turns if t.speaker == label and t.end - t.start >= MIN_TURN
            and not any(o.start < t.end and o.end > t.start for o in others)]
    solo.sort(key=lambda t: t.end - t.start, reverse=True)
    spans = []
    for t in solo[:CLIPS_PER_LABEL]:
        length = min(CLIP_SECONDS, t.end - t.start)
        middle = (t.start + t.end) / 2
        spans.append((middle - length / 2, length))
    return spans


def verify(mapping: dict, confidence: dict, answers: dict[str, list[str]], people: int,
           all_labels: bool = False) -> tuple[dict, dict]:
    verified, status = dict(mapping), {}
    for label in mapping:
        if confidence[label] >= CONFIDENCE_THRESHOLD and not all_labels:
            status[label] = "confident"
            continue
        votes = Counter(a for a in answers.get(label, []) if a != "unclear")
        winner = next((int(a) - 1 for a, n in votes.most_common(1) if n >= AGREE), None)
        if winner is None or not 0 <= winner < people:
            status[label] = "flagged"
            continue
        taken = {face for other, face in verified.items() if other != label}
        if winner != mapping[label] and winner in taken:
            status[label] = "flagged"
            continue
        verified[label] = winner
        status[label] = "confirmed" if winner == mapping[label] else "moved"
    return verified, status


def build_cases(live: bool, only: str = "", all_labels: bool = False) -> tuple[list[dict], list[tuple]]:
    """Bind every window/source/repeat; return cases and (case, label, calls, video, start, seconds, taps, size) jobs."""
    jobs, cases = [], []
    for window, (run_dir, truth_dir) in WINDOWS.items():
        if only and (window.startswith(only[1:]) if only.startswith("!") else not window.startswith(only)):
            continue
        run, truth_dir = Path(run_dir), Path(truth_dir)
        doc = json.loads((run / "earshot.json").read_text())
        truth = json.loads((truth_dir / "truth.json").read_text())
        diarization = CallLog(run, replay=True)
        verify_calls = CallLog(run, replay=not live)
        tracks = Tracks.load(run / "tracks.json")
        motion = [head_motion(gray_frames(run / doc["video"]), tracks, p) for p in range(len(doc["people"]))]
        taps = [(p["tap"][0], p["tap"][1]) for p in doc["people"]]
        size = (doc["info"]["width"], doc["info"]["height"])
        sources = {
            "raw": (resample(read_audio(run / doc["video"], SEPARATION_SR), SEPARATION_SR, TRANSCRIBE_SR),
                    "bench repeat {i}: diarize the raw mix"),
            "delay_sum": (read_audio(run / doc["array"]["delay_sum"], TRANSCRIBE_SR),
                          "bench repeat {i}: diarize GCC-PHAT delay-and-sum 8-mic baseline"),
        }
        for source, (audio, purpose) in sources.items():
            for i in range(REPEATS):
                turns = transcribe(audio, diarization, purpose=purpose.format(i=i), repeat=i)
                mapping, confidence = attribute_with_confidence(turns, motion, doc["info"]["fps"])
                case = {"window": window, "source": source, "repeat": i, "doc": doc, "run": run, "truth": truth,
                        "truth_dir": truth_dir, "turns": turns, "mapping": mapping, "confidence": confidence,
                        "answers": {}, "all": all_labels}
                for label in mapping:
                    if confidence[label] >= CONFIDENCE_THRESHOLD and not all_labels:
                        continue
                    for start, seconds in clip_spans(turns, label):
                        jobs.append((case, label, verify_calls, run / doc["video"], start, seconds, taps, size))
                cases.append(case)

    return cases, jobs


def report(cases: list[dict], clips: int, out_path: Path) -> None:
    rows, by_window = [], {}
    for case in cases:
        names = [p["name"] for p in case["doc"]["people"]]
        verified, status = verify(case["mapping"], case["confidence"], case["answers"], len(names), case.get("all", False))
        oracle = oracle_speaker_mapping([{"speaker": t.speaker, "start": t.start, "end": t.end, "text": t.text}
                                         for t in case["turns"]], case["truth"]["people"])
        before = score_mapping(case["doc"], case["run"], case["truth"], case["truth_dir"], case["turns"],
                               case["mapping"], case["confidence"])
        after = score_mapping(case["doc"], case["run"], case["truth"], case["truth_dir"], case["turns"],
                              verified, case["confidence"])
        for label in case["mapping"]:
            if label not in oracle:
                continue
            rows.append({"window": case["window"], "source": case["source"], "repeat": case["repeat"],
                         "label": label, "status": status[label], "answers": case["answers"].get(label, []),
                         "before": names[case["mapping"][label]], "after": names[verified[label]],
                         "oracle": oracle[label]})
        by_window.setdefault(case["window"], {}).setdefault(case["source"], []).append(
            {"binding": before["binding"], "verified": after["binding"], "oracle": before["oracle"]})
    summary = {}
    for source in ("raw", "delay_sum"):
        subset = [r for r in rows if r["source"] == source]
        flagged = [r for r in subset if r["status"] != "confident"]
        summary[source] = {
            "flagged": len(flagged),
            "resolved": sum(r["status"] in ("confirmed", "moved") for r in flagged),
            "fixed": sum(r["before"] != r["oracle"] and r["after"] == r["oracle"] for r in subset),
            "broken": sum(r["before"] == r["oracle"] and r["after"] != r["oracle"] for r in subset),
            "wrong_before": sum(r["before"] != r["oracle"] for r in subset),
            "wrong_after": sum(r["after"] != r["oracle"] for r in subset),
            "answers": dict(Counter(a for r in flagged for a in r["answers"])),
        }
    out = {"summary": summary, "right_person": by_window, "rows": rows, "clips": clips}
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    for window, sources in by_window.items():
        for source, reps in sources.items():
            mean = lambda key: round(sum(r[key] for r in reps) / len(reps), 3)
            print(f"{window:28} {source:9} binding {mean('binding')} verified {mean('verified')} oracle {mean('oracle')}")



def main() -> None:
    cases, jobs = build_cases("--live" in sys.argv)
    unique = {}
    for case, label, calls, video, start, seconds, taps, size in jobs:
        clip = case["run"] / "calls" / "verify_clips" / f"{start:.2f}_{seconds:.2f}.mp4"
        if clip not in unique:
            unique[clip] = (calls, numbered_clip(video, start, seconds, taps, size, clip))
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = dict(zip(unique, pool.map(lambda item: ask_spark(*item), unique.values())))
    for case, label, calls, video, start, seconds, taps, size in jobs:
        clip = case["run"] / "calls" / "verify_clips" / f"{start:.2f}_{seconds:.2f}.mp4"
        case["answers"].setdefault(label, []).append(answers[clip])
    report(cases, len(unique), Path("review/spark_verify_probe.json"))


if __name__ == "__main__":
    main()
