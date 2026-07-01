# Design

## Data model

**ApprovalRequest**

| field | type | notes |
|---|---|---|
| id | uuid (string) | primary key |
| workspace_id | uuid (string) | indexed, tenant boundary |
| source_type | enum: publication/scenario/edit/external | |
| source_id | string | id of the thing being approved, in the source system |
| title | string | |
| description | string, nullable | |
| reviewer_user_ids | json array of strings | informational, not enforced |
| status | enum: pending/approved/rejected/cancelled | |
| created_by | string | from auth stub |
| idempotency_key | string | unique per workspace |
| created_at / updated_at | datetime | |

**ApprovalDecision** (audit trail, one row per decision)

| field | type | notes |
|---|---|---|
| id | uuid (string) | primary key |
| request_id | fk -> approval_requests.id | |
| action | enum: approve/reject/cancel | |
| actor_user_id | string | |
| comment | string, nullable | set on approve |
| reason | string, nullable | set on reject/cancel |
| created_at | datetime | |

An `ApprovalRequest` moves `pending -> approved|rejected|cancelled` exactly once. Each transition creates one `ApprovalDecision` row, so the full history of who decided what and when is reconstructable from `ApprovalDecision` alone, independent of the current state of `ApprovalRequest`.

## Service boundaries (what is intentionally not implemented)

- No real authentication/authorization — see "Known trade-offs" below.
- No notification of reviewers (email, Slack, etc.) — that's a consumer of the events described below, not this service's job.
- No SLA/expiry/auto-escalation of pending requests.
- No update/edit endpoint for an existing request — a request is either decided on or cancelled and superseded by a new one.
- `reviewer_user_ids` is stored but not enforced: any authenticated actor with `approval:decide` can approve/reject, this service does not check that the actor is one of the listed reviewers. Enforcing that is a product decision left to the caller/API gateway.
- No soft delete / GDPR erasure flow.

## Idempotency

Creation is idempotent per `(workspace_id, idempotency_key)`, enforced by a unique constraint at the database level (not just an application-level check), so it's race-safe under concurrent retries with the same key.

Flow for `POST .../approval-requests`:
1. Caller supplies `Idempotency-Key` header.
2. The service looks up an existing `ApprovalRequest` with the same `workspace_id` + `idempotency_key`.
3. If found, that existing request is returned as-is with `200 OK` (no new row, no state change).
4. If not found, a new request is created and returned with `201 Created`.

The idempotency key is scoped to a workspace, not global, since the same key value from two different callers/workspaces must not collide.

## Events / future integration

An `EventPublisher` abstraction (`app/services/events.py`) is called after every successful `approve`/`reject`/`cancel`. It currently has one implementation, `NoOpEventPublisher`, which just logs `event_type`, `request_id`, `workspace_id`, and `actor_user_id`.

The intent is that a future implementation swaps in a real publisher (e.g. to SQS, Kafka, or a webhook dispatcher) behind the same interface, without touching the request-handling code. Event types emitted today: `approval_request.approved`, `approval_request.rejected`, `approval_request.cancelled`. `approval_request.created` is a natural next addition once a consumer needs it.

## Known trade-offs

- **Auth is a stub.** `X-Auth-Context` is trusted as-is with no signature/verification — in production this header would be set by a trusted gateway/sidecar after verifying a real token, never accepted directly from an untrusted client. This service only handles the authorization shape (workspace scoping, action checks), not authentication.
- **IDs are stored as `String(36)`, not native UUID/PostgreSQL `uuid` columns.** This keeps the schema and Alembic migrations identical across SQLite (tests) and Postgres (runtime), at the cost of slightly larger storage and no DB-level UUID format validation.
- **Enums are stored as plain strings with `native_enum=False`**, not Postgres native enum types, for the same cross-database portability reason — adding a new enum value later is a plain migration, not an `ALTER TYPE`.
- **No pagination cursor, only limit/offset.** Simple to reason about and sufficient at expected scale; would need revisiting if a workspace accumulates a very large number of requests.
- **Reviewer authorization is not enforced** (see boundaries above) — `approval:decide` alone gates who can approve/reject, not membership in `reviewer_user_ids`.
