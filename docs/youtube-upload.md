# YouTube upload without n8n (self-host)

The Telegram intake bot uploads approved clips by posting them to a webhook
(`N8N_UPLOAD_WEBHOOK_URL`, contract in [telegram-bot.md](telegram-bot.md)). The
API ships a receiver for that contract, so no n8n is needed:

```
POST /api/integrations/youtube/upload
```

It uploads the clip with the YouTube Data API v3 (`videos.insert`, resumable
upload) to the channel you sign in with once. Code:
`silentshorts/integrations/youtube_upload.py`.

## What you need

- A Google account with a YouTube channel.
- A Google Cloud project with an OAuth client of type **Desktop app**.
- A shell on the server, and a browser on any computer (the server can be
  headless).

## 1. Google Cloud project

1. Open the Google Cloud console and create a project (any name).
2. APIs & Services → Library: enable **YouTube Data API v3**.
3. APIs & Services → OAuth consent screen (Google Auth Platform):
   - User type **External**, app name and support email of your choice.
   - Scopes: you can leave them empty; the helper asks for
     `https://www.googleapis.com/auth/youtube.upload` itself.
   - Audience / Test users: add the Google account that owns the channel.
   - Leave the publishing status on **Testing**.
4. APIs & Services → Credentials → Create credentials → OAuth client ID →
   application type **Desktop app**. Download the JSON
   (`client_secret_….json`) and copy it to the server, outside the repository.

## 2. Sign in once (on the server)

Run it as the same user that runs the API, from the repository root:

```
python -m silentshorts.integrations.youtube_upload auth --client-secret /path/to/client_secret.json
```

1. The helper prints a Google address. Open it in a browser on any computer.
2. Sign in with the channel's account. Google warns that the app is not
   verified: it is your own app, so choose Continue, and allow the upload
   access.
3. The browser then goes to `http://127.0.0.1:8765/?state=…&code=…` and shows
   a "can't connect" page. That is expected: nothing listens there. Copy the
   whole address from the address bar.
4. Paste it into the helper and press Enter. It says "YouTube is connected" and
   saves the token.

A code works once and for a few minutes; if the exchange fails, run the helper
again. Pasting just the `code` value also works.

The token file holds the client id, the client secret and the refresh token.
It is written owner-only (mode 0600, in a 0700 folder) to
`YOUTUBE_TOKEN_PATH`, or by default to
`$XDG_STATE_HOME/silentshorts/youtube_token.json`
(`~/.local/state/silentshorts/youtube_token.json`). It is never written to the
repository or to the logs. Delete it to disconnect; you can also revoke the
access in your Google account (Security, Third-party connections).

Why not the device flow ("enter this code on another device"): Google allows
only the `youtube` and `youtube.readonly` scopes there, not `youtube.upload`,
and it needs a different client type. The old copy/paste (out-of-band)
redirect is no longer supported. The loopback redirect plus PKCE, with the
address pasted back, is the Desktop-app flow Google documents.

## 3. Point the bot at the receiver

In `.env` (then restart the API):

```
N8N_UPLOAD_WEBHOOK_URL=http://127.0.0.1:<API port>/api/integrations/youtube/upload
N8N_WEBHOOK_SECRET=<a long random string, e.g. from: openssl rand -hex 32>
# optional, default ~/.local/state/silentshorts/youtube_token.json
YOUTUBE_TOKEN_PATH=
```

The bot sends the secret in `X-SilentShorts-Secret` and the receiver checks it
against the same `N8N_WEBHOOK_SECRET`. The variable names stay those of the bot
for now, because the bot reads them.

## How the receiver behaves

- Off (404) unless `N8N_WEBHOOK_SECRET` is set, and always off in the Cloud
  edition (`BILLING_ENABLED`). A wrong or missing secret gets 401 (the secret
  is compared in constant time). The endpoint has no other authentication:
  keep the API bound to loopback.
- Fields as in the bot's contract. Refused with 400: privacy other than
  `private|unlisted|public`, an empty title or one over 100 characters, a
  `video` that is not an mp4 (`ftyp` magic bytes). Refused with 413: over
  100 MB (the bot sends 50 MB at most). A body without `Content-Length` gets
  411.
- The video is spooled to an unnamed temporary file, which is deleted when the
  request ends, on every path.
- Metadata: title, description (5000 characters, `<` and `>` removed, since
  YouTube refuses them), tags from the `tags` field, `categoryId` 22 (People &
  Blogs), `selfDeclaredMadeForKids` false, `privacyStatus` from the bot.
- The access token is refreshed from the refresh token on every upload. The
  upload is a resumable session: an interrupted transfer asks YouTube how much
  arrived and continues from there (4 tries).
- Answer: `{"ok": true, "youtube_url": "https://youtu.be/<id>", "privacy": "…"}`,
  or `{"ok": false, "error": "<short reason>"}`. Google's own error text is
  never passed on, only its short reason code. The bot shows the error in the
  chat. This receiver has no Drive copy, so the bot's message shows
  `Drive: ?`.

| Error in the chat | What to do |
| --- | --- |
| YouTube is not connected … | Run the auth helper (step 2). |
| YouTube sign-in expired or was revoked … | Run the auth helper again. An app in **Testing** gets refresh tokens that expire after 7 days. Publish the app (OAuth consent screen → Publish app) for tokens that last; Google may then ask to verify the app for the upload scope. |
| YouTube upload quota used up for today … | Wait for the daily reset (midnight Pacific time). |
| This Google account has no YouTube channel yet | Create the channel, then sign in again. |
| YouTube refused the upload (HTTP 400/403: reason) | The reason is Google's code (`invalidTitle`, `forbidden`, …). |

## Quota

Uploads count against the project's YouTube Data API quota. The current
`videos.insert` reference lists 1 unit in a separate "Video Uploads" bucket and
100 calls per day; projects on the older accounting pay 1600 of the default
10,000 daily units per upload, about 6 uploads a day. The Quotas page of the
Cloud console shows which applies to your project.

## Private-only uploads (unaudited projects)

Google has locked videos uploaded through unaudited API projects to private
until the project passes the YouTube API compliance audit. The current
`videos.insert` reference says unverified projects are no longer restricted,
but an account's own settings can still make uploads private. The receiver does
not guess: when YouTube answers with `privacyStatus: private` for a clip that
was sent as unlisted or public, the link in the chat says "YouTube kept it
private, not <privacy>". To lift a project lock, apply for the audit (YouTube
API Services audit and quota extension form), or change the video's visibility
by hand in YouTube Studio.
