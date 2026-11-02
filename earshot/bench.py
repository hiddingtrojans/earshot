"""Dinner Table Bench: score a run against ground truth. Deterministic.

Truth file (JSON):

    {
      "people": {"Ana": "what Ana said, as one text", "Raúl": "..."},   # required
      "reference_tracks": {"Ana": "ref_left.wav", "Raúl": "ref_right.wav"},  # optional (composed clips)
      "turns": [{"person": "Ana", "start": 0.5, "end": 3.0, "text": "..."}],  # optional timing
      "words": [{"person": "Ana", "start": 0.5, "end": 0.7, "text": "word"}]  # optional exact timing
    }

Word-level truth takes precedence and marks a word overlapping when its interval
intersects another person's word. If `words` and `turns` are missing but
`reference_tracks` are given, truth turns come from transcribing each clean track
on its own (what captions would show with no overlap at all), so overlap recall
measures how much of that Earshot recovers.

Metrics per person:
  wer                — word error rate of Earshot's captions vs that person's text
  attribution        — share of caption words that belong to that person's text
  overlap_recall     — share of words spoken while someone else was talking that
                       appear in that person's captions (needs turn timing)
  si_sdr_db          — separation quality of the isolated track (needs references)
Baseline = Voice Transcribe's single diarized stream of the mix, with each
anonymous speaker mapped to the person it matches best (an oracle mapping, so the
baseline is shown at its best).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .timeline import tokens


def align(hyp: list[str], ref: list[str]) -> tuple[int, int, list[int]]:
    """Returns (word edit distance, matched words, indexes of matched ref words).

    Edits come from Levenshtein distance (for WER); matched words from the
    longest common subsequence (for attribution and overlap recall).
    """
    n, m = len(hyp), len(ref)
    d = np.zeros((n + 1, m + 1), dtype=np.int32)
    d[:, 0] = np.arange(n + 1)
    d[0, :] = np.arange(m + 1)
    lcs = np.zeros((n + 1, m + 1), dtype=np.int32)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            same = hyp[i - 1] == ref[j - 1]
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (not same))
            lcs[i, j] = lcs[i - 1, j - 1] + 1 if same else max(lcs[i - 1, j], lcs[i, j - 1])
    i, j, matched = n, m, []
    while i > 0 and j > 0:
        if hyp[i - 1] == ref[j - 1]:
            matched.append(j - 1)
            i, j = i - 1, j - 1
        elif lcs[i - 1, j] >= lcs[i, j - 1]:
            i -= 1
        else:
            j -= 1
    return int(d[n, m]), len(matched), sorted(matched)


def wer(hyp: str, ref: str) -> float:
    r = tokens(ref)
    return align(tokens(hyp), r)[0] / max(1, len(r))


def person_scores(caption_text: str, truth_text: str, overlap_ref_idx: set[int] | None) -> dict:
    hyp, ref = tokens(caption_text), tokens(truth_text)
    edits, matches, matched = align(hyp, ref)
    out = {"words_truth": len(ref), "words_captioned": len(hyp),
           "wer": round(edits / max(1, len(ref)), 3),
           "attribution": round(matches / max(1, len(hyp)), 3)}
    if overlap_ref_idx:
        out["overlap_words"] = len(overlap_ref_idx)
        out["overlap_recall"] = round(len(overlap_ref_idx & set(matched)) / len(overlap_ref_idx), 3)
    return out


def overlap_word_indexes(turns: list[dict], person: str) -> set[int]:
    """Indexes (into the person's concatenated truth words) spoken during someone else's turn."""
    idx, out = 0, set()
    for t in sorted((t for t in turns if t["person"] == person), key=lambda t: t["start"]):
        ws = tokens(t["text"])
        others = [o for o in turns if o["person"] != person and o["end"] > t["start"] and o["start"] < t["end"]]
        for k in range(len(ws)):
            # word time by linear interpolation within the turn
            wt = t["start"] + (k + 0.5) * (t["end"] - t["start"]) / max(1, len(ws))
            if any(o["start"] <= wt <= o["end"] for o in others):
                out.add(idx + k)
        idx += len(ws)
    return out


def overlap_word_indexes_from_words(words: list[dict], person: str) -> set[int]:
    """Indexes into the person's truth text, using exact word-level overlap intervals."""
    out = set()
    index = 0
    own = sorted((word for word in words if word["person"] == person),
                 key=lambda word: (word["start"], word["end"], word["person"]))
    for word in own:
        size = len(tokens(word["text"]))
        overlaps = any(other["person"] != person and other["start"] < word["end"]
                       and other["end"] > word["start"] for other in words)
        if overlaps:
            out.update(range(index, index + size))
        index += size
    return out


def oracle_baseline_text(baseline: list[dict], truth: dict[str, str]) -> dict[str, str]:
    by_speaker: dict[str, list[str]] = {}
    for t in sorted(baseline, key=lambda t: t["start"]):
        by_speaker.setdefault(t["speaker"], []).append(t["text"])
    scores = {(spk, p): align(tokens(" ".join(txt)), tokens(truth[p]))[1]
              for spk, txt in by_speaker.items() for p in truth}
    mapping: dict[str, str] = {}
    for (spk, p), _ in sorted(scores.items(), key=lambda kv: -kv[1]):
        if spk not in mapping:
            mapping[spk] = p
    out = {p: [] for p in truth}
    for t in sorted(baseline, key=lambda t: t["start"]):
        out[mapping.get(t["speaker"], next(iter(truth)))].append(t["text"])
    return {p: " ".join(v) for p, v in out.items()}


def si_sdr(est: np.ndarray, ref: np.ndarray) -> float:
    n = min(est.size, ref.size)
    est, ref = est[:n] - est[:n].mean(), ref[:n] - ref[:n].mean()
    alpha = float(est @ ref) / (float(ref @ ref) + 1e-12)
    noise = est - alpha * ref
    return 10 * math.log10((alpha * alpha * float(ref @ ref) + 1e-12) / (float(noise @ noise) + 1e-12))


def score(run: Path, truth: dict, truth_dir: Path) -> dict:
    doc = json.loads((run / "earshot.json").read_text())
    return score_document(doc, run, truth, truth_dir)


def score_document(doc: dict, run: Path, truth: dict, truth_dir: Path) -> dict:
    names = [p["name"] for p in doc["people"]]
    people_truth: dict[str, str] = truth["people"]
    words = truth.get("words")
    turns = truth.get("turns")
    if words is None and turns is None and truth.get("reference_tracks"):
        turns = _turns_from_references(run, truth, truth_dir)
    caps = {n: " ".join(c["text"] for c in sorted(doc["captions"], key=lambda c: c["start"]) if c["name"] == n)
            for n in names}
    base = oracle_baseline_text(doc["baseline"], people_truth)
    result = {"run": str(run), "separator": doc["separator"], "people": {}}
    for n in people_truth:
        if words is not None:
            ov = overlap_word_indexes_from_words(words, n)
        else:
            ov = overlap_word_indexes(turns, n) if turns else None
        entry = {"earshot": person_scores(caps.get(n, ""), people_truth[n], ov),
                 "baseline": person_scores(base.get(n, ""), people_truth[n], ov)}
        ref_path = (truth.get("reference_tracks") or {}).get(n)
        person = next((p for p in doc["people"] if p["name"] == n), None)
        if ref_path and person and person.get("stem"):
            from .media import SEPARATION_SR, read_audio

            ref = read_audio(truth_dir / ref_path, SEPARATION_SR)
            entry["si_sdr_db"] = {"isolated": round(si_sdr(read_audio(run / person["stem"], SEPARATION_SR), ref), 2),
                                  "mixture": round(si_sdr(read_audio(run / doc["video"], SEPARATION_SR), ref), 2)}
        result["people"][n] = entry
    result["summary"] = _summary(result["people"])
    return result


def _turns_from_references(run: Path, truth: dict, truth_dir: Path) -> list[dict]:
    from .calls import CallLog
    from .media import TRANSCRIBE_SR, read_audio
    from .transcribe import transcribe

    calls = CallLog(run)
    out = []
    for name, path in truth["reference_tracks"].items():
        audio = read_audio(truth_dir / path, TRANSCRIBE_SR)
        for t in transcribe(audio, calls, purpose=f"bench: transcribe {name}'s clean reference track"):
            out.append({"person": name, "start": t.start, "end": t.end, "text": t.text})
    return out


def _summary(people: dict) -> dict:
    def mean(system: str, key: str):
        vals = [p[system][key] for p in people.values() if key in p[system]]
        return round(sum(vals) / len(vals), 3) if vals else None

    summary = {system: {k: mean(system, k) for k in ("wer", "attribution", "overlap_recall")}
               for system in ("earshot", "baseline")}
    gains = [p["si_sdr_db"]["isolated"] - p["si_sdr_db"]["mixture"]
             for p in people.values() if "si_sdr_db" in p]
    if gains:
        summary["si_sdr_gain_db"] = round(sum(gains) / len(gains), 3)
    return summary


def _score_repeats(run: Path, truth: dict, truth_dir: Path, count: int) -> list[dict]:
    from copy import deepcopy

    from .activity import overlap_windows, speech_segments
    from .calls import CallLog
    from .media import SEPARATION_SR, TRANSCRIBE_SR, read_audio, resample
    from .timeline import build_captions
    from .transcribe import Turn, transcribe

    doc = json.loads((run / "earshot.json").read_text())
    names = [person["name"] for person in doc["people"]]
    calls = CallLog(run)
    mixture = read_audio(run / doc["video"], SEPARATION_SR)
    mix24 = resample(mixture, SEPARATION_SR, TRANSCRIBE_SR)
    lite = "Earshot-Lite" in doc["separator"]
    if lite:
        from .lite import attribute_turns, gray_frames, head_motion
        from .tracking import Tracks

        tracks = Tracks.load(run / "tracks.json")
        frames = gray_frames(run / doc["video"])
        motion = [head_motion(frames, tracks, person) for person in range(len(names))]
        isolated = []
    else:
        if not all(person.get("stem") for person in doc["people"]):
            raise ValueError("repeats need either an Earshot-Lite run or isolated stems for every person")
        isolated = [read_audio(run / person["stem"], SEPARATION_SR) for person in doc["people"]]
        activity = [speech_segments(resample(audio, SEPARATION_SR, 16_000), 16_000) for audio in isolated]

    results = []
    for index in range(count):
        baseline = transcribe(mix24, calls, purpose=f"bench repeat {index}: diarize the raw mix", repeat=index)
        if lite:
            mapping = attribute_turns(baseline, motion, doc["info"]["fps"])
            turns = [[Turn(str(person), turn.start, turn.end, turn.text) for turn in baseline
                      if mapping.get(turn.speaker) == person] for person in range(len(names))]
            activity = [[(turn.start, turn.end) for turn in person_turns] for person_turns in turns]
        else:
            turns = [transcribe(resample(audio, SEPARATION_SR, TRANSCRIBE_SR), calls,
                                purpose=f"bench repeat {index}: transcribe {name}'s isolated voice", repeat=index)
                     for name, audio in zip(names, isolated)]
        captions = build_captions(names, turns, activity)
        repeated = deepcopy(doc)
        repeated["baseline"] = [{"speaker": turn.speaker, "start": turn.start, "end": turn.end, "text": turn.text}
                                for turn in baseline]
        repeated["captions"] = [caption.to_json() for caption in captions]
        repeated["activity"] = activity
        repeated["overlaps"] = overlap_windows(activity)
        repeated["threads"] = []
        repeated["catchups"] = []
        results.append(score_document(repeated, run, truth, truth_dir))
    return results


def _spread(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"mean": round(sum(values) / len(values), 3),
            "min": round(min(values), 3), "max": round(max(values), 3)}


def _repeat_summary(repeats: list[dict]) -> dict:
    summary = {}
    for system in ("earshot", "baseline"):
        summary[system] = {}
        for key in ("wer", "attribution", "overlap_recall"):
            values = [repeat["summary"][system][key] for repeat in repeats
                      if repeat["summary"][system][key] is not None]
            summary[system][key] = _spread(values)
    gains = [repeat["summary"]["si_sdr_gain_db"] for repeat in repeats
             if "si_sdr_gain_db" in repeat["summary"]]
    if gains:
        summary["si_sdr_gain_db"] = _spread(gains)
    return summary


def run_bench(run: Path, truth_path: Path, out: Path | None = None, repeat: int | None = None) -> dict:
    truth = json.loads(truth_path.read_text())
    if repeat is not None:
        if repeat < 1:
            raise ValueError("--repeat must be at least 1")
        repeats = _score_repeats(run, truth, truth_path.parent, repeat)
        res = {"run": str(run), "separator": repeats[0]["separator"], "repeat_count": repeat,
               "repeats": repeats, "summary": _repeat_summary(repeats)}
    else:
        res = score(run, truth, truth_path.parent)
    out = out or (run / "bench.json")
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    s = res["summary"]
    print(f"{'':16}{'Earshot':>22}{'Single stream':>22}")
    for k, label in (("wer", "Word error rate"), ("attribution", "Right person"), ("overlap_recall", "Overlap words")):
        e, b = s["earshot"][k], s["baseline"][k]
        if e is None:
            continue
        if repeat is not None:
            print(f"{label:16}{e['mean']:>10.3f} [{e['min']:.3f}, {e['max']:.3f}]"
                  f"{b['mean']:>12.3f} [{b['min']:.3f}, {b['max']:.3f}]")
        else:
            print(f"{label:16}{e:>22.3f}{b:>22.3f}")
    if "si_sdr_gain_db" in s:
        gain = s["si_sdr_gain_db"]
        if repeat is not None:
            print(f"SI-SDR gain dB {gain['mean']:.3f} [{gain['min']:.3f}, {gain['max']:.3f}]")
        else:
            print(f"SI-SDR gain dB {gain:.3f}")
    print(f"wrote {out}")
    return res
