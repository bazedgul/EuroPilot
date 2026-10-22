# Domain Model

Status: Proposed; Phase 2 lifecycle decisions are approved planning scope, but implementation has not started.

## Concepts

An invoice/payable is an obligation record. A logical payment/transaction represents intended settlement. A payment attempt is one submission or retry. A provider event is an observed provider message. An event-delivery occurrence records delivery identity when duplicate delivery must be distinguished from event identity. An incident/investigation groups uncertainty or conflict. Evidence records observed facts and provenance. A finding records a deterministic result or advisory explanation.

A reconciliation case is the analyst workflow around one investigation. Its lifecycle is separate from the payment outcome. A case note is bounded untrusted text. An audit event records a material case action and synthetic local actor. An idempotency record stores a normalized request fingerprint and original response for safe replay.

## Existing and approved Phase 2 rules

- A timeout or network error does not establish success or failure.
- A retry is not automatically a new logical payment.
- Duplicate delivery is not automatically a new event or transaction.
- Amount/time similarity alone cannot correlate records.
- Unknown event types and conflicting statuses remain explicit and safe.
- Case states are `open`, `under_review`, `resolved`, and `deferred`.
- Approved transitions are `open → under_review|deferred`, `under_review → resolved|deferred`, and `deferred → open|under_review`; `resolved` is terminal for this phase.
- `resolved` and `deferred` require trimmed, non-empty reasons of no more than 500 characters.
- Notes require trimmed, non-empty text of no more than 2,000 characters and are rendered as untrusted text.
- The server assigns `synthetic_local_operator` to every note and audit event; clients cannot override it.
- Request IDs are mandatory, trimmed, non-empty, at most 128 characters, and unique within `(case_id, action, request_id)`; invalid values are rejected without truncation.
- Fingerprints use normalized transition target/reason or normalized note text. Same-key/same-fingerprint requests replay the original result; differing fingerprints return conflict.
- Successful case actions and their corresponding audit events commit atomically. Rejected or failed operations leave no partial state or audit history.
- Case state cannot alter the deterministic payment outcome. Findings remain derived from Phase 1 evidence.

## Remaining open questions

The synthetic actor’s internal storage type and future retention/deletion policy remain implementation details or deferred decisions. The synthetic actor is not an authenticated human identity, and production authorization, tenancy, and audit immutability are out of scope.
