# Progress: applying `maintainer-review.md`

Rules for this work: one step at a time, full test suite after each step (`.venv-ci/bin/python -m pytest tests -q`), nothing committed, no behavior change beyond what a step states.

**Baseline before any step:** 1908 passed, 51 skipped.
**Now:** 1942 passed, 51 skipped (34 new tests). `ruff check .` clean. `npm run lint` clean. App restarted on the new code.

| Step | Review item | Status |
|---|---|---|
| 1 | P0-2 restore `LICENSE` | done |
| 2 | P0-1 / P1-2 job id validation, `pending_` exclusion, tests | done |
| 3 | P1-1 self-host bind and CORS | done |
| 4 | P2-1 / P2-2 upload write and slot cap | done |
| 5 | P1-6 / P2-6 Ruff and frontend lint in CI | done |
| 6 | Quick wins (`CLAUDE.md`, `.gitignore`, dead code) | done |
| 7 | P3-1 owner cache eviction | done |
| - | P2-3 owner marker failure | not changed (see below) |
| - | P1-3 router split, P1-4 bounded stores, P1-5 logging, P2-4 long functions, P2-5 Remotion, P2-7 binaries | not started (see below) |

## Log

### Step 1: restore `LICENSE`
- `git checkout -- LICENSE`. The file keeps its original "Copyright (c) 2024 OpenShorts" line, matching `NOTICE`.

### Step 2: job ids and the pending-upload leak (P0-1, P1-2)
- `app.py`: new `_require_job_id` and `valid_job_id` (a FastAPI dependency) after `_is_uuid_id`. Applied with `dependencies=[Depends(valid_job_id)]` to 11 routes: `cancel`, `keep` (POST and DELETE), `status`, `source-url`, `source`, `download-all`, `restore`, `transcript`, `edl`, `scenes`. A non-UUID id answers `404 {"detail": "Not found"}`.
- `_locate_source_for_range` returns `(None, 0.0)` for a non-UUID id and skips `pending_*` files in its glob, so every caller is covered, including the body-based routes (`rerender`, `reframe`, `split`, `edit`).
- **Not done on purpose:** the review's step (c), "deny in `_assert_disk_job_owner` when no owner is found". Ownerless jobs are legitimate (BYOK and self-host jobs never get an owner), so denying would break them. The leak needed a guessable id, and ids are now uuid4 only.
- Tests: `tests/test_source_access.py` gained `TestIdsThatAreNotJobs` (reproduces the leak with cloud mode on and no user, plus path-shaped ids, self-host, and the locator) and a parametrized test that all 9 job-path routes refuse a non-UUID id. I confirmed the new tests fail on the old `app.py`.
- Test fixtures that used ids like `"keepjob"` or `"j1"` now use uuid-shaped ids (`test_clip_keep`, `test_clip_split_endpoint`, `test_deploy_drain`, `test_job_cancel`, `test_mcp_endpoint`, `test_minutes_transparency`, `test_reframe_endpoint`, `test_rerender_endpoint`, `test_source_access`, `test_source_pieces_access`). Production ids were always uuid4.
- Live check on the running app: `/api/source/pending`, `/api/source/pending_zzzz`, `/api/status/pending` and `/api/source/../app.py` all return 404.
- **Left alone:** `GET /api/saasshorts/status/{job_id}` and `DELETE /api/social/scheduled/{job_id}`. The first uses its own id space that I did not verify, the second takes an Upload-Post id, not ours.

### Step 3: self-host exposure (P1-1)
- `docker-compose.yml`: backend, frontend and renderer ports now bind `127.0.0.1`. The frontend proxies `/api`, so publishing it on all interfaces would have exposed the API even with the backend bound to loopback.
- `app.py`: `_cors_origins()`. Self-host defaults to the local dashboard origins (`localhost` and `127.0.0.1` on 5173, 5175, 8000). `ALLOWED_ORIGINS` (comma separated, `*` allowed) overrides it. Credentials are only allowed when the list has no `*`.
- The dashboard uses relative URLs through its proxy, so it is same-origin and unaffected. curl, n8n, the Telegram bot and MCP clients are not browsers and are unaffected.
- `.env.example` and `README.md` explain the change. New `tests/test_cors_policy.py`.
- Live check: a preflight from `https://evil.example.com` gets 400 with no `allow-origin`; from `http://localhost:5175` it is allowed.
- **Not done:** the optional `API_TOKEN` for self-host. It is a feature (the review lists it under features), not a fix.

### Step 4: uploads (P2-1, P2-2)
- `put_upload`: disk writes go through the executor in 1 MiB batches, the slot is marked incomplete while a PUT is in progress, and the partial file is removed on any failure (too large, client dropped, disk error).
- `create_upload`: self-host now has a cap on open slots for the whole server (`MAX_PENDING_UPLOADS_SELF_HOST`, default 20). Cloud keeps its per-user cap.
- **Not needed:** "refuse PUT after `/api/process` claimed the slot". `/api/process` already pops the slot, so a later PUT gets 404.
- New `tests/test_upload_slots.py` (7 tests).

### Step 5: lint in CI (P1-6, P2-6)
- New `ruff.toml` selecting only `E9, F63, F7, F82` (syntax errors, undefined names, invalid comparisons). `ruff check .` is clean.
- Wider rules were not turned on: ruff reports 35 unused imports, and names in `app.py` are reached by tests as `app_module.<name>`, so a bulk fix could break the suite. `B904` alone has 78 hits.
- `.github/workflows/ci.yml`: new `backend-lint` job, and `npm run lint` before the dashboard build.
- Ruff found one real defect: unreachable code after `return` in `saasshorts.py` that referenced an undefined `result`. I deleted it (13 lines).
- Ruff did **not** catch a `SyntaxError` ("await outside async function") that I introduced and fixed during this work. Importing the app (`python -c "import app"`) and the test run did catch it.

### Step 6: quick wins
- `CLAUDE.md`: corrected the lazy-import line (`main.py` imports torch and friends at module level) and added the job id and lint rules.
- `.gitignore`: `HANDOFF_PROMPT.md`.

### Step 7: owner cache (P3-1)
- `_media_project` evicts the older half (`_evict_oldest_half`) instead of clearing the whole cache. Two tests in `tests/test_media_access.py`.

## Corrections to the review
- **"`subprocess.check_output` blocks the event loop at `app.py:6383`" was wrong.** That call is inside `run_effects_generation`, which already runs through `run_in_executor`. I tried to move it, hit a `SyntaxError`, and reverted. No change made.
- The `get_clip_scenes` `subprocess.run` at the old line 5680 is also inside a nested function that runs in a worker. Nothing to do there.

## Not done, and why
- **P2-3 owner marker write failure.** The code fails closed: with no `.owner`, `_media_owner` returns nothing and `/videos` denies access after the legacy window. It prints a warning. Raising its level only matters once logging is migrated (P1-5).
- **P1-3 router split, P1-4 bounded stores, P1-5 logging, P2-4 long functions.** These are large, wide changes that the review says to do one commit at a time, after the steps above settle. They need your go-ahead and deserve separate sessions.
- **P2-5 Remotion drift.** The review says to diff the four files first to see which differences are intended. That needs a decision from you.
- **P2-7 binaries in git, P2-8 further tests.** Moving the demo videos changes README and site links.
