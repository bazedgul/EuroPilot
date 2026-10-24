# Phase 02 — Deterministic Reconciliation Case Workflow

## Status

Approved Phase 2 scope; Steps 1–6 are implemented locally according to previously reported automated and isolated-browser evidence. Production-supported concurrent duplicate-request guarantees remain deferred/not verified, and formal owner acceptance is pending. This specification extends Phase 1 with read-only payment operations and local case-management mutations. It does not authorize production authentication, tenancy, payment actions, live providers, AI authority, or infrastructure changes.

## Objective

Provide an operations analyst with a minimal case workflow around a Phase 1 investigation: track case status, record bounded untrusted notes, record explicit resolution or deferral reasons, and inspect append-only application audit history. The payment outcome remains derived from Phase 1 evidence and is never changed by case actions.

## Approved decisions

- **Case states:** `open`, `under_review`, `resolved`, `deferred`.
- **Transitions:** `open → under_review|deferred`; `under_review → resolved|deferred`; `deferred → open|under_review`; `resolved` is terminal for this phase.
- `resolved` and `deferred` transitions require a trimmed, non-empty reason of at most 500 characters. Submitted content is rejected when invalid; it is never silently truncated.
- Notes are separate persisted records with trimmed, non-empty text of at most 2,000 characters. Notes and reasons are untrusted text and are rendered without interpreting HTML.
- The server assigns fixed actor identifier `synthetic_local_operator` to every note and audit event. Clients cannot select or override it. This is a synthetic application actor, not an authenticated human identity.
- Every state-changing operation requires a trimmed, non-empty request ID of at most 128 characters. The server rejects invalid input and never silently truncates it. The database uniqueness scope is `(case_id, action, request_id)`.
- For transitions, the normalized semantic fingerprint contains target state and transition reason. For note creation, it contains note text. The server trims before validation, persistence, and fingerprinting; JSON key ordering and insignificant surrounding whitespace cannot change the fingerprint.
- A same-key/same-fingerprint retry replays the original HTTP status and response body without another operation or audit event. A same-key/different-fingerprint request returns `409 Conflict` with `idempotency_key_reused`.
- Original status and response body are persisted with the idempotency record. Process-local memory is not sufficient. Database uniqueness and transactions are the intended guards for concurrent requests. Concurrent behavior has not been demonstrated on the supported production database backend, so SQLite test results must not be treated as proof that only one logical operation takes effect under concurrency.
- Failed validation, rejected transitions, and failed transactions leave case state, notes, successful-operation idempotency results, and audit history unchanged. A retry after transient transaction failure is safe and deterministic.
- Findings remain derived from current Phase 1 evidence. No persisted finding snapshot is in scope.
- Case and audit persistence must commit atomically.

## Scope

### In scope

- Persisted case lifecycle separate from payment outcome.
- Validated transitions, bounded reasons, and separate bounded notes.
- Append-only application audit events containing action, entity references, timestamp, synthetic actor, and action-specific metadata.
- Read and mutation API contracts with stable validation errors and deterministic duplicate-request behavior.
- Minimal frontend status, transition, note, resolution, audit-history, loading, retry, and error workflow.
- Additive migrations, object/payment isolation, database uniqueness, and regression tests.

### Out of scope

Real payment execution or money movement; live providers; cancellation, reversal, refund, or approval; AI-authoritative decisions; production authentication or tenancy; notifications, SLA/work queues, analytics, deployment infrastructure, and tamper-proof/compliance-certified audit claims.

## Domain and integrity rules

- A case belongs to exactly one investigation and therefore one logical payment.
- A note belongs to exactly one case and is bounded untrusted text.
- Minimum audit actions are `case_transitioned` and `note_created`.
- `case_transitioned` records case ID, `synthetic_local_operator`, timestamp, previous state, new state, transition reason, and request ID or idempotency-record reference.
- `note_created` records case ID, `synthetic_local_operator`, timestamp, note ID, and request ID or idempotency-record reference.
- Audit events are append-only through the application model; this does not claim protection from privileged database modification.
- A successful transition and its audit event commit atomically. A successful note and its audit event commit atomically.
- A request for one case cannot read or mutate another case’s notes, audit events, or idempotency records through an improperly scoped query.
- Case lifecycle state never overwrites or influences the deterministic payment outcome. Findings remain derived from existing evidence.

## Implemented API behavior (local)

The implemented local paths are:

- `GET /api/v1/cases/` for a bounded case list.
- `GET /api/v1/cases/<case_id>/` for case detail, notes, and audit history.
- `POST /api/v1/cases/<case_id>/transitions/` for transitions.
- `POST /api/v1/cases/<case_id>/notes/` for note creation.

The contract requires:

- Case state and audit-history reads for an investigation.
- Case transition submission with target state, reason where required, and request ID.
- Note creation with note text and request ID.
- Server-controlled actor assignment.
- Stable error envelope `{"error": {"code": "invalid_transition", "message": "The requested transition is not allowed."}}`.
- `200` for successful transitions and same-payload replays; `201` for successful note creation and same-payload replays; `400` for structural errors; `404` for missing cases; `409` for invalid transitions or idempotency-key reuse with a different fingerprint; `422` for blank or overlong reasons/notes; and `503` with `concurrency_retryable` when persistence/concurrency cannot be safely resolved.
- Minimum error codes: `invalid_request`, `request_id_required`, `case_not_found`, `invalid_transition`, `reason_required`, `reason_too_long`, `note_required`, `note_too_long`, and `idempotency_key_reused`.
- Internal database errors and stack traces are never returned. A `503` retry must retain the same request ID and normalized payload for the same logical action.

No endpoint may execute or authorize a payment action.

## Implementation sequence

1. ~~Implement the exact API paths, fields, 128-character request-ID bound, and success response bodies defined in the API Contract.~~ **Implemented and tested.**
2. ~~Add additive case, note, audit, and idempotency persistence with database constraints and migration review.~~ **Implemented; live migration execution remains separately approved work.**
3. ~~Implement domain transition validation and transactional services.~~ **Implemented and tested.**
4. ~~Implement API endpoints, stable errors, fingerprinting, and deterministic replay.~~ **Implemented and tested.**
5. ~~Add the minimal frontend workflow with visible character limits and safe text rendering.~~ **Implemented and tested.**
6. Add backend/frontend acceptance tests, review the complete diff, and run existing validation commands. **Implemented locally with reported test evidence; production-backend concurrency remains outstanding. Phase 2 is not formally accepted.**

The case backfill management command is restricted to single-process execution. Do not run multiple backfill instances concurrently. Same-investigation duplicate protection relies on the database one-to-one constraint and `get_or_create()`, but this is not proof of full concurrent safety across database backends. Concurrent command execution remains unsupported until it is tested on the supported database backend.

## Acceptance criteria and evidence status

The criteria below define the approved requirements. Implementation and test evidence exists for the core workflow, but criteria must not be marked fully verified without criterion-specific evidence. Frontend automated tests reportedly cover the `409` idempotency-conflict and `503` retry paths, with 18 tests passing across 2 files; those tests were not rerun during this documentation update. Any manual browser verification beyond the reported evidence remains unverified. Production-supported concurrent-request behavior and formal owner acceptance remain outstanding.

- **AC-201:** A persisted case exposes one of the four approved lifecycle states independently of the Phase 1 payment outcome.
- **AC-202:** Only approved transitions succeed; invalid transitions, including transitions from terminal `resolved`, return `409` with `invalid_transition`.
- **AC-203:** `resolved` and `deferred` transitions reject whitespace-only or overlong reasons with `422`; accepted reasons are trimmed and never truncated. **Reported evidence:** empty-string and whitespace-only reasons each returned `422` with `reason_required`; in both isolated tests, the case state and audit history remained unchanged.
- **AC-204:** Every successful transition creates exactly one `case_transitioned` audit event with required metadata.
- **AC-205:** Every successful note creation creates exactly one persisted note and one `note_created` audit event with required metadata.
- **AC-206:** Notes accept trimmed text from 1 through 2,000 characters; reasons accept trimmed text from 1 through 500 characters; client limits do not replace server validation.
- **AC-207:** Every note and audit event receives server-controlled `synthetic_local_operator`; clients cannot override it.
- **AC-208:** Repeating the same case/action/request ID with the same fingerprint replays the original status/body and creates no duplicate operation or audit event.
- **AC-209:** Reusing the same case/action/request ID with a different fingerprint returns `409` with `idempotency_key_reused`; database uniqueness is the duplicate-operation guard, while concurrent duplicate-request behavior remains deferred verification on the supported production database backend.
- **AC-210:** Case, note, audit, and idempotency operations cannot cross investigation/payment boundaries.
- **AC-211:** Successful transitions/audits and successful notes/audits commit atomically; rejected or failed operations leave no partial state, successful-operation idempotency result, or audit event.
- **AC-212:** The payment outcome remains derived from Phase 1 evidence and is unchanged by case actions; no finding snapshot is introduced.
- **AC-213:** The implemented local case endpoints expose case state, reasons, notes, audit history, and stable safe validation errors without internal details, using the locked response shapes and status codes.
- **AC-214:** The frontend displays payment outcome separately from case state, enforces visible character limits, safely renders text, and provides loading, retry, validation-error, conflict-error, and success states.
- **AC-215:** Existing Phase 1 GET behavior, evidence provenance, conflict handling, retries, duplicate deliveries, and read-only guarantees remain compatible.
- **AC-216:** No payment execution, live provider, AI authority, production authentication/tenancy, or infrastructure is introduced.

## Reported acceptance evidence

The owner reported isolated verification on backend port `8002` using the fresh synthetic test database: case `case-investigation-1` began `under_review` with zero notes and one audit event; both a three-space reason and an empty-string reason for `under_review` → `resolved` returned HTTP `422` and `reason_required`; each final read showed `under_review`, zero notes, and one audit event. This verifies both required-reason input forms. It does not verify production-backend concurrency.

## Required tests

Test every approved transition, invalid and terminal transitions, whitespace-only and boundary-length content, no truncation, server-controlled actor assignment, fingerprint normalization/equality/mismatch, exact status/body replay, concurrent duplicate requests, database uniqueness, exactly one audit event per successful logical action, atomic rollback, cross-case/payment isolation, unchanged Phase 1 outcomes, stable API errors, and safe frontend note/reason rendering. Previously reported results cover substantial automated and happy-path browser evidence; production-backend concurrent duplicate requests remain deferred verification.

## Limitations and deferred decisions

Actor identity is synthetic and local. Retention, deletion, production authorization, tenancy, and audit immutability remain deferred. No tamper-proof or compliance-certified audit guarantee is claimed.
