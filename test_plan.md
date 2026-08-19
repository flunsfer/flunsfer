# Test Plan — flunsfer FastAPI backend (PR #1)

Server: `.venv/bin/uvicorn app.main:app --port 8000` (already running, fresh flunsfer.db).
Primary tool: Swagger UI at http://localhost:8000/docs (browser, recorded).
Expired/garbage token checks: shell (curl + python token crafting), text evidence only.

Code evidence: `app/routers/auth.py` (409 duplicate, 401 bad login), `app/schemas.py`
(EmailStr, password min_length=8), `app/routers/tasks.py` (`_get_owned_task` → 404 for
non-owned), `app/auth.py` (JWT HS256, 401 "Could not validate credentials").

## T1: Health & docs
- GET /health via Swagger → 200 `{"status":"ok"}`. /docs page renders with auth + tasks sections.

## T2: Registration validation
- POST /auth/register `{"email":"alice@example.com","password":"supersecret1"}` → **201**, body has id, email, created_at, NO password field.
- Same email again → **409** `"Email already registered"`.
- `{"email":"bob@example.com","password":"short"}` → **422** (string_too_short, min 8).
- `{"email":"not-an-email","password":"supersecret1"}` → **422** (email validation).
- Register `bob@example.com` / `bobpassword1` → 201 (for isolation test).

## T3: Login
- Swagger Authorize dialog with alice@example.com / wrong password → 401 shown in dialog.
- Correct password → authorized (locked padlock). POST /auth/token via endpoint also returns `access_token` + `token_type: bearer`.

## T4: Unauthenticated / bad token rejection
- In Swagger BEFORE authorizing (or after logout): GET /tasks → **401** `{"detail":"Not authenticated"}`.
- Shell: `curl -H "Authorization: Bearer garbage"` GET /tasks → **401** "Could not validate credentials".
- Shell: craft token with exp in the past using real SECRET_KEY → **401**; token signed with WRONG key → **401**.

## T5: Task CRUD (as alice, via Swagger)
- POST /tasks `{"title":"Buy milk","description":"2 liters"}` → **201**, done=false, owner_id set.
- GET /tasks → list containing that task.
- GET /tasks/{id} → 200 same task.
- PATCH /tasks/{id} `{"done":true,"title":"Buy oat milk"}` → 200 with updated fields.
- DELETE /tasks/{id} → **204**; GET /tasks/{id} after → **404**.

## T6: Per-user isolation
- As alice, create task, note id N.
- Logout in Swagger, authorize as bob.
- GET /tasks as bob → `[]` (does NOT contain alice's task).
- GET /tasks/N → **404** "Task not found"; PATCH /tasks/N → **404**; DELETE /tasks/N → **404**.
- Re-verify (shell, alice's token): alice's task still exists and unmodified.
