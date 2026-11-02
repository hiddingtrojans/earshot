# Dinner Table Bench — recording scripts

Short scripted conversations with **planned overlaps**, so we know exactly what each person said. Read naturally, and start your line where the script says even if the other person hasn't finished. That overlap is the point.

Recording setup: phone in landscape on the table or propped at eye level, everyone's face visible, 1–2 m away, normal room noise (TV low is fine). Everyone in the recording agrees to it.

Save each person's lines as plain text in a truth file (see `truth_template.json`).

## Set A: composed (ground truth audio; can be recorded alone)

Record each part **separately** in its own seat, as two videos of ~20 s. Then:

```bash
python spike/earshot_spike.py compose --left a_left.mp4 --right a_right.mp4 --out bench/A1
```

That gives `mix.mov` plus `ref_left.wav` / `ref_right.wav`. Each person starts their first line at the second shown.

**Left (start at 0 s):** "Did anyone book a table for Friday? I tried calling Casa Lola but nobody picked up. Maybe we should just go to the usual place. Anyway, tell me what you think tonight."

**Right (start at 2 s):** "I booked Casa Lola for eight already. They answered on the second try. The terrace was full, so we're inside. Bring a jacket, it gets cold after ten."

## Set B: real table, two people

**Ana:** Did anyone book a table for Friday?
**Raúl** *(starts before Ana finishes)*: I booked Casa Lola for eight.
**Ana:** Great, is Marta coming too?
**Raúl** *(changes topic, over Ana)*: The dog ate my shoe again this morning.
**Ana** *(over Raúl)*: Wait, which shoe, the new ones?
**Raúl:** Yes, the blue ones from Saturday.
**Ana:** Okay, so Friday at eight then.

## Set C: real table, three people, two conversations at once

**Ana & Raúl** talk about the trip while **Marta** talks to Raúl about the dog; at least three lines from different conversations overlap.

**Ana:** So are we taking the train or driving to Valencia?
**Marta** *(at the same time, to Raúl)*: Did you take Toby to the vet in the end?
**Raúl** *(to Ana)*: Train, it's two hours and we can sleep.
**Raúl** *(to Marta, straight after)*: Yes, he's fine, it was just a splinter.
**Ana:** Then I'll buy the tickets tonight, the nine o'clock one.
**Marta** *(over Ana)*: Poor thing, he was limping all week.
**Ana:** Marta, are you coming with us or not?
**Marta:** Only if we're back by Sunday night.
