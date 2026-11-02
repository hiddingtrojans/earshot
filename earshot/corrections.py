"""User-confirmed voice-to-face corrections with immediate replay updates."""

from __future__ import annotations

import math

from .lite import CONFIDENCE_THRESHOLD


def nearest_person(doc: dict, x: float, y: float, exclude: int) -> tuple[int, float]:
    candidates = []
    for index, person in enumerate(doc["people"]):
        if index == exclude:
            continue
        px, py, _ = person["tap"]
        candidates.append((math.hypot(x - px, y - py), index))
    return min(candidates)


def apply_correction(doc: dict, from_person: int, to_person: int, x: float, y: float, frame: int) -> dict:
    correction = {"from": from_person, "to": to_person, "tap": [x, y, frame]}
    target_name = doc["people"][to_person]["name"]
    for caption in doc["captions"]:
        if caption["person"] == from_person:
            caption["person"] = to_person
            caption["name"] = target_name
    if doc.get("activity"):
        doc["activity"][to_person].extend(doc["activity"][from_person])
        doc["activity"][from_person] = []
    attribution = doc.get("attribution") or {}
    for label, person in list((attribution.get("mapping") or {}).items()):
        if person == from_person:
            attribution["mapping"][label] = to_person
    for label in list((attribution.get("confidence") or {}).keys()):
        attribution["confidence"][label] = 1.0
    doc.setdefault("corrections", []).append(correction)
    return correction


def taps_to_oracle(mapping: dict[str, int], confidence: dict[str, float],
                   oracle: dict[str, str], names: list[str]) -> dict:
    indexes = {name: index for index, name in enumerate(names)}
    mismatches = [label for label, person in oracle.items() if mapping.get(label) != indexes[person]]
    return {
        "taps": len(mismatches),
        "low_confidence": [label for label in mismatches if confidence.get(label, 0.0) < CONFIDENCE_THRESHOLD],
    }


def apply_saved_corrections(doc: dict) -> None:
    for correction in list(doc.get("corrections", [])):
        x, y, frame = correction["tap"]
        apply_correction(doc, correction["from"], correction["to"], x, y, frame)
    doc["corrections"] = []
