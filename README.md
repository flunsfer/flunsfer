# flunsfer API

FastAPI backend with JWT authentication and a per-user task CRUD.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then set SECRET_KEY, e.g. openssl rand -hex 32
```

## Run

```bash
uvicorn app.main:app --reload
```

Docs at http://localhost:8000/docs

## Test & Lint

```bash
pytest
ruff check .
```

## Security notes

- Secrets come from environment variables / `.env` (never committed).
- Passwords hashed with bcrypt; auth via short-lived HS256 JWTs.
- All `/tasks` endpoints require authentication and enforce per-user ownership.
- Input validated with Pydantic (email format, password length, field size limits).
- Database access via SQLAlchemy ORM (parameterized queries, no raw SQL).
- CORS restricted to origins listed in `CORS_ORIGINS`.
