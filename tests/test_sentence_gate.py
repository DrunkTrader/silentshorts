"""Never mid-sentence: the QA gate after bounds, snap and dedupe.

A small corpus of transcripts whose clips cut mid-sentence, in English
(``.?!`` and segment edges) and in Hindi (the danda ``।``)."""
import json

import pytest

from silentshorts.selection import clip_selection as cs


def _seg(t0, text, step=0.6):
    """One segment, one word every ``step`` seconds (each 0.5 s long)."""
    words = [{"word": w, "start": round(t0 + i * step, 3), "end": round(t0 + i * step + 0.5, 3)}
             for i, w in enumerate(text.split())]
    return {"start": t0, "end": words[-1]["end"], "text": text, "words": words}


def _transcript(*segs, language="en"):
    return {"language": language, "segments": list(segs)}


def _word(tr, text, which="start"):
    """Time of the first word equal to ``text``."""
    for g in tr["segments"]:
        for w in g["words"]:
            if w["word"] == text:
                return w[which]
    raise KeyError(text)


# Ten-word sentences, 6 s each, all in one segment: only punctuation marks the sentences.
EN = _transcript(_seg(0.0, " ".join(
    f"s{n}a s{n}b s{n}c s{n}d s{n}e s{n}f s{n}g s{n}h s{n}i s{n}j." for n in range(20))))
# Hindi: sentences end with the danda, attached to the last word.
HI = _transcript(_seg(0.0, " ".join(
    f"शब्द{n}क बात{n}ख यह{n}ग है{n}घ ठीक{n}ङ और{n}च फिर{n}छ वह{n}ज गया{n}झ घर{n}ञ।" for n in range(20))),
    language="hi")


def _gate(tr, clips, lo=10.0, hi=30.0):
    return cs.sentence_gate(clips, tr, 120.0, lo, hi)


def test_a_clip_on_sentence_boundaries_is_untouched():
    clip = {"start": _word(EN, "s2a") - 0.05, "end": _word(EN, "s4j.", "end") + 0.05,
            "source_window_id": "window_001"}
    kept, notes = _gate(EN, [clip])
    assert kept == [clip] and notes == []


def test_mid_sentence_start_and_end_are_extended_to_the_nearest_boundaries():
    clip = {"start": _word(EN, "s2e") - 0.05, "end": _word(EN, "s4c", "end") + 0.05,
            "source_window_id": "window_001"}
    kept, notes = _gate(EN, [clip])
    assert len(kept) == 1 and len(notes) == 1 and "mid-sentence" in notes[0]
    s, e = kept[0]["start"], kept[0]["end"]
    assert _word(EN, "s2a") - 0.35 <= s <= _word(EN, "s2a")
    assert _word(EN, "s4j.", "end") <= e <= _word(EN, "s4j.", "end") + 0.45
    assert "s4c" not in notes[0]   # notes never carry transcript text


def test_past_the_max_it_trims_back_to_the_boundary_inside():
    # s1e .. s5c is ~23 s; extending both ends would pass 26 s, so it trims instead.
    clip = {"start": _word(EN, "s1e") - 0.05, "end": _word(EN, "s5c", "end") + 0.05}
    kept, _ = _gate(EN, [clip], lo=10.0, hi=24.0)
    s, e = kept[0]["start"], kept[0]["end"]
    assert e - s <= 24.0 and e - s >= 10.0
    # Either edge lands on a sentence boundary.
    starts = [_word(EN, f"s{n}a") for n in range(20)]
    ends = [_word(EN, f"s{n}j.", "end") for n in range(20)]
    assert any(0 <= a - s <= 0.35 for a in starts)
    assert any(0 <= e - b <= 0.45 for b in ends)


def test_dropped_when_no_boundary_fits_the_band():
    # Inside one long sentence: no boundary to extend to within 8 s, none inside to trim to.
    long = _transcript(_seg(0.0, " ".join(f"w{i}" for i in range(60)) + "."))
    clip = {"start": 10.0, "end": 16.0, "source_window_id": "window_007"}
    kept, notes = cs.sentence_gate([clip], long, 120.0, 5.0, 8.0)
    assert kept == [] and notes and notes[0].startswith("dropped window_007")


def test_segment_edges_count_as_sentence_boundaries():
    tr = _transcript(_seg(0.0, "no punctuation here at all"), _seg(10.0, "second segment starts here"),
                     _seg(20.0, "and a third one"))
    clip = {"start": 9.9, "end": 11.9}   # second segment, cut before its last word
    kept, _ = cs.sentence_gate([clip], tr, 60.0, 1.0, 30.0)
    assert kept[0]["start"] == 9.9   # its first word opens the segment
    assert kept[0]["end"] >= _word(tr, "here", "end")


def test_hindi_danda_marks_the_sentence():
    clip = {"start": _word(HI, "यह3ग") - 0.05, "end": _word(HI, "और5च", "end") + 0.05}
    kept, notes = _gate(HI, [clip])
    assert len(kept) == 1 and notes
    assert _word(HI, "शब्द3क") - 0.35 <= kept[0]["start"] <= _word(HI, "शब्द3क")
    assert kept[0]["end"] >= _word(HI, "घर5ञ।", "end")
    on = {"start": _word(HI, "शब्द3क") - 0.05, "end": _word(HI, "घर5ञ।", "end") + 0.05}
    assert _gate(HI, [on]) == ([on], [])


def test_nonspeech_and_wordless_clips_are_exempt():
    silent = {"start": 1.5, "end": 9.0, "kind": "nonspeech"}
    nowords = {"start": 500.0, "end": 530.0}
    assert _gate(EN, [silent, nowords]) == ([silent, nowords], [])


# --- in get_viral_clips: after bounds/snap/dedupe, before the floor -------------

@pytest.fixture
def main():
    return pytest.importorskip("silentshorts.pipeline.main")


def _corpus():
    # 40 sentences of 15 s, two segments each: a clip 30 s long fits 2 sentences.
    segs = []
    for i in range(40):
        t = i * 15.0
        segs.append(_seg(t, " ".join(f"x{i}{c}" for c in "abcdefghijklmnopqrstuvwx") + "."))
    return _transcript(*segs)


def test_the_pipeline_extends_mid_sentence_picks_and_logs_it(main, monkeypatch, capsys):
    tr = _corpus()
    out = _pipeline(main, monkeypatch, tr, lambda w: (w["start"] + 4.0, w["start"] + 34.0))
    assert out
    for c in out:
        words = [x for g in tr["segments"] for x in g["words"]
                 if c["start"] <= (x["start"] + x["end"]) / 2 <= c["end"]]
        assert words[0]["word"].endswith("a") and words[-1]["word"].endswith(".")
    assert "QA gate:" in capsys.readouterr().out


def test_dropped_picks_still_leave_the_floor_to_the_code(main, monkeypatch, capsys):
    # Every first pick lies inside one endless sentence and is dropped; the floor
    # asks the unused windows again.
    tr = _transcript(_seg(0.0, " ".join(f"z{i}" for i in range(900)) + ".", step=0.66))
    calls = []
    out = _pipeline(main, monkeypatch, tr, lambda w: (w["start"] + 4.0, w["start"] + 34.0), calls)
    assert "QA gate: dropped" in capsys.readouterr().out
    assert len([c for c in calls if c == "detail"]) >= 2
    assert out is None or out == []


def _pipeline(main, monkeypatch, tr, span, calls=None):
    calls = [] if calls is None else calls

    def fake_stage(client, model, prompt, schema):
        if schema is main.gemini_worker.ScoreResponse:
            payload = json.loads(prompt.split("WINDOWS_JSON:")[-1].split("Return only:")[0])
            calls.append("score")
            return {"windows": [{"id": w["id"], "start": 0, "end": 90, "score": 50, "reason": "r"}
                                for w in payload]}, None
        calls.append("detail")
        windows = json.loads(prompt.split("CANDIDATE_WINDOWS_JSON:")[-1].split("Return only:")[0])
        return {"shorts": [{"start": span(w)[0], "end": span(w)[1], "source_window_id": w["id"],
                            "predicted_score": 50, "video_description_for_tiktok": "d",
                            "video_description_for_instagram": "d",
                            "video_title_for_youtube_short": "t", "viral_hook_text": "h", "why": "w"}
                           for w in windows]}, None

    monkeypatch.setattr(main, "_run_gemini_stage", fake_stage)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main.genai, "Client", lambda api_key=None: object())
    res = main.get_viral_clips(tr, 600.0)
    return (res or {}).get("shorts")
