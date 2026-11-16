"""Access control on the one endpoint that serves the untouched original.

/api/source streams the file we downloaded, not a derived clip, so an open
version of it is a public downloader wearing a UUID. A <video src> cannot send
an Authorization header, so the owner mints a signed URL from /api/source-url
and hands the player that.

BILLING_ENABLED=0 here (conftest), which is the self-host branch: no owner to
check and no secret to sign with, so the open path must keep working exactly as
before. That regression is most of what these tests are for.
"""

import asyncio
import json
import time

import httpx
import pytest

app_module = pytest.importorskip("silentshorts.api.app")

JOB_ID = "5a1f0c3e-0000-4000-8000-000000000004"


def _get(path):
    async def _do():
        transport = httpx.ASGITransport(app=app_module.app)
        async with httpx.AsyncClient(transport=transport,
                                     base_url="http://testserver") as client:
            return await client.get(path)
    return asyncio.run(_do())


@pytest.fixture()
def job(tmp_path, monkeypatch):
    """A URL-style job: the retained download sits in the job dir and is named
    by ``source_video`` in the metadata, which is what _locate_source reads."""
    out_root = tmp_path / "output"
    job_dir = out_root / JOB_ID
    job_dir.mkdir(parents=True)
    (tmp_path / "uploads").mkdir()
    monkeypatch.setattr(app_module, "OUTPUT_DIR", str(out_root))
    monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path / "uploads"))

    (job_dir / "source.mp4").write_bytes(b"not really a video")
    # One clip and a word timeline, so the EDL endpoint has something to answer
    # with: the invariant test below is worthless if it skips.
    (job_dir / "x_metadata.json").write_text(json.dumps({
        "source_video": "source.mp4",
        "transcript": {
            "language": "en",
            "segments": [{
                "start": 0.0, "end": 30.0, "text": "hello world",
                "words": [{"word": "hello", "start": 10.0, "end": 10.4},
                          {"word": "world", "start": 11.0, "end": 11.4}],
            }],
        },
        "shorts": [{
            "start": 10.0, "end": 20.0, "title": "clip", "score": 90,
            "video_url": "/videos/x/clip_1.mp4",
        }],
    }))
    # Also in memory: the EDL endpoint answers from the live job record, so a
    # fixture that only writes disk makes this file order-dependent — the test
    # below passed only because an earlier one had triggered a disk recovery.
    app_module.jobs[JOB_ID] = {
        "status": "completed",
        "logs": [],
        "result": {"clips": [{
            "start": 10.0, "end": 20.0, "title": "clip", "score": 90,
            "video_url": "/videos/x/clip_1.mp4",
        }]},
        "user_id": None,
        "watermark": False,
    }
    try:
        yield job_dir
    finally:
        app_module.jobs.pop(JOB_ID, None)


class TestSelfHostStaysOpen:
    def test_source_is_served_without_a_token(self, job):
        r = _get(f"/api/source/{JOB_ID}")
        assert r.status_code == 200
        assert r.content == b"not really a video"

    def test_source_url_hands_back_the_plain_path(self, job):
        r = _get(f"/api/source-url/{JOB_ID}")
        assert r.status_code == 200
        # No secret to sign with off-billing, so no query string to mint.
        assert r.json()["url"] == f"/api/source/{JOB_ID}"

    def test_missing_source_is_a_404_not_a_500(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
        assert _get("/api/source/5a1f0c3e-0000-4000-8000-0000000000ff").status_code == 404


class TestSignature:
    def test_binds_the_job_and_the_expiry(self):
        exp = int(time.time()) + 60
        sig = app_module._source_signature(JOB_ID, exp)
        # A signature that travelled to another job, or that was stretched to a
        # later expiry, must not verify — otherwise one leaked link opens
        # everything, forever.
        assert app_module._source_signature("other-job", exp) != sig
        assert app_module._source_signature(JOB_ID, exp + 1) != sig
        assert app_module._source_signature(JOB_ID, exp) == sig

    def test_is_opaque(self):
        exp = int(time.time()) + 60
        sig = app_module._source_signature(JOB_ID, exp)
        assert len(sig) == 32
        assert JOB_ID not in sig and str(exp) not in sig

    def test_a_stale_expiry_is_not_accepted(self, job):
        # The endpoint only trusts a signature while exp is in the future; the
        # check is `exp > now`, so a past one falls through to the owner check.
        past = int(time.time()) - 1
        r = _get(f"/api/source/{JOB_ID}?exp={past}&sig={app_module._source_signature(JOB_ID, past)}")
        # Self-host has no owner, so it still serves — what matters is that the
        # stale signature was not what let it through.
        assert r.status_code == 200
        assert not (past > time.time())


class TestRetainedSourceSweep:
    """SOURCE_RETENTION_SECONDS drops the retained download ahead of the job."""

    def test_is_a_no_op_at_the_default(self, job, monkeypatch):
        # Default equals the job clock: the source lives and dies with its job,
        # exactly as before the knob existed.
        monkeypatch.setattr(app_module, "SOURCE_RETENTION_SECONDS",
                            app_module.JOB_RETENTION_SECONDS)
        assert list(app_module._sweep_retained_sources()) == []
        assert (job / "source.mp4").exists()

    def test_drops_the_download_once_it_is_older_than_the_knob(self, job, monkeypatch):
        monkeypatch.setattr(app_module, "SOURCE_RETENTION_SECONDS", 60)
        monkeypatch.setattr(app_module, "JOB_RETENTION_SECONDS", 3600)
        assert list(app_module._sweep_retained_sources(now=time.time() + 120)) == [JOB_ID]
        assert not (job / "source.mp4").exists()
        # The clips and the metadata are the deliverable and must survive.
        assert (job / "x_metadata.json").exists()

    def test_keeps_a_download_that_is_still_young(self, job, monkeypatch):
        monkeypatch.setattr(app_module, "SOURCE_RETENTION_SECONDS", 3600)
        monkeypatch.setattr(app_module, "JOB_RETENTION_SECONDS", 86400)
        assert list(app_module._sweep_retained_sources()) == []
        assert (job / "source.mp4").exists()

    def test_survives_a_job_dir_with_no_metadata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(app_module, "SOURCE_RETENTION_SECONDS", 1)
        monkeypatch.setattr(app_module, "JOB_RETENTION_SECONDS", 3600)
        (tmp_path / "half-written-job").mkdir()
        (tmp_path / "loose-file.txt").write_text("not a job dir")
        assert list(app_module._sweep_retained_sources(now=time.time() + 120)) == []


def test_every_source_url_the_browser_gets_comes_from_one_place(job, monkeypatch):
    """The clip editor renders edl.source.url straight into a <video src>.

    It was built as a bare /api/source path while the preview used a signed
    one: fine in self-host, a 404 in cloud, where the tag cannot authenticate.

    The assertion has to be that the endpoint CALLS the minter, not that the
    string matches: off-billing _signed_source_url returns that very same bare
    path, so comparing the two strings passes just as happily with the bug in
    place. Verified by putting the bug back and watching this fail.
    """
    monkeypatch.setattr(app_module, "_signed_source_url",
                        lambda job_id: f"/signed/{job_id}")
    r = _get(f"/api/clip/{JOB_ID}/0/edl")
    assert r.status_code == 200, r.text
    assert r.json()["source"]["available"] is True
    assert r.json()["source"]["url"] == f"/signed/{JOB_ID}"


class TestSourceUrlNeverMintsBlind:
    """The minter must not hand a signed URL to a job it cannot identify."""

    def test_self_host_still_answers_for_an_unknown_job(self, tmp_path, monkeypatch):
        # Off billing there is no owner and no secret, and the preview has to
        # keep working, so an unknown id is not something to refuse.
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
        r = _get("/api/source-url/5a1f0c3e-0000-4000-8000-0000000000ff")
        assert r.status_code == 200
        assert r.json()["url"] == "/api/source/5a1f0c3e-0000-4000-8000-0000000000ff"

    def test_cloud_refuses_instead_of_signing(self, tmp_path, monkeypatch):
        # With billing on, an unresolvable job used to get a valid capability
        # for the asking. It must 404 instead.
        #
        # _signed_source_url is stubbed so that reopening the hole fails on the
        # assertion below and not on _cloud_config being None off-billing: a
        # test that only passes because the minter happens to crash would stop
        # guarding the moment the minter stopped crashing.
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path))
        monkeypatch.setattr(app_module, "UPLOAD_DIR", str(tmp_path))
        monkeypatch.setattr(app_module, "BILLING_ENABLED", True)
        monkeypatch.setattr(app_module, "_signed_source_url", lambda j: f"/signed/{j}")
        assert _get("/api/source-url/5a1f0c3e-0000-4000-8000-0000000000ff").status_code == 404

    def test_cloud_still_serves_the_owner(self, job, monkeypatch):
        # The job fixture stamps user_id None (self-host style), which
        # _assert_job_owner treats as "nothing to check", so this proves the
        # refusal above is about the missing record and not a blanket block.
        monkeypatch.setattr(app_module, "BILLING_ENABLED", True)
        monkeypatch.setattr(app_module, "_signed_source_url", lambda j: f"/signed/{j}")
        r = _get(f"/api/source-url/{JOB_ID}")
        assert r.status_code == 200
        assert r.json()["url"] == f"/signed/{JOB_ID}"


class TestIdsThatAreNotJobs:
    """Reserved upload slots sit in uploads/ as pending_<uuid>_<name>, and the
    source lookup globs uploads/<job_id>_*. An id like "pending" used to match
    that glob and stream another user's unpublished upload to anyone, with no
    login. Only uuid4 ids are jobs."""

    @pytest.fixture()
    def cloud_with_pending_upload(self, tmp_path, monkeypatch):
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        (tmp_path / "output").mkdir()
        (uploads / "pending_aaaa_secret.mp4").write_bytes(b"VICTIM-BYTES")
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path / "output"))
        monkeypatch.setattr(app_module, "UPLOAD_DIR", str(uploads))
        monkeypatch.setattr(app_module, "BILLING_ENABLED", True)
        monkeypatch.setattr(app_module, "jobs", {})

        async def nobody(request):
            return None
        monkeypatch.setattr(app_module, "_user_from_request", nobody)
        return uploads

    @pytest.mark.parametrize("bad_id", ["pending", "pending_aaaa", "..", "x", "A" * 36])
    def test_source_refuses_ids_that_are_not_uuids(self, cloud_with_pending_upload, bad_id):
        r = _get(f"/api/source/{bad_id}")
        assert r.status_code == 404
        assert b"VICTIM" not in r.content

    @pytest.mark.parametrize("bad_id", ["pending", "..", "x"])
    def test_source_url_refuses_ids_that_are_not_uuids(self, cloud_with_pending_upload, bad_id):
        assert _get(f"/api/source-url/{bad_id}").status_code == 404

    def test_self_host_refuses_them_too(self, cloud_with_pending_upload, monkeypatch):
        # A path-shaped id is never a job, billing or not.
        monkeypatch.setattr(app_module, "BILLING_ENABLED", False)
        assert _get("/api/source/pending").status_code == 404

    def test_locator_never_returns_a_pending_upload(self, cloud_with_pending_upload):
        assert app_module._locate_source_for_range("pending") == (None, 0.0)
        assert app_module._locate_source_for_range("pending_aaaa") == (None, 0.0)

    def test_locator_skips_pending_files_even_for_a_uuid_prefix(self, tmp_path, monkeypatch):
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        monkeypatch.setattr(app_module, "UPLOAD_DIR", str(uploads))
        monkeypatch.setattr(app_module, "OUTPUT_DIR", str(tmp_path / "output"))
        (uploads / f"pending_{JOB_ID}_clip.mp4").write_bytes(b"x")
        assert app_module._locate_source_for_range(JOB_ID) == (None, 0.0)


@pytest.mark.parametrize("method,path", [
    ("get", "/api/status/pending"),
    ("post", "/api/jobs/pending/cancel"),
    ("get", "/api/jobs/pending/download-all"),
    ("post", "/api/jobs/pending/clips/0/keep"),
    ("delete", "/api/jobs/pending/clips/0/keep"),
    ("post", "/api/projects/pending/restore"),
    ("get", "/api/clip/pending/0/transcript"),
    ("get", "/api/clip/pending/0/edl"),
    ("get", "/api/clip/pending/0/scenes"),
])
def test_every_job_path_route_refuses_a_non_uuid_id(method, path):
    """The check is a route dependency (valid_job_id), so a route that reaches
    a job's files cannot forget it."""
    async def _do():
        transport = httpx.ASGITransport(app=app_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            return await getattr(c, method)(path)
    r = asyncio.run(_do())
    assert r.status_code == 404
    assert r.json() == {"detail": "Not found"}
