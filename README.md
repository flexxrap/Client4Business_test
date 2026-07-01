# approval-service

Backend service for managing approval requests (publications, scenarios, edits, external sources) with an audit trail of decisions.

## Stack

- Python + FastAPI
- PostgreSQL (via docker-compose) / SQLite for local development and tests
- SQLAlchemy + Alembic
- pytest

## Running with Docker

```
cp .env.example .env
docker-compose up --build
```

This starts Postgres and the API, running Alembic migrations automatically before the app starts. The API is available at `http://localhost:8000`.

## Running locally without Docker

```
python -m venv .venv
.venv/Scripts/activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

By default `DATABASE_URL` is unset and the app falls back to a local SQLite file (`sqlite:///./approval_service.db`).

Apply migrations:

```
alembic upgrade head
```

Run the app:

```
uvicorn main:app --reload
```

## Running tests

```
pytest
```

Tests run against an in-memory SQLite database and do not require Docker or Postgres.

## Auth stub

Every request (except `/health` and `/ready`) must include an `X-Auth-Context` header with a JSON payload:

```json
{
  "workspace_id": "ws_1",
  "user_id": "usr_1",
  "actions": ["approval:read", "approval:create", "approval:decide", "approval:cancel"]
}
```

The `workspace_id` in the path must match the `workspace_id` in the header, or the request is rejected with 403.

## API

- `GET /health` — liveness check
- `GET /ready` — checks database connectivity
- `POST /api/v1/workspaces/{workspace_id}/approval-requests` — create a request (requires `approval:create`, `Idempotency-Key` header)
- `GET /api/v1/workspaces/{workspace_id}/approval-requests` — list requests (requires `approval:read`, supports `status`, `limit`, `offset`)
- `GET /api/v1/workspaces/{workspace_id}/approval-requests/{request_id}` — get a single request (requires `approval:read`)
- `POST .../{request_id}/approve` — approve (requires `approval:decide`)
- `POST .../{request_id}/reject` — reject (requires `approval:decide`)
- `POST .../{request_id}/cancel` — cancel (requires `approval:cancel`)

See [DESIGN.md](DESIGN.md) for data model, idempotency, and design decisions.
