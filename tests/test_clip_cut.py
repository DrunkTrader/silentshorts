"""Pick it yourself: POST /api/clip/cut and the quote matching behind it.

The endpoint renders through the rerender source path (stubbed at the
recut.perform_recut seam, as in test_rerender_endpoint.py)."""
import asyncio
import json
import os
from types import SimpleNamespace

import httpx
import pytest

from silentshorts.selection import manual_cut as mc


def _words(*items):
    return [{"w": w, "s": s, "e": s + 0.4} for w, s in items]


# --- quote matching -------------------------------------------------------------
def test_quotes_match_case_accents_and_punctuation_insensitively():
    words = _words(("So,", 1.0), ("the", 2.0), ("Café", 3.0), ("opened.", 4.0), ("Then", 9.0),
                   ("it", 10.0), ("CLOSED!", 12.0))
    assert mc.find_quotes(words, "the cafe", "it closed") == (2.0, 12.4)
    assert mc.tokens("Ça  va? «Oui»") == ["ca", "va", "oui"]


def test_to_quote_must_come_after_the_from_quote():
    words = _words(("end", 0.0), ("start", 10.0), ("middle", 14.0), ("end", 20.0))
    assert mc.find_quotes(words, "start", "end") == (10.0, 20.4)
    with pytest.raises(mc.CutError, match="after"):
        mc.find_quotes(words, "middle", "start")
    with pytest.raises(mc.CutError, match="Could not find"):
        mc.find_quotes(words, "nowhere", "end")


def test_too_short_or_too_long_between_quotes_is_refused():
    words = _words(("a", 0.0), ("b", 1.0), ("c", 300.0))
    with pytest.raises(mc.CutError, match="5-180"):
        mc.find_quotes(words, "a", "b")
    with pytest.raises(mc.CutError, match="5-180"):
        mc.find_quotes(words, "a", "c")


def test_devanagari_quotes_match_a_devanagari_transcript():
    words = _words(("मेरा", 1.0), ("नाम", 2.0), ("राहुल", 3.0), ("है।", 4.0), ("बात", 8.0),
                   ("ख़त्म", 9.0), ("हुई।", 10.0))
    assert mc.find_quotes(words, "मेरा नाम", "ख़त्म हुई") == (1.0, 10.4)


def test_hinglish_typed_against_a_devanagari_transcript():
    words = _words(("मेरा", 1.0), ("नाम", 2.0), ("राहुल", 3.0), ("है।", 4.0), ("अब", 8.0),
                   ("खत्म", 9.0), ("हुआ", 10.0))
    # Typed spellings differ from the transliteration (raahul, khatam): still found.
    assert mc.find_quotes(words, "Mera Naam rahul", "khatam") == (1.0, 9.4)
    assert mc.find_quotes(words, "meraa naam", "khattam huaa") == (1.0, 10.4)


def test_resolve_checks_the_range_and_snaps_it_to_words():
    tr = {"segments": [{"words": [{"word": "hello", "start": 12.0, "end": 12.5},
                                  {"word": "world", "start": 20.0, "end": 20.4}]}]}
    s, e = mc.resolve(tr, 60.0, start=12.3, end=20.2)
    assert 11.6 <= s < 12.0 and 20.4 <= e <= 20.9
    for bad in ((10.0, 14.0), (0.0, 181.0), (-1.0, 10.0)):
        with pytest.raises(mc.CutError):
            mc.resolve(tr, 600.0, *bad)
    with pytest.raises(mc.CutError, match="only 60 s"):
        mc.resolve(tr, 60.0, start=50.0, end=70.0)
    with pytest.raises(mc.CutError):
        mc.resolve(tr, 60.0)


# --- endpoint -------------------------------------------------------------------
app_module = pytest.importorskip("silentshorts.api.app")
from silentshorts.render import recut  # noqa: E402

JOB_ID = "5a1f0c3e-0000-4000-8000-0000000000c7"
TRANSCRIPT = {"language": "en", "segments": [{"start": 0.0, "end": 60.0, "text": "hello world again", "words": [
    {"word": "hello", "start": 12.0, "end": 12.5}, {"word": "world", "start": 20.0, "end": 20.4},
    {"word": "again", "start": 50.0, "end": 50.5}]}]}


def _post(body):
    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app_module.app),
                                     base_url="http://testserver") as c:
            return await c.post("/api/clip/cut", json=body)
    return asyncio.run(go())


@pytest.fixture()
def job(tmp_path, monkeypatch):
    out, up = tmp_path / "output", tmp_path / "uploads"
    d = out / JOB_ID
    d.mkdir(parents=True)
    up.mkdir()
    monkeypatch.setattr(app_module, "OUTPUT_DIR", str(out))
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(up))
    clip = {"start": 10.0, "end": 40.0, "video_title_for_youtube_short": "first",
            "video_url": f"/videos/{JOB_ID}/t_clip_1.mp4"}
    (d / "t_metadata.json").write_text(json.dumps({
        "shorts": [clip], "transcript": TRANSCRIPT, "source_video": "src.mp4", "output_format": "auto"}))
    (d / "t_clip_1.mp4").write_bytes(b"c")
    (d / "src.mp4").write_bytes(b"s")
    app_module.jobs[JOB_ID] = {"status": "completed", "logs": [], "user_id": None,
                               "result": {"clips": [dict(clip)]}}
    try:
        yield d
    finally:
        app_module.jobs.pop(JOB_ID, None)


@pytest.fixture()
def renders(monkeypatch):
    calls = []

    def fake(**kw):
        calls.append(kw)
        name = f"recut_1_{kw['clean_name']}"
        with open(os.path.join(kw["output_dir"], name), "wb") as f:
            f.write(b"r")
        return name, name
    monkeypatch.setattr(recut, "perform_recut", fake)
    return calls


def test_a_time_range_becomes_a_new_clip_from_the_source(job, renders):
    r = _post({"job_id": JOB_ID, "start": 12.2, "end": 20.3})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["clip_index"] == 1 and body["render_path"] == "source"
    assert len(renders) == 1 and renders[0]["reframe"] is True
    assert renders[0]["clean_name"] == "t_clip_2.mp4"
    assert renders[0]["input_path"].endswith("src.mp4")
    meta = json.loads((job / "t_metadata.json").read_text())
    new = meta["shorts"][1]
    assert new["manual"] is True and new["excerpt"] == "hello world"
    assert 11.6 <= new["start"] < 12.0 and 20.4 <= new["end"] <= 20.9   # snapped to words
    assert new["video_url"] == body["new_video_url"]
    assert meta["shorts"][0]["video_title_for_youtube_short"] == "first"   # untouched
    mem = app_module.jobs[JOB_ID]["result"]["clips"]
    assert len(mem) == 2 and mem[1]["video_url"] == body["new_video_url"]


def test_quotes_are_found_in_the_stored_transcript(job, renders):
    r = _post({"job_id": JOB_ID, "from_text": "Hello", "to_text": "AGAIN"})
    assert r.status_code == 200, r.text
    assert r.json()["start"] < 12.0 and r.json()["end"] >= 50.5


@pytest.mark.parametrize("body,code", [
    ({"start": 12.0, "end": 14.0}, 400),                       # under 5 s
    ({"start": 0.0, "end": 200.0}, 400),                       # over 180 s
    ({"from_text": "nowhere", "to_text": "again"}, 400),
    ({}, 400),
])
def test_bad_ranges_render_nothing(job, renders, body, code):
    r = _post({"job_id": JOB_ID, **body})
    assert r.status_code == code and renders == []
    assert len(json.loads((job / "t_metadata.json").read_text())["shorts"]) == 1


def test_a_range_outside_the_kept_source_is_a_409(job, renders):
    os.remove(job / "src.mp4")
    r = _post({"job_id": JOB_ID, "start": 12.0, "end": 30.0})
    assert r.status_code == 409 and "not on the server" in r.json()["detail"] and renders == []


def test_a_running_job_and_a_non_job_id_are_refused(job, renders):
    app_module.jobs[JOB_ID]["status"] = "processing"
    assert _post({"job_id": JOB_ID, "start": 12.0, "end": 30.0}).status_code == 409
    assert _post({"job_id": "pending", "start": 12.0, "end": 30.0}).status_code == 404
    assert renders == []


def test_a_failed_render_leaves_the_job_as_it_was(job, monkeypatch):
    def boom(**kw):
        raise RuntimeError("ffmpeg died")
    monkeypatch.setattr(recut, "perform_recut", boom)
    assert _post({"job_id": JOB_ID, "start": 12.0, "end": 30.0}).status_code == 500
    assert len(json.loads((job / "t_metadata.json").read_text())["shorts"]) == 1
    assert len(app_module.jobs[JOB_ID]["result"]["clips"]) == 1


def test_cloud_owner_check_hides_another_users_job(job, renders, monkeypatch):
    class U:
        id, plan = 2, "pro"

    async def stranger(request):
        return U()
    monkeypatch.setattr(app_module, "BILLING_ENABLED", True)
    monkeypatch.setattr(app_module, "_user_from_request", stranger)
    monkeypatch.setattr(app_module, "managed_keys", SimpleNamespace(has_active_entitlement=lambda u: True))
    app_module.jobs[JOB_ID]["user_id"] = 1
    r = _post({"job_id": JOB_ID, "start": 12.0, "end": 30.0})
    assert r.status_code == 404 and renders == []
    assert len(json.loads((job / "t_metadata.json").read_text())["shorts"]) == 1
