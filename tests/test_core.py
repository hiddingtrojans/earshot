import numpy as np

from earshot.activity import active_fraction, overlap_windows, speech_segments
from earshot.timeline import build_captions, jaccard
from earshot.tracking import Tap, object_prompt_text, parse_raw_output, records_to_tracks
from earshot.transcribe import Turn, turns_from_response

SR = 16_000


def tone(seconds, on_spans, freq=220.0, amp=0.3, noise=0.002, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    x = noise * rng.standard_normal(t.size)
    for a, b in on_spans:
        m = (t >= a) & (t < b)
        x[m] += amp * np.sin(2 * np.pi * freq * t[m])
    return x.astype(np.float32)


def test_speech_segments_find_spans():
    x = tone(6, [(1.0, 2.0), (3.5, 5.0)])
    segs = speech_segments(x, SR)
    assert len(segs) == 2
    assert abs(segs[0][0] - 1.0) < 0.05 and abs(segs[1][1] - 5.0) < 0.25


def test_silent_track_has_no_speech():
    assert speech_segments(tone(5, []), SR) == []


def test_active_fraction_and_overlap_windows():
    assert active_fraction([(0, 1), (2, 3)], 0.5, 2.5) == 0.5
    assert overlap_windows([[(0, 2)], [(1, 3)], [(5, 6)]]) == [(1, 2)]


def test_build_captions_drops_bleed_and_flags_overlap():
    names = ["Ana", "Raúl"]
    turns = [
        [Turn("0", 0.0, 2.0, "did you book the table"), Turn("0", 2.2, 3.0, "for friday then")],
        [Turn("0", 1.0, 3.0, "for friday then"),  # Raúl really said this...
         Turn("0", 6.0, 7.0, "faint leak")],        # ...and this is bleed on a quiet track
    ]
    activity = [[(0.0, 2.0)], [(1.0, 3.0)]]  # Ana speaks 0-2, Raúl 1-3
    caps = build_captions(names, turns, activity)
    texts = [(c.name, c.text) for c in caps]
    assert ("Ana", "did you book the table") in texts
    assert ("Raúl", "for friday then") in texts      # kept in the track where he's active
    assert ("Ana", "for friday then") not in texts   # duplicate in Ana's track dropped
    assert all(c.text != "faint leak" for c in caps)
    ana = next(c for c in caps if c.name == "Ana")
    assert ana.overlap and ana.overlap_with == [1]
    assert [c.id for c in caps] == ["c001", "c002"]


def test_jaccard():
    assert jaccard("Hello there!", "hello there") == 1.0
    assert jaccard("", "x") == 0.0


def test_turns_from_response():
    turns = turns_from_response({"turns": [
        {"speaker": "1", "startMs": 1500, "endMs": 2500, "transcript": " second "},
        {"speaker": "0", "startMs": 0, "endMs": 1000, "transcript": "first"},
        {"speaker": "0", "startMs": 3000, "endMs": 3100, "transcript": ""},
    ]})
    assert [t.text for t in turns] == ["first", "second"]


# Example SAM 3.1 output from meta_sam_parser's documentation (two objects, frame 0).
SAM_EXAMPLE = (
    "<0f>0<|box;x1=211;y1=228;x2=270;y2=254;w=320;h=334|>"
    "<|mask;x=0;y=0;data=27,60,~!!!!M!0c[0o91w?q1!pIH4pPRVp2B3'7`e.ioeAf6-k/#Xd8%dX9x(|>"
    ",1<|box;x1=155;y1=228;x2=202;y2=254;w=320;h=334|>"
    "<|mask;x=0;y=0;data=27,48,~!!!!J!0c[q=Pj_zs=*4C4(/./x#:/`S_GnD`=o3?X{emCgO$y@|>\n"
)


def test_sam_output_to_tracks_and_anchors():
    result = parse_raw_output(SAM_EXAMPLE)
    tracks = records_to_tracks(result, ["A", "B"], ["0", "1"], 320, 334, 25.0, 1)
    m = tracks.mask(0, 0)
    assert m.shape == (334, 320) and m.any()
    ys, xs = np.nonzero(m)
    assert xs.min() >= 211 and xs.max() < 271 and ys.min() >= 228
    assert not tracks.mask(1, 5).any()  # frame without data -> empty
    (t, x, y), = tracks.anchors(0, step=1)
    assert t == 0.0 and 211 / 320 < x < 271 / 320 and abs(y - 228 / 334) < 0.02


def test_tap_parse_and_object_prompt():
    tap = Tap.parse("Ana@0.25,0.5#3")
    assert tap == Tap("Ana", 0.25, 0.5, 3)
    text = object_prompt_text([tap, Tap("B", 0.75, 0.5)], 640, 360)
    assert text.startswith("<0f>2<|point;x=480;y=180") or "<3f>1<|point;x=160;y=180" in text
