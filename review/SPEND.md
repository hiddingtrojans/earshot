# Estimated Meta API spend

Run cap: **$20.00**. Estimates use the list prices in the implementation pack and actual response usage where exposed by the API. Cached calls cost $0. Local models cost $0 in API spend.

**Running total after T1 run 1: $0.055881.** T1 run 2 used replay mode and added $0.

| Run | Model | Usage basis | Estimated USD |
|---|---|---|---:|
| T1 run 1 | Files | Upload has no model list-price charge | $0.000000 |
| T1 run 1 | `sam-3.1` | 252 processed frames × $0.20 / 1,000 | $0.050400 |
| T1 run 1 | `muse-voice-transcribe-1.0` | 10.08 seconds × $0.18 / 3,600 | $0.000504 |
| T1 run 1 | `muse-spark-1.3` threads | 267 input + 439 output tokens | $0.002200 |
| T1 run 1 | `muse-spark-1.3` catch-up | 226 input + 587 output tokens | $0.002777 |
| T1 run 2 | All | 4 cache hits; replay enabled | $0.000000 |

Spark arithmetic uses $1.25 / 1M uncached input tokens and $4.25 / 1M output tokens; both responses reported 0 cached input tokens. Totals are rounded to six decimals after summing unrounded estimates.
