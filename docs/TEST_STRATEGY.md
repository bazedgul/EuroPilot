# Test Strategy

Status: Phase 2 implementation and reported automated coverage exist; formal owner acceptance remains pending. The results below distinguish previously reported evidence from checks performed during a future review.

## Existing regression coverage

Retain Phase 1 domain, persistence, API, and frontend coverage for deterministic outcomes, provenance, conflicts, retries, duplicate deliveries, payment isolation, idempotent synthetic seeding, read-only GET behavior, pagination, loading, empty, error, and outcome presentation.

## Phase 2 required coverage

### Domain and persistence

- Every approved transition succeeds; invalid transitions and terminal `resolved` fail.
- Whitespace-only and overlong reasons/notes fail; 500-character reasons and 2,000-character notes are accepted without truncation.
- Whitespace-only, overlong, and 129-character request IDs fail; trimmed request IDs from 1 through 128 characters are accepted without truncation.
- Normalization trims surrounding whitespace consistently for validation, persistence, and fingerprinting.
- Every note and audit event receives server-controlled actor `synthetic_local_operator`.
- Database uniqueness enforces `(case_id, action, request_id)`.
- Same key and same fingerprint replay the original status/body; same key and different fingerprint returns `409` with `idempotency_key_reused`.
- Production-supported concurrent duplicate requests must result in one logical operation, one note or transition, and one audit event; this behavior is deferred/not verified and is outside the currently demonstrated local evidence.
- Transaction rollback leaves case state, notes, successful-operation idempotency results, and audit history unchanged.
- Case, note, audit, and idempotency records cannot cross investigation/payment boundaries.
- Payment outcome remains unchanged and derived from Phase 1 evidence after case actions.

### API

- Required stable error envelope and codes for malformed request IDs, missing cases, invalid transitions, missing/overlong reasons, missing/overlong notes, and idempotency mismatch.
- Correct status mapping: 200 transition/replay, 201 note creation, 400 structural errors, 404 missing case, 409 transition/idempotency conflicts, and 422 content validation.
- Original replay status and response body are returned exactly; no duplicate audit events are produced.
- Failed validation, rejected transitions, and transient transaction failures do not leave partial writes.
- Existing Phase 1 GET endpoints remain read-only and compatible.

### Frontend

- Case outcome and case lifecycle are displayed separately.
- Character limits are visible and enforced client-side, with server validation authoritative.
- Notes and reasons render as text without HTML interpretation.
- Loading, retry, validation-error, conflict-error, and successful mutation states are visible and safe.
- Audit entries distinguish `case_transitioned` from `note_created` and show synthetic actor labels.

Commands and results must be reported as `Command`, `Result`, and `Evidence`; this document claims no new test result.

## Reported Phase 2 evidence

The owner previously reported 85 backend tests passing, 16 frontend tests passing, a passing Django system check, no pending model changes, and a passing frontend production build. These are reported results, not independently rerun by this document.

The owner also reported isolated verification on backend port `8002` using the fresh synthetic test database: both an empty-string reason and a three-space reason for `under_review` → `resolved` returned HTTP `422` with `reason_required`; the case remained `under_review` and note/audit counts remained `0` and `1` after each test.

The frontend suite reported 2 test files and 18 tests passing. The added UI tests verify that a `409` idempotency conflict shows the safe conflict message without automatic retry or false success, and that a `503` retryable error shows retry guidance, reuses the identical request ID and payload, and refreshes only after a successful retry.

## Unverified and deferred coverage

Concurrent duplicate-request behavior has not been demonstrated on the supported production database backend; SQLite test results do not establish production-grade concurrency guarantees. Production-supported concurrency remains deferred/not verified. Formal owner acceptance is also outstanding.
