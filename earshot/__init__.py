"""Earshot: every voice at the table, captioned — even when people talk at once.

Pipeline (all runtime models are Meta models):

    video ──► SAM 3.1 (hosted) tracks each tapped person ──► per-frame masks
          └─► SAM Audio (local, Meta open weights) isolates each person's voice
              using their mask as a visual prompt
          ──► Muse Voice Transcribe (hosted) transcribes each isolated voice
          ──► deterministic voice activity + timeline merge (overlap, bleed)
          ──► Muse Spark (hosted) groups turns into threads and writes
              "What did I miss?" summaries that must cite turn IDs
"""

__version__ = "0.1.0"
