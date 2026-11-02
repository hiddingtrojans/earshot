# Benchmark data

**No family, friends or private footage.** The benchmark uses the public AMI Meeting Corpus (CC BY 4.0): meeting ES2008a, 12:25–13:40, four people, far-field room mic, hand-made word timings. `tools/make_ami_clip.py` builds it (see the implementation pack, `04_DATA_AND_BENCHMARK.md`).

## Optional: composed clip of yourself (ground-truth audio)

Only if you want to appear. Film yourself twice in two different seats, ~20 s each, reading different lines, then:

```bash
python spike/earshot_spike.py compose --left take_left.mp4 --right take_right.mp4 --out bench/self_A1
```

That gives `mix.mov` plus `ref_left.wav` / `ref_right.wav`. Start the right-seat lines ~2 s after the left ones so they overlap.

**Left (start at 0 s):** "Did anyone book a table for Friday? I tried calling the restaurant but nobody picked up. Maybe we should just go to the usual place. Anyway, tell me what you think tonight."

**Right (start at 2 s):** "I booked it for eight already. They answered on the second try. The terrace was full, so we're inside. Bring a jacket, it gets cold after ten."
