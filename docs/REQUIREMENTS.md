# Requirements

Status: Proposed pending owner review. No requirement is implemented or verified in Phase 0.

## Product requirements

- **REQ-001**: The MVP shall use synthetic data and simulated provider events.
- **REQ-002**: The system shall represent logical payments separately from attempts, provider events, delivery occurrences, invoices, incidents, and evidence where the approved model requires them.
- **REQ-003**: The system shall preserve an unknown outcome when authoritative evidence is insufficient.
- **REQ-004**: Duplicate, late, out-of-order, malformed, and conflicting events shall be handled explicitly and safely.
- **REQ-005**: Material findings shall reference the evidence and deterministic rules supporting them.
- **REQ-006**: AI explanations shall be advisory, evidence-bound, schema-validated, and unable to override deterministic classifications.
- **REQ-007**: The MVP shall not execute payments, move money, approve financial transactions, or claim to cancel/reverse/refund submitted payments.
- **REQ-008**: Investigation data and access shall be protected by server-side validation, authorization, bounded queries, and auditability appropriate to the approved deployment model.
- **REQ-009**: The architecture shall remain a modular monolith unless an approved ADR establishes a concrete need for additional infrastructure.
- **REQ-010**: Documentation shall distinguish facts, approved decisions, proposals, assumptions, open questions, and deferred work.

## Open approvals

Owner approval is required for exact state taxonomy, tenancy, retention, public API shape, architecture/tool versions, and Phase 1 scope. These choices affect persistence, authorization, and compatibility.
