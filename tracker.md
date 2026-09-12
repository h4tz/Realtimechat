# Project Tracker — Django + FastAPI Real-Time Chat

## Status Summary

| Area | Done | Total | Status |
|------|------|-------|--------|
| Phase 1: Bug Fixes | 7 | 7 | Complete |
| Phase 2: Test Infrastructure | 6 | 6 | Complete |
| Phase 3: Backend Tests | 2 | 7 | In Progress |
| Phase 4: Frontend Tests | 0 | 5 | Not Started |

---

## Phase 1: Bug Fixes — All Complete

- [x] 1.1 **Per-connection PubSub** — Removed shared PubSub from `ConnectionManager`; each WS connection gets its own `redis.pubsub()` via `create_pubsub()`
- [x] 1.2 **User-keyed connections** — Changed from IP-based (`websocket.client.host`) to `user_{user_id}` keying
- [x] 1.3 **Graceful cancellation** — Redis listener tasks cancelled in `finally` blocks with `asyncio.CancelledError` handling
- [x] 1.4 **Expiry calculation** — Uses `timedelta(days=1)` instead of broken `day+1` arithmetic; removed dead `get_user_id_pair`; moved imports to top of `ws_service/models.py`
- [x] 1.5 **Secret key validation** — `ws_service/config.py` requires `JWT_SECRET_KEY` in production; `settings.py` enforces secure keys when `DEBUG=False`
- [x] 1.6 **Refresh token rotation** — JTI claims on all tokens; used JTIs tracked; reuse returns 401
- [x] 1.7 **WS auth via first message** — Changed from `?token=` URL query to `{type: "auth", token: "..."}` first message pattern; updated `useWebSocket.ts`, `chat.py`, `private.py`, both Django templates

### Files Modified (Phase 1)
- `ws_service/connection_manager.py`
- `ws_service/routers/chat.py`
- `ws_service/routers/private.py`
- `ws_service/models.py`
- `ws_service/config.py`
- `ws_service/auth.py`
- `chat/api.py`
- `realtimechat/settings.py`
- `frontend/src/composables/useWebSocket.ts`
- `frontend/src/types/index.ts`
- `chat/templates/chat/minimal_room.html`
- `chat/templates/chat/private.html`

---

## Phase 2: Test Infrastructure — All Complete

- [x] `requirements-dev.txt` created & installed
- [x] Frontend test deps installed (vitest, @vue/test-utils, happy-dom)
- [x] `pyproject.toml` — pytest config, coverage settings
- [x] `conftest.py` — fixtures: user, other_user, admin_user, access_token, refresh_token, expired_token, message, private_message, api_client, auth_client
- [x] `vitest.config.ts` — happy-dom environment
- [x] `Makefile` — `make test`, `make test-backend`, `make test-frontend`, `make test-coverage`

---

## Phase 3: Backend Tests — 39/93 Passing

### Passing (39 tests)
- `tests/test_models.py` — 30/30 tests pass (all model classes)
- `tests/test_auth.py` — 5/17 (TokenUtils only)
- `tests/test_ws_auth.py` — 7/9 (edge cases pass)
- `tests/test_smoke.py` — 1/2

### Failing (54 tests) — BUGS / NEEDS FIX

#### BUG-1: `TypeError: 'NinjaAPI' object is not callable` (38 tests)
- **Affected:** All API endpoint tests in `test_auth.py`, `test_rooms.py`, `test_messages.py`, `test_private.py`
- **Cause:** `httpx.AsyncClient(ASGITransport(app=api))` — the `api` object is a Django Ninja `NinjaAPI` instance which isn't directly callable by httpx's ASGI transport
- **Fix needed:** Use Django Ninja's own test client or wrap the `NinjaAPI` app in a callable ASGI adapter
- **Tests failing:** 12 auth, 14 rooms, 13 messages, 8 private (minus 9 db-locked ones that also fail)

#### BUG-2: `database table is locked` (9 tests)
- **Affected:** `test_messages.py`, `test_rooms.py`, `test_private.py` — tests that use `auth_client` for first request then make another
- **Cause:** SQLite in-memory DB locking under async concurrent access via httpx
- **Fix needed:** Either use `aiosqlite` for tests, or serialize requests, or switch to PostgreSQL for tests

#### BUG-3: `assert None is not None` — WS auth JWT key (2 tests)
- **Affected:** `test_ws_auth.py::test_decode_valid_token`, `test_authenticate_valid_token`
- **Cause:** `ws_service.config.JWT_SECRET_KEY` is `None` at module import time — pytest imports the module before `conftest.py` sets env vars. The `config` module is cached in `sys.modules` with `None` values
- **Fix needed:** Make `ws_service/config.py` read env vars lazily (e.g., use functions instead of module-level constants), or force reimport in conftest

#### BUG-4: `assert 3 == 1` — Smoke test (1 test)
- **Affected:** `tests/test_smoke.py::test_two_users`
- **Cause:** Test expectation is wrong, or user count is off

---

## Phase 4: Frontend Tests — Not Started

- [ ] WebSocket composable tests (`useWebSocket.ts`)
- [ ] Vue component unit tests
- [ ] Store/state management tests
- [ ] Integration tests (API calls)
- [ ] Coverage configuration

---

## Known Test Issues Quick Reference

| Bug | Error | Tests | Severity |
|-----|-------|-------|----------|
| BUG-1 | `NinjaAPI not callable` | 38 | High — blocks all API tests |
| BUG-2 | `database table locked` | 9 | Medium — SQLite async issue |
| BUG-3 | `JWT key is None` | 2 | Medium — module import order |
| BUG-4 | Wrong assertion | 1 | Low — test expectation fix |
