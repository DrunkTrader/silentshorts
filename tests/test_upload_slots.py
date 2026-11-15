"""Upload slots: the self-host cap, and what a failed PUT leaves on disk."""
import asyncio
import os

import httpx
import pytest

app_module = pytest.importorskip("app")


def _run(coro):
    return asyncio.run(coro)


def _client():
    transport = httpx.ASGITransport(app=app_module.app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture()
def uploads(tmp_path, monkeypatch):
    up = tmp_path / "uploads"
    up.mkdir()
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(up))
    monkeypatch.setattr(app_module, "pending_uploads", {})
    monkeypatch.setattr(app_module, "_media_duration_seconds", lambda p: 60.0)
    return up


def _reserve(c):
    return c.post("/api/uploads", json={"filename": "a.mp4"})


def test_self_host_caps_open_slots_for_the_whole_server(uploads, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_PENDING_UPLOADS_SELF_HOST", 2)

    async def go():
        async with _client() as c:
            return [(await _reserve(c)).status_code for _ in range(3)]
    assert _run(go()) == [200, 200, 429]


def test_a_freed_slot_makes_room_again(uploads, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_PENDING_UPLOADS_SELF_HOST", 1)

    async def go():
        async with _client() as c:
            first = (await _reserve(c)).json()["upload_id"]
            assert (await _reserve(c)).status_code == 429
            assert (await c.delete(f"/api/uploads/{first}")).status_code == 200
            return (await _reserve(c)).status_code
    assert _run(go()) == 200


def test_a_good_put_completes_the_slot(uploads):
    async def go():
        async with _client() as c:
            uid = (await _reserve(c)).json()["upload_id"]
            r = await c.put(f"/api/uploads/{uid}", content=b"x" * 3000)
            return uid, r
    uid, r = _run(go())
    assert r.status_code == 200 and r.json()["bytes"] == 3000
    slot = app_module.pending_uploads[uid]
    assert slot["complete"] is True
    assert os.path.getsize(slot["path"]) == 3000


def test_a_body_larger_than_one_write_batch_arrives_intact(uploads, monkeypatch):
    monkeypatch.setattr(app_module, "_UPLOAD_WRITE_BATCH", 1000)
    data = os.urandom(5321)

    async def go():
        async with _client() as c:
            uid = (await _reserve(c)).json()["upload_id"]
            await c.put(f"/api/uploads/{uid}", content=data)
            return uid
    uid = _run(go())
    with open(app_module.pending_uploads[uid]["path"], "rb") as f:
        assert f.read() == data


def test_too_large_is_413_and_leaves_no_file(uploads, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_FILE_SIZE_MB", 0.001)  # about 1 KB

    async def go():
        async with _client() as c:
            uid = (await _reserve(c)).json()["upload_id"]
            return uid, await c.put(f"/api/uploads/{uid}", content=b"x" * 5000)
    uid, r = _run(go())
    assert r.status_code == 413
    assert not os.path.exists(app_module.pending_uploads[uid]["path"])
    assert app_module.pending_uploads[uid]["complete"] is False


def test_a_client_that_drops_mid_body_leaves_no_partial_file(uploads):
    class _Dropped:
        async def stream(self):
            yield b"x" * 2048
            raise ConnectionError("client went away")

    async def go():
        async with _client() as c:
            uid = (await _reserve(c)).json()["upload_id"]
        with pytest.raises(ConnectionError):
            await app_module.put_upload(uid, _Dropped())
        return uid
    uid = _run(go())
    assert not os.path.exists(app_module.pending_uploads[uid]["path"])


def test_a_second_put_marks_the_slot_unusable_until_it_finishes(uploads):
    seen = {}

    class _Probe:
        def __init__(self, slot):
            self.slot = slot

        async def stream(self):
            seen["complete_during_put"] = self.slot["complete"]
            yield b"y" * 100

    async def go():
        async with _client() as c:
            uid = (await _reserve(c)).json()["upload_id"]
            await c.put(f"/api/uploads/{uid}", content=b"x" * 100)
        await app_module.put_upload(uid, _Probe(app_module.pending_uploads[uid]))
        return uid
    uid = _run(go())
    assert seen["complete_during_put"] is False
    assert app_module.pending_uploads[uid]["complete"] is True
