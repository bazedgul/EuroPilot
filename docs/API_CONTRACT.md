# API Contract

Status: Phase 1 read-only endpoints and the Phase 2 case list/detail and mutation endpoints are implemented locally. The frontend workflow is implemented locally and has reported automated and isolated-browser evidence; formal owner acceptance remains pending.

## Existing Phase 1 API

Verified in `backend/europilot/urls.py`:

- `GET /api/health/`
- `GET /api/v1/investigations/`
- `GET /api/v1/investigations/<id>/`

These endpoints remain read-only, preserve Phase 1 outcome semantics, and must not seed or mutate persisted state.

## Phase 2 resources (implemented locally; acceptance status remains evidence-based)

The case list/detail and mutation endpoints below are implemented locally. They use the local synthetic actor `synthetic_local_operator`; this is not authentication, authorization, or production tenancy.

### List cases

`GET /api/v1/cases/`

Read-only bounded list. Proposed response:

```json
{
  "count": 1,
  "page": 1,
  "page_size": 20,
  "results": [{
    "id": "case-1",
    "investigation_id": "investigation-1",
    "payment_id": "payment-1",
    "state": "open",
    "payment_outcome": "unknown",
    "updated_at": "2026-01-05T00:00:00Z"
  }]
}
```

### Case detail

`GET /api/v1/cases/<case_id>/`

Read-only detail with notes and audit history:

```json
{
  "id": "case-1",
  "investigation_id": "investigation-1",
  "payment_id": "payment-1",
  "state": "open",
  "payment_outcome": "unknown",
  "resolution_reason": null,
  "updated_at": "2026-01-05T00:00:00Z",
  "notes": [{
    "id": "note-1",
    "text": "Provider response remains unavailable.",
    "actor": "synthetic_local_operator",
    "created_at": "2026-01-05T00:00:00Z"
  }],
  "audit_events": [{
    "id": "audit-1",
    "action": "note_created",
    "actor": "synthetic_local_operator",
    "created_at": "2026-01-05T00:00:00Z",
    "note_id": "note-1",
    "request_id": "req-note-1"
  }]
}
```

### Transition a case

`POST /api/v1/cases/<case_id>/transitions/`

Request:

```json
{"request_id": "req-transition-1", "target_state": "under_review", "reason": null}
```

For `resolved` or `deferred`, `reason` is required after trimming and must be 1–500 characters. The server assigns the actor and does not accept an actor field.

Successful response: `200 OK`.

```json
{
  "case": {"id": "case-1", "state": "under_review", "payment_outcome": "unknown"},
  "audit_event": {
    "id": "audit-2",
    "action": "case_transitioned",
    "actor": "synthetic_local_operator",
    "previous_state": "open",
    "new_state": "under_review",
    "reason": null,
    "request_id": "req-transition-1",
    "created_at": "2026-01-05T00:01:00Z"
  }
}
```

An idempotent replay returns the original `200` status and identical response body.

### Create a case note

`POST /api/v1/cases/<case_id>/notes/`

Request:

```json
{"request_id": "req-note-1", "text": "Provider response remains unavailable."}
```

After trimming, `text` must be 1–2,000 characters. The server assigns `synthetic_local_operator` and does not accept an actor field.

Successful response: `201 Created`.

```json
{
  "note": {
    "id": "note-1",
    "case_id": "case-1",
    "text": "Provider response remains unavailable.",
    "actor": "synthetic_local_operator",
    "created_at": "2026-01-05T00:00:00Z"
  },
  "audit_event": {
    "id": "audit-1",
    "action": "note_created",
    "actor": "synthetic_local_operator",
    "note_id": "note-1",
    "request_id": "req-note-1",
    "created_at": "2026-01-05T00:00:00Z"
  }
}
```

An idempotent replay returns the original `201` status and identical response body.

## Idempotency and request IDs

Every state-changing operation requires a request ID. After trimming, it must be non-empty and no longer than 128 characters. The server validates it and never silently truncates it. The database uniqueness scope is `(case_id, action, request_id)`.

The semantic fingerprint is computed after validation and trimming. Transition fingerprints contain `target_state` and `reason`; note fingerprints contain `text`. The synthetic actor is server-controlled and excluded from the client payload. JSON key ordering and insignificant surrounding whitespace cannot change a fingerprint.

The idempotency record persists the normalized fingerprint, original HTTP status, and original response body. A repeated key with the same fingerprint replays that status/body without another case change, note, or audit event. A repeated key with a different fingerprint returns `409 Conflict` and `idempotency_key_reused`. Database uniqueness and transaction handling are the intended guards for concurrent same-key requests, but concurrent behavior has not been demonstrated on the supported production database backend; SQLite test results do not establish that guarantee.

## Errors

All errors use:

```json
{"error": {"code": "invalid_transition", "message": "The requested transition is not allowed."}}
```

| Condition | Status | Code |
|---|---:|---|
| Missing/malformed request ID or malformed body | 400 | `request_id_required` or `invalid_request` |
| Case does not exist | 404 | `case_not_found` |
| Disallowed lifecycle transition | 409 | `invalid_transition` |
| Same key with different semantic payload | 409 | `idempotency_key_reused` |
| Blank reason | 422 | `reason_required` |
| Reason over 500 characters | 422 | `reason_too_long` |
| Blank note | 422 | `note_required` |
| Note over 2,000 characters | 422 | `note_too_long` |

Internal database errors and stack traces are never returned. Failed validation, rejected transitions, or rolled-back transactions leave case state, notes, idempotency results, and audit history unchanged.

Malformed JSON and structurally invalid payloads return `400` with `invalid_request`. A retryable unresolved persistence/concurrency condition returns `503` with `concurrency_retryable`. Clients must retry that operation with the same request ID and normalized payload.

## Atomicity, audit, and compatibility

Successful transitions atomically persist the state change, idempotency record, and exactly one `case_transitioned` audit event. Successful note creation atomically persists the note, idempotency record, and exactly one `note_created` audit event. Audit metadata includes case ID, actor, timestamp, action-specific fields, and request ID or idempotency reference.

Case, note, audit, and idempotency queries are scoped to the requested case and payment relationship. Case state never overwrites or influences the Phase 1 payment outcome; findings remain derived from evidence. Audit records are append-only through the application workflow, not tamper-proof or compliance-certified storage.
