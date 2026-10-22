# Business Rules

Status: Proposed; Phase 2 rules are approved planning scope and are not implemented or verified.

- **DOM-001**: Unknown is a valid payment outcome.
- **DOM-002**: Evidence is traceable by source, identifier, observed time, received time, and provenance.
- **DOM-003**: Deterministic rules own authoritative classifications; AI cannot override them.
- **DOM-004**: Retries, duplicate deliveries, replayed events, late/out-of-order events, and conflicts require explicit handling.
- **DOM-005**: Monetary values use decimal-safe representation, never binary floating point.
- **DOM-006**: Provider-specific mappings come from approved synthetic fixtures/adapters; no universal mapping is assumed.
- **DOM-007**: Missing evidence produces an investigation state or finding, not invented certainty.
- **DOM-008**: Case lifecycle state is separate from and cannot influence the deterministic payment outcome.
- **DOM-009**: Only approved transitions are valid: `open → under_review|deferred`, `under_review → resolved|deferred`, and `deferred → open|under_review`; `resolved` is terminal for Phase 2.
- **DOM-010**: `resolved` and `deferred` require trimmed, non-empty reasons no longer than 500 characters; invalid content is rejected without truncation.
- **DOM-011**: Notes are separate records containing trimmed, non-empty text no longer than 2,000 characters and are rendered as untrusted text.
- **DOM-012**: The server assigns `synthetic_local_operator` to notes and audit events; clients cannot select or override it.
- **DOM-013**: State-changing requests require a trimmed, non-empty request ID of at most 128 characters, unique within `(case_id, action, request_id)`; invalid values are rejected without truncation.
- **DOM-014**: Fingerprints use normalized semantic payloads; same-key/same-fingerprint requests replay the original status/body, while mismatches return `409 Conflict` with `idempotency_key_reused`.
- **DOM-015**: Successful case actions and corresponding audit events commit atomically; rejected or failed operations leave case state, successful-operation idempotency results, and audit history unchanged.
- **DOM-016**: Findings remain derived from existing evidence; case actions cannot create payment certainty or persist a Phase 2 snapshot.
- **DOM-017**: Audit actions are at minimum `case_transitioned` and `note_created`, with action-specific entity references and metadata.

No production authentication, tenancy, live provider, payment action, money movement, AI authority, or infrastructure guarantee is implied.
