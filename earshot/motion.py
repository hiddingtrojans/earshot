"""Fixed-threshold mouth-motion activity for array guides and Lite overlap estimates."""

from __future__ import annotations

import numpy as np

from .transcribe import Turn

MOTION_NOISE_FLOOR = 0.1
MOTION_MAD_MULTIPLIER = 3.0
MOTION_SMOOTH_SECONDS = 0.5
MIN_EVENT_SECONDS = 0.5


def interval_mask(segments: list[tuple[float, float]], frames: int, fps: float) -> np.ndarray:
    mask = np.zeros(frames, dtype=bool)
    for start, end in segments:
        first = max(0, int(round(start * fps)))
        last = min(frames, max(first + 1, int(round(end * fps))))
        mask[first:last] = True
    return mask


def turns_mask(turns: list[Turn], frames: int, fps: float) -> np.ndarray:
    return interval_mask([(turn.start, turn.end) for turn in turns], frames, fps)


def motion_activity(motion: np.ndarray, fps: float) -> tuple[np.ndarray, float | None]:
    from scipy.ndimage import uniform_filter1d

    values = np.asarray(motion, dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros(values.size, dtype=bool), None
    median = float(np.median(np.abs(values[finite])))
    mad = float(np.median(np.abs(values[finite] - median)))
    threshold = max(MOTION_NOISE_FLOOR, median + MOTION_MAD_MULTIPLIER * mad)
    smoothed = uniform_filter1d(np.nan_to_num(values, nan=0.0),
                                size=max(1, int(round(MOTION_SMOOTH_SECONDS * fps))), mode="nearest")
    return smoothed >= threshold, threshold


def events_from_mask(mask: np.ndarray, fps: float,
                     minimum: float = MIN_EVENT_SECONDS) -> list[tuple[float, float]]:
    indices = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    return [(start / fps, end / fps) for start, end in zip(indices[::2], indices[1::2])
            if end - start >= minimum * fps]


def guide_activities(turns: list[list[Turn]], motion: list[np.ndarray], fps: float,
                     frames: int) -> tuple[list[np.ndarray], dict]:
    other_turns = [turns_mask(person_turns, frames, fps) for person_turns in turns]
    guides, thresholds, fallbacks = [], {}, []
    for person, person_turns in enumerate(turns):
        others = np.any([mask for index, mask in enumerate(other_turns) if index != person], axis=0)
        if person_turns:
            guide = other_turns[person] & ~others
        else:
            activity, threshold = motion_activity(motion[person], fps)
            guide = activity & ~others
            thresholds[str(person)] = threshold
            fallbacks.append(person)
        guides.append(guide)
    return guides, {"motion_thresholds": thresholds, "motion_fallback_people": fallbacks}


def talked_over(captions, turns: list[list[Turn]], motion: list[np.ndarray], fps: float) -> dict:
    if not captions:
        return {}, {}
    frames = max(1, max(values.size for values in motion))
    activity_info = [motion_activity(values, fps) for values in motion]
    activities = [activity for activity, _ in activity_info]
    thresholds = [threshold for _, threshold in activity_info]
    markers = {}
    for caption in captions:
        target = turns_mask(turns[caption.person], frames, fps)
        for other, activity in enumerate(activities):
            if other == caption.person:
                continue
            for start, end in events_from_mask(target & activity, fps):
                left, right = max(start, caption.start), min(end, caption.end)
                if right - left >= MIN_EVENT_SECONDS:
                    markers.setdefault(caption.id, []).append({
                        "person": other, "start": round(left, 3), "end": round(right, 3),
                    })
    return markers, {str(person): threshold for person, threshold in enumerate(thresholds)}


def truth_overlap_mask(words: list[dict], person: str, frames: int, fps: float) -> np.ndarray:
    own = interval_mask([(word["start"], word["end"]) for word in words if word["person"] == person], frames, fps)
    others = interval_mask([(word["start"], word["end"]) for word in words if word["person"] != person], frames, fps)
    return own & others


def overlap_metrics(turns: list[list[Turn]], motion: list[np.ndarray], words: list[dict],
                    names: list[str], fps: float) -> dict:
    frames = max(int(np.ceil(max(word["end"] for word in words) * fps)),
                 max(values.size for values in motion), 1)
    motion_masks = []
    for values in motion:
        activity, _ = motion_activity(values, fps)
        activity = np.pad(activity, (0, max(0, frames - activity.size)))[:frames]
        motion_masks.append(activity)
    per_person = {}
    totals = np.zeros(3, dtype=np.int64)
    for person, name in enumerate(names):
        others = np.any([mask for index, mask in enumerate(motion_masks) if index != person], axis=0)
        predicted = turns_mask(turns[person], frames, fps) & others
        predicted = interval_mask(events_from_mask(predicted, fps), frames, fps)
        truth = truth_overlap_mask(words, name, frames, fps)
        true_positive = int(np.count_nonzero(predicted & truth))
        predicted_count, truth_count = int(predicted.sum()), int(truth.sum())
        totals += [true_positive, predicted_count, truth_count]
        per_person[name] = {
            "precision": round(true_positive / predicted_count, 4) if predicted_count else None,
            "recall": round(true_positive / truth_count, 4) if truth_count else None,
            "predicted_frames": predicted_count, "truth_frames": truth_count,
        }
    true_positive, predicted_count, truth_count = totals
    return {
        "frame_rate": fps, "frame_precision": "40 ms frames at 25 fps",
        "precision": round(float(true_positive / predicted_count), 4) if predicted_count else None,
        "recall": round(float(true_positive / truth_count), 4) if truth_count else None,
        "true_positive_frames": int(true_positive),
        "predicted_frames": int(predicted_count), "truth_frames": int(truth_count),
        "per_person": per_person,
    }
