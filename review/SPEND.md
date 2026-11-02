# Estimated Meta API spend

Run cap: **$20.00**. **Running total: $1.561797.**

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

Total before rounding: $1.561796950000. Stop new live calls before the cap is reached.
