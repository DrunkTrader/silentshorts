"""Built-in YouTube upload receiver (youtube_upload.py), with no network:
every Google endpoint answers through httpx.MockTransport."""
import asyncio
import io
import json
import logging
import os
import stat

import httpx
import pytest
import starlette.formparsers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from silentshorts.integrations import youtube_upload as yu

SECRET = "test-webhook-secret"
REFRESH = "1//refresh-token-value"
ACCESS = "ya29.access-token-value"
CLIENT_SECRET = "GOCSPX-client-secret-value"
SESSION = "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=abc"
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100


@pytest.fixture
def token(tmp_path, monkeypatch):
    path = str(tmp_path / "state" / "youtube_token.json")
    yu.save_token({"client_id": "cid", "client_secret": CLIENT_SECRET, "refresh_token": REFRESH}, path)
    monkeypatch.setenv("YOUTUBE_TOKEN_PATH", path)
    monkeypatch.setattr(yu, "RETRY_DELAY", 0)
    return path


class Google:
    """A scripted Google: token endpoint, resumable init, then the PUT answers in order."""

    def __init__(self, puts=None, init=None, refresh=None):
        self.puts = list(puts or [httpx.Response(200, json={"id": "VID123", "status": {"privacyStatus": "unlisted"}})])
        self.init = init or httpx.Response(200, headers={"Location": SESSION})
        self.refresh = refresh or httpx.Response(200, json={"access_token": ACCESS, "expires_in": 3599})
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        if str(request.url) == yu.TOKEN_URL:
            return self.refresh
        if request.method == "POST":
            return self.init
        answer = self.puts.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def client(self):
        return httpx.AsyncClient(transport=httpx.MockTransport(self))


def run_upload(google, data=MP4, privacy="unlisted", **kw):
    async def go():
        async with google.client() as c:
            return await yu.upload_video(c, io.BytesIO(data), len(data), title="T", description="D",
                                         tags=["a", "b"], privacy=privacy, **kw)
    return asyncio.run(go())


# --- token refresh ---------------------------------------------------------
def test_refresh_sends_the_refresh_token_and_uses_the_access_token(token):
    g = Google()
    run_upload(g)
    form = dict(x.split("=", 1) for x in g.calls[0].content.decode().split("&"))
    assert g.calls[0].url == yu.TOKEN_URL
    assert form["grant_type"] == "refresh_token" and form["client_id"] == "cid"
    assert "refresh_token" in form and "client_secret" in form
    assert g.calls[1].headers["authorization"] == f"Bearer {ACCESS}"
    assert g.calls[2].headers["authorization"] == f"Bearer {ACCESS}"


def test_a_rotated_refresh_token_is_saved(token):
    g = Google(refresh=httpx.Response(200, json={"access_token": ACCESS, "refresh_token": "1//new"}))
    run_upload(g)
    assert json.load(open(token))["refresh_token"] == "1//new"
    assert stat.S_IMODE(os.stat(token).st_mode) == 0o600


@pytest.mark.parametrize("answer, expected", [
    (httpx.Response(400, json={"error": "invalid_grant", "error_description": "Token has been expired or revoked."}), yu.REAUTH),
    (httpx.Response(401, json={"error": "invalid_client"}), "no longer knows the OAuth client"),
    (httpx.Response(500, text="boom"), "Google sign-in failed (HTTP 500)"),
])
def test_refresh_errors_are_short(token, answer, expected):
    with pytest.raises(yu.UploadError) as e:
        run_upload(Google(refresh=answer))
    assert expected in str(e.value) and "revoked." not in str(e.value)


def test_no_token_file_means_not_connected(tmp_path):
    with pytest.raises(yu.UploadError) as e:
        run_upload(Google(), path=str(tmp_path / "missing.json"))
    assert str(e.value) == yu.NOT_CONNECTED


# --- resumable upload ------------------------------------------------------
def test_resumable_sequence(token):
    g = Google()
    res = run_upload(g)
    init, put = g.calls[1], g.calls[2]
    assert init.method == "POST" and init.url.params["uploadType"] == "resumable"
    assert init.url.params["part"] == "snippet,status"
    assert init.headers["x-upload-content-type"] == "video/mp4"
    assert init.headers["x-upload-content-length"] == str(len(MP4))
    meta = json.loads(init.content)
    assert meta["snippet"] == {"title": "T", "description": "D", "tags": ["a", "b"], "categoryId": "22"}
    assert meta["status"] == {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}
    assert put.method == "PUT" and str(put.url) == SESSION
    assert put.content == MP4 and put.headers["content-range"] == f"bytes 0-{len(MP4) - 1}/{len(MP4)}"
    assert res == {"video_id": "VID123", "youtube_url": "https://youtu.be/VID123",
                   "privacy": "unlisted", "forced_private": False}


def test_an_interrupted_upload_resumes_where_google_stopped(token):
    g = Google(puts=[httpx.Response(503), httpx.Response(308, headers={"Range": "bytes=0-9"}),
                     httpx.Response(201, json={"id": "VID123", "status": {"privacyStatus": "unlisted"}})])
    assert run_upload(g)["video_id"] == "VID123"
    query, rest = g.calls[3], g.calls[4]
    assert query.headers["content-range"] == f"bytes */{len(MP4)}" and query.content == b""
    assert rest.headers["content-range"] == f"bytes 10-{len(MP4) - 1}/{len(MP4)}"
    assert rest.content == MP4[10:]


def test_network_errors_give_up_after_a_few_tries(token):
    g = Google(puts=[httpx.ConnectError("x")] * (2 * yu.TRIES))
    with pytest.raises(yu.UploadError, match="kept failing"):
        run_upload(g)


def test_forced_private_is_flagged(token):
    g = Google(puts=[httpx.Response(200, json={"id": "V", "status": {"privacyStatus": "private"}})])
    assert run_upload(g, privacy="public")["forced_private"] is True


def _google_error(status, reason):
    return httpx.Response(status, json={"error": {"code": status, "message": "LONG GOOGLE TEXT",
                                                  "errors": [{"reason": reason, "message": "LONG GOOGLE TEXT"}]}})


@pytest.mark.parametrize("answer, expected", [
    (_google_error(403, "quotaExceeded"), yu.QUOTA),
    (_google_error(400, "uploadLimitExceeded"), yu.QUOTA),
    (_google_error(401, "authError"), yu.REAUTH),
    (_google_error(401, "youtubeSignupRequired"), "no YouTube channel"),
    (_google_error(400, "invalidTitle"), "YouTube refused the upload (HTTP 400: invalidTitle)"),
    (httpx.Response(500, text="<html>"), "YouTube upload failed (HTTP 500)"),
])
def test_api_errors_are_short(token, answer, expected):
    with pytest.raises(yu.UploadError) as e:
        run_upload(Google(init=answer))
    assert str(e.value) == expected or expected in str(e.value)
    assert "LONG GOOGLE TEXT" not in str(e.value)


def test_quota_error_on_the_put_too(token):
    with pytest.raises(yu.UploadError, match="quota"):
        run_upload(Google(puts=[_google_error(403, "quotaExceeded")]))


# --- token file ------------------------------------------------------------
def test_token_file_is_owner_only(tmp_path):
    path = str(tmp_path / "new" / "tok.json")
    yu.save_token({"refresh_token": REFRESH}, path)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode) == 0o700
    assert os.listdir(os.path.dirname(path)) == ["tok.json"]   # no temp file left


def test_token_path_default_is_the_state_dir():
    assert yu.token_path({"HOME": "/h", "XDG_STATE_HOME": "/s"}) == "/s/silentshorts/youtube_token.json"
    assert yu.token_path({"YOUTUBE_TOKEN_PATH": "/x.json"}) == "/x.json"


def test_tokens_never_reach_the_logs(token, caplog):
    caplog.set_level(logging.DEBUG)
    run_upload(Google())
    for answer in (_google_error(403, "quotaExceeded"), httpx.Response(400, json={"error": "invalid_grant"})):
        with pytest.raises(yu.UploadError):
            run_upload(Google(init=answer, refresh=answer if answer.status_code == 400 else None))
    for s in (REFRESH, ACCESS, CLIENT_SECRET):
        assert s not in caplog.text


# --- the endpoint ----------------------------------------------------------
@pytest.fixture
def spooled(monkeypatch):
    """Every temp file the multipart parser spools the video into."""
    made = []

    class Tracked(starlette.formparsers.SpooledTemporaryFile):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            made.append(self)

    monkeypatch.setattr(starlette.formparsers, "SpooledTemporaryFile", Tracked)
    return made


@pytest.fixture
def api(monkeypatch, token, spooled):
    monkeypatch.setenv("N8N_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("BILLING_ENABLED", "0")
    google = Google()
    monkeypatch.setattr(yu, "client_factory", google.client)
    app = FastAPI()
    app.include_router(yu.router)
    client = TestClient(app, raise_server_exceptions=False)
    client.google = google
    return client


def post(client, secret=SECRET, video=MP4, **fields):
    data = {"title": "My clip", "description": "Desc #one", "tags": "one,two",
            "privacy": "unlisted", "job_id": "j", "clip_index": "0", **fields}
    headers = {} if secret is None else {"X-SilentShorts-Secret": secret}
    files = {"video": ("clip.mp4", video, "video/mp4")} if video is not None else None
    return client.post("/api/integrations/youtube/upload", data=data, files=files, headers=headers)


def test_right_secret_uploads(api, spooled):
    r = post(api)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "youtube_url": "https://youtu.be/VID123", "privacy": "unlisted"}
    meta = json.loads(api.google.calls[1].content)
    assert meta["snippet"]["tags"] == ["one", "two"] and meta["snippet"]["title"] == "My clip"
    assert api.google.calls[2].content == MP4
    assert spooled and all(f.closed for f in spooled)


def test_forced_private_note_reaches_the_bot(api):
    api.google.puts = [httpx.Response(200, json={"id": "V", "status": {"privacyStatus": "private"}})]
    r = post(api, privacy="public")
    assert r.json()["ok"] is True
    assert r.json()["youtube_url"].startswith("https://youtu.be/V (YouTube kept it private")


@pytest.mark.parametrize("secret", [None, "", "wrong", SECRET + "x", SECRET[:-1]])
def test_wrong_or_missing_secret(api, secret):
    r = post(api, secret=secret)
    assert r.status_code == 401 and r.json()["ok"] is False
    assert api.google.calls == []


def test_secret_is_compared_in_constant_time(api, monkeypatch):
    seen = []
    real = yu.hmac.compare_digest

    def spy(a, b):
        seen.append((a, b))
        return real(a, b)
    monkeypatch.setattr(yu.hmac, "compare_digest", spy)
    assert post(api, secret="wrong").status_code == 401
    assert post(api).status_code == 200
    assert seen == [(b"wrong", SECRET.encode()), (SECRET.encode(), SECRET.encode())]


def test_disabled_without_secret(api, monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_SECRET")
    assert post(api).status_code == 404
    assert post(api, secret="").status_code == 404
    assert api.google.calls == []


def test_disabled_under_billing(api, monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "1")
    assert post(api).status_code == 404
    assert api.google.calls == []


def test_not_connected(api, monkeypatch, tmp_path, spooled):
    monkeypatch.setenv("YOUTUBE_TOKEN_PATH", str(tmp_path / "none.json"))
    r = post(api)
    assert r.status_code == 503 and r.json() == {"ok": False, "error": yu.NOT_CONNECTED}
    assert all(f.closed for f in spooled)


@pytest.mark.parametrize("fields, video, why", [
    ({"privacy": "friends"}, MP4, "privacy"),
    ({"privacy": ""}, MP4, "privacy"),
    ({"title": "   "}, MP4, "title"),
    ({"title": "<>"}, MP4, "title"),
    ({"title": "x" * 101}, MP4, "title"),
    ({}, b"GIF89a" + b"\x00" * 50, "not an mp4"),
    ({}, b"\x00\x00\x00\x18ftyp", "not an mp4"),
    ({}, None, "must be a file"),
])
def test_field_validation(api, spooled, fields, video, why):
    r = post(api, video=video, **fields)
    assert r.status_code == 400 and why in r.json()["error"]
    assert api.google.calls == []
    assert all(f.closed for f in spooled)


def test_title_of_100_chars_is_fine(api):
    assert post(api, title="x" * 100).json()["ok"] is True


def test_size_cap(api, monkeypatch, spooled):
    monkeypatch.setattr(yu, "MAX_BYTES", 1000)
    r = post(api, video=MP4 + b"\x00" * 100_000)
    assert r.status_code == 413 and api.google.calls == []
    r = post(api, video=MP4 + b"\x00" * 900)   # under the Content-Length slack, over the cap
    assert r.status_code == 413 and api.google.calls == []
    assert all(f.closed for f in spooled)


def test_temp_file_closed_when_youtube_fails(api, spooled):
    api.google.init = _google_error(403, "quotaExceeded")
    r = post(api)
    assert r.status_code == 502 and r.json() == {"ok": False, "error": yu.QUOTA}
    assert spooled and all(f.closed for f in spooled)


def test_temp_file_closed_on_a_crash(api, monkeypatch, spooled):
    async def boom(*a, **kw):
        raise RuntimeError("bug")
    monkeypatch.setattr(yu, "upload_video", boom)
    assert post(api).status_code == 500
    assert spooled and all(f.closed for f in spooled)


# --- sign-in helper --------------------------------------------------------
def test_auth_url_uses_pkce_loopback_and_upload_scope():
    verifier, challenge = yu.pkce_pair()
    assert 43 <= len(verifier) <= 128
    url = httpx.URL(yu.auth_url("cid", challenge, "st"))
    p = url.params
    assert p["scope"] == yu.SCOPE == "https://www.googleapis.com/auth/youtube.upload"
    assert p["redirect_uri"].startswith("http://127.0.0.1:")
    assert p["code_challenge_method"] == "S256" and p["code_challenge"] == challenge
    assert p["access_type"] == "offline" and p["state"] == "st"


def test_parse_redirect():
    assert yu.parse_redirect("http://127.0.0.1:8765/?state=st&code=4/abc&scope=x", "st") == "4/abc"
    assert yu.parse_redirect("  4/bare-code \n", "st") == "4/bare-code"
    for bad in ("http://127.0.0.1:8765/?state=other&code=4/abc",
                "http://127.0.0.1:8765/?error=access_denied&state=st", ""):
        with pytest.raises(SystemExit):
            yu.parse_redirect(bad, "st")


def _client_file(tmp_path, kind="installed"):
    path = tmp_path / "client_secret.json"
    path.write_text(json.dumps({kind: {"client_id": "cid", "client_secret": CLIENT_SECRET}}))
    return str(path)


def test_auth_saves_an_owner_only_token_and_prints_no_secret(tmp_path, monkeypatch, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    seen = {}

    def fake_post(url, data, timeout):
        seen.update(data)
        return httpx.Response(200, json={"access_token": ACCESS, "refresh_token": REFRESH})

    monkeypatch.setattr(yu.httpx, "post", fake_post)
    out = str(tmp_path / "s" / "tok.json")

    def paste(prompt):
        url = httpx.URL(capsys.readouterr().out.split("\n\n")[1].strip())
        return f"http://127.0.0.1:8765/?state={url.params['state']}&code=4/xyz"

    assert yu.auth(_client_file(tmp_path), out, ask=paste) == 0
    assert seen["code"] == "4/xyz" and seen["grant_type"] == "authorization_code"
    assert seen["code_verifier"] and seen["redirect_uri"] == yu.REDIRECT_URI
    assert json.load(open(out)) == {"client_id": "cid", "client_secret": CLIENT_SECRET, "refresh_token": REFRESH}
    assert stat.S_IMODE(os.stat(out).st_mode) == 0o600
    printed = capsys.readouterr()
    for s in (REFRESH, ACCESS, CLIENT_SECRET):
        assert s not in printed.out + printed.err + caplog.text


def test_auth_without_a_paste_saves_nothing(tmp_path, capsys):
    out = tmp_path / "tok.json"

    def eof(prompt):
        raise EOFError
    assert yu.auth(_client_file(tmp_path), str(out), ask=eof) == 1
    assert "accounts.google.com" in capsys.readouterr().out and not out.exists()


def test_auth_refuses_a_web_client(tmp_path):
    with pytest.raises(SystemExit, match="Desktop app"):
        yu.auth(_client_file(tmp_path, "web"), str(tmp_path / "t.json"))
