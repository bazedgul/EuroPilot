# EuroPilot — Project Source of Truth

## Document status

This document defines EuroPilot’s product purpose, terminology, scope boundaries, domain principles, and acceptance principles. It is not an agent workflow document; repository instructions are in [`../AGENTS.md`](../AGENTS.md).

Status: Proposed product foundation; owner approval required for material unresolved decisions.

EuroPilot is an early-stage concept. This document does not establish customer demand, market uniqueness, revenue potential, compliance, security certification, or production readiness.

## Product purpose and users

EuroPilot is an AI-assisted payment incident investigation and reconciliation platform. It helps operators understand uncertain, delayed, duplicated-looking, or contradictory payment-related events across automated systems.

The initial target user is a payment or operations operator investigating an incident. Additional roles, tenancy, and permissions require owner approval.

The working market hypothesis is that businesses operating automated or agent-initiated B2B payment workflows may need a cross-system investigation layer. This hypothesis is unvalidated.

## Problem scenarios and workflow

Initial scenarios include:

- A payment request times out and a retry occurs, but the original outcome is unknown.
- Duplicate event deliveries make one transaction appear to have multiple attempts.
- An invoice or payable record conflicts with provider events.
- Provider events arrive late or out of order.
- A payment attempt has no final, trustworthy provider response.

The proposed investigation workflow is to load synthetic records; preserve source identity, delivery identity, timestamps, and provenance; correlate records; build an auditable evidence timeline; apply deterministic rules; present findings, conflicts, missing evidence, and limitations; and optionally generate an AI explanation or investigation questions from supplied evidence. Exact state transitions, correlation precedence, and manual-review rules require approval.

## Domain concepts

The domain must distinguish the following concepts; final relationships and schema constraints require approval:

- **Invoice/payable** — an obligation record.
- **Logical payment/transaction** — intended settlement, distinct from submissions.
- **Payment attempt** — one submission or retry associated with a logical payment.
- **Provider event** — an observed message from a simulated provider source.
- **Event-delivery occurrence** — a delivery instance when duplicate delivery differs from event identity.
- **Incident/investigation** — uncertainty, conflict, or reconciliation work.
- **Evidence item** — an observed fact with source, identity, timing, and provenance.
- **Finding/recommendation** — a deterministic result, missing-evidence statement, or advisory explanation.
- **Audit record** — a record of material access or change where required by the approved model.

A retry is not automatically a new logical payment, and a delivered event is not automatically a new transaction.

## Evidence and reconciliation principles

- A timeout, network error, or missing response does not prove success or failure.
- If authoritative evidence is missing, the outcome remains unknown or requires further investigation.
- Material findings must be traceable to supporting evidence and deterministic rules.
- Observed facts, deterministic findings, AI explanations, hypotheses, missing evidence, conflicts, and unknown outcomes must remain distinguishable.
- Duplicate, replayed, late, out-of-order, malformed, unknown, and conflicting records must remain explicit and be handled safely.
- Amount and timestamp similarity alone cannot establish identity or correlation.
- Provider status mappings must come from approved synthetic fixtures or adapters; no universal mapping is assumed.
- Monetary values must use decimal-safe representations, not binary floating point.
- The same inputs and approved configuration should produce reproducible rule results.

## MVP scope and non-goals

The initial MVP is a development, demonstration, and product-validation project. It must use synthetic data and simulated provider events; focus on investigation, evidence correlation, reconciliation, and operator visibility; keep financial operations read-only; make uncertainty explicit; use deterministic rules for authoritative classification; and keep core investigation functional without an external AI service.

It must not initiate or execute real payments, move money, automatically approve or reject financial transactions, automatically cancel/reverse/refund real payments, claim to stop a submitted payment, connect production bank accounts, require production payment credentials, or claim production-grade compliance, certification, or readiness without evidence.

Any future real-provider integration or financial-action capability requires a separate feature specification, explicit owner authorization, provider-access review, security/privacy assessment, and updated acceptance criteria.

## AI responsibilities and limits

AI is advisory, not authoritative payment state. It may summarize supplied evidence, explain deterministic results and discrepancies, identify missing evidence, suggest investigation questions, and generate structured summaries when validated.

AI must not invent events, responses, timestamps, identifiers, or evidence; declare success or failure when authoritative evidence is missing; override deterministic rules; change authoritative payment state; initiate, approve, cancel, reverse, or refund payments; or access databases, shells, payment systems, or privileged APIs without separately approved, constrained tooling.

Model output is untrusted until schema validation. Invoice text, event metadata, notes, and logs are untrusted content and must not become instructions. Only minimum necessary, sanitized evidence may be sent to an AI provider. Local inference may be considered, but does not remove privacy, access-control, or validation requirements.

## Security, privacy, and auditability

Future implementation must use secure defaults, server-side validation, authentication and authorization, appropriate object or tenant isolation, least privilege, safe errors, bounded queries, timeouts, and bounded retries. Secrets, credentials, bank details, and unnecessary sensitive payloads must not be committed or logged.

Retention, deletion, tenancy, audit immutability, payload redaction, sensitive-data classification, and external-AI privacy require owner approval before real customer information or production integrations. Material findings and changes must be auditable to the extent defined by the approved model. No security audit or certification has been performed.

## Acceptance principles

Documentation and future implementation must keep scope consistent across requirements, domain, architecture, API, UI, security, testing, and phase documents; preserve unknown outcomes when evidence is insufficient; keep deterministic behavior independent of AI; provide evidence provenance for material findings; specify duplicate/retry/order/malformed/conflict/missing-evidence cases; label proposals and assumptions; and make no unverified implementation, benchmark, security, market, or deployment claims.

## Assumptions and owner decisions

Owner approval is still required for payment/attempt/event/incident/finding states; correlation precedence, idempotency, replay and conflict handling; tenancy; authentication and authorization; retention and deletion; audit and sensitive-data rules; public API shape and versioning; architecture and tool versions; deployment and CI limits; performance targets; and Phase 1 scope. These are open questions, not approved decisions.

## Related specifications

- [`REQUIREMENTS.md`](REQUIREMENTS.md)
- [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md)
- [`BUSINESS_RULES.md`](BUSINESS_RULES.md)
- [`DATA_MODEL.md`](DATA_MODEL.md)
- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md)
- [`SECURITY.md`](SECURITY.md)
- [`phases/PHASE_00_FOUNDATION.md`](phases/PHASE_00_FOUNDATION.md)
- [`features/FEATURE_REGISTRY.md`](features/FEATURE_REGISTRY.md)
