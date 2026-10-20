# Phase 00 — Documentation Foundation

Status: In Progress; owner approval required. The documentation foundation is complete enough to guide the current local demo implementation; Phase 0 is not a production-readiness approval.

## Objective and scope

Establish accurate, linked product, domain, architecture, security, UI/UX, testing, performance, requirements, phase, and feature-index documentation. Preserve useful existing content and surface contradictions.

## Feature specifications

No implementation feature is approved. `DOC-000` is the documentation foundation tracked by this phase; the registry is not a substitute for future feature specifications.

## Acceptance criteria

- **AC-001**: Root agent instructions and product source are distinct and linked.
- **AC-002**: MVP read-only synthetic-data boundaries are consistent.
- **AC-003**: Stable requirement and acceptance IDs exist.
- **AC-004**: Proposals, assumptions, open questions, and deferred work are labeled.
- **AC-005**: No application code, dependencies, services, secrets, or test claims are introduced.
- **AC-006**: Owner review blockers and next-phase prerequisites are explicit.

## Completed work and evidence

The documentation foundation was reviewed on the dedicated branch. The mixed source-of-truth content was reorganized into a product-focused document while agent workflow remains in `AGENTS.md`. Subsequent local demo work added the deterministic backend, SQLite persistence, read-only API, and React dashboard; their checks are reported in implementation handoffs, not treated as Phase 0 approval.

## Exit criteria and blockers

Owner approval remains required for domain states/correlation, architecture/toolchain, security/tenancy/retention, API direction, and Phase 1 scope. Until then status remains In Progress.
