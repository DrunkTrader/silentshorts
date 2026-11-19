"""/api/process: the ``language`` and ``hindi_script`` job fields."""
import asyncio

import httpx
import pytest

app_module = pytest.importorskip("silentshorts.api.app")


@pytest.fixture()
def dirs(tmp_path, monkeypatch):
    out_root, up_root = tmp_path / "output", tmp_path / "uploads"
    out_root.mkdir(); up_root.mkdir()
    monkeypatch.setattr(app_module, "OUTPUT_DIR", str(out_root))
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(up_root))
    monkeypatch.setattr(app_module, "_media_duration_seconds", lambda p: 120.0)

    async def fake_put(item):
        pass
    monkeypatch.setattr(app_module.job_queue, "put", fake_put)


def _job_env(**form):
    async def _go():
        transport = httpx.ASGITransport(app=app_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver",
                                     headers={"X-Gemini-Key": "k"}) as c:
            return await c.post("/api/process", data={"acknowledged": "true", **form},
                                files={"file": ("a.mp4", b"x" * 100, "video/mp4")})
    resp = asyncio.run(_go())
    assert resp.status_code == 200, resp.text
    return app_module.jobs[resp.json()["job_id"]]["env"]


def test_defaults_are_auto_and_hinglish(dirs):
    env = _job_env()
    assert env["TRANSCRIBE_LANGUAGE"] == "auto" and env["HINDI_SCRIPT"] == "hinglish"


@pytest.mark.parametrize("sent,expected", [("hi", "hi"), ("EN", "en"), ("auto", "auto"),
                                           ("fr", "auto"), ("", "auto")])
def test_language_is_validated(dirs, sent, expected):
    assert _job_env(language=sent)["TRANSCRIBE_LANGUAGE"] == expected


@pytest.mark.parametrize("sent,expected", [("devanagari", "devanagari"), ("Hinglish", "hinglish"),
                                           ("latin", "hinglish")])
def test_hindi_script_is_validated(dirs, sent, expected):
    assert _job_env(hindi_script=sent)["HINDI_SCRIPT"] == expected
