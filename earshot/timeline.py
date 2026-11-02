"""Merge per-person transcripts into one caption timeline. Deterministic.

Two jobs:
* drop *bleed*: words from person B that leak faintly into person A's isolated
  track get transcribed in A's track too. A turn is kept only if its own track
  is active for enough of it, and when the same words appear in two tracks at
  the same time, only the track where that person is clearly speaking keeps them;
* flag *overlap*: a caption overlaps when someone else is speaking during it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .activity import Segment, active_fraction
from .transcribe import Turn

MIN_OWN_ACTIVITY = 0.25  # fraction of a turn its own track must be active
OVERLAP_ACTIVITY = 0.20  # someone else active for this fraction => overlap
DUPLICATE_JACCARD = 0.5


@dataclass
class Caption:
    id: str
    person: int
    name: str
    start: float
    end: float
    text: str
    overlap: bool = False
    overlap_with: list[int] = field(default_factory=list)
    own_activity: float = 1.0
    thread: int | None = None

    def to_json(self) -> dict:
        return asdict(self)


def tokens(text: str) -> list[str]:
    return re.findall(r"[\w']+", text.lower())


def jaccard(a: str, b: str) -> float:
    sa, sb = set(tokens(a)), set(tokens(b))
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def time_overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def build_captions(names: list[str], turns: list[list[Turn]], activity: list[list[Segment]]) -> list[Caption]:
    candidates: list[Caption] = []
    for person, person_turns in enumerate(turns):
        for t in person_turns:
            own = active_fraction(activity[person], t.start, t.end)
            if own < MIN_OWN_ACTIVITY:
                continue  # faint bleed or a hallucinated turn on a quiet track
            candidates.append(Caption("", person, names[person], t.start, t.end, t.text, own_activity=round(own, 3)))

    # Same words at the same time in two tracks: keep the more active one.
    dropped: set[int] = set()
    for i, a in enumerate(candidates):
        for j in range(i + 1, len(candidates)):
            b = candidates[j]
            if a.person == b.person or i in dropped or j in dropped:
                continue
            shorter = min(a.end - a.start, b.end - b.start)
            if shorter <= 0 or time_overlap(a.start, a.end, b.start, b.end) < 0.5 * shorter:
                continue
            if jaccard(a.text, b.text) >= DUPLICATE_JACCARD:
                dropped.add(j if a.own_activity >= b.own_activity else i)
    kept = sorted((c for k, c in enumerate(candidates) if k not in dropped), key=lambda c: (c.start, c.person))

    for n, c in enumerate(kept, start=1):
        c.id = f"c{n:03d}"
        others = [q for q in range(len(names))
                  if q != c.person and active_fraction(activity[q], c.start, c.end) >= OVERLAP_ACTIVITY]
        c.overlap, c.overlap_with = bool(others), others
    return kept


def captions_in_window(captions: list[Caption], t0: float, t1: float) -> list[Caption]:
    return [c for c in captions if c.end > t0 and c.start < t1]
