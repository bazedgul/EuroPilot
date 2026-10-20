# EuroPilot Agent Instructions

## Status

This file contains repository workflow and agent rules. Product scope and terminology are defined in [`docs/PROJECT_SOURCE_OF_TRUTH.md`](docs/PROJECT_SOURCE_OF_TRUTH.md).

## Required workflow

1. Read this file, the source of truth, the applicable phase, feature specification, ADRs, and related requirements before changing behavior.
2. Inspect the working tree and preserve user changes. Never reset, discard, overwrite, or force-push shared history.
3. Work on a dedicated branch from the latest `main`; never commit or push directly to `main`.
4. Implement only approved scope. Do not invent evidence, requirements, provider guarantees, benchmarks, approvals, or test results.
5. Add appropriate tests for implementation work, review the complete diff, and report exact commands and outcomes.
6. Open a PR to `main` when GitHub access is available. Do not merge without owner approval.

## Documentation rules

- Use stable IDs such as `REQ-001`, `DOM-001`, `SEC-001`, `API-001`, and `AC-001`.
- Distinguish `Verified fact`, `Approved decision`, `Proposed design`, `Unvalidated assumption`, `Open question`, and `Deferred work`.
- A feature registry is only an index; every implemented feature needs its own specification.
- Do not mark documentation-only work, requirements, or features implemented or verified without evidence.
- Material scope, domain, security, architecture, data, API, or phase decisions require owner approval.

## Security and testing

- Never commit secrets, credentials, tokens, private keys, real payment credentials, or unnecessary sensitive payloads.
- Validate untrusted input at server boundaries, enforce authorization server-side, avoid sensitive logging, and treat imported content as untrusted.
- New implementation behavior requires appropriate unit, integration, API, frontend, security, regression, and end-to-end tests as applicable.
- Do not delete, weaken, skip, or hide failing tests to obtain a passing result. Report unrun checks as `NOT RUN`.

## Scope and AI safety

- Do not add application features, dependencies, infrastructure, provider integrations, or external AI services without approved scope and documentation.
- AI is advisory and must not invent evidence, override deterministic rules, declare uncertain payments successful or failed, or initiate, approve, cancel, reverse, or refund payments.
- The initial MVP uses synthetic data and simulated provider events and must not move money or execute real payments. See the source of truth for the authoritative product definition.

## Branch and review workflow

- Read this file, the source of truth, the relevant phase and feature documents, ADRs, and related specifications before implementation.
- Inspect status, branch, remotes, and recent history before editing; preserve all existing user work.
- Work on a dedicated branch from the latest `main`. Never commit or push directly to `main`, force-push, rewrite shared history, or merge without owner approval.
- Review the complete tracked and untracked diff for scope, secrets, accidental deletions, and documentation consistency before commit or PR.
- Use exact command output when reporting tests, validation, commits, pushes, PRs, or merges. Never claim an operation succeeded without evidence.

## Product safety boundaries

The initial MVP uses synthetic data and simulated provider events. It is read-only: it must not execute payments, move money, approve financial transactions, or claim to cancel or reverse submitted payments. Unknown outcomes remain unknown when authoritative evidence is missing. AI is advisory, evidence-bound, validated, and cannot override deterministic rules.

## Reporting

Every handoff must list changed files, requirements and acceptance criteria, exact checks, actual outcomes, security/regression checks, limitations, branch/commit/push/PR status, and the next owner decision. Do not start the next phase automatically.
