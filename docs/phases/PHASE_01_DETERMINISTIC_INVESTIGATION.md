# Phase 01 — Deterministic Investigation Vertical Slice

## Status

Proposed; awaiting explicit owner approval. Phase 0 remains `In Progress` until its documented owner decisions are approved. This plan authorizes no implementation by itself.

## Objective

Define the smallest testable vertical slice for investigating one synthetic logical payment with one or more attempts and provider events. The slice should show how evidence is represented, correlated, reconciled, and presented when the outcome is confirmed or remains unknown.

## Scope

The proposed slice includes:

- Synthetic fixtures for an invoice/payable, logical payment, payment attempts, provider events, delivery occurrences, and evidence items.
- Deterministic correlation and reconciliation services for one investigation.
- Read-only investigation and evidence responses through an approved API contract.
- A minimal operator flow: investigation list, investigation detail, evidence timeline, finding, and explicit unknown/conflict state.
- Tests for a timeout/retry with unknown outcome, duplicate delivery, late or out-of-order events, and conflicting evidence.

## Non-goals

No real payment execution, money movement, approval, cancellation, reversal, refund, production provider integration, production credentials, AI integration, multi-service architecture, Celery, Redis, or unrelated UI/platform work is in scope. AI explanations, authentication/tenancy, and deployment are not silently approved by this plan.

## Assumptions

- Data is synthetic and provider behavior comes only from approved fixtures.
- Deterministic rules are authoritative; unknown remains a valid result.
- The first slice can use a modular-monolith boundary, but exact stack versions and persistence choices remain proposed in [`../SYSTEM_ARCHITECTURE.md`](../SYSTEM_ARCHITECTURE.md).
- The API and UI are specified before implementation and may be narrowed further by the owner.

## Proposed minimal model

The slice should represent, subject to approval:

- `Invoice`: payable identifier and amount using decimal-safe representation.
- `Payment`: logical payment identifier and relationship to the invoice.
- `Attempt`: attempt identifier, payment relationship, retry relation, request time, and observed request outcome.
- `ProviderEvent`: provider/source identity, event identity, event type, event time, received time, payload reference, and status information.
- `EventDelivery`: delivery identity and link to a provider event for duplicate/replay handling.
- `Evidence`: source, identity, provenance, observed/received times, and the fact or conflict it supports.
- `Investigation`: related records, deterministic finding, uncertainty/conflict state, and missing-evidence indicators.

Exact fields, lifecycle states, uniqueness constraints, tenant ownership, retention, and payload-redaction rules require owner approval before implementation.

## Deterministic reconciliation proposal

1. Identify records using explicit approved identifiers and provider/event identity; amount and timestamp similarity alone is insufficient.
2. Treat retries as attempts related to a logical payment, not as automatic new payments.
3. Deduplicate delivery occurrences without discarding provenance.
4. Normalize event ordering for the evidence timeline while retaining original event and receipt times.
5. Apply approved deterministic rules to classify confirmed evidence, conflict, or unknown.
6. Keep the result unknown when authoritative success/failure evidence is absent or contradictory.
7. Attach supporting evidence and missing-evidence reasons to every material finding.

The precedence rules and final state taxonomy are open owner decisions; this section is not an approval of those semantics.

## Proposed API and UI slice

The API should expose a read-only investigation list and detail response, including related attempts, provider events, evidence, finding, uncertainty/conflict state, and pagination where needed. Endpoint names, schemas, authentication, authorization, versioning, and error envelopes remain subject to [`../API_CONTRACT.md`](../API_CONTRACT.md) and owner approval.

The UI should provide an investigation list and detail view with a timeline showing source, event type, event time, receipt time, correlation status, evidence references, missing evidence, and an explicit unknown/conflict presentation. Loading, empty, error, partial-data, and retryable states are required. No green success styling should be used for an unknown outcome.

## Required tests

- A timed-out attempt followed by a retry with no authoritative final event remains unknown.
- A duplicate delivery does not create a second logical payment or unsupported success.
- Late and out-of-order events retain provenance and produce deterministic results.
- Conflicting provider evidence is visible and does not silently become success or failure.
- Missing, malformed, and unknown event types fail safely or remain explicit.
- The same approved fixture produces the same finding repeatedly.
- Unauthorized or invalid API requests are rejected once authentication/authorization is approved.
- Evidence and findings expose no unnecessary sensitive payloads.

## Security, privacy, auditability, and failure handling

Treat fixture payloads and imported text as untrusted. Validate input at boundaries, use server-side access control, avoid sensitive logging, preserve evidence provenance, and record material investigation changes where the approved audit model requires it. Bound queries and external calls; the core deterministic flow must not depend on AI. Invalid or unavailable AI, if later added, must not alter authoritative findings.

Failures must preserve source records where safe, report validation/correlation problems explicitly, and avoid converting timeouts or integration errors into payment success or failure.

## Proposed implementation sequence

1. Obtain owner approval for the domain state taxonomy, correlation/idempotency rules, data fields, API shape, security model, and slice acceptance criteria.
2. Write or approve synthetic fixtures and deterministic rule examples.
3. Implement and test the domain/evidence layer.
4. Implement approved persistence and read-only API behavior.
5. Implement the minimal investigation list/detail UI and accessibility states.
6. Run unit, integration, API, frontend, security-negative, and selected end-to-end checks appropriate to the approved slice.
7. Review the diff, update the feature registry/specifications, and obtain owner review before expanding scope.

## Acceptance criteria

- **AC-101**: The approved slice represents payments, attempts, events, deliveries, evidence, and investigations without conflating their identities.
- **AC-102**: A timeout/retry with insufficient evidence remains explicitly unknown.
- **AC-103**: Duplicate, late, out-of-order, and conflicting events are represented and handled deterministically.
- **AC-104**: Every material finding references supporting evidence or a documented missing-evidence reason.
- **AC-105**: The API and UI expose read-only investigation data with explicit unknown/conflict and failure states.
- **AC-106**: Required security, privacy, authorization, and audit checks for the approved slice have evidence.
- **AC-107**: No real payment, money movement, production provider, AI authority, or unapproved infrastructure is introduced.

## Risks and unresolved decisions

High-impact risks are incorrect correlation, false certainty from incomplete evidence, accidental sensitive-data retention, and scope expansion into payment operations. Owner approval is required for state taxonomy, provider fixture semantics, correlation precedence, tenancy/authentication, retention, API contracts, architecture/tool versions, and whether AI belongs in a later phase.

## Verification commands

Commands must be finalized after the owner approves the toolchain. At minimum, the implementation task must record exact commands and results for domain tests, persistence/API tests, frontend checks, accessibility/security checks, and selected end-to-end tests. Until then, no test result or performance benchmark is claimed.
