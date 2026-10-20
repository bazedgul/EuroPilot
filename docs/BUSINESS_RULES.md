# Business Rules

Status: Proposed; not implemented or verified.

- **DOM-001**: Unknown is a valid payment outcome.
- **DOM-002**: Evidence must be traceable by source, identifier, observed time, received time, and provenance once the schema is approved.
- **DOM-003**: Deterministic rules own authoritative classifications; AI cannot override them.
- **DOM-004**: Retries, duplicate deliveries, replayed events, late events, out-of-order events, and conflicts require explicit handling.
- **DOM-005**: Monetary values use decimal-safe representation, never binary floating point.
- **DOM-006**: Provider-specific mappings must come from approved synthetic fixtures/adapters; no universal mapping is assumed.
- **DOM-007**: Missing evidence produces an investigation state or finding, not invented certainty.

Open approvals: exact state machine, precedence rules, manual-review triggers, and reconciliation policy.
