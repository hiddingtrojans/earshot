"""Export per-person captions as positioned WebVTT and labelled SRT."""

from __future__ import annotations

import html
import json
from pathlib import Path


def timestamp(seconds: float, srt: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    separator = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{milliseconds:03d}"


def anchor_at(doc: dict, person: int, time: float) -> tuple[float, float]:
    anchors = doc["people"][person].get("anchors") or []
    fallback = ((person + 0.5) / len(doc["people"]), 0.35)
    if not anchors:
        return fallback
    if time <= anchors[0][0]:
        return tuple(anchors[0][1:]) if anchors[0][0] - time < 0.5 else fallback
    if time >= anchors[-1][0]:
        return tuple(anchors[-1][1:]) if time - anchors[-1][0] < 0.5 else fallback
    for before, after in zip(anchors, anchors[1:]):
        if before[0] <= time <= after[0]:
            if after[0] - before[0] > 1.0:
                return fallback
            fraction = (time - before[0]) / (after[0] - before[0] or 1)
            return (before[1] + (after[1] - before[1]) * fraction,
                    before[2] + (after[2] - before[2]) * fraction)
    return fallback


def clean_text(value: object) -> str:
    return html.escape(" ".join(str(value).split()), quote=False)


def vtt(doc: dict) -> str:
    lines = ["WEBVTT", "", "STYLE"]
    for index, person in enumerate(doc["people"]):
        lines.append(f"::cue(.spk{index}) {{ color: {person['color']}; }}")
    lines.append("")
    for caption in sorted(doc["captions"], key=lambda item: (item["start"], item["person"])):
        person_index = caption["person"]
        person = doc["people"][person_index]
        x, y = anchor_at(doc, person_index, caption["start"])
        position = round(min(95.0, max(5.0, x * 100)))
        line = round(min(95.0, max(5.0, y * 100)))
        start, end = caption["start"], max(caption["end"], caption["start"] + 0.001)
        lines += [
            f"{timestamp(start)} --> {timestamp(end)} line:{line}% position:{position}% align:middle size:45%",
            f"<c.spk{person_index}><v {clean_text(person['name'])}>{clean_text(caption['text'])}</v></c>",
            "",
        ]
    return "\n".join(lines)


def srt(doc: dict) -> str:
    blocks = []
    captions = sorted(doc["captions"], key=lambda item: (item["start"], item["person"]))
    for index, caption in enumerate(captions, start=1):
        name = " ".join(str(doc["people"][caption["person"]]["name"]).split())
        text = " ".join(str(caption["text"]).split())
        start, end = caption["start"], max(caption["end"], caption["start"] + 0.001)
        blocks.append(f"{index}\n{timestamp(start, True)} --> {timestamp(end, True)}\n"
                      f"[{name}] {text}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def export(run: Path, vtt_path: Path | None = None, srt_path: Path | None = None) -> None:
    doc = json.loads((run / "earshot.json").read_text())
    if vtt_path:
        vtt_path.write_text(vtt(doc))
        print(f"wrote {vtt_path}")
    if srt_path:
        srt_path.write_text(srt(doc))
        print(f"wrote {srt_path}")
