---
name: testing-flunsfer-api
description: How to run and end-to-end test the flunsfer FastAPI backend (JWT auth + per-user task CRUD) locally, including Swagger UI tips and token edge-case testing.
---

# Testing the flunsfer FastAPI backend

## Run the app
1. From repo root, create `.env` (required — app fails to start without SECRET_KEY):
   `cp .env.example .env && sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$(openssl rand -hex 32)/" .env`
2. Start with a fresh DB when testing: `rm -f flunsfer.db` (DB path comes from DATABASE_URL in `.env`; tables auto-create on startup via lifespan in `app/main.py`).
3. `.venv/bin/uvicorn app.main:app --port 8000` (venv already exists per blueprint; deps via `.venv/bin/pip install -e ".[dev]"`).
4. Smoke check: `curl http://localhost:8000/health` → `{"status":"ok"}`; Swagger UI at `http://localhost:8000/docs`.

## Swagger UI gotchas
- The Authorize dialog (top-right) drives POST /auth/token; username = email. A wrong password shows "Auth Error ... Unauthorized" inside the dialog; success shows the padlock locked.
- To switch users mid-test: Authorize → Logout → fill new credentials → Authorize. Requests before authorizing return 401 `{"detail":"Not authenticated"}` — useful for the unauthenticated test.
- Form fields in "Try it out" for /auth/token are pre-filled with the literal default "string" — clear them (triple-click + ctrl+a) before typing or your input gets appended.
- SQLite reuses the max rowid after deletes: if you delete the highest-id task and create a new one, it may get the same id. Always read the id from the create response, don't assume it increments.

## Token edge cases (shell)
Use the venv python with the app's own settings to craft tokens:
- Expired: `jwt.encode({'sub':'1','exp': now-5min}, get_settings().secret_key, algorithm='HS256')` → expect 401 "Could not validate credentials".
- Forged: sign with a wrong key → expect 401.
- Garbage: `Authorization: Bearer garbage.token.here` → expect 401.

## Expected security behaviors (from code)
- `app/schemas.py`: password min_length=8 (422), EmailStr validation (422).
- `app/routers/auth.py`: duplicate email → 409 "Email already registered"; bad login → 401 "Incorrect email or password".
- `app/routers/tasks.py` `_get_owned_task`: other users' tasks → 404 "Task not found" (not 403 — no existence leak).
