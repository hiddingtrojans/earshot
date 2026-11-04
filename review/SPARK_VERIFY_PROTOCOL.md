# Can Muse Spark confirm flagged bindings instead of a human tap?

Written 2026-11-04 shortly before 19:45 CET, before any Spark verifier call. Committed before the run.

## Motivation

`review/FLAG_COVERAGE.md`: on array input every wrong binding was flagged, but so were 16 of 35 correct ones. A person confirming flags reviews about half the labels. If Muse Spark can watch short clips and say whose mouth is moving, it could resolve flags without a human.

## Method (`tools/spark_verify_probe.py`)

- Runs **only on flagged labels** (binding confidence < 0.15, unchanged). Confident bindings are never touched.
- For each flagged diarized label, up to 3 of that label's own turns that overlap no other label's turn and last ≥ 1.5 s (longest first). Each becomes a **muted** clip of at most 2.5 s from the middle of the turn, with large numbers 1–4 burned in at each person's tap position. Only runtime information picks the clips; truth is never used.
- `muse-spark-1.3`, low reasoning, strict JSON schema with an enum: `"1"`–`"4"` or `"unclear"`. The prompt asks which numbered person's mouth is moving.
- Decision in code: if at least 2 clips name the same person, the label moves to that person (or stays, if that is already its binding) and is marked **confirmed**. Otherwise it stays as bound and **flagged** for a human. If a move would put two labels on one face, the label stays as bound and flagged.

## Data

All four existing windows (ES2008a 745/635 s, ES2008b 150 s, ES2008c 355 s), raw and delay-and-sum inputs, the same three cached diarization repeats. Every window has been seen, so this is **exploratory**. A claim would need a held-out meeting.

## Pass rule (frozen)

Exploratory PASS only if all hold:

1. Delay-and-sum: fixes at least 1 of the 2 wrong bindings and makes no correct binding wrong.
2. Raw: fixes more wrong bindings than it breaks.
3. At least half of all flagged labels end up confirmed, i.e. no longer need a human.

Otherwise FAIL, reported in the README.
