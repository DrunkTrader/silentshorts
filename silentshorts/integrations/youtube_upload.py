"""YouTube upload without n8n: a built-in receiver for the intake bot's webhook.

The Telegram bot posts each approved clip to ``N8N_UPLOAD_WEBHOOK_URL`` (the
multipart contract in docs/telegram-bot.md). Pointing that URL at
``POST /api/integrations/youtube/upload`` on the local API makes this module the
receiver: it checks ``X-SilentShorts-Secret`` against ``N8N_WEBHOOK_SECRET``
and uploads the mp4 with the YouTube Data API v3 (``videos.insert``, resumable
upload, plain httpx).

Sign-in is a one-time OAuth 2.0 "Desktop app" flow with PKCE, run on the server
with ``python -m silentshorts.integrations.youtube_upload auth --client-secret
<file>``. The device flow is not an option: Google allows only the ``youtube``
and ``youtube.readonly`` scopes there, not ``youtube.upload``, and the old
copy/paste (OOB) redirect is no longer supported. So the redirect goes to a
loopback address nothing listens on, and the user copies the address the
browser ends up on. The refresh token lives in a 0600 file outside the repo
(``token_path``) and is never logged or printed. Setup: docs/youtube-upload.md.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sys
import tempfile
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

log = logging.getLogger(__name__)
router = APIRouter()

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
# Nothing listens here: the browser shows "can't connect" and the user copies its address.
REDIRECT_URI = "http://127.0.0.1:8765"

PRIVACY = ("private", "unlisted", "public")
TITLE_CHARS = 100
DESCRIPTION_CHARS = 5000
TAG_CHARS = 450                  # YouTube caps all tags at 500 characters
MAX_BYTES = 100 * 1024 * 1024    # the bot sends 50 MB at most (Bot API limit)
CHUNK = 1024 * 1024
TRIES = 4
RETRY_DELAY = 2.0                # seconds, times the attempt number

NOT_CONNECTED = ("YouTube is not connected: run `python -m silentshorts.integrations."
                 "youtube_upload auth` on the server (docs/youtube-upload.md)")
REAUTH = ("YouTube sign-in expired or was revoked (sign-ins of an app in Testing last "
          "7 days): run the auth helper again")
QUOTA = ("YouTube upload quota used up for today (it resets at midnight Pacific time)")
_QUOTA_REASONS = {"quotaExceeded", "uploadLimitExceeded", "dailyLimitExceeded",
                  "rateLimitExceeded", "userRateLimitExceeded"}


class UploadError(Exception):
    """A short reason that is safe to show in the chat."""


def client_factory():
    return httpx.AsyncClient(timeout=httpx.Timeout(60.0, write=600.0))


# --- token file ----------------------------------------------------------
def token_path(env=None) -> str:
    env = os.environ if env is None else env
    if env.get("YOUTUBE_TOKEN_PATH"):
        return env["YOUTUBE_TOKEN_PATH"]
    base = env.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "silentshorts", "youtube_token.json")


def save_token(data: dict, path: str) -> None:
    """Write the token file atomically, readable by its owner only."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, mode=0o700, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".youtube_token.")   # created 0600
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def load_token(path: str) -> dict:
    try:
        with open(path) as f:
            tok = json.load(f)
    except FileNotFoundError:
        raise UploadError(NOT_CONNECTED) from None
    except (OSError, ValueError):
        raise UploadError("The YouTube token file is unreadable: run the auth helper again") from None
    if not isinstance(tok, dict) or not tok.get("client_id") or not tok.get("refresh_token"):
        raise UploadError("The YouTube token file is incomplete: run the auth helper again")
    return tok


# --- Google answers ------------------------------------------------------
def _reason(r: httpx.Response) -> str:
    """Google's short error code (``invalid_grant``, ``quotaExceeded``...), never its message."""
    try:
        err = r.json().get("error")
    except (ValueError, AttributeError):
        return ""
    if isinstance(err, dict):   # Data API: {"error": {"errors": [{"reason": ...}], ...}}
        first = (err.get("errors") or [{}])[0]
        err = first.get("reason") if isinstance(first, dict) else ""
        err = err or ""
    return re.sub(r"[^A-Za-z_]", "", str(err))[:40]


def _api_error(r: httpx.Response) -> UploadError:
    reason = _reason(r)
    log.warning("youtube upload refused: HTTP %s %s", r.status_code, reason)
    if reason in _QUOTA_REASONS:
        return UploadError(QUOTA)
    if reason == "youtubeSignupRequired":   # a 401, but signing in again will not help
        return UploadError("This Google account has no YouTube channel yet")
    if r.status_code == 401:
        return UploadError(REAUTH)
    if r.status_code in (400, 403):
        return UploadError(f"YouTube refused the upload (HTTP {r.status_code}"
                           + (f": {reason})" if reason else ")"))
    return UploadError(f"YouTube upload failed (HTTP {r.status_code})")


async def access_token(client: httpx.AsyncClient, tok: dict, path: str) -> str:
    """A fresh access token from the refresh token (one call per upload)."""
    data = {"grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
            "client_id": tok["client_id"]}
    if tok.get("client_secret"):
        data["client_secret"] = tok["client_secret"]
    try:
        r = await client.post(TOKEN_URL, data=data)
    except httpx.HTTPError:
        raise UploadError("Google sign-in did not answer (network)") from None
    if r.status_code != 200:
        reason = _reason(r)
        log.warning("youtube token refresh refused: HTTP %s %s", r.status_code, reason)
        if reason == "invalid_grant":
            raise UploadError(REAUTH)
        if reason in ("invalid_client", "unauthorized_client"):
            raise UploadError("Google no longer knows the OAuth client: run the auth helper "
                              "again with a current client file")
        raise UploadError(f"Google sign-in failed (HTTP {r.status_code})")
    body = r.json()
    if body.get("refresh_token") and body["refresh_token"] != tok["refresh_token"]:
        tok["refresh_token"] = body["refresh_token"]   # rotated: keep the new one
        save_token(tok, path)
    if not body.get("access_token"):
        raise UploadError("Google sign-in answered without an access token")
    return body["access_token"]


# --- the upload ----------------------------------------------------------
async def _chunks(f, offset: int):
    # Local-disk reads of 1 MB: short enough not to stall the loop.
    f.seek(offset)
    while chunk := f.read(CHUNK):
        yield chunk


async def _put(client, session, headers, content_range, content=b"", length=0):
    try:
        return await client.put(session, content=content, headers={
            **headers, "Content-Length": str(length), "Content-Range": content_range})
    except httpx.HTTPError:
        return None


def _done(r: httpx.Response, privacy: str) -> dict:
    try:
        body = r.json()
    except ValueError:
        body = {}
    vid = body.get("id") if isinstance(body, dict) else None
    if not vid:
        raise UploadError("YouTube answered without a video id")
    got = (body.get("status") or {}).get("privacyStatus") or privacy
    return {"video_id": vid, "youtube_url": f"https://youtu.be/{vid}", "privacy": got,
            "forced_private": privacy != "private" and got == "private"}


async def upload_video(client: httpx.AsyncClient, f, size: int, *, title: str,
                       description: str, tags: list, privacy: str, path: str | None = None) -> dict:
    """Upload the open mp4 ``f`` (``size`` bytes) with a resumable session."""
    path = path or token_path()
    tok = load_token(path)
    auth = {"Authorization": f"Bearer {await access_token(client, tok, path)}"}
    meta = {"snippet": {"title": title, "description": description, "tags": tags,
                        "categoryId": "22"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    try:
        r = await client.post(UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"},
                              json=meta, headers={**auth, "X-Upload-Content-Type": "video/mp4",
                                                  "X-Upload-Content-Length": str(size)})
    except httpx.HTTPError:
        raise UploadError("YouTube did not answer (network)") from None
    session = r.headers.get("location")
    if r.status_code != 200 or not session:
        raise _api_error(r)

    offset = 0
    for attempt in range(TRIES):
        if attempt:
            # Interrupted: wait, then ask how much arrived and resume from there.
            await asyncio.sleep(RETRY_DELAY * attempt)
            r = await _put(client, session, auth, f"bytes */{size}")
            if r is None or r.status_code >= 500:
                continue
            if r.status_code in (200, 201):
                return _done(r, privacy)
            if r.status_code != 308:
                raise _api_error(r)
            m = re.fullmatch(r"bytes=0-(\d+)", r.headers.get("range", ""))
            offset = int(m.group(1)) + 1 if m else 0
        r = await _put(client, session, auth, f"bytes {offset}-{size - 1}/{size}",
                       _chunks(f, offset), size - offset)
        if r is not None and r.status_code in (200, 201):
            return _done(r, privacy)
        if r is not None and r.status_code < 500 and r.status_code != 308:
            raise _api_error(r)
    raise UploadError("YouTube upload kept failing (network or server errors): try again later")


# --- the webhook receiver ------------------------------------------------
def _fail(status: int, error: str) -> JSONResponse:
    return JSONResponse({"ok": False, "error": error}, status_code=status)


def _billing() -> bool:
    return os.environ.get("BILLING_ENABLED", "").lower() in ("1", "true", "yes")


def _clean(text: str) -> str:
    return text.replace("<", "").replace(">", "")   # YouTube refuses both in titles/descriptions


def _tags(raw: str) -> list:
    out, used = [], 0
    for t in (t.strip().lstrip("#") for t in raw.split(",")):
        if t and used + len(t) <= TAG_CHARS:
            out.append(t)
            used += len(t) + 1
    return out


@router.post("/api/integrations/youtube/upload")
async def youtube_upload_endpoint(request: Request):
    secret = os.environ.get("N8N_WEBHOOK_SECRET", "")
    if _billing() or not secret:
        raise HTTPException(404)   # fail closed: no secret, no endpoint; never in the Cloud
    given = request.headers.get("x-silentshorts-secret", "")
    if not hmac.compare_digest(given.encode(), secret.encode()):
        return _fail(401, "wrong or missing X-SilentShorts-Secret")
    try:
        length = int(request.headers.get("content-length", ""))
    except ValueError:
        return _fail(411, "Content-Length is required")
    if length > MAX_BYTES + 64 * 1024:   # the body cannot outgrow its Content-Length
        return _fail(413, f"video too large (max {MAX_BYTES // (1024 * 1024)} MB)")
    try:
        form = await request.form(max_files=1, max_fields=10)
    except Exception:
        return _fail(400, "unreadable multipart form")
    try:   # the video is spooled to an unnamed temp file; form.close() deletes it
        title = " ".join(str(form.get("title") or "").split())
        privacy = str(form.get("privacy") or "")
        video = form.get("video")
        if privacy not in PRIVACY:
            return _fail(400, "privacy must be private, unlisted or public")
        if not _clean(title) or len(title) > TITLE_CHARS:
            return _fail(400, f"title must be 1 to {TITLE_CHARS} characters")
        if not isinstance(video, UploadFile):
            return _fail(400, "the video field must be a file")
        head = await video.read(12)
        if len(head) < 12 or head[4:8] != b"ftyp":
            return _fail(400, "the video is not an mp4")
        size = video.size if video.size is not None else video.file.seek(0, os.SEEK_END)
        if size > MAX_BYTES:
            return _fail(413, f"video too large (max {MAX_BYTES // (1024 * 1024)} MB)")
        description = _clean(str(form.get("description") or ""))[:DESCRIPTION_CHARS]
        try:
            async with client_factory() as client:
                res = await upload_video(client, video.file, size, title=_clean(title),
                                         description=description,
                                         tags=_tags(str(form.get("tags") or "")), privacy=privacy)
        except UploadError as e:
            return _fail(503 if str(e) == NOT_CONNECTED else 502, str(e))
        log.info("youtube upload done: video %s, privacy %s", res["video_id"], res["privacy"])
        url = res["youtube_url"]
        if res["forced_private"]:
            # The bot shows youtube_url as is: the only place the note reaches the chat.
            url += f" (YouTube kept it private, not {privacy}: see docs/youtube-upload.md)"
        return {"ok": True, "youtube_url": url, "privacy": res["privacy"]}
    finally:
        await form.close()


# --- one-time sign-in (CLI) ----------------------------------------------
def _read_client(path: str) -> dict:
    with open(path) as f:
        data = json.load(f)
    if "installed" not in data:
        raise SystemExit("That is not a Desktop app client file: in Google Cloud create an "
                         "OAuth client of type 'Desktop app' and download its JSON.")
    c = data["installed"]
    if not c.get("client_id"):
        raise SystemExit("The client file has no client_id.")
    return c


def pkce_pair() -> tuple:
    verifier = secrets.token_urlsafe(64)   # 86 characters: PKCE wants 43 to 128
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge.rstrip(b"=").decode()


def auth_url(client_id: str, challenge: str, state: str) -> str:
    return AUTH_URL + "?" + urlencode({
        "client_id": client_id, "redirect_uri": REDIRECT_URI, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent",
        "code_challenge": challenge, "code_challenge_method": "S256", "state": state})


def parse_redirect(text: str, state: str) -> str:
    """The code from the pasted address (or the bare code itself)."""
    text = text.strip()
    if "code=" not in text and "error=" not in text:
        if not text:
            raise SystemExit("Nothing pasted.")
        return text   # a bare code: still bound to this sign-in by PKCE
    q = parse_qs(urlsplit(text).query if "://" in text else text.lstrip("?"))
    if q.get("error"):
        raise SystemExit(f"Google refused the sign-in: {q['error'][0][:60]}")
    if q.get("state", [""])[0] != state:
        raise SystemExit("That address is from another sign-in: paste the one from this run.")
    if not q.get("code", [""])[0]:
        raise SystemExit("No code in that address.")
    return q["code"][0]


def auth(client_file: str, path: str, ask=input) -> int:
    client = _read_client(client_file)
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(16)
    print("1. Open this address in a browser on any computer and sign in with the Google\n"
          "   account that owns the YouTube channel (allow the 'unverified app' warning:\n"
          "   it is your own app):\n\n" + auth_url(client["client_id"], challenge, state) + "\n\n"
          "2. After you allow access the browser goes to 127.0.0.1 and shows an error page\n"
          "   (nothing listens there). Copy the whole address from the address bar.\n")
    try:
        pasted = ask("3. Paste that address here and press Enter: ")
    except (EOFError, KeyboardInterrupt):
        print("\nNo address pasted; nothing saved.", file=sys.stderr)
        return 1
    code = parse_redirect(pasted, state)
    data = {"grant_type": "authorization_code", "code": code, "client_id": client["client_id"],
            "code_verifier": verifier, "redirect_uri": REDIRECT_URI}
    if client.get("client_secret"):
        data["client_secret"] = client["client_secret"]
    r = httpx.post(TOKEN_URL, data=data, timeout=30)
    if r.status_code != 200:
        print(f"Google refused the code ({_reason(r) or f'HTTP {r.status_code}'}). A code works "
              "once and for a few minutes: run auth again.", file=sys.stderr)
        return 1
    refresh = r.json().get("refresh_token")
    if not refresh:
        print("Google sent no refresh token. Remove the app's access in your Google account "
              "(Security, Third-party connections) and run auth again.", file=sys.stderr)
        return 1
    save_token({"client_id": client["client_id"], "client_secret": client.get("client_secret", ""),
                "refresh_token": refresh}, path)
    print(f"YouTube is connected. Token saved to {path} (owner-only, mode 0600).")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m silentshorts.integrations.youtube_upload",
                                description="One-time YouTube sign-in for the built-in uploader.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auth", help="sign in once and save the refresh token")
    a.add_argument("--client-secret", required=True,
                   help="the client_secret_*.json of a Google Cloud 'Desktop app' OAuth client")
    a.add_argument("--token-path", help="where to save the token (default: YOUTUBE_TOKEN_PATH "
                                        "or ~/.local/state/silentshorts/youtube_token.json)")
    args = p.parse_args(argv)
    return auth(args.client_secret, args.token_path or token_path())


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()   # same YOUTUBE_TOKEN_PATH as the API
    sys.exit(main())
