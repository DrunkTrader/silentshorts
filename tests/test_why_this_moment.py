"""Why this moment: every clip carries the model's reason, the words it covers
and a 1-5 confidence from the global window ranking (never a virality %)."""
import json

import pytest

from silentshorts.selection import clip_selection as cs
from silentshorts.selection import gemini_worker, language_notes


def test_confidence_comes_from_rank_score_not_predicted_score():
    assert cs.confidence({"rank_score": 1.0, "predicted_score": 10}) == 5
    assert cs.confidence({"rank_score": 0.81}) == 5
    assert cs.confidence({"rank_score": 0.5, "predicted_score": 99}) == 3
    assert cs.confidence({"rank_score": 0.0, "predicted_score": 99}) == 1
    # No rank at all (vision clips): the model's score is the only signal left.
    assert cs.confidence({"predicted_score": 41}) == 3


def test_explain_clips_fills_rank_excerpt_and_why():
    words = [{"w": " Hello", "s": 1.0, "e": 1.4}, {"w": "world.", "s": 1.5, "e": 2.0},
             {"w": "Later", "s": 9.0, "e": 9.5}]
    shorts = [{"start": 0.8, "end": 2.2, "source_window_id": "window_002", "why": "  a   b "},
              {"start": 8.8, "end": 9.9, "source_window_id": "window_ns_001", "rank_score": 0.9},
              {"start": 0.0, "end": 1.0, "source_window_id": "made_up"}]
    cs.explain_clips(shorts, words, {"window_001": 0, "window_002": 1}, 4)
    assert shorts[0]["rank_score"] == 0.75 and shorts[0]["confidence"] == 4
    assert shorts[0]["excerpt"] == "Hello world." and shorts[0]["why"] == "a b"
    # A rank set by the merged ranking is kept.
    assert shorts[1]["rank_score"] == 0.9 and shorts[1]["confidence"] == 5
    assert shorts[2]["why"] == "" and "rank_score" not in shorts[2]


def test_detail_prompt_asks_for_why_and_keeps_its_placeholders():
    assert "why" in gemini_worker.DetailClipModel.model_fields
    out = gemini_worker.DETAIL_PROMPT_TEMPLATE.format(
        video_duration=60, language="en", min_clips=1, max_clips=2,
        min_secs=30, max_secs=60, windows_json="[]")
    assert '"why"' in out


def test_hinglish_why_never_stays_in_devanagari():
    clip = {"why": "यह बहुत ज़रूरी है", "viral_hook_text": "ok"}
    assert language_notes.finalize_copy([clip], "hi", "hinglish") == 1
    assert clip["why"] == "yeh bahut zaroori hai"
    assert "why" in language_notes.note("hi", "hinglish", copy=True)
    assert "why" in language_notes.note("hi", "devanagari", copy=True)
    dev = {"why": "यह बहुत ज़रूरी है"}
    assert language_notes.finalize_copy([dev], "hi", "devanagari") == 0


# --- through get_viral_clips ---------------------------------------------------

@pytest.fixture
def main():
    return pytest.importorskip("silentshorts.pipeline.main")


def _transcript(language="en"):
    segs = []
    for i in range(40):
        t = i * 15.0
        segs.append({"start": t, "end": t + 15.0, "text": f"line {i}.",
                     "words": [{"word": f"w{i}.", "start": t, "end": t + 0.4}]})
    return {"language": language, "segments": segs}


def _run(main, monkeypatch, transcript, why="because the number lands"):
    def fake_stage(client, model, prompt, schema):
        if schema is main.gemini_worker.ScoreResponse:
            payload = json.loads(prompt.split("WINDOWS_JSON:")[-1].split("Return only:")[0])
            # Scored in reverse: the LAST window is the best one of the video.
            return {"windows": [{"id": w["id"], "start": 0, "end": 90, "score": int(w["id"][-3:]),
                                 "reason": "r"} for w in payload]}, None
        windows = json.loads(prompt.split("CANDIDATE_WINDOWS_JSON:")[-1].split("Return only:")[0])
        return {"shorts": [{"start": w["start"], "end": w["start"] + 30.0, "source_window_id": w["id"],
                            "predicted_score": 50, "video_description_for_tiktok": "d",
                            "video_description_for_instagram": "d",
                            "video_title_for_youtube_short": "t", "viral_hook_text": "h", "why": why}
                           for w in windows]}, None

    monkeypatch.setattr(main, "_run_gemini_stage", fake_stage)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(main.genai, "Client", lambda api_key=None: object())
    return main.get_viral_clips(transcript, 600.0)["shorts"]


def test_every_clip_carries_why_excerpt_and_confidence(main, monkeypatch):
    clips = _run(main, monkeypatch, _transcript())
    assert clips
    for c in clips:
        assert c["why"] == "because the number lands"
        assert c["excerpt"].startswith("w") and 1 <= c["confidence"] <= 5
        assert 0 <= c["rank_score"] <= 1
    # The best-ranked window (the last one) is the most confident clip.
    best = max(clips, key=lambda c: c["start"])
    assert best["confidence"] == 5
    assert min(c["confidence"] for c in clips) < 5


def test_hinglish_job_gets_its_why_out_of_devanagari(main, monkeypatch):
    monkeypatch.setenv("HINDI_SCRIPT", "hinglish")
    clips = _run(main, monkeypatch, _transcript("hi"), why="यह बहुत ज़रूरी है")
    assert clips and all(c["why"] == "yeh bahut zaroori hai" for c in clips)
