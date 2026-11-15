# Ponytail review: OpenShorts

Reviewed at commit `acc80cf` (branch state with `LICENSE` deleted and `HANDOFF_PROMPT.md` untracked).

**Load assumed:** two modes. Self-host (one person, `docker compose up`, no billing) and the Cloud edition (`BILLING_ENABLED`, many users, shared disk, two containers during deploys). Findings say which mode they hit.

**What this project does:** OpenShorts turns long videos into short vertical clips. A FastAPI server (`app.py`) takes a YouTube link or an upload, runs a child process (`main.py`) that transcribes, picks moments with an LLM, cuts with FFmpeg and reframes. The `cloud/` folder adds accounts, billing and per-user media access. A Telegram bot, an MCP server and a React dashboard sit on top.

**Checked:** 1908 tests pass, 51 skipped (`.venv-ci`, 34 s). I read the media-access code, upload and source endpoints, CORS setup, URL safety (SSRF) guards, the Telegram allow-list, and `gpu_render._eval`. I did not read all 32k lines of Python.

---

## Must fix

1. **Anyone can download another user's in-progress upload in Cloud mode** (`app.py:L4608-4644`, `L4475-4491`, `L3827`)
   - **What this is:** `GET /api/source/{job_id}` streams the original video of a job. In Cloud mode it checks the owner, unless the request carries a valid signature.
   - **Problem:** The id is never checked to be a UUID (a random 36-character id). Reserved upload slots are saved as `uploads/pending_<uuid>_<name>`, and the source lookup is `glob("uploads/<job_id>_*")`. Calling `/api/source/pending` finds no job record, so `_assert_disk_job_owner` finds no owner and returns without raising. The glob then matches `pending_*` and the first pending upload of any user is served, with no login. I traced this by reading the code. I did not run it against a live Cloud instance.
   - **Fix:** At the top of `get_source_video` and `get_source_url`, reject ids that fail `_is_uuid_id(job_id)` (the helper already exists at `L2925`). Better: when `BILLING_ENABLED` and no owner can be found, deny instead of return in `_assert_disk_job_owner`. Add one test that asks for `/api/source/pending` with a pending file present.
   - **If we skip it:** One user can read another user's unpublished raw video, which is a privacy breach.

2. **Self-host API has no login, allows every website, and listens on every network interface** (`app.py:L2859-2869`, `docker-compose.yml:L5-6`)
   - **What this is:** Self-host mode is meant for one person on their own machine. CORS (the browser rule about which sites may call an API) is set to `*`, with `allow_credentials=True`. Docker publishes port 8000 as `0.0.0.0:8000`.
   - **Problem:** Any web page the user opens can send requests to `http://localhost:8000` and read the answers: list jobs, start jobs, download clips, delete uploads. On a VPS or office network, the same API is open to the whole network, with the user's Gemini and S3 keys behind it. The 64 routes include `/api/social/post`, which posts to the user's social accounts.
   - **Fix:** In `docker-compose.yml` publish `127.0.0.1:8000:8000`. In self-host mode default `allow_origins` to the dashboard origins (`http://localhost:5175`, `http://localhost:5173`), with an env var to widen it. Drop `allow_credentials` for the wildcard case. Optionally add an `API_TOKEN` env var for anyone who exposes it.
   - **If we skip it:** A malicious web page can use the user's OpenShorts, including posting to their social accounts, with no prompt.

3. **`LICENSE` is deleted in the working tree** (`git status`: ` D LICENSE`)
   - **What this is:** The root `LICENSE` file holds the MIT license. `NOTICE`, `README.md` and `cloud/LICENSE` all say "see LICENSE".
   - **Problem:** If this deletion is committed, the repo has no license text for the core app. The README badge and `NOTICE` then point at a missing file. Anyone who copies the code has no grant.
   - **Fix:** `git checkout -- LICENSE`, unless the deletion was on purpose.
   - **If we skip it:** The project is legally unlicensed, and the README link is broken.

---

## Should fix

4. **Upload endpoint writes to disk inside the async handler** (`app.py:L3845-3873`)
   - **What this is:** `PUT /api/uploads/{id}` streams the request body into a file.
   - **Problem:** `out.write(chunk)` is a plain blocking call inside `async def`. While a multi-hundred-MB upload is written, the whole server (status polls, other uploads) waits on the disk. If the client disconnects mid-upload, `request.stream()` raises and the half-written file stays on disk until the sweep removes it. A second `PUT` to the same slot is allowed during processing and replaces the file.
   - **Fix:** Write with `await run_in_executor(None, out.write, chunk)` (or `aiofiles`). Wrap the loop in `try/except BaseException` that removes the partial file. Refuse a `PUT` once the slot is claimed by `/api/process`.
   - **If we skip it:** Under many users, uploads stall unrelated requests. Cut-off uploads leave junk on disk.

5. **Self-host has no cap on upload slots** (`app.py:L3809-3822`)
   - **What this is:** The per-user limit on open upload slots runs only when `BILLING_ENABLED`.
   - **Problem:** Combined with finding 2, anyone who can reach the port can create unlimited slots and `PUT` up to `MAX_FILE_SIZE_MB` into each. `pending_uploads` and `uploads/` grow until the TTL sweep, and the disk can fill.
   - **Fix:** Apply a single global cap (for example 20 open slots) in self-host as well. Three lines in the same function.
   - **If we skip it:** A script can fill the disk of a self-host box.

6. **Job ids are not validated on most `/api/*/{job_id}` routes** (`app.py`, for example `L3527`, `L4451`, `L4584`, `L4608`, `L4647`)
   - **What this is:** Many routes take `job_id` from the URL and join it onto `OUTPUT_DIR` or `UPLOAD_DIR`. Only a few call `_JOB_ID_RE`.
   - **Problem:** Each route needs its own care to stay safe, and finding 1 shows what happens when one is missed. For example `job_id=".."` makes `os.path.join(OUTPUT_DIR, "..")` a real directory.
   - **Fix:** One FastAPI dependency (`Depends(valid_job_id)`) that raises 404 for non-UUID ids, applied to every route with a `{job_id}` path part. Fixes finding 1 for all routes at once.
   - **If we skip it:** The next new route that forgets the check repeats finding 1.

7. **`app.py` is 9,210 lines and `main.py` is 3,251** (`app.py`, `main.py`)
   - **What this is:** `app.py` holds 64 routes, the job queue, deploy handover, media auth, uploads, social, thumbnails and SaaS Shorts.
   - **Problem:** Several jobs in one file. It is hard to read, and a missing check in one area (finding 1) is easy to overlook.
   - **Fix:** Split by job into `APIRouter` modules: `routes/uploads.py`, `routes/media.py`, `routes/social.py`, `routes/thumbnail.py`, `routes/saasshorts.py`. Move code only, no rewrites. The repo already does this for `mcp_server.py` and `free_tools.py` (`app.include_router`). Do it one router per commit.
   - **If we skip it:** Review and bug-finding stay slow, and merge conflicts stay frequent.

8. **No test for the media-access rules** (`tests/`, 143 files)
   - **What this is:** The `/videos`, `/thumbnails` and `/api/source` rules decide who sees whose clips.
   - **Problem:** I found no test that asks for another user's media, or for a non-UUID id, and expects a refusal. The suite is large (1,908 tests), so this gap is easy to miss. This is the kind of code where a regression leaks user data.
   - **Fix:** One parametrized test in Cloud mode: owner gets 200, other user gets 403/404, no credentials gets 403/404, for `/videos/…`, `/api/source/…` and `/thumbnails/…`, including ids `pending`, `..` and a valid UUID with no record.
   - **If we skip it:** A future refactor can reopen finding 1 without any test failing.

9. **Large binaries are committed to git** (`demo-openshorts.mp4`, `churchil_queen_vertical*.gif`, 18 files in `dashboard/public/demo/*.mp4`)
   - **What this is:** Demo videos and GIFs live in the repo, although `.gitignore` lists `*.mp4`.
   - **Problem:** Every clone downloads them forever, even after deletion. `.gitignore` does not protect files that were force-added.
   - **Fix:** Move the demos to GitHub Releases or a CDN and link them from the README. Keep only the ones the site needs. For history size, a one-time `git filter-repo` is optional.
   - **If we skip it:** Clone and CI checkout time grow with each new demo.

---

## Nice to have

10. **`HANDOFF_PROMPT.md` is untracked at the repo root**
    - **What this is:** A working note for another agent session.
    - **Problem:** I read it for secrets and hosts and found none, but it names the private LLM tunnel setup. It is easy to commit by accident with `git add -A` in a public repo.
    - **Fix:** Add it to `.gitignore` or delete it when the session is done.
    - **If we skip it:** Low risk. It could be committed by mistake.

11. **Cache clearing in `_media_project`** (`app.py:L2993-2994`)
    - **What this is:** The owner cache is wiped entirely when it reaches 5,000 entries.
    - **Problem:** After the wipe, every request re-queries the database at once (a burst).
    - **Fix:** Drop only the oldest half, or use `functools.lru_cache`-style eviction. Only matters at high traffic.
    - **If we skip it:** An occasional database spike.

---

**Verdict: fix 1, 2 and 3 first.** Then 4 to 6 and 8.

**Lean:** no big deletions. Finding 7 is a move, not a delete. Finding 6 removes repeated per-route checks once the dependency exists.

**Not checked:** The React dashboard and `remotion/`, the `cloud/` billing and auth logic, the Telegram bot beyond its allow-list, and `main.py`'s processing pipeline. Finding 1 is traced by reading the code and was not reproduced against a running Cloud instance.
