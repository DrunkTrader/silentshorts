# OpenShorts maintainer review

Reviewed at commit `acc80cf`. No source file was changed. The only thing I ran beyond reading was the existing test suite (1908 passed, 51 skipped, 34 s) and one throwaway test for item 1, which I created and deleted (`git status` shows only your pre-existing `LICENSE` deletion and untracked files).

**Scope and limits.** About 41k lines of Python, 142 test files, a React dashboard, a second Remotion project, a Rust renderer (`osrender/`). I read the code that decides who may see what (media, source, upload, CORS, SSRF guard), the job queue and cleanup, the Dockerfile, CI, dependency files, and the shape of every large function. I did not read all of `main.py`, `saasshorts.py`, `cloud/billing.py`, `cloud/autopilot.py`, the dashboard components, or `osrender/`. Where a claim comes from reading rather than running, I say so.

**Corrections to my earlier review (`ponytail-review.md`).**
- Finding 8 ("no test for media access") was wrong as written. `tests/test_media_access.py`, `test_source_access.py` and `test_id_path_guards.py` cover owner, signature, cookie and legacy-link cases well. What is missing is a test with a non-UUID id such as `pending` (see item 1).
- Finding 1 is now reproduced, not just traced (see item 1).

**Load assumed.** Two modes. Self-host: one person, one container, no billing. Cloud (`BILLING_ENABLED`): many users, Postgres, two containers during a deploy, shared disk.

---

## Current Architecture

- **One FastAPI process** (`app.py`, 9,210 lines, 64 routes) is the whole backend. It holds the job queue (`asyncio.PriorityQueue` plus `concurrency_semaphore`, `MAX_CONCURRENT_JOBS=5`), in-memory stores (`jobs`, `thumbnail_sessions`, `pending_uploads`, `publish_jobs`, about 17 module-level dicts and sets), media serving, and every feature endpoint.
- **One child process per job.** `app.py:run_job` launches `main.py` (3,251 lines) as a subprocess. `main.py` does download (yt-dlp), transcription (faster-whisper or Parakeet), scene detection, the LLM moment pick (Gemini or an OpenAI-compatible backend via `llm_backend.py`), FFmpeg cut, reframing, and writes `*_metadata.json` into `output/<job_id>/`.
- **The disk is the shared state.** `*_metadata.json`, `.owner` and a manifest with a heartbeat let a restarted or second container recover jobs (`_job_view_from_disk`, `_recover_jobs_from_disk`). This is how deploy handover works (`docs/architecture/jobs-and-deploys.md`).
- **Feature modules** are plain top-level files: layouts (`layout_picker.py`, `reframe_v2.py`, `split_layout.py`, `screencast_layout.py`, `camera_inset.py`), editing (`editor.py`, `hooks.py`, `subtitles.py`, `translate.py`, `thumbnail.py`), plus `saasshorts.py`, `telegram_bot.py`, `mcp_server.py`/`mcp_stdio.py`, `free_tools.py`.
- **Cloud edition** lives in `cloud/` under a separate commercial license. It is attached at import time by `cloud.setup_sync(app)` only when `BILLING_ENABLED` is set, and `app.py` branches on `BILLING_ENABLED` throughout.
- **Frontend.** `dashboard/` (React 18, Vite 4, Tailwind, Remotion for in-browser preview). `remotion/` is a second copy of the compositions used for server rendering.
- **Packaging.** One Dockerfile with CPU and GPU variants, fully pinned lock files, a digest-pinned base image. CI runs pytest on Linux and Windows and `npm run build`.

**Already well designed (leave alone).**
- `ssrf_guard.py` and `security_utils.py`: allowlist by `is_global`, handles IPv6-embedded IPv4, guards at DNS level for yt-dlp too, and has its own tests.
- `jsonfile.write_json_atomic`: a small, correct fix for a real race.
- Dockerfile: digest pins, locked installs with `pip check`, a `--no-index` pass that catches drift between `requirements*.txt` and the lock.
- The tests: fast (34 s for 1,908), deliberately runnable without the ML stack, with `tests/main_harness.py` stubbing heavy imports. Test names state the behavior. Regression tests such as `test_no_blocking_http_in_async.py` guard past incidents.
- `docs/architecture/*.md`: 1,350 lines explaining the hard parts. This is unusually good.
- `cloud/` is gated so self-hosters do not import it.

---

## Key Problems

1. Authorization is checked per route, so a missed check leaks data. One already does (item 1).
2. Self-host exposes an unauthenticated API with wildcard CORS and credentials on all interfaces (item 2).
3. `app.py` mixes about ten responsibilities, with 17 pieces of process-local global state.
4. Logging is `print` (286 calls in `app.py` and `main.py`, zero `logging` calls). There are 146 `except Exception` blocks, and 42 of them are followed by `pass`.
5. Several handler functions are 150 to 400 lines (`process_endpoint` 396, `add_subtitles` 222, `saasshorts_generate` 193). `main.py:_download_youtube_video` is 456 lines.
6. No linter, formatter, type checker or pre-commit config. CI does not lint the frontend either.
7. Remotion compositions exist twice and have drifted.
8. Dead or unneeded dependencies and committed binaries.

---

## Recommendations

### P0

**P0-1. Another user's pending upload can be downloaded without logging in (cloud mode)**
- **Problem:** `GET /api/source/{job_id}` does not validate `job_id`. Reserved upload slots are saved as `uploads/pending_<uuid>_<name>` (`app.py:3827`). `_locate_source_for_range` (`app.py:4475`) globs `uploads/<job_id>_*`. A request for `/api/source/pending` finds no job record, `_assert_disk_job_owner` finds no owner and returns, and the glob serves the first pending file. **Reproduced:** with `BILLING_ENABLED=True` and no user, `/api/source/pending` and `/api/source/pending_aaaa` both returned 200 with the file bytes. The `thumb_` prefix is already excluded in that glob; `pending_` is not.
- **Why it matters:** The raw, unpublished video of any user with an open slot can be read by anyone. Slots live for `UPLOAD_TTL_SECONDS`, and `pending_` is a fixed, guessable prefix.
- **Solution:** (a) Reject ids that fail `_is_uuid_id` in `get_source_video`, `get_source_url`, and `_locate_source_for_range`. (b) Exclude `pending_*` in the glob next to the `thumb_` exclusion. (c) In `_assert_disk_job_owner`, in cloud mode, deny when no owner is found (today it allows). Do (c) with a check that legacy ownerless jobs still work, since `docs/architecture` notes BYOK jobs have no owner. (d) Add the repro as a test in `tests/test_source_access.py`.
- **Files:** `app.py` (`get_source_video`, `get_source_url`, `_assert_disk_job_owner`, `_locate_source_for_range`), `tests/test_source_access.py`.
- **Complexity:** Low.

**P0-2. Restore `LICENSE`**
- **Problem:** `git status` shows `LICENSE` deleted. `NOTICE`, `README.md` and `cloud/LICENSE` refer to it.
- **Why it matters:** Committing this leaves the MIT grant for the core app without a text.
- **Solution:** `git checkout -- LICENSE` unless intentional.
- **Files:** `LICENSE`. **Complexity:** Low.

### P1

**P1-1. Self-host API is reachable from any website and the network**
- **Problem:** `app.py:2859` uses `allow_origins=["*"]` with `allow_credentials=True` in self-host. `docker-compose.yml` publishes `8000:8000` on all interfaces. The API can start jobs, list and download clips, call `/api/social/post`, and spend the user's Gemini key.
- **Why it matters:** Any page the user visits can talk to `localhost:8000`. On a VPS the whole internet can. The README presents self-host as the default path.
- **Solution:** Publish `127.0.0.1:8000:8000` by default. Default self-host CORS to the dashboard origins (`localhost:5173`, `localhost:5175`) with an `ALLOWED_ORIGINS` override. Drop credentials when the origin is `*`. Optional `API_TOKEN` env var checked by one dependency for people who expose it. Keep behavior for the dashboard unchanged.
- **Files:** `app.py` (CORS block), `docker-compose.yml`, `.env.example`, `README.md`.
- **Complexity:** Low (ports and CORS) to Medium (token).

**P1-2. Validate `job_id` once, not per route**
- **Problem:** Most `{job_id}` routes (`/api/status`, `/api/source`, `/api/jobs/.../download-all`, `/cancel`, `/keep`) do not call `_JOB_ID_RE` (`app.py:4723`). Defined at line 4723, after many of its users.
- **Why it matters:** This is the cause of P0-1, and it makes every new route a chance to repeat it.
- **Solution:** A `valid_job_id` FastAPI dependency returning 404 for non-UUID ids, applied through a shared `APIRouter(dependencies=[...])` for job routes. Check first whether any legitimate job ids are not UUIDs: `tests/test_source_access.py` uses `"source-access-test-job"`, so test fixtures will need real UUIDs.
- **Files:** `app.py`, a handful of tests.
- **Complexity:** Medium.

**P1-3. Split `app.py` into routers, moving code only**
- **Problem:** 9,210 lines, 64 routes, about ten domains: jobs and queue, uploads, media auth, clip editing, subtitles and hooks, translate, social, thumbnail, SaaS Shorts, gallery HTML, deploy drain. The repo already shows the pattern works: `mcp_server.router` and `free_tools.router` use `app.include_router`.
- **Why it matters:** Review is slow. State is shared through module globals, so a mistake in one area is hard to see (P0-1 lived in it unnoticed). Merge conflicts concentrate in one file.
- **Solution:** One router per domain, one commit each, no behavior change, the full suite as the safety net. Order by independence: `saasshorts` routes, thumbnail, social, gallery HTML, then uploads and media auth. Leave queue and job state last. Tests monkeypatch `app_module.X` heavily (for example `OUTPUT_DIR`, `jobs`, `BILLING_ENABLED`), so each move needs those names to stay reachable or the tests to be updated in the same commit.
- **Files:** `app.py`, new `routes/*.py`, many tests.
- **Complexity:** High (mechanical but wide).

**P1-4. Move the 17 process-local dicts behind small stores**
- **Problem:** `jobs`, `thumbnail_sessions`, `pending_uploads`, `publish_jobs`, `_submissions`, `_probe_times`, `_ai_edit_counts`, `_render_owners`, `_post_request_owners`, `_restore_locks`, `_rerender_locks`, `_scenes_locks` and others are module globals. Several only grow (the lock dicts keyed by job id; `_render_owners`, `_post_request_owners`).
- **Why it matters:** Memory growth in a long-lived process; and with two containers during a deploy the state differs per container (the code already works around this with disk fallbacks). `_media_project_cache` clears everything at 5,000 entries (`app.py:2993`).
- **Solution:** Do not add Redis. Add a tiny `BoundedDict` (max size, TTL, evict oldest) in one module and use it for the unbounded ones. Group job-related state into one `JobStore` class only when splitting routers (P1-3) forces it.
- **Files:** `app.py`, new `state.py`.
- **Complexity:** Medium.

**P1-5. Replace `print` with `logging`**
- **Problem:** 286 `print` calls and no `logging` in `app.py` and `main.py`. Many carry emoji prefixes used as severity.
- **Why it matters:** No levels, no timestamps, no structured output, no way to silence noise or route errors to alerting. `cloud/alerts.py` exists, so someone already wants this signal.
- **Solution:** `logging.getLogger(__name__)` per module and `basicConfig` once at startup. Convert with a script (`print(f"⚠ ...")` to `log.warning`), keep message text so existing greps still work. `main.py` writes to stdout, which `app.py` captures into job logs, so leave `main.py` job-log lines as they are and convert only operational messages.
- **Files:** `app.py`, `main.py`, `telegram_bot.py`, others.
- **Complexity:** Medium.

**P1-6. Add Ruff and a pre-commit hook**
- **Problem:** No `pyproject.toml`, Ruff, flake8, mypy or pre-commit at the root. CI runs `npm run build` but not `npm run lint` (`CLAUDE.md` tells people to run it by hand).
- **Why it matters:** At 41k lines, unused imports, undefined names and swallowed exceptions go unnoticed. `ruff check` with just `F` (pyflakes) and `B` rules would find real bugs without reformatting anything.
- **Solution:** Root `pyproject.toml` with `[tool.ruff]` selecting `F,E9,B` only. Add a CI job running `ruff check` and `npm run lint`. Do not run a formatter over existing code; that would be pure churn.
- **Files:** new `pyproject.toml`, `.github/workflows/ci.yml`.
- **Complexity:** Low.

### P2

**P2-1. Upload path does blocking disk writes in async code, and leaves partial files** (`put_upload`, `app.py:3845`)
- **Problem:** `out.write(chunk)` runs on the event loop. On disconnect the exception propagates and the partial file stays until the sweep. A second PUT can replace the file after `/api/process` claimed it.
- **Why it matters:** One slow disk write stalls every request. Under Cloud load with several large uploads, status polls lag.
- **Solution:** Write chunks through `run_in_executor` (the repo already does this 62 times), delete the partial on any exception, refuse PUT once the slot is consumed.
- **Files:** `app.py`. **Complexity:** Low.

**P2-2. Self-host has no upload slot cap** (`create_upload`, `app.py:3809`)
- **Problem:** The per-user cap only applies when `BILLING_ENABLED`.
- **Why it matters:** With P1-1 unfixed, a script can fill the disk.
- **Solution:** One global cap (for example 20) in self-host.
- **Files:** `app.py`. **Complexity:** Low.

**P2-3. Swallowed exceptions**
- **Problem:** 146 `except Exception` in `app.py` and `main.py`; 42 are followed by a bare `pass`. Some are right (cleanup of a temp file), others hide failures (a failed owner marker write only prints and the job continues unowned, `_write_owner_marker`).
- **Why it matters:** A failed `.owner` write means `/videos` later cannot find the owner after a restart. This is exactly the inconsistent state the media rules depend on.
- **Solution:** After Ruff (P1-6), review `B` hits. Convert the data-bearing ones (owner marker, metadata writes, manifest writes) to log at `error` and surface to the job log. Leave file-cleanup ones.
- **Files:** `app.py`, `main.py`. **Complexity:** Medium.

**P2-4. Break up the longest functions where they have separable steps**
- **Problem:** `process_endpoint` (396 lines, `app.py:3998`), `add_subtitles` (222), `saasshorts_generate` (193), `edit_clip` (170), `_download_youtube_video` (456, `main.py:896`), `get_viral_clips` (302), `process_video_to_vertical` (217).
- **Why it matters:** These mix input validation, quota, file handling and job creation. They are the hardest places to test or change safely.
- **Solution:** Extract by job only: request validation, source resolution (URL vs upload vs slot), job record creation. Do not split `_download_youtube_video` before it has fake-based tests per client fallback (`tests/ydl_fakes.py` and `test_yt_clients.py` exist, which helps). Skip functions that are long but linear.
- **Files:** `app.py`, `main.py`. **Complexity:** High.

**P2-5. Drift between the two Remotion copies**
- **Problem:** `remotion/src` and `dashboard/src/remotion` differ in `HookOverlay.tsx`, `Subtitles.tsx`, `lib/fonts.ts`, `lib/types.ts`. `CLAUDE.md` asks developers to change both by hand.
- **Why it matters:** A server render can differ from the browser preview the user approved.
- **Solution:** Make `dashboard/src/remotion/compositions` and `lib` the source and have `remotion/` import or copy it at build time (a symlink or an npm workspace). First diff the four files to see which differences are intended.
- **Files:** `remotion/`, `dashboard/src/remotion/`, Dockerfiles. **Complexity:** Medium.

**P2-6. Mandatory frontend checks**
- **Problem:** No frontend tests (`find dashboard -name "*.test.*"` returns none). CI builds but does not lint.
- **Why it matters:** `App.jsx` is the main component and has no safety net.
- **Solution:** Add `npm run lint` to CI now. Add Vitest only for pure helpers in `dashboard/src/lib` first.
- **Files:** `.github/workflows/ci.yml`, `dashboard/`. **Complexity:** Low (lint), Medium (tests).

**P2-7. Binaries in git**
- **Problem:** `demo-openshorts.mp4`, two `churchil_queen_vertical*.gif`, 18 mp4 files in `dashboard/public/demo/`, even though `.gitignore` excludes `*.mp4`. `.git` is 111 MB.
- **Why it matters:** Every clone and CI checkout pays for it.
- **Solution:** Host the large ones as release assets or on a CDN. Keep only what the built site needs. Rewriting history is optional and disruptive; skip it unless clone size hurts.
- **Files:** `dashboard/public/demo/*`, root media, `README.md`. **Complexity:** Low.

**P2-8. Add tests for the gaps below** (see Testing).

### P3

- **P3-1. Bounded owner cache** (`_media_project`, `app.py:2993`): evict half instead of `.clear()`, to avoid a database burst. Low.
- **P3-2. `HANDOFF_PROMPT.md`** is untracked at the root of a public repo. Ignore or delete when done. Low.
- **P3-3. `bs4` for one module.** `beautifulsoup4` is used only in `saasshorts.py`. Fine to keep; only replace if scraping there is trivial. Low.
- **P3-4. Pre-commit for `ruff check`.** Low, after P1-6.

---

## Performance

I found no hot-path problem that justifies a rewrite. Specific, justified points:

> **Correction (see `PROGRESS.md`):** the claim below that `app.py:6383` blocks the event loop is wrong. That call runs inside `run_effects_generation`, which is already dispatched with `run_in_executor`. The `subprocess.run` in `get_clip_scenes` is also inside a worker function.

- **Event loop blocking.** `app.py:6383` calls `subprocess.check_output(probe_cmd)` directly inside `async def generate_effects_config`, which blocks the loop for the length of an ffprobe. Move it to `run_in_executor` like the neighbours. `subprocess.run` at `3670` is already wrapped in a `_run` helper for an executor. Check the one at `5680` inside async `get_clip_scenes`: I did not confirm whether it runs in an executor. Low.
- **`_job_view_from_disk`** rescans the output directory through `_recover_jobs_from_disk` whenever a job has metadata but no manifest and is not in memory. `get_source_video` already avoids it off-billing (the code comment says so). `/api/status` for an unknown id in cloud mode can hit it on every poll. Cache the negative result for a few seconds. Low.
- **Per-job full process.** Each job loads YOLO and MediaPipe at import (`main.py:60`), costing seconds and RAM per job at `MAX_CONCURRENT_JOBS=5`. This is a design choice with a documented VRAM story (`docs/architecture/jobs-and-deploys.md`). Only revisit if startup shows up in job timings; I did not measure it.
- **CPU image.** The Dockerfile already installs CPU-only torch to avoid several GB. Good.

---

## Testing

**Existing:** 142 files, fast, deterministic, strong around cloud/billing, SSRF, layouts, jobs and deploy drain, MCP. This is a real strength. CI runs Linux and Windows.

**Gaps (each is one focused test):**
1. `/api/source/pending`, `/api/source/<non-uuid>` and `/api/source-url/<non-uuid>` in cloud mode with no user and with another user. This is the P0-1 repro.
2. Same non-UUID ids against `/api/status`, `/api/jobs/{id}/download-all`, `/cancel` and `/keep`.
3. `put_upload` with a client disconnect (partial file removed) and a second PUT after `/api/process`.
4. `create_upload` slot cap in self-host.
5. CORS: assert the self-host default origin policy once P1-1 lands.
6. `_write_owner_marker` failure (read-only dir): the job must report it, not continue silently.
7. `saasshorts.py` (1,511 lines) has no test importing it by name. Add tests for the pure parts (`generate_scripts` parsing, actor selection) with the LLM faked.
8. `editor.py`, `edit_builder.py`, `file_hosts.py`, `mcp_ui.py`, `hook_grounding.py` show only a single test file each; `verify_*.py` at the root are manual scripts, not tests. Check what they cover before moving them under `tests/`.
9. `main.py` end-to-end on a tiny fixture video with a fake LLM and the real ffmpeg: one smoke test (skipped when ffmpeg is missing) that the pipeline produces a clip and metadata. Today it is only exercised in parts.
10. Frontend: no tests. Start with pure helpers.

Coverage numbers: I did not run a coverage tool, so these gaps come from reading names and greps, not measured coverage.

---

## Features worth building

**Essential (reliability and trust)**
1. **Auth for self-host** (`API_TOKEN` env var, checked by one dependency; the dashboard sends it). Anyone who deploys on a VPS needs this. Fits `app.py` and `dashboard/src/config.js`.
2. **Job resume after crash.** The manifest and heartbeat already exist for deploy handover. Extending them to resume a job that died mid-pipeline (re-queue when the heartbeat is stale, which `_job_view_from_disk` already reports as `queued`) reuses existing code.
3. **`/health/ready` that checks dependencies** (disk space on `OUTPUT_DIR`, ffmpeg present, LLM reachable when configured). The probe exists; it only reports `_stopping`.
4. **Disk-space guard before accepting an upload or job**, using `shutil.disk_usage` on `UPLOAD_DIR`. Prevents the full-disk case that P2-2 can trigger.

**Useful**
5. **Per-job cost and time summary** in `*_metadata.json` (LLM tokens, minutes of GPU). `cloud/metering.py` already tracks this for billing; show it to self-hosters.
6. **CLI parity.** `cli/` (the PyPI `openshorts` package) should cover `process`, `status`, `download` for the same endpoints MCP exposes. I did not read `cli/` in depth; check what it already covers first.
7. **Webhook retry with signature** for job completion (the webhook URL is already SSRF-checked at `app.py:4088`).

**Nice to have**
8. Batch processing of a playlist.
9. A dry-run "estimate" for self-host (the endpoint `/api/process/estimate` exists; check it works without billing).

---

## Developer experience

- **Setup is documented** (`CLAUDE.md`, `README.md`, `docs/native-install.md`) and `.env.example` exists. Good.
- **CI installs a hand-typed package list** (twice, Linux and Windows, "keep in sync"). A `requirements-test.txt` would remove the duplication. Low.
- **No lint, format or type tooling** (P1-6). Frontend lint is not in CI (P2-6).
- **`CLAUDE.md` is stale on one point.** It says pipeline modules import the ML stack lazily, but `main.py` imports torch, ultralytics and mediapipe at the top and the tests work around that with `tests/main_harness.py`. Either fix the doc or fix the imports.
- **Configuration is spread over many env vars** with defaults inside `app.py` (`MAX_CONCURRENT_JOBS`, `JOB_RETENTION_SECONDS`, and more). `.env.example` is long (the first 40 lines alone cover ten variables). A single `settings.py` read once would make defaults discoverable, but this is only worth doing during P1-3, not alone.
- **Compose mounts `.:/app`** for the backend, so local edits apply without a rebuild. Good for dev, but then also in the same file used for production-like runs; there is a separate `docker-compose.cloud.yml`.

---

## Security and reliability summary

| Item | Status |
|---|---|
| Cross-user source download via `pending_*` | Open, reproduced (P0-1) |
| Self-host CORS `*` + credentials, public bind | Open (P1-1) |
| SSRF on user URLs, webhooks, actor images | Well handled (`ssrf_guard.py`, `security_utils.py`, tests) |
| `gpu_render._eval` | Uses `ast` with an operator allowlist, no `eval`. Safe |
| `shell=True`, `os.system`, `pickle`, `yaml.load` | None found |
| Telegram bot | Requires both chat id and user id in the allow list, bot disabled when billing is on or the list is empty. Good |
| Secrets | `.env` ignored; `.env.example` has placeholders only; `HANDOFF_PROMPT.md` has none but names a private setup |
| Atomic JSON writes | Good (`jsonfile.py`) |
| Owner marker write failure | Logged only (P2-3) |
| Unbounded in-memory dicts | Several (P1-4) |
| Pinned dependencies | Locked in Docker; `yt-dlp` deliberately unpinned in `requirements.txt` (it changes weekly to track YouTube; acceptable) |

---

## Dependencies

- **Heavy but used:** `torch`, `torchvision`, `ultralytics`, `mediapipe`, `faster-whisper`, `scenedetect`, `transnetv2-pytorch`. Each is imported (checked by grep). `scene_detection.py` uses both `scenedetect` and TransNetV2, so there are two scene detectors. That may be deliberate (fallback); it is the first place to look if the image size must shrink.
- **Unused by import:** `alembic` is in `requirements-billing.txt` and `alembic/` has only `env.py` and no versions. `cloud/database.py` says it is "available later". Keep only if a migration is planned (`CLAUDE.md` says schema is `create_all` and additive). `asyncpg` is never imported by name but is the SQLAlchemy driver named in the DB URL, so it is needed. `itsdangerous` is never imported by name but Starlette's `SessionMiddleware` requires it (`cloud/__init__.py:26`), so it is needed.
- **Single-use:** `tqdm` (only `main.py`), `beautifulsoup4` (only `saasshorts.py`), `py3langid` (only `transcribe_backends.py`). All small; no action.
- **Version style:** pins like `torch==2.11.0` and `ultralytics==8.4.46` are newer than I can verify from memory. I did not check them against PyPI.
- **Frontend:** `vite ^4.5.3` is two majors behind current, and `lucide-react ^0.344.0` is old. Neither is a risk by itself. Upgrade only when touching the build.
- **Net:** no dependency removal is clearly justified; the only candidate is `alembic`.

---

## Refactoring Roadmap

1. Fix P0-1 (validation plus `pending_` exclusion plus the test). Restore `LICENSE`.
2. Bind compose to `127.0.0.1` and tighten self-host CORS (P1-1).
3. Add Ruff with `F,E9,B` and run it in CI, plus `npm run lint` (P1-6, P2-6). Fix only what it flags as real bugs.
4. Add the `valid_job_id` dependency and apply it to job routes (P1-2).
5. Make `put_upload` non-blocking and clean up partials, add the self-host slot cap (P2-1, P2-2).
6. Introduce `logging` module by module, starting with `app.py` startup and error paths (P1-5).
7. Review swallowed exceptions on data-bearing writes (P2-3).
8. Add `BoundedDict` for the growing dicts (P1-4).
9. Split `app.py` into routers, one domain per commit, in the order given in P1-3 (P1-3).
10. Extract steps from `process_endpoint` and the other long functions, only after the router split settles (P2-4).
11. Unify the Remotion copies (P2-5).

Steps 1 to 5 need no structural change and can ship independently.

## Feature Roadmap

1. Self-host `API_TOKEN`.
2. Disk-space guard.
3. Dependency-aware `/health/ready`.
4. Resume of a job whose heartbeat went stale.
5. Per-job cost and time summary.
6. CLI parity with MCP tools.
7. Webhook retry and signature.
8. Playlist batch (optional).

## Quick Wins

- `git checkout -- LICENSE`.
- `127.0.0.1:8000:8000` in `docker-compose.yml`.
- Exclude `pending_*` next to `thumb_*` in `_locate_source_for_range`.
- `_is_uuid_id` check at the top of the two source routes.
- Add `ruff check` and `npm run lint` to CI.
- Move the `subprocess.check_output` at `app.py:6383` to `run_in_executor`.
- Fix the `CLAUDE.md` line about lazy ML imports.
- Ignore or delete `HANDOFF_PROMPT.md`.

## Long-Term Improvements

- Router split of `app.py` with a small shared state module.
- A real `logging` setup with levels and a request id per job.
- One source for the Remotion compositions.
- A pipeline smoke test with a real ffmpeg and a fake LLM.
- Moving demo binaries out of git.
- Extracting steps from the 200 to 450 line functions, guarded by tests first.

## Recommended Next Step

**Fix P0-1, with its test.** It is a confirmed, reproducible leak of other users' private videos in the cloud edition, and the fix is about ten lines in `app.py` plus one test in `tests/test_source_access.py`. The same change shows whether `valid_job_id` (P1-2) should come next, and it needs no refactor. Do it before anything structural.
