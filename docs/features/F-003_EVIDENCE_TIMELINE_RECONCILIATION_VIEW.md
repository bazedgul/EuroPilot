# F-003 — Evidence Timeline and Reconciliation View

## Status

Scope and implementation authorized on 2026-10-24 for the bounded local/demo scope only. Phase 2 acceptance, production readiness, and production database concurrency verification remain outstanding.

Owner: **Bazed Gul**

This specification defines a bounded read-only presentation feature. It does not claim that F-003 is implemented or accepted.

## User problem

Phase 1 provides deterministic investigation results and an evidence timeline. Phase 2 provides reconciliation case state, notes, and audit history. Operators need to review those existing resources together without confusing payment outcome with case lifecycle state.

## Approved scope

F-003 is a narrow, read-only frontend composition feature that presents existing Phase 2 reconciliation case context alongside the existing Phase 1 investigation result and evidence.

### Required behavior

- Use the existing case-detail and investigation-detail APIs.
- Treat `case.investigation_id` as the authoritative investigation lookup.
- Preserve the case shell if the investigation relationship is missing, malformed, or mismatched.
- Show a safe investigation error when related investigation data cannot be loaded or validated.
- Never show evidence from an unrelated investigation.
- Use the existing retryable-error behavior for manual retry.
- Compose the existing investigation result/evidence with case state, notes, and audit history.
- Reuse existing Phase 1 timeline and result behavior; do not duplicate its outcome rules or timeline engine.

### Explicitly out of scope

- New backend endpoints.
- New database schema, persistence, or migrations.
- New payment actions or payment-state mutations.
- New provider integrations.
- New outcome or evidence-authority rules.
- AI-generated authority over payment outcomes.
- Evidence filters and advanced search.
- Changes to Phase 1 AC-108 beyond documenting reuse and avoiding duplication.

## Outcome and evidence invariants

- Payment outcome remains separate from case lifecycle state.
- The existing outcomes remain `confirmed_success`, `confirmed_failure`, `unknown`, and `conflict`.
- Evidence provenance, source, type, reference, provider information when available, event time, received time, and authority information when available remain visible through the existing investigation response.
- F-003 does not calculate, override, persist, or reinterpret findings.
- Missing, delayed, malformed, unknown, and conflicting evidence remains explicit according to Phase 1 behavior.

## Relationship and failure behavior

The case response's `investigation_id` is the authoritative lookup source. If the relationship or related investigation is missing, malformed, inconsistent, or cannot be safely validated:

- keep the case shell visible;
- show a safe investigation error;
- provide manual retry using existing retryable-error behavior where applicable;
- never fall back to lookup by amount, timestamp, similarity, or an unrelated identifier; and
- never render evidence from an unrelated investigation.

## Dependencies and limitations

- Existing Phase 1 investigation result, evidence, and timeline behavior.
- Existing Phase 2 case-detail, notes, and audit-history behavior.
- Existing case-detail and investigation-detail API contracts.
- Phase 2 formal owner acceptance remains pending.
- Production-supported database concurrency guarantees remain unverified.
- No production readiness is established by this specification.

## Acceptance criteria

- **AC-301:** The case-detail workflow composes the case response with the investigation identified by `case.investigation_id`.
- **AC-302:** Payment outcome and case lifecycle state are displayed as separate concepts.
- **AC-303:** Existing Phase 1 result, timeline, evidence, provenance, timestamps, and explicit unknown/conflict states are reused without a duplicate outcome or timeline engine.
- **AC-304:** Missing, malformed, or mismatched investigation relationships keep the case shell visible, show a safe investigation error, and render no unrelated evidence.
- **AC-305:** Manual retry follows existing retryable-error behavior.
- **AC-306:** Existing case state, notes, audit history, transitions, validation, and idempotency behavior remain unchanged.
- **AC-307:** No new endpoint, schema, persistence, migration, payment action, provider integration, outcome rule, evidence-authority rule, or AI authority is introduced.
- **AC-308:** Evidence filters and advanced search remain outside F-003.
- **AC-309:** Phase 2 formal acceptance and production database concurrency limitations remain explicitly unresolved unless separately evidenced and approved.

## Test planning

Implementation planning must include focused frontend/API-contract, regression, accessibility, and security-negative tests for combined loading, partial case-shell states, retry, missing/malformed/mismatched relationships, unrelated-evidence isolation, outcome/state separation, safe text rendering, and preservation of Phase 1/Phase 2 behavior.

No test result is claimed by this specification.

## Governance and authorization

The owner authorized implementation on 2026-10-24 only within the bounded local/demo scope documented here. This authorization does not constitute implementation completion, formal Phase 2 acceptance, production readiness, or production database concurrency verification.

## Changelog

- 2026-10-24: Initial proposed specification and recorded scope approval.
