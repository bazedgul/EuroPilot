# Data Model

Status: Proposed conceptual model. Phase 2 case-workflow records and migrations are documented as implemented locally. Formal Phase 2 acceptance remains pending, and production database concurrency guarantees and production readiness remain unverified.

## Existing Phase 1 records and persistence

Verified repository records include invoice/payable, logical payment, payment attempt, provider event, event-delivery occurrence, investigation, evidence item, and a derived-at-read-time finding representation. They are implemented as Django models and additive migrations backed by local synthetic SQLite persistence. Phase 1 findings are calculated from current evidence for API responses; the persisted finding-related records are not a Phase 2 snapshot design.

The conceptual model does not define a production database. The current repository uses local synthetic SQLite persistence and Django migrations.

## Proposed Phase 2 records and constraints

Phase 2 proposes a reconciliation case belonging to exactly one investigation, separate note records belonging to one case, append-only application audit events, and persisted idempotency records. These records and constraints are documented as implemented in the local Phase 2 workflow. Formal acceptance, supported-production concurrency verification, and production readiness remain unresolved.

Proposed case fields include lifecycle state, investigation reference, timestamps, and any approved resolution reason. Notes include case reference, note ID, normalized text up to 2,000 characters, timestamp, and server-controlled actor `synthetic_local_operator`. Transition reasons are normalized text up to 500 characters. Request IDs are normalized, non-empty, and at most 128 characters. Audit events include action, case/entity references, actor, timestamp, and action-specific metadata. Idempotency records include case, action, request ID, normalized request fingerprint, original status, and original response body.

The request uniqueness constraint is `(case_id, action, request_id)`. State-changing operations and their audit events must be written atomically. Case, note, audit, and idempotency access must enforce case/payment isolation. Notes and reasons are untrusted text and must not be stored or rendered as executable markup.

Database constraints enforce supported case/action values, non-empty request IDs, scoped idempotency uniqueness, one-to-one case/investigation and audit/idempotency relationships, and foreign-key protection. Normalization, maximum lengths, fingerprint hexadecimal format, cross-record action/request consistency, transition validity, and atomic multi-record behavior require the model validation or future transactional domain/service boundary; direct bulk/raw database writes can bypass Python validation where no portable database constraint exists.

Audit events are append-only through the application workflow, not tamper-proof storage. Migrations must add tables/columns and constraints without deleting or rewriting Phase 1 data.

## Deferred concerns

Production tenancy, retention/deletion, payload storage/redaction beyond this synthetic workflow, event versioning, authentication, authorization, and audit immutability remain deferred. No Phase 2 finding snapshot is proposed because findings remain derived from existing evidence.
