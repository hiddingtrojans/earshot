# 10 — Organizers' ruling on SAM Audio and T5 (2 Nov 2026), which overrides older docs
Thread: https://discord.com/channels/1557169028080869426/1564043204725182484/threads/1566631376868876419
Ruling (Cerebral Valley bot, 2 Nov 06:06 Madrid): "SAM Audio is an open-source Meta model, so it counts as a Meta model however you run it, and the frozen T5-base encoder inside it is fine with no workaround or precomputation needed. Organizers have ruled that open-source non-Meta models can run alongside Meta's models as long as Meta's models do real work; disclose the T5 encoder in your README and demo. Closed third-party AI models are still not allowed."

What changes:
1. T5 is no longer a compliance problem. --allow-t5 is allowed. Older lines saying "never use --allow-t5", "no Google T5 at runtime" or "T5 not loaded" as a requirement no longer apply.
2. The default stays the precomputed assets/text_features.npz. New check in T3: run the spike on the same 10 s twice with the same seed, once with the default and once with --allow-t5, and report the SI-SDR of one output against the other. If it's below 30 dB, make --allow-t5 the default and record why.
3. Disclosure is required. README models table: add the row "T5-base text encoder (Google, open source, Apache-2.0), part of SAM Audio's text conditioning. Earshot ships its output for the two fixed prompts as constants (assets/text_features.npz), or runs it locally with --allow-t5." Replace the README paragraph that says the bot ruled T5 out with the ruling above, plus the link and date. Demo video: on-screen line "SAM Audio includes a frozen Google T5-base text encoder (open source). Allowed by the organizers; disclosed in the README."
4. Update the wording, not the behaviour, of: the --allow-t5 help text in earshot/cli.py, the docstring and error message in earshot/separation.py, the report note in spike/earshot_spike.py (around line 418), and the Status paragraph in assets/README.md.
5. Everything else stays Meta-only. Don't use the new allowance for anything besides T5: no Whisper, pyannote, Silero, speechbrain, CLAP, OCR, NER, sentence-transformers or non-Meta TTS.
6. SAM Audio's re-rankers and span predictor stay off (reranking_candidates=1, predict_spans=False). That's now for speed, and because CLAP isn't Meta.
7. Lite is no longer the T5 fallback. It's only the fallback if separation fails the T3 go/no-go.
