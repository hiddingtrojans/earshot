# Does the low-confidence flag catch wrong bindings?

Run 2026-11-04 19:33 CET, cache-only (`EARSHOT_REPLAY=1`), `python -m tools.flag_coverage` → `review/flag_coverage.json`. Every window here has now been seen (ES2008a 745/635 s, ES2008b 150 s, ES2008c 355 s), so this is **exploratory**. No threshold was changed: flag = binding confidence < 0.15.

A binding is wrong when the diarized label is assigned to a different face than the hand-matched (oracle) mapping on the same diarization. Labels the oracle leaves unmatched are excluded.

| Input | Bindings | Wrong | Wrong and flagged | Right but flagged |
|---|---:|---:|---:|---:|
| Raw single far-field mic | 38 | 11 | 8 | 11 |
| Delay-and-sum 8-mic array | 37 | 2 | **2** | 16 |

- On array input, **both** wrong bindings were flagged; no error was silent. Both are the same ES2008c label, where one voice covers ~65 of 75 s and its mouth-motion correlation has little on/off contrast.
- On the single mic, 3 of 11 errors were confident and unflagged (0.256, 0.269 and 0.235).
- The flag is cautious: it also fires on 16 of 35 correct array bindings, so a person confirming flags would review about half the labels.
