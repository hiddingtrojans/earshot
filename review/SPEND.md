# Estimated Meta API spend

Run cap: **$20.00**. **Running total: $4.115609.**

Generated from `cache=miss` rows in the supplied run folders. Cache hits and local models add $0. Prices: SAM $0.20/1,000 processed video frames; Voice $0.18/audio hour; Spark $1.25/1M uncached input, $0.15/1M cached input, and $4.25/1M output tokens. Unknown hosted models are an error, not a zero.

| Run | Model | Purpose | Actual usage | Estimated USD |
|---|---|---|---|---:|
| runs/live_smoke | `files` | upload analysis video | file upload | $0.000000 |
| runs/live_smoke | `sam-3.1` | track tapped people | 252 video frames | $0.050400 |
| runs/live_smoke | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 10.080 audio seconds | $0.000504 |
| runs/live_smoke | `muse-spark-1.3` | split conversation into threads | 267 uncached + 0 cached input; 439 output tokens | $0.002200 |
| runs/live_smoke | `muse-spark-1.3` | what did I miss: the table | 226 uncached + 0 cached input; 587 output tokens | $0.002777 |
| runs/ami_lite | `files` | upload analysis video | file upload | $0.000000 |
| runs/ami_lite | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_lite | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/ami_lite | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 928 output tokens | $0.004629 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 242 uncached + 0 cached input; 479 output tokens | $0.002338 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker A | 190 uncached + 0 cached input; 443 output tokens | $0.002120 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker C | 206 uncached + 0 cached input; 588 output tokens | $0.002756 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 330 uncached + 0 cached input; 540 output tokens | $0.002707 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker D | 241 uncached + 0 cached input; 433 output tokens | $0.002142 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 487 output tokens | $0.002456 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker B | 71 uncached + 113 cached input; 351 output tokens | $0.001597 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 594 output tokens | $0.002932 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker B | 110 uncached + 113 cached input; 505 output tokens | $0.002301 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker D | 257 uncached + 0 cached input; 828 output tokens | $0.003840 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 369 uncached + 0 cached input; 592 output tokens | $0.002977 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker B | 248 uncached + 0 cached input; 661 output tokens | $0.003119 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker D | 275 uncached + 0 cached input; 651 output tokens | $0.003110 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 601 output tokens | $0.002932 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker D | 208 uncached + 0 cached input; 623 output tokens | $0.002908 |
| runs/ami_lite | `muse-voice-transcribe-1.0` | bench repeat 0: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_lite | `muse-voice-transcribe-1.0` | bench repeat 1: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_lite | `muse-voice-transcribe-1.0` | bench repeat 2: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_lite | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 802 output tokens | $0.004093 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 129 uncached + 113 cached input; 592 output tokens | $0.002694 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker C | 190 uncached + 0 cached input; 453 output tokens | $0.002163 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker D | 206 uncached + 0 cached input; 611 output tokens | $0.002854 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 217 uncached + 113 cached input; 505 output tokens | $0.002434 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker A | 241 uncached + 0 cached input; 458 output tokens | $0.002248 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 498 output tokens | $0.002503 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 473 output tokens | $0.002418 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker A | 257 uncached + 0 cached input; 612 output tokens | $0.002922 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 256 uncached + 113 cached input; 668 output tokens | $0.003176 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker A | 162 uncached + 113 cached input; 782 output tokens | $0.003543 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 582 output tokens | $0.002851 |
| runs/ami_lite | `muse-spark-1.3` | what did I miss: Speaker A | 95 uncached + 113 cached input; 585 output tokens | $0.002622 |
| runs/ami_lite | `muse-spark-1.3` | translate captions to es | 473 uncached + 0 cached input; 987 output tokens | $0.004786 |
| runs/ami_lite | `muse-spark-1.3` | translate captions to es | 492 uncached + 0 cached input; 1023 output tokens | $0.004963 |
| runs/ami_lite | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 738 output tokens | $0.003821 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker B | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker D | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker A | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker C | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker A | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker C | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker A | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker C | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ami_lite | `muse-glimmer` | what did I miss: Speaker A | local/cached | $0.000000 |
| runs/ami_lite | `muse-spark-1.3` | translate captions to es | 492 uncached + 0 cached input; 1094 output tokens | $0.005265 |
| runs/ami_lite_635 | `files` | upload analysis video | file upload | $0.000000 |
| runs/ami_lite_635 | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_lite_635 | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/ami_lite_635 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_lite_635 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_lite_635 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_negative | `files` | upload analysis video | file upload | $0.000000 |
| runs/ami_negative | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_negative | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/ui_live | `files` | upload analysis video | file upload | $0.000000 |
| runs/ui_live | `sam-3.1` | track tapped people | 252 video frames | $0.050400 |
| runs/ui_live | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 10.080 audio seconds | $0.000504 |
| runs/ui_live | `muse-spark-1.3` | split conversation into threads | 265 uncached + 0 cached input; 406 output tokens | $0.002057 |
| runs/ui_live | `muse-spark-1.3` | what did I miss: the table | 224 uncached + 0 cached input; 694 output tokens | $0.003230 |
| runs/ui_live | `muse-spark-1.3` | what did I miss: Speaker A | 176 uncached + 0 cached input; 562 output tokens | $0.002609 |
| runs/ui_live | `muse-spark-1.3` | what did I miss: Speaker B | 202 uncached + 0 cached input; 548 output tokens | $0.002582 |
| runs/ui_live | `muse-glimmer` | what did I miss: the table | local/cached | $0.000000 |
| runs/ui_live | `muse-glimmer` | what did I miss: Speaker A | local/cached | $0.000000 |
| runs/ui_live | `muse-glimmer` | what did I miss: Speaker B | local/cached | $0.000000 |
| runs/ami_samaudio | `files` | upload analysis video | file upload | $0.000000 |
| runs/ami_samaudio | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 928 output tokens | $0.004629 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 242 uncached + 0 cached input; 479 output tokens | $0.002338 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 190 uncached + 0 cached input; 443 output tokens | $0.002120 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker C | 206 uncached + 0 cached input; 588 output tokens | $0.002756 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 330 uncached + 0 cached input; 540 output tokens | $0.002707 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 241 uncached + 0 cached input; 433 output tokens | $0.002142 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 487 output tokens | $0.002456 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker B | 71 uncached + 113 cached input; 351 output tokens | $0.001597 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 594 output tokens | $0.002932 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker B | 110 uncached + 113 cached input; 505 output tokens | $0.002301 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 257 uncached + 0 cached input; 828 output tokens | $0.003840 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 369 uncached + 0 cached input; 592 output tokens | $0.002977 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker B | 248 uncached + 0 cached input; 661 output tokens | $0.003119 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 275 uncached + 0 cached input; 651 output tokens | $0.003110 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 601 output tokens | $0.002932 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 208 uncached + 0 cached input; 623 output tokens | $0.002908 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 0: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 1: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 2: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 802 output tokens | $0.004093 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 129 uncached + 113 cached input; 592 output tokens | $0.002694 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker C | 190 uncached + 0 cached input; 453 output tokens | $0.002163 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 206 uncached + 0 cached input; 611 output tokens | $0.002854 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 217 uncached + 113 cached input; 505 output tokens | $0.002434 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 241 uncached + 0 cached input; 458 output tokens | $0.002248 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 498 output tokens | $0.002503 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 473 output tokens | $0.002418 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 257 uncached + 0 cached input; 612 output tokens | $0.002922 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 256 uncached + 113 cached input; 668 output tokens | $0.003176 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 162 uncached + 113 cached input; 782 output tokens | $0.003543 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 582 output tokens | $0.002851 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 95 uncached + 113 cached input; 585 output tokens | $0.002622 |
| runs/ami_samaudio | `muse-spark-1.3` | translate captions to es | 473 uncached + 0 cached input; 987 output tokens | $0.004786 |
| runs/ami_samaudio | `muse-spark-1.3` | translate captions to es | 492 uncached + 0 cached input; 1023 output tokens | $0.004963 |
| runs/ami_samaudio | `facebook/sam-audio-small-tv` | isolate Speaker A's voice | local/cached | $0.000000 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `facebook/sam-audio-small-tv` | isolate Speaker B's voice | local/cached | $0.000000 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `facebook/sam-audio-small-tv` | isolate Speaker C's voice | local/cached | $0.000000 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `facebook/sam-audio-small-tv` | isolate Speaker D's voice | local/cached | $0.000000 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-spark-1.3` | split conversation into threads | 451 uncached + 0 cached input; 840 output tokens | $0.004134 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 277 uncached + 0 cached input; 590 output tokens | $0.002854 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 243 uncached + 0 cached input; 526 output tokens | $0.002539 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker B | 174 uncached + 0 cached input; 466 output tokens | $0.002198 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker C | 167 uncached + 0 cached input; 394 output tokens | $0.001883 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 345 uncached + 0 cached input; 758 output tokens | $0.003653 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 197 uncached + 113 cached input; 644 output tokens | $0.003000 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 325 uncached + 0 cached input; 792 output tokens | $0.003772 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 289 uncached + 0 cached input; 567 output tokens | $0.002771 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker D | 168 uncached + 0 cached input; 435 output tokens | $0.002059 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 265 uncached + 0 cached input; 874 output tokens | $0.004046 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 250 uncached + 0 cached input; 499 output tokens | $0.002433 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: the table | 182 uncached + 0 cached input; 398 output tokens | $0.001919 |
| runs/ami_samaudio | `muse-spark-1.3` | what did I miss: Speaker A | 69 uncached + 113 cached input; 498 output tokens | $0.002220 |
| runs/ami_samaudio | `muse-spark-1.3` | translate captions to es | 395 uncached + 0 cached input; 821 output tokens | $0.003983 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/sparkav_smoke | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/sparkav_smoke | `muse-spark-1.3` | unverified AV overlap transcription 0.0 | 3044 uncached + 0 cached input; 2050 output tokens | $0.012518 |
| runs/spark_ami | `files` | upload analysis video | file upload | $0.000000 |
| runs/spark_ami | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/spark_ami | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/spark_ami | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 928 output tokens | $0.004629 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 242 uncached + 0 cached input; 479 output tokens | $0.002338 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker A | 190 uncached + 0 cached input; 443 output tokens | $0.002120 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker C | 206 uncached + 0 cached input; 588 output tokens | $0.002756 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 330 uncached + 0 cached input; 540 output tokens | $0.002707 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker D | 241 uncached + 0 cached input; 433 output tokens | $0.002142 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 487 output tokens | $0.002456 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker B | 71 uncached + 113 cached input; 351 output tokens | $0.001597 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 594 output tokens | $0.002932 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker B | 110 uncached + 113 cached input; 505 output tokens | $0.002301 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker D | 257 uncached + 0 cached input; 828 output tokens | $0.003840 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 369 uncached + 0 cached input; 592 output tokens | $0.002977 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker B | 248 uncached + 0 cached input; 661 output tokens | $0.003119 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker D | 275 uncached + 0 cached input; 651 output tokens | $0.003110 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 601 output tokens | $0.002932 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker D | 208 uncached + 0 cached input; 623 output tokens | $0.002908 |
| runs/spark_ami | `muse-voice-transcribe-1.0` | bench repeat 0: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/spark_ami | `muse-voice-transcribe-1.0` | bench repeat 1: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/spark_ami | `muse-voice-transcribe-1.0` | bench repeat 2: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/spark_ami | `muse-spark-1.3` | split conversation into threads | 548 uncached + 0 cached input; 802 output tokens | $0.004093 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 129 uncached + 113 cached input; 592 output tokens | $0.002694 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker C | 190 uncached + 0 cached input; 453 output tokens | $0.002163 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker D | 206 uncached + 0 cached input; 611 output tokens | $0.002854 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 217 uncached + 113 cached input; 505 output tokens | $0.002434 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker A | 241 uncached + 0 cached input; 458 output tokens | $0.002248 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 309 uncached + 0 cached input; 498 output tokens | $0.002503 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 326 uncached + 0 cached input; 473 output tokens | $0.002418 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker A | 257 uncached + 0 cached input; 612 output tokens | $0.002922 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 256 uncached + 113 cached input; 668 output tokens | $0.003176 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker A | 162 uncached + 113 cached input; 782 output tokens | $0.003543 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: the table | 302 uncached + 0 cached input; 582 output tokens | $0.002851 |
| runs/spark_ami | `muse-spark-1.3` | what did I miss: Speaker A | 95 uncached + 113 cached input; 585 output tokens | $0.002622 |
| runs/spark_ami | `muse-spark-1.3` | translate captions to es | 473 uncached + 0 cached input; 987 output tokens | $0.004786 |
| runs/spark_ami | `muse-spark-1.3` | translate captions to es | 492 uncached + 0 cached input; 1023 output tokens | $0.004963 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 0.0 | 3044 uncached + 0 cached input; 1509 output tokens | $0.010218 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 10.0 | 3079 uncached + 0 cached input; 991 output tokens | $0.008060 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 20.0 | 2915 uncached + 113 cached input; 1455 output tokens | $0.009844 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 30.0 | 3073 uncached + 0 cached input; 1433 output tokens | $0.009931 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 40.0 | 3055 uncached + 0 cached input; 1132 output tokens | $0.008630 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 50.0 | 3053 uncached + 0 cached input; 1138 output tokens | $0.008653 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 60.0 | 3002 uncached + 0 cached input; 1603 output tokens | $0.010565 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 70.0 | 1711 uncached + 0 cached input; 1157 output tokens | $0.007056 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 0.0 | 2927 uncached + 113 cached input; 2106 output tokens | $0.012626 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 10.0 | 3076 uncached + 0 cached input; 2228 output tokens | $0.013314 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 20.0 | 3025 uncached + 0 cached input; 1113 output tokens | $0.008511 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 30.0 | 3068 uncached + 0 cached input; 1780 output tokens | $0.011400 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 40.0 | 2941 uncached + 113 cached input; 1438 output tokens | $0.009805 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 50.0 | 2973 uncached + 113 cached input; 2175 output tokens | $0.012977 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 60.0 | 2890 uncached + 113 cached input; 1233 output tokens | $0.008870 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 70.0 | 1600 uncached + 113 cached input; 999 output tokens | $0.006263 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 0.0 | 3044 uncached + 0 cached input; 1557 output tokens | $0.010422 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 10.0 | 2997 uncached + 113 cached input; 1377 output tokens | $0.009615 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 20.0 | 2911 uncached + 113 cached input; 1081 output tokens | $0.008250 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 30.0 | 2954 uncached + 113 cached input; 1700 output tokens | $0.010934 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 40.0 | 2939 uncached + 113 cached input; 1017 output tokens | $0.008013 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 50.0 | 2941 uncached + 113 cached input; 1459 output tokens | $0.009894 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 60.0 | 2890 uncached + 113 cached input; 1616 output tokens | $0.010497 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 70.0 | 1598 uncached + 113 cached input; 1609 output tokens | $0.008853 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 0.0 | 2927 uncached + 113 cached input; 1657 output tokens | $0.010718 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 10.0 | 2962 uncached + 113 cached input; 1539 output tokens | $0.010260 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 20.0 | 2910 uncached + 113 cached input; 2279 output tokens | $0.013340 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 30.0 | 2990 uncached + 113 cached input; 1684 output tokens | $0.010911 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 40.0 | 2940 uncached + 113 cached input; 2476 output tokens | $0.014215 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 50.0 | 2939 uncached + 113 cached input; 1445 output tokens | $0.009832 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 60.0 | 2889 uncached + 113 cached input; 1061 output tokens | $0.008137 |
| runs/spark_ami | `muse-spark-1.3` | unverified AV overlap transcription 70.0 | 1712 uncached + 0 cached input; 1290 output tokens | $0.007622 |
| runs/ami_samaudio_keep | `files` | upload analysis video | file upload | $0.000000 |
| runs/ami_samaudio_keep | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `facebook/sam-audio-small-tv` | isolate tapped voices | local/cached | $0.000000 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 0: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 1: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 2: diarize the raw mix | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `facebook/sam-audio-small-tv` | isolate tapped voices | local/cached | $0.000000 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_samaudio_keep_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_cleanmic | `muse-voice-transcribe-1.0` | diarize the raw mix (today's captions) | 75.040 audio seconds | $0.003752 |
| runs/array_wrong_args_backup | `files` | upload analysis video | file upload | $0.000000 |
| runs/array_wrong_args_backup | `sam-3.1` | track tapped people | 1875 video frames | $0.375000 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_8_635 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_5_635 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 0: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 0: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 1: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 1: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker A's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker B's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker C's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 2: transcribe Speaker D's isolated voice | 75.040 audio seconds | $0.003752 |
| runs/ami_array_4_635 | `muse-voice-transcribe-1.0` | bench repeat 2: diarize GCC-PHAT delay-and-sum 8-mic baseline | 75.040 audio seconds | $0.003752 |

Total before rounding: $4.115608600000. Stop new live calls before the cap is reached.
