# EuroPilot — Master Agent Instructions

**Repository:** `https://github.com/bazedgul/EuroPilot`  
**Document:** `AGENTS.md`  
**Status:** Initial project charter  
**Created:** 2026-10-20

---

## 1. Purpose of This File

This file defines the mandatory engineering rules for all developers and AI coding agents working on EuroPilot.

Every agent MUST read this file before making changes to the repository. These instructions apply to all features, fixes, refactors, tests, documentation changes, and deployment-related work.

EuroPilot must be developed through a controlled software development lifecycle. The objective is to build a reliable, secure, maintainable, testable, and professionally presented application—not to generate code quickly without understanding the requirements.

**Core rule: No implementation before specification, no completion claim without evidence, and no merge without review.**

## 2. Mandatory Reading Order

Before planning or implementing a task, the agent MUST read the following documents in this order:

1. `AGENTS.md`
2. `docs/PROJECT_SOURCE_OF_TRUTH.md`
3. The relevant phase document under `docs/phases/`
4. The relevant feature specification under `docs/features/`
5. Relevant architecture decision records under `docs/ADR/`
6. Related requirements, domain rules, API contracts, security rules, data models, and UI specifications
7. Existing implementation, tests, and project setup instructions relevant to the task

If a required document does not exist, the agent must not pretend that it has been read. The agent must identify the missing document and follow the approved documentation workflow before implementing behavior that depends on it.

If the documentation is incomplete or contradictory, the agent must stop the affected implementation and report the conflict.

### Source-of-Truth Rules

`docs/PROJECT_SOURCE_OF_TRUTH.md` is the authoritative document for approved product scope, goals, terminology, and MVP boundaries.

`AGENTS.md` is authoritative for agent behavior, repository workflow, and engineering rules.

Feature specifications define the detailed requirements and acceptance criteria for individual features.

Phase documents define the scope, dependencies, completion requirements, and exit criteria of each phase.

Architecture Decision Records (ADRs) record approved material technical decisions.

If existing code conflicts with an approved specification, the agent must not assume the existing code is correct. It must report the conflict and propose the appropriate fix.

An implementation, test, comment, or assumption does not automatically override an approved specification.

Applicable law and explicit owner-approved security requirements must also be respected. If any instruction creates a security or legal concern, stop and report it.

---

## 3. What Is EuroPilot?

EuroPilot is an early-stage concept for an AI-assisted payment incident investigation and reconciliation platform.

Its initial purpose is to help operators investigate uncertain, delayed, duplicated-looking, or contradictory payment-related events across automated systems.

Example scenarios include:

- A payment request times out and the system retries it, but the actual payment outcome is unknown.
- Duplicate event deliveries make a transaction appear to have multiple attempts.
- An invoice record and payment-provider events disagree.
- Provider events arrive late or out of order.
- A payment attempt has no final, trustworthy provider response.
- An operator needs to understand what happened, which evidence supports the conclusion, what remains unknown, and what action should be considered next.

EuroPilot should correlate available records, apply deterministic business rules, create an auditable evidence timeline, identify missing evidence, and optionally use AI to explain the investigation.

### Market Hypothesis

The working hypothesis is that businesses operating automated or agent-initiated B2B payment workflows may need a cross-system investigation layer to explain uncertain payment outcomes.

This is a hypothesis, not an established market fact.

Agents must not claim that EuroPilot has a unique market position, confirmed demand, validated willingness to pay, or no meaningful competitors unless reliable research establishes those claims.

Market research and customer validation must be documented separately from technical implementation.

### Initial MVP Boundaries

The initial MVP MUST:

- Use synthetic data and simulated provider events.
- Focus on investigation, evidence correlation, reconciliation, and operator visibility.
- Keep financial operations read-only.
- Make uncertainty explicit.
- Use deterministic rules for authoritative domain classifications.
- Allow AI-assisted explanations without giving AI unrestricted authority over the domain.
- Work without an external AI service for core deterministic investigation behavior.

The initial MVP MUST NOT:

- Initiate real payments.
- Transfer money.
- Automatically approve or reject financial transactions.
- Automatically cancel, reverse, or refund real payments.
- Claim to stop a payment already submitted to an external provider.
- Connect to production bank accounts or require production payment credentials.
- Claim production-grade financial compliance or security certification without evidence.

Any future real-provider integration or financial-action capability requires a separately approved feature specification, explicit owner authorization, appropriate provider access, a security and privacy assessment, and updated acceptance criteria.

EuroPilot is initially a development, demonstration, and product-validation project. Do not describe it as a production-ready financial control system.

---

## 4. Engineering Principles

All work must follow these principles:

1. Specification before implementation.
2. Small, independently reviewable tasks.
3. One clearly defined objective per feature branch.
4. Automated tests for new and changed behavior.
5. Explicit and testable acceptance criteria.
6. Secure defaults and server-side validation.
7. Deterministic business logic for authoritative decisions.
8. Evidence-based AI explanations.
9. Documentation updated alongside implementation.
10. No unnecessary complexity or premature optimization.
11. No unapproved features, dependencies, or architecture changes.
12. Honest reporting of completed work, test results, and limitations.
13. Preserve a working `main` branch.
14. Owner approval for material product and architecture decisions.

Do not use uncontrolled vibe coding. The agent must understand the requirements, inspect the relevant code, implement the defined scope, test it, review the changes, and report evidence.

---

## 5. Initial Technical Direction

The following stack is the proposed direction. It must be reviewed and confirmed during Phase 0 before implementation begins.

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- A reusable, accessible component system
- React Router
- TanStack Query for server state
- React Hook Form and Zod where appropriate

shadcn/ui may be evaluated for reusable components. Material UI must not be introduced unless the project owner explicitly approves it.

### Backend

- Python
- Django
- Django REST Framework
- Modular monolith architecture

Do not introduce separate backend services or microservices without an approved ADR demonstrating a concrete requirement.

### Database

- PostgreSQL

Database schema, constraints, relationships, indexes, and migration strategy must be defined in the relevant specifications.

### AI

- An explicit AI provider/adapter interface.
- Local Ollama as the preferred initial development option to avoid mandatory per-request API costs.
- Validated structured output where appropriate.
- Deterministic domain rules independent of AI availability.

The project must not require AI to determine whether a payment definitely succeeded or failed when authoritative evidence is missing.

### Testing and Quality

The final testing stack must be confirmed in Phase 0. The proposed direction includes:

- pytest
- Django API and integration tests
- Frontend component tests
- TypeScript checks
- Linting and formatting
- Playwright for selected end-to-end workflows
- GitHub Actions CI

### Local Development

Docker Compose may be used to provide a reproducible development environment. Dependency versions, setup commands, and environment configuration must be documented.

Do not install every proposed package automatically. Add dependencies only when justified by the approved requirements.

Use free local tools where practical. Any service with usage limits, paid features, or required external accounts must be clearly documented. Never assume that a hosting or CI service will remain free indefinitely.

---

## 6. Repository Structure

The intended structure is:

```text
EuroPilot/
├── AGENTS.md
├── README.md
├── docs/
│   ├── PROJECT_SOURCE_OF_TRUTH.md
│   ├── PRODUCT_BRIEF.md
│   ├── REQUIREMENTS.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DOMAIN_MODEL.md
│   ├── BUSINESS_RULES.md
│   ├── DATA_MODEL.md
│   ├── API_CONTRACT.md
│   ├── SECURITY.md
│   ├── UI_UX_SPEC.md
│   ├── TEST_STRATEGY.md
│   ├── PERFORMANCE.md
│   ├── ADR/
│   ├── phases/
│   ├── features/
│   └── runbooks/
├── backend/
├── frontend/
├── tests/
├── docker-compose.yml
└── .github/
    └── workflows/
```

This is a proposed structure, not a requirement to create empty files or folders immediately.

Phase 0 must establish which directories and files are actually needed. Update this structure through an approved documentation change if necessary.

Never create implementation files simply to make the repository look complete.

---

## 7. Documentation Requirements

Documentation is part of the product and must remain consistent with the implementation.

Every independently deliverable feature MUST have its own Markdown specification under `docs/features/`.

Every development phase MUST have its own Markdown plan under `docs/phases/`.

Every significant architectural decision MUST be recorded in `docs/ADR/`.

Every feature and phase document must show its actual status.

Use these status values consistently:

- `Proposed`
- `Approved`
- `In Progress`
- `Blocked`
- `Implemented`
- `Verified`
- `Deferred`

Use `Verified` only when the applicable acceptance criteria have been tested and the evidence has been recorded.

### Required Feature Specification Template

Every feature document must contain:

1. Feature ID and title.
2. Current status.
3. Related phase and dependencies.
4. Problem statement.
5. Intended outcome.
6. Scope.
7. Explicit non-goals.
8. User roles and workflow.
9. Requirements with stable IDs.
10. Domain rules and state transitions.
11. API changes, if applicable.
12. Database changes, if applicable.
13. UI/UX changes, if applicable.
14. Security and privacy considerations.
15. Failure cases and recovery behavior.
16. Acceptance criteria.
17. Test scenarios.
18. Implementation checklist.
19. Verification commands and actual results.
20. Remaining issues and limitations.
21. Changelog.

### Required Phase Document Template

Every phase plan must contain:

1. Phase objective.
2. Phase status.
3. Required prerequisite documents.
4. Scope and non-goals.
5. Feature specification IDs.
6. Dependencies and blockers.
7. Ordered implementation tasks.
8. Acceptance criteria.
9. Required automated tests.
10. Security and regression checks.
11. Required documentation updates.
12. Exit criteria.
13. Completed work.
14. Actual commands and test outcomes.
15. Relevant commit and PR references.
16. Deferred work and unresolved risks.
17. Decision on readiness for the next phase.

### Documentation Accuracy

Do not invent requirements, customer research, provider behavior, test results, benchmarks, or security guarantees.

Clearly label proposals and assumptions as such.

When an approved requirement changes, update the source of truth and affected feature documents before or alongside the implementation.

Do not mark a phase complete merely because its files have been created.

---

## 8. Git Branch and Merge Policy

This section is mandatory.

### Main Branch

`main` is the integration branch and must remain in a working state.

Agents MUST NOT:

- Implement features directly on `main`.
- Commit directly to `main`.
- Push directly to `main`.
- Force-push to `main`.
- Delete `main`.
- Rewrite shared branch history.
- Merge unreviewed changes into `main`.

All work must enter `main` through a Pull Request.

Configure GitHub branch protection or rulesets for `main` when available. Require pull requests and passing checks where the repository settings support them.

For a solo project, the owner must still inspect the diff, specification, and test evidence before merging. A self-review must not be represented as an independent review.

### One Feature, One Branch

Every feature, bug fix, documentation task, refactor, or independently reviewable unit must have its own branch.

Examples:

```text
docs/phase-00-project-charter
docs/feature-001-domain-specification
feature/001-synthetic-provider-events
feature/002-event-idempotency
feature/003-incident-classification
feature/004-investigation-timeline
fix/005-out-of-order-event-correlation
test/006-concurrency-regression
```

These are naming examples, not pre-approved feature requirements. Use the actual feature IDs from the approved registry.

Do not implement multiple unrelated features in one branch.

If a task expands into multiple independently testable features, stop and split the work into separate tasks and branches.

Small changes may share a branch only when they are necessary parts of the same approved feature and cannot reasonably be reviewed independently.

### Mandatory Branch Workflow

For each task:

1. Read `AGENTS.md` and the relevant approved specifications.
2. Inspect the current branch, working tree, and recent Git history.
3. Identify any existing uncommitted user changes.
4. Never overwrite or discard those changes.
5. Confirm the latest `origin/main` state.
6. Update the local `main` safely before branching.
7. Create a new feature branch from the latest `main`.
8. Implement only the approved scope.
9. Add or update tests.
10. Run applicable tests, linting, type checks, and builds.
11. Review the complete diff for scope creep, secrets, accidental files, and missing tests.
12. Update the feature specification and phase document with actual progress.
13. Commit with a clear, conventional message.
14. Push the feature branch.
15. Open a Pull Request targeting `main`.
16. Include the feature ID, scope, requirements, tests, actual outcomes, risks, and documentation changes.
17. Review the diff against the acceptance criteria.
18. Resolve review comments and ensure required CI checks pass.
19. Obtain project-owner approval before merging.
20. Merge through the approved GitHub workflow.
21. Verify the resulting `main` state and update the task documentation.

If the agent cannot access GitHub or cannot perform a requested action, it must explain the limitation and give the owner the exact next step.

Never claim that a branch was pushed, a PR was opened, a test passed, or a merge completed without direct evidence.

### Parallel Agents

Multiple agents may work in parallel only on separate, clearly scoped branches with minimal file overlap.

Only one coding agent may actively modify a particular task/branch at a time.

Do not assign multiple coding agents to edit the same files independently and then blindly combine their work.

Reviewers must inspect the actual code diff and test evidence, not merely trust the implementer's summary.

---

## 9. Agent Rules: Allowed and Prohibited Actions

### Agents MUST

- Read the mandatory documents before starting.
- State the assigned task and feature ID.
- Inspect relevant existing code and tests.
- Follow the approved specification.
- Make the smallest coherent change that satisfies the requirements.
- Add tests for new and changed behavior.
- Handle failure cases explicitly.
- Update documentation with real progress.
- Preserve existing user work.
- Report changed files and exact verification commands.
- Distinguish facts, assumptions, proposals, and verified results.
- Stop and ask when a material requirement is unclear.
- Report blockers honestly.

### Agents MUST NOT

- Add unapproved features.
- Invent business rules or provider guarantees.
- Change API contracts without approval.
- Change authoritative transaction semantics without approval.
- Introduce new dependencies without a documented justification and required approval.
- Remove, skip, weaken, or delete failing tests merely to obtain a passing result.
- Suppress errors without appropriate handling.
- Hard-code secrets, tokens, passwords, private keys, or production credentials.
- Print secret values in logs or reports.
- Modify environment files or deployment secrets unless explicitly authorized.
- Refactor unrelated files.
- Make broad formatting changes unrelated to the task.
- Run destructive commands without explicit approval and an impact assessment.
- Reset a database or delete data without explicit authorization and a verified backup plan.
- Rewrite shared Git history.
- Claim successful testing or deployment without evidence.
- Start the next feature automatically after finishing the assigned task.

If a material decision is missing, provide:

- **Blocker:** What is missing or contradictory.
- **Impact:** Why it matters.
- **Options:** Reasonable alternatives.
- **Recommendation:** The preferred option and why.
- **Approval required:** The decision needed from the owner.

Wait for approval before implementing material changes to scope, security, architecture, data semantics, or public contracts.

---

## 10. Payment Domain Rules

The following principles apply throughout the project.

### Unknown Is a Valid Outcome

A timeout or missing response does not prove that a payment failed.

A network error does not prove that a payment succeeded.

If authoritative evidence is missing, the outcome must remain uncertain or require further investigation.

### Transactions and Attempts Are Different

The domain model must distinguish:

- A logical payment or transaction.
- An individual payment submission attempt.
- A provider event.
- An event-delivery occurrence, when needed.
- An invoice or payable record.
- An incident or investigation.
- Evidence used to support a finding.

The exact entities and relationships must be approved in the domain specification.

### Retries and Duplicate Events

Do not equate each retry with a separate successful payment.

Do not treat each delivered event as a new transaction.

Define event identity, idempotency keys, retry relationships, correlation logic, and conflict handling explicitly.

Never infer that two events refer to the same payment solely because their amounts and timestamps are similar.

### Provider-Specific Semantics

Do not invent a universal payment-provider status mapping.

Provider behavior must be represented in documented synthetic fixtures and adapter specifications.

Unknown event types or conflicting statuses must be handled safely and must not silently become success or failure.

### Evidence-Based Findings

Every material incident finding must be traceable to the evidence and rules supporting it.

The system should distinguish:

- Observed facts.
- Deterministic rule-based findings.
- AI-generated explanations.
- Hypotheses.
- Missing evidence.
- Unknown outcomes.

AI-generated explanations must not be presented as authoritative provider evidence.

---

## 11. Data Integrity and Reliability

The domain and data specifications must define the exact schema before implementation.

Evaluate the need for the following entities:

- Organization or workspace.
- Invoice or payable record.
- Logical payment/transaction.
- Payment attempt.
- Provider event.
- Event-delivery identity.
- Incident/investigation.
- Evidence item.
- Finding or recommendation.
- Audit record.

Do not create separate database tables automatically merely because an entity is listed here. Finalize the model through Phase 0.

The implementation and tests must address, as applicable:

- Duplicate events.
- Replayed events.
- Out-of-order events.
- Missing and malformed fields.
- Unknown event types.
- Conflicting provider states.
- Ambiguous payment outcomes.
- Retries and timeouts.
- Concurrent event ingestion.
- Database transaction boundaries.
- Unique constraints and idempotency.
- Time-zone normalization.
- Monetary precision.
- Correlation failures.
- Manual-review fallback.

Use decimal-safe representations for monetary amounts. Do not use binary floating-point for financial calculations.

Business rules must produce reproducible results for the same inputs and approved configuration.

---

## 12. Security and Privacy Requirements

Security must be designed into the architecture from Phase 0.

- Never commit real secrets.
- Provide an `.env.example` containing placeholder values only.
- Validate untrusted input at API boundaries.
- Enforce authentication and authorization on the server.
- Do not rely on frontend permissions for security.
- Define tenant isolation before enabling multi-tenant access.
- Scope database queries and object access appropriately.
- Use database constraints for critical integrity requirements.
- Use safe, consistent API error responses.
- Do not expose stack traces or internal secrets in production-facing responses.
- Use least privilege.
- Avoid logging sensitive payloads, credentials, bank details, or unnecessary personal information.
- Define timeouts and bounded retries for external dependencies.
- Use pagination and bounded filters for list endpoints.
- Consider rate limits and abuse protection before exposing endpoints publicly.
- Define data retention and deletion requirements before processing real customer information.
- Include negative security tests for unauthorized and invalid requests.
- Treat imported events, invoice descriptions, logs, and provider payloads as untrusted data.

### Prompt-Injection Safety

External content must never be treated as trusted instructions for the AI model.

Invoice descriptions, event metadata, imported notes, and log messages must not be allowed to override system instructions or authorize tool use.

AI must not gain unrestricted access to the database, shell, payment systems, or privileged APIs.

Any future tool access requires explicit scope, authorization, input validation, auditability, and separate approval.

### AI Privacy

Send only the minimum required, appropriately sanitized evidence to an AI provider.

Do not send sensitive data to an external AI service without explicit approval and a documented privacy/security decision.

Local Ollama is the preferred initial option, but local inference does not remove the need for input validation, access controls, or output validation.

---

## 13. AI Responsibilities and Limits

AI is an advisory investigation assistant, not the authority for payment state.

AI may:

- Summarize supplied evidence.
- Explain deterministic rule results.
- Identify missing evidence.
- Suggest investigation questions.
- Generate structured, validated incident summaries.

AI must not:

- Invent events or provider responses.
- Fabricate timestamps or transaction identifiers.
- Declare an outcome that the evidence does not establish.
- Override deterministic domain rules.
- Initiate, approve, cancel, reverse, or refund payments.
- Change authoritative payment state directly.
- Make unrestricted database or external API calls.

Validate structured AI output against an explicit schema.

Treat model output as untrusted until validated.

If the AI provider is unavailable, slow, or returns invalid output, the core deterministic investigation flow must remain functional.

Show an appropriate fallback or error state. Do not convert AI failure into payment success or failure.

Where useful, record the model/provider and relevant prompt or schema version without storing secrets or unnecessary sensitive information.

---

## 14. API and Backend Engineering Rules

- Keep API handlers focused on authentication, authorization, validation, orchestration, and response mapping.
- Keep domain logic in testable services or domain modules.
- Use explicit request and response schemas.
- Define stable response and error formats.
- Validate pagination and filtering inputs.
- Avoid N+1 queries.
- Use database transactions where integrity requires them.
- Define idempotency behavior explicitly.
- Protect object-level access.
- Keep external calls behind explicit adapters.
- Set reasonable timeouts and bounded retries.
- Do not expose internal stack traces to clients.
- Do not return fields that a user is not authorized to access.
- Document endpoints and their behavior in `docs/API_CONTRACT.md`.
- Update API tests whenever the contract changes.
- Obtain approval before changing public API contracts.

Do not add caching, message brokers, microservices, or distributed coordination layers without an approved need.

---

## 15. Frontend and UI/UX Rules

EuroPilot should feel like a polished, trustworthy fintech operations product, not a generic admin template.

### Visual Direction

- Prefer a modern navy/dark visual direction.
- Use restrained, purposeful semantic colors.
- Do not use Material UI unless explicitly approved.
- Do not use green as the default theme.
- Use success green only when it communicates a meaningful success state.
- Define reusable design tokens for color, spacing, typography, radius, and focus states.
- Keep typography and spacing consistent.
- Build reusable components rather than duplicating UI patterns.

### Usability

The application must provide appropriate states for:

- Loading.
- Empty data.
- API errors.
- Partial data.
- Unknown or uncertain payment outcomes.
- Missing evidence.
- Successful data retrieval.
- Retryable failures.

An uncertain payment outcome must never look identical to confirmed success or confirmed failure.

Investigation timelines should show relevant event timestamps, sources, event types, correlation status, and available evidence.

Filters, sorting, pagination, and search must behave predictably.

Avoid rendering thousands of rows at once. Use server-side pagination or a justified virtualization approach.

### Accessibility

- Use semantic HTML.
- Support keyboard navigation.
- Provide visible focus states.
- Associate inputs with labels.
- Maintain appropriate contrast.
- Do not rely on color alone to communicate status.
- Provide accessible names and status announcements where needed.

### Performance

Avoid unnecessary re-renders, repeated network requests, blocking UI work, and excessive animations.

Use loading and error states instead of leaving the interface unresponsive.

UI acceptance criteria must be verifiable. “Looks good” alone is not an acceptance criterion.

---

## 16. Testing Requirements

Every feature must have tests appropriate to its risk and behavior.

### Unit Tests

Test domain rules, state transitions, validation, correlation, and monetary calculations.

### Integration Tests

Test database integrity, constraints, transactions, and relevant adapters.

### API Tests

Test authentication, authorization, input validation, error responses, pagination, and contract behavior.

### Frontend Tests

Test important components, forms, filters, loading/error states, and accessibility-critical behavior.

### End-to-End Tests

Test essential operator journeys across the frontend and backend where practical.

### Security Tests

Test unauthorized access, cross-tenant access where tenancy exists, invalid payloads, injection attempts, and permission boundaries.

### Regression Tests

When a defect is fixed, add a reproducible regression test where practical.

### Performance Tests

Use a defined dataset, documented environment, repeatable command, and recorded result. Do not claim performance based on intuition.

### Test Integrity

Never delete, skip, or weaken a failing test just to obtain a passing suite.

If a test is genuinely obsolete, document why, replace its coverage where necessary, and obtain approval for the change.

Do not mock away the exact behavior a test is intended to verify.

Do not claim all tests passed if some checks were not run.

Use this reporting format:

```text
Command: <exact command>
Result: PASS | FAIL | BLOCKED | NOT RUN
Evidence: <actual output summary>
Reason: <required for FAIL, BLOCKED, or NOT RUN>
```

Exact commands must be documented in `README.md` and `docs/TEST_STRATEGY.md` once Phase 0 confirms the toolchain.

---

## 17. Performance and Maintainability

- Define measurable performance targets in `docs/PERFORMANCE.md`.
- Treat targets as goals tied to a defined test environment, not universal guarantees.
- Measure before optimizing.
- Avoid N+1 database queries.
- Use indexes based on query patterns and measured need.
- Keep list endpoints bounded and paginated.
- Keep slow AI calls out of request-critical paths when appropriate.
- Add background processing only when requirements justify it.
- Use bounded concurrency and timeouts for expensive operations.
- Prefer a modular monolith until there is evidence for a more complex architecture.
- Keep code cohesive, readable, and testable.
- Avoid abstractions without a clear use case.
- Document non-obvious technical decisions.
- Prioritize correctness, maintainability, and reliability over cleverness.

---

## 18. Development Phases

The following is the intended sequence. Detailed plans and acceptance criteria must be documented during Phase 0.

### Phase 0 — Foundation and Specifications

Goals:

- Define the product problem, intended users, terminology, and MVP scope.
- Separate facts from assumptions and unvalidated market hypotheses.
- Define domain entities, payment states, event semantics, correlation rules, and incident classification.
- Approve the architecture and dependency choices.
- Define the security and threat model.
- Define API, data, UI/UX, test, and performance specifications.
- Establish the feature registry and branch workflow.
- Create the documentation structure and local setup instructions.

**No feature implementation during this phase unless explicitly approved as necessary for the foundation.**

Exit criteria:

- The owner has reviewed and approved the core specifications.
- High-impact domain, security, and architecture ambiguities have been resolved.
- The Phase 1 scope and acceptance criteria are documented.
- The required documentation is consistent and reviewed.

### Phase 1 — Deterministic Domain Engine

Potential scope, subject to approved specifications:

- Domain models.
- Synthetic provider fixtures.
- Event ingestion.
- Event identity and idempotency.
- Attempt and transaction correlation.
- Deterministic incident classification.
- Evidence generation.
- Tests for retries, duplicate delivery, timeouts, conflicting states, out-of-order events, and concurrency.

Exit criteria:

- Approved domain behavior is implemented.
- Required tests pass.
- Behavior and limitations are documented.
- The phase is reviewed before progression.

### Phase 2 — API and Persistence

Potential scope:

- Approved database schema and migrations.
- API endpoints.
- Input validation.
- Authorization and permissions.
- Pagination and filtering.
- Safe errors.
- API contract and integration tests.

Exit criteria:

- API contracts are documented.
- Required security and integrity tests pass.
- The feature branches have passed review.

### Phase 3 — Frontend and Operator Workflow

Potential scope:

- Reusable design system.
- Incident list and detail pages.
- Investigation timeline.
- Evidence display.
- Filters and pagination.
- Loading, empty, error, and uncertain-outcome states.
- Responsive and accessible layouts.

Exit criteria:

- Required operator journeys work.
- UI acceptance criteria and applicable automated tests pass.
- The UI is consistent with `docs/UI_UX_SPEC.md`.

### Phase 4 — AI-Assisted Investigation

Potential scope:

- AI provider abstraction.
- Local model integration where practical.
- Structured summaries and findings.
- Evidence references.
- Missing-evidence explanations.
- Uncertainty handling.
- Safe fallback behavior.

Exit criteria:

- AI output is validated.
- AI cannot override authoritative business rules.
- Core investigation works without AI.
- Relevant failure and security tests pass.

### Phase 5 — Hardening and Delivery

Potential scope:

- Security review.
- Authorization and data-isolation review.
- Concurrency and regression testing.
- Accessibility review.
- Performance measurements.
- Operational documentation.
- Deployment and configuration review.

Exit criteria:

- Required acceptance criteria and release checks have evidence.
- Known limitations and operational risks are documented.
- The owner explicitly approves release readiness.

A phase is not complete merely because its code exists. It must satisfy its documented exit criteria.

---

## 19. Definition of Done

A task may be marked complete only when all applicable conditions are satisfied:

- [ ] An approved feature specification exists.
- [ ] Acceptance criteria are clear and testable.
- [ ] The change stays within the assigned branch and scope.
- [ ] Business logic follows the approved specification.
- [ ] Relevant automated tests have been added or updated.
- [ ] Applicable tests, lint, type checks, and builds have actually run.
- [ ] Failures and unrun checks are reported honestly.
- [ ] No secrets or unrelated changes are included.
- [ ] Documentation reflects the actual implementation.
- [ ] The diff has been reviewed against the specification.
- [ ] Remaining limitations and blockers are documented.
- [ ] The PR targets `main`.
- [ ] Required CI checks pass.
- [ ] Project-owner approval is recorded.
- [ ] The merge and resulting branch state are verified before the task is marked merged.

---

## 20. Mandatory Task Handoff Report

At the end of every assigned task, the agent must report:

1. Task ID and title.
2. Branch name and target branch.
3. Summary of the changes.
4. Files created, changed, or deleted.
5. Requirements and acceptance criteria addressed.
6. Exact test and check commands.
7. Actual PASS, FAIL, BLOCKED, or NOT RUN results.
8. Security and regression checks performed.
9. Documentation updated.
10. Known limitations and unresolved issues.
11. Commit SHA, push status, PR status, and merge status when verified.
12. The next recommended action or required owner decision.

The agent must not begin the next feature automatically. Wait for the next approved task or explicit owner instruction.

---

## 21. First Task After Adding AGENTS.md

The first task is **documentation-only Phase 0 setup**.

Create a branch from the latest `main`, for example:

`docs/phase-00-project-charter`

Then create and review the Phase 0 documentation set.

At minimum, the Phase 0 task must establish:

- `docs/PROJECT_SOURCE_OF_TRUTH.md`
- `docs/PRODUCT_BRIEF.md`
- `docs/REQUIREMENTS.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DOMAIN_MODEL.md`
- `docs/BUSINESS_RULES.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
- `docs/SECURITY.md`
- `docs/UI_UX_SPEC.md`
- `docs/TEST_STRATEGY.md`
- `docs/PERFORMANCE.md`
- `docs/phases/PHASE_00_FOUNDATION.md`
- `docs/features/FEATURE_REGISTRY.md`
- Any necessary ADRs under `docs/ADR/`
- A concise `README.md` documenting the project and linking to the approved source of truth

The exact contents and dependencies of these files must be consistent.

Clearly label unvalidated assumptions. Do not fabricate customer interviews, competitor research, provider guarantees, benchmarks, or completed test results.

Do not implement Phase 1 until the owner has reviewed and approved the Phase 0 documentation.

---

## 22. Owner Approval Required for Material Decisions

The project owner controls product scope, priorities, and material trade-offs.

Agents may recommend decisions but must not silently make high-impact decisions on the owner's behalf.

Approval is required before changing:

- MVP boundaries or financial-action capabilities.
- Transaction semantics, domain states, or correlation rules.
- Authentication, tenancy, privacy, data retention, or security posture.
- Public API contracts.
- Persisted data semantics or destructive migrations.
- Major dependencies or architecture boundaries.
- Phase exit criteria.
- Acceptance requirements.
- The policy for connecting real payment providers or external AI services.

Low-risk implementation details may be selected by the agent when consistent with approved specifications. Document the choice if it affects future behavior or maintainability.

---

## 23. Final Rule

**Read the source of truth first. Read the assigned feature specification next. Implement only what is approved. Test what changed. Document what happened. Use a separate branch. Open a PR to `main`. Merge only after review and owner approval. Never invent evidence or claim unverified success.**

These rules apply to every phase and every feature in EuroPilot.
