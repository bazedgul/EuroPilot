# Phase 01 — Deterministic Investigation Vertical Slice

## Status

Proposed implementation task; owner-approved decisions recorded below. Phase 0 remains `In Progress` until its own completion requirements are satisfied. The deterministic domain, read-only API, frontend dashboard, and SQLite local/demo persistence are implemented in the working tree; this document remains the scope and safety reference, not a production-readiness claim.

## Objective

Define the smallest testable vertical slice for investigating one synthetic logical payment with multiple attempts and provider events. The slice should correlate evidence, reconcile it deterministically, and present a confirmed or explicitly unknown/conflicting result to an operator.

## Goals

- Represent the minimum records needed for one synthetic investigation.
- Preserve identity, provenance, event time, receipt time, and delivery history.
- Demonstrate timeout/retry, duplicate delivery, late/out-of-order evidence, conflict, and insufficient-evidence behavior.
- Expose a read-only investigation result through a proposed API shape and minimal operator UI.
- Produce repeatable deterministic findings from the same approved evidence set.

## Non-goals

No real payment execution, money movement, approval, cancellation, reversal, refund, production provider integration, production credentials, AI integration, production tenancy, multi-service architecture, Celery, Redis, deployment work, or unrelated UI/platform work is in scope. The local deterministic backend, SQLite persistence, read-only API, and dashboard are implemented within this demo scope; this plan does not approve production operation.

## Assumptions and constraints

- All records and provider behavior are synthetic fixtures.
- Deterministic rules are authoritative; unknown is a valid result.
- A modular-monolith boundary remains a proposal, consistent with [`../SYSTEM_ARCHITECTURE.md`](../SYSTEM_ARCHITECTURE.md).
- The API and UI are specified before implementation and may be narrowed by the owner.
- No provider-specific idempotency or status semantics are inferred without an approved fixture definition.

## Owner-approved decisions

The owner approved the six decisions below for the synthetic, read-only MVP. Approval does not claim implementation, production readiness, or completion of Phase 0. No approval date is recorded because no repository convention supplies one.

### Payment identity and retries — Approved

The model should distinguish an invoice/payable, logical payment, payment attempt, provider event, event delivery, investigation, and evidence record. Correlation should use explicit logical-payment, attempt, invoice, provider, event, and delivery identifiers only where their scope and provenance are defined. Amount, timestamps, descriptions, or other similarities must never establish identity by themselves.

A retry should be a distinct attempt related to the same logical payment when an explicit retry relationship or approved request identity supports that relationship. Request idempotency concerns repeated submissions for a logical payment; provider-event deduplication concerns repeated delivery of an already identified provider event. They are separate mechanisms and must not be conflated. Provider-specific idempotency behavior remains undefined until represented by an approved synthetic fixture.

### Findings and outcome taxonomy — Approved

The approved taxonomy is:

- `confirmed_success`: approved authoritative evidence establishes successful settlement for the logical payment, with no unresolved contradictory authoritative evidence.
- `confirmed_failure`: approved authoritative evidence establishes failure for the logical payment, with no unresolved contradictory authoritative evidence.
- `unknown`: evidence is missing, delayed, non-authoritative, or insufficient to establish success or failure.
- `conflict`: authoritative evidence supports incompatible outcomes or otherwise cannot be reconciled by an approved rule.

An approved timeout, missing event, delayed event, network error, or non-authoritative status cannot alone establish success or failure. Contradictory authoritative evidence remains visible as `conflict` unless an explicitly approved reconciliation rule resolves it. No generic event is authoritative across all providers; authority is defined by the synthetic provider fixture and its provenance.

### Event ordering and duplicates — Approved

Every event representation should preserve original provider event time and local received time. Delivery occurrences should remain traceable to the underlying provider event, including repeated deliveries and replays. Late or out-of-order events may change a finding only when the approved deterministic rule says the new evidence changes the evidence set; the timeline must retain both original ordering facts and the resulting evaluation.

Invalid, unknown, and conflicting evidence must not be silently discarded. Evaluation must use a deterministic ordering and rule version so the same evidence set and approved configuration produce the same result.

### Minimal data integrity — Approved for the first slice

The approved minimum constraints are: unique provider/event identity within an approved provider scope; unique delivery identity within its source scope; explicit relationships between invoice, logical payment, attempt, event, delivery, evidence, and investigation; a non-ambiguous logical-payment identifier; and a constraint preventing an attempt from belonging to multiple logical payments.

Event identity scope, request-idempotency scope, concurrency behavior, retention, payload storage/redaction, and evidence immutability/versioning remain bounded implementation details or deferred decisions; they must not be expanded into production claims.

## Authorized first implementation milestone

This is the owner-authorized first coding task, not an implementation claim:

1. A synthetic invoice/payable is associated with one logical payment.
2. The first payment attempt times out, so the outcome is `unknown` because no authoritative final result exists.
3. A retry creates a distinct attempt under the same logical payment.
4. Duplicate and delayed provider-event deliveries are represented through event identity and delivery identity without creating another logical payment.
5. The investigation API returns a deterministic finding, supporting evidence, missing-evidence reasons, and `unknown` or `conflict` where the evidence warrants it.
6. The UI presents the timeline and result without implying unsupported payment success or failure.

Essential first-slice behavior is limited to this scenario and its negative cases. Later extensions include additional provider fixtures, richer reconciliation, tenancy, AI explanation, production authentication, API endpoints, and frontend work.

## Executable implementation task

Implement only the deterministic domain/evidence layer and automated tests for the authorized milestone.

The implementation uses a minimal conventional backend layout and dependency manifest. Its responsibilities are:

- A domain module for invoice, logical payment, attempt, provider event, delivery, evidence, investigation, and approved outcome values.
- A deterministic rules module for identity relationships, retry/attempt correlation, delivery deduplication, evidence provenance, and outcome evaluation.
- Synthetic fixture builders for timeout/retry, duplicate-delivery, delayed/out-of-order, confirmed, conflict, and insufficient-evidence cases.
- Automated tests covering those rules and fixtures.

The API, frontend, migrations, and SQLite seed command are implemented only for the approved local/demo slice. AI adapters, provider integrations, and additional infrastructure remain out of scope.

Required behavior includes preserving all entity distinctions, keeping timeout without authoritative evidence as `unknown`, representing retries as distinct attempts under one logical payment, retaining delivery provenance, preserving provider and receipt times, applying the approved taxonomy, and rejecting or leaving unresolved amount/time-only correlations, invalid event types, malformed evidence, and insufficient evidence.

The current verification commands are documented in the root README and include Django checks/migrations, pytest, Python compilation, frontend tests, and the frontend production build. Visual browser verification remains manual follow-up.

## Approved minimal domain and evidence representation

- `Invoice`: payable identifier and decimal-safe amount.
- `Payment`: logical payment identifier and invoice relationship.
- `Attempt`: attempt identifier, payment relationship, retry relation, request time, and observed request outcome.
- `ProviderEvent`: provider/source identity, event identity, type, original event time, received time, and status/payload reference.
- `EventDelivery`: delivery identity, source scope, received time, and provider-event relationship.
- `Evidence`: source, identity, provenance, event/receipt times, observed fact, and links to the records it supports or contradicts.
- `Investigation`: related records, proposed outcome, supporting evidence, missing-evidence reasons, conflicts, and rule version.

Exact field names and internal module layout are safe engineering choices within this approved model. Production tenancy, retention, payload policy, and external integrations remain out of scope.

## Deterministic reconciliation

1. Correlate only using explicit approved identifiers and scoped relationships.
2. Treat retries as attempts related to a logical payment, not automatic new payments.
3. Deduplicate delivery occurrences without discarding provenance.
4. Retain original and received times when presenting ordered evidence.
5. Apply the approved evidence-precedence rules to derive `confirmed_success`, `confirmed_failure`, `unknown`, or `conflict`.
6. Keep insufficient or contradictory evidence explicit rather than converting it to certainty.
7. Attach supporting evidence, missing-evidence reasons, and rule/version provenance to every material finding.

The owner-approved taxonomy and provider-scoped authority apply to this milestone. Any new provider semantics or precedence rule requires a new approval.

## Implemented API and UI scope

The read-only investigation list/detail API and minimal UI are implemented for the local synthetic slice. Their response shape is documented in [`../API_CONTRACT.md`](../API_CONTRACT.md).

The UI provides investigation list/detail views and explicit outcome states. Visual browser verification is not claimed as complete without browser tooling.

## Security, privacy, auditability, and failure handling

For this local/demo domain milestone, synthetic data and local-access assumptions apply; production authentication, tenancy, and authorization are out of scope. Domain input validation, bounded collections, safe errors, untrusted fixture handling, sensitive-data minimization/redaction, and evidence provenance remain required. This is not a production-security claim.

Record material investigation changes and source provenance to the extent required by the approved audit model. Invalid input, unknown event types, duplicate deliveries, correlation failures, and unavailable dependencies must produce explicit safe outcomes. Timeouts and integration errors must never become payment success or failure. AI is excluded from this first slice unless separately approved; if later added, it cannot alter authoritative findings.

## Required tests and evidence

- A timed-out first attempt and retry with no authoritative final event returns `unknown`; evidence: a deterministic test fixture and observed response/finding.
- Duplicate delivery does not create a second event or logical payment; evidence: identity/constraint test and resulting investigation record.
- Late and out-of-order events preserve both times and produce the same result independent of ingestion order when the evidence set is the same; evidence: paired fixture runs and comparison.
- Contradictory authoritative evidence returns visible `conflict` unless an approved rule resolves it; evidence: fixture, finding, and evidence references.
- Missing, malformed, and unknown event types remain explicit or fail safely; evidence: validation/error assertions.
- Unsupported amount/time-only correlation is rejected or left unresolved; evidence: negative correlation test.
- The same fixture and rule version produce the same finding repeatedly; evidence: repeat-run comparison.
- API security tests are required only for the approved access mode and must demonstrate the approved validation/authorization behavior; no production security result is claimed here.
- Sensitive fields are minimized or redacted in responses and logs; evidence: response/log inspection under the approved test setup.

No performance benchmark or application test result is claimed before implementation.

## Acceptance criteria

- **AC-101**: Approved fixture data contains one invoice, one logical payment, two distinct attempts, provider events, deliveries, evidence, and one investigation without identity conflation. Evidence: fixture/schema assertions.
- **AC-102**: A timeout followed by a retry with insufficient authoritative evidence produces `unknown`, not success or failure. Evidence: deterministic rule test and API response assertion.
- **AC-103**: Duplicate deliveries remain linked to one provider event and do not create a second logical payment. Evidence: identity and deduplication test.
- **AC-104**: Original event time and received time remain visible for late/out-of-order evidence, and equal evidence sets produce repeatable findings. Evidence: ordering and repeatability tests.
- **AC-105**: Contradictory authoritative evidence is returned as visible `conflict` unless an approved rule resolves it. Evidence: conflict fixture, finding, and evidence references.
- **AC-106**: Every material finding includes supporting evidence or a missing-evidence reason, with provenance and rule version. Evidence: response/schema assertion.
- **AC-107**: Invalid, unknown, unsupported, and amount/time-only-correlated inputs are rejected or remain explicit without unsupported certainty. Evidence: negative tests.
- **AC-108**: The read-only API and minimal UI show the proposed result, timeline, evidence, and failure/unknown/conflict states without implying unsupported success. Evidence: API contract assertions and UI acceptance checks.
- **AC-109**: The approved local/demo security mode has server-side validation, bounded queries, untrusted-payload handling, and sensitive-data minimization. Evidence: security test checklist matched to the approved mode; this is conditional, not a production-security claim.
- **AC-110**: No real payment, money movement, production provider, AI authority, unapproved infrastructure, or unrelated feature is present. Evidence: scope/diff review.

## Implementation sequence after approval

1. Select and document minimal backend/tooling from the actual repository state.
2. Define fixtures and deterministic rule examples for the first vertical slice.
3. Implement and test the domain/evidence layer.
4. Review the deterministic diff and observed test output with the owner.
5. Review the API/UI demo behavior; defer AI, production security, tenancy, and integrations to later approved milestones.

## Owner decision checklist

### Recorded approvals

| Decision | Recommended default | Consequence of deferral |
|---|---|---|
| Outcome taxonomy and evidence precedence | Approved: four outcomes with provider-scoped authority | New statuses or precedence rules require approval |
| Correlation, request idempotency, and deduplication | Approved: separate logical-payment/attempt correlation from event-delivery deduplication | Provider-specific behavior remains fixture-scoped |
| Minimum fields and constraints | Approved for first slice: proposed records, relationships, scoped uniqueness, decimal amounts, preserved timestamps | Production schema expansion remains deferred |
| Local/demo security mode | Approved: synthetic local access, validation, bounded queries, safe errors, redaction, provenance | Not production authentication or security assurance |
| API response shape and pagination | Approved direction for a later read-only milestone | No API implementation in this task |
| AI exclusion from first slice | Approved: no AI in authoritative reconciliation or outcome decisions | AI requires a later approval |

### Safe to defer, with explicit limitation

| Decision | Recommended default | Consequence of deferral |
|---|---|---|
| Persistence/toolchain versions | Select minimal conventional tooling after repository inspection | No dependency or benchmark claim is made now |
| Retention and payload storage/redaction | Store only minimum synthetic data and redact by default; defer production retention policy | No real customer data or production integration may be introduced |
| Production tenancy/authentication | Defer; do not imply production authorization | The first coding task remains local/demo only |
| Additional provider fixtures and richer reconciliation | Defer until the first fixture behavior is approved | Coverage remains intentionally narrow |

## Risks and unresolved decisions

Primary risks are incorrect correlation, false certainty from incomplete evidence, accidental sensitive-data retention, ambiguous provider authority, and scope expansion into payment operations. The open decisions above and Phase 0 blockers remain owner decisions, not implementation assumptions.

## Verification commands

The current verification commands are recorded in the root README. API, frontend, migration, and deterministic tests are implemented and must continue to report observed results. Visual browser, end-to-end, performance, and production-security claims remain deferred; no benchmark or browser result is claimed here.
