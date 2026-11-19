"""The LLM for a Hindi transcript: model/server choice, prompt notes, copy fix-up,
and the reasoning_effort handling for models without a thinking mode."""
import json

import httpx
import pytest

from silentshorts.selection import language_notes, llm_backend, gemini_worker


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://main.test/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen")
    monkeypatch.setenv("LLM_MODEL_HI", "gemma")
    monkeypatch.delenv("LLM_BASE_URL_HI", raising=False)
    monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    llm_backend.no_thinking.clear()


def test_model_choice_by_language(env, monkeypatch):
    assert llm_backend.model_name("hi") == "gemma"
    assert llm_backend.model_name("en") == "qwen"
    assert llm_backend.model_name(None) == "qwen" and llm_backend.model_name("unknown") == "qwen"
    monkeypatch.delenv("LLM_MODEL_HI")
    assert llm_backend.model_name("hi") == "qwen"  # unset: Hindi uses the default model


def test_base_url_for_hindi(env, monkeypatch):
    assert llm_backend.base_url("hi") == "http://main.test/v1"
    monkeypatch.setenv("LLM_BASE_URL_HI", "http://hi.test/v1/")
    assert llm_backend.base_url("hi") == "http://hi.test/v1"
    assert llm_backend.base_url("en") == llm_backend.base_url() == "http://main.test/v1"


def _serve(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(llm_backend, "_client", lambda **kw: httpx.Client(transport=transport, **kw))


def _ok():
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"shorts": []})}}]})


def test_generate_json_goes_to_the_hindi_server_for_the_hindi_model(env, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL_HI", "http://hi.test/v1")
    seen = []
    _serve(monkeypatch, lambda r: seen.append((str(r.url), json.loads(r.content)["model"])) or _ok())
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model=llm_backend.model_name("hi"))
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model=llm_backend.model_name("en"))
    assert seen == [("http://hi.test/v1/chat/completions", "gemma"),
                    ("http://main.test/v1/chat/completions", "qwen")]


def test_reasoning_effort_dropped_for_a_model_without_thinking(env, monkeypatch):
    """Ollama: gemma3 accepts "none" but answers 400 'does not support thinking' to
    low/medium/high. The call is repeated without the field, once, then remembered."""
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    bodies = []

    def handler(req):
        body = json.loads(req.content)
        bodies.append(body)
        if "reasoning_effort" in body and body["model"] == "gemma":
            return httpx.Response(400, json={"error": {"message": '"gemma" does not support thinking'}})
        return _ok()
    _serve(monkeypatch, handler)
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model="gemma")
    assert ["reasoning_effort" in b for b in bodies] == [True, False]
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model="gemma")
    assert ["reasoning_effort" in b for b in bodies] == [True, False, False]  # remembered
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model="qwen")
    assert bodies[-1]["reasoning_effort"] == "low"  # other models are asked as before


def test_reasoning_effort_still_sent_when_the_model_accepts_it(env, monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "none")
    bodies = []
    _serve(monkeypatch, lambda r: bodies.append(json.loads(r.content)) or _ok())
    llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model="qwen")
    assert bodies[0]["reasoning_effort"] == "none"


def test_other_400s_are_not_swallowed(env, monkeypatch):
    monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
    _serve(monkeypatch, lambda r: httpx.Response(400, json={"error": {"message": "context too long"}}))
    with pytest.raises(RuntimeError, match="400"):
        llm_backend.generate_json("p", gemini_worker.SilentCopyResponse, model="qwen")


# --- prompt notes and the copy fix-up ---------------------------------------

def test_notes_only_for_hindi():
    assert language_notes.add("P", "en") == "P" and language_notes.add("P", "de", copy=True) == "P"
    judge = language_notes.add("P", "hi")
    assert "Hindi (Devanagari)" in judge and "Hinglish" not in judge
    assert language_notes.add("P", "hi", copy=True).count("Hinglish") >= 2  # said before and after the prompt
    assert "Do not use Devanagari" in language_notes.add("P", "hi", "hinglish", copy=True)
    assert "normal English spelling" in language_notes.add("P", "hi", "hinglish", copy=True)
    assert "English spelling" not in language_notes.add("P", "hi", "devanagari", copy=True)
    dev = language_notes.add("P", "hi", "devanagari", copy=True)
    assert "in Devanagari script" in dev and "Hinglish" not in dev


def _clip():
    return {"viral_hook_text": "क्या बात है", "video_title_for_youtube_short": "Great video",
            "video_description_for_tiktok": "मैं नहीं जानता", "video_description_for_instagram": "ok #shorts"}


def test_finalize_copy_transliterates_devanagari_for_hinglish():
    c = _clip()
    assert language_notes.finalize_copy([c], "hi", "hinglish") == 2
    assert c["viral_hook_text"] == "kya baat hai" and c["video_description_for_tiktok"] == "main nahi jaanta"
    assert c["video_title_for_youtube_short"] == "Great video"


def test_finalize_copy_leaves_devanagari_and_other_languages_alone():
    for lang, script in (("hi", "devanagari"), ("en", "hinglish")):
        c = _clip()
        assert language_notes.finalize_copy([c], lang, script) == 0 and c == _clip()


# --- through get_viral_clips ---------------------------------------------------

def _hindi_transcript():
    seg = lambda a: {"start": float(a), "end": a + 10.0, "text": "यह बहुत अच्छा है " * 4,
                     "words": [{"word": " बहुत", "start": float(a), "end": a + 0.4}]}
    return {"language": "hi", "segments": [seg(t) for t in range(0, 300, 10)]}


def _run(main, monkeypatch, language, script="hinglish"):
    monkeypatch.setenv("HINDI_SCRIPT", script)
    seen = []

    def fake_stage(client, model, prompt, schema):
        seen.append((model, prompt))
        if schema is gemini_worker.ScoreResponse:
            payload = json.loads(prompt.split("WINDOWS_JSON:")[-1].split("Return only:")[0])
            return {"windows": [{"id": w["id"], "start": 0, "end": 90, "score": 80, "reason": "r"}
                                for w in payload]}, None
        wins = json.loads(prompt.split("CANDIDATE_WINDOWS_JSON:")[-1].split("Return only:")[0])
        return {"shorts": [{"start": 10.0, "end": 50.0, "source_window_id": wins[0]["id"],
                            "predicted_score": 80, "video_description_for_tiktok": "यह है",
                            "video_description_for_instagram": "यह है",
                            "video_title_for_youtube_short": "क्या बात है", "viral_hook_text": "वो भी",
                            "why": ""}]}, None
    monkeypatch.setattr(main, "_run_gemini_stage", fake_stage)
    tr = _hindi_transcript()
    tr["language"] = language
    out = main.get_viral_clips(tr, 300.0)
    return out, seen


def test_hindi_job_uses_the_hindi_model_in_every_stage(main, env, monkeypatch):
    out, seen = _run(main, monkeypatch, "hi")
    assert seen and {m for m, _ in seen} == {"gemma"}
    assert all("Judge it as Hindi" in p for _, p in seen)
    assert any("Do not use Devanagari" in p for _, p in seen)
    c = out["shorts"][0]
    assert c["video_title_for_youtube_short"] == "kya baat hai" and c["viral_hook_text"] == "woh bhi"


def test_hindi_job_with_devanagari_script_keeps_the_copy(main, env, monkeypatch):
    out, seen = _run(main, monkeypatch, "hi", "devanagari")
    assert any("in Devanagari script" in p for _, p in seen)
    assert out["shorts"][0]["video_title_for_youtube_short"] == "क्या बात है"


def test_english_job_keeps_the_default_model_and_prompts(main, env, monkeypatch):
    out, seen = _run(main, monkeypatch, "en")
    assert {m for m, _ in seen} == {"qwen"}
    assert not any("NOTE:" in p for _, p in seen)
