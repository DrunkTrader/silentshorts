# Changelog

Changes made during the audit work. Nothing here is committed yet.

## Renamed project from OpenShorts to SilentShorts

### Changed
- Display name `OpenShorts` is now `SilentShorts`. Identifiers `openshorts` and `OPENSHORTS_*` are now `silentshorts` and `SILENTSHORTS_*`. About 140 files changed.
- Email `info@openshorts.app` is now `reachoutneerajkumar@gmail.com`.
- Domain `openshorts.app` is now `drunktrader.dev`. Subdomains are kept (`api.`, `mcp.`, `www.`, `cdn.`).
- GitHub links `mutonby/openshorts` are now `DrunkTrader/silentshorts`.
- Maintainer in `glama.json` is now `DrunkTrader`.
- Renamed files and folders:
  - `cli/openshorts_cli.py` to `cli/silentshorts_cli.py`
  - `cli/openshorts.egg-info/` to `cli/silentshorts.egg-info/`
  - `skills/openshorts/` to `skills/silentshorts/`
  - `dashboard/public/logo-openshorts.png` to `logo-silentshorts.png`
  - `demo-openshorts.mp4` to `demo-silentshorts.mp4`
  - `fonts/openshorts-fontmap.conf` to `silentshorts-fontmap.conf`
  - three `examples/n8n/openshorts-*.json` files to `silentshorts-*.json`

### Breaking for existing users and deployments
- Webhook headers are now `X-SilentShorts-Signature` and `X-SilentShorts-Secret`. Receivers must be updated.
- Cookie and localStorage keys are renamed, so current users are logged out once.
- The CLI package and command are now `silentshorts`. Publishing needs a new PyPI project.
- Deploy paths (`/opt/silentshorts/`, `/etc/silentshorts-backup.env`) and container names changed. A live server needs the same rename.
- `drunktrader.dev`, `api.drunktrader.dev` and `mcp.drunktrader.dev` need DNS and hosting you control.

### Left unchanged on purpose
- `NOTICE` and `cloud/LICENSE` keep the original "OpenShorts" copyright and license text. `NOTICE` now says SilentShorts is a fork of `mutonby/openshorts`.
- Two `mutonby/skill-autoshorts` links in `dashboard/src/App.jsx` (a different upstream repo).
- Text drawn inside demo images and video (only the file names changed).
- The local folder is still named `openshorts`.
- `HANDOFF_PROMPT.md` and the earlier review files in `audit/markdown/`.

### Verified
- `pytest tests/`: 1908 passed, 51 skipped.
- `npm run build` and `npm run lint` in `dashboard/`: pass.
- `docker-compose.yml` and `docker-compose.cloud.yml` parse.

## Stopped running services
- Stopped the app on port 8010 (`uvicorn app:app`, pid 203423). The Telegram bot runs inside it, so it stopped too.
- Left running: Docker container `openshorts-n8n-n8n-1` (n8n example stack), and unrelated services on port 8000.

## Added review reports
- `audit/markdown/ponytail-review.md`: change review with 11 findings.
- `audit/markdown/maintainer-review.md`: full architecture, quality, testing, features and roadmap review. It also corrects two points in the first report and reproduces the cloud-mode upload leak (`GET /api/source/pending`).

## Applied the maintainer review (`audit/markdown/maintainer-review.md`)

Step by step log with reasons and decisions: `audit/markdown/PROGRESS.md`. Tests: 1908 passed before, 1942 passed after (51 skipped both times).

### Security
- **Fixed the cloud-mode leak of other users' pending uploads.** `/api/source/pending` used to stream a reserved upload with no login. Job ids must now be uuid4 strings. 11 `{job_id}` routes declare `Depends(valid_job_id)` and answer 404 for anything else, and the source locator skips `pending_*` files.
- **Self-host CORS no longer answers `*` with credentials.** It allows the local dashboard origins. Set `ALLOWED_ORIGINS` to allow others (`*` restores the old behavior).
- **`docker-compose.yml` binds backend, frontend and renderer to `127.0.0.1`.** Other machines can no longer reach them. Change the ports back if you rely on that.
- Restored the `LICENSE` file.

### Reliability
- Upload PUT writes to disk through the executor, marks the slot incomplete while writing, and deletes the partial file on any failure.
- Self-host caps open upload slots at 20 (`MAX_PENDING_UPLOADS_SELF_HOST`).
- The media owner cache drops its older half when full, not everything at once.

### Developer experience
- Added `ruff.toml` and a `backend-lint` CI job (real errors only). `npm run lint` now runs in CI.
- Deleted 13 lines of unreachable code in `saasshorts.py` that referenced an undefined name.
- `CLAUDE.md` corrected and extended. `HANDOFF_PROMPT.md` is git-ignored.

### Tests added or changed
- New: `tests/test_cors_policy.py`, `tests/test_upload_slots.py`. Extended: `tests/test_source_access.py`, `tests/test_media_access.py`.
- Ten existing test files switched from short fake job ids to uuid-shaped ones.

### Breaking for existing setups
- Anything that calls `/api/*/{job_id}` with an id that is not a uuid4 now gets 404.
- A browser app on another origin needs `ALLOWED_ORIGINS`.
- Reaching the Docker ports from another machine needs a port change or a reverse proxy.

### Corrections to the review
- Two performance notes about blocking `subprocess` calls in async routes were wrong; both already run in workers. No change made.

### Not done (needs your decision or a separate session)
- Router split of `app.py`, bounded stores, `logging` migration, long-function extraction, Remotion unification, moving demo binaries out of git, self-host `API_TOKEN`.
- The 35 unused imports are left as is, because tests reach some of them through `app_module`.

### Running state
- The app was restarted on the new code (`127.0.0.1:8010`, Telegram bot polling). Live checks of the 404s and CORS passed.

## Open items
- See "Not done" above. The three items listed here earlier (upload leak, `LICENSE`, self-host bind and CORS) are now fixed.
