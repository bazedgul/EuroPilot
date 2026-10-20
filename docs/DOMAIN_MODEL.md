# Domain Model

Status: Proposed; high-impact semantics require owner approval.

## Concepts

An invoice/payable is an obligation record. A logical payment/transaction represents intended settlement. A payment attempt is one submission or retry. A provider event is an observed provider message. An event-delivery occurrence records delivery identity when duplicate delivery must be distinguished from event identity. An incident/investigation groups uncertainty or conflict. Evidence records observed facts and provenance. A finding records a deterministic result or advisory explanation. An audit record records material access or change.

## Rules needing approval

- A timeout or network error does not establish success or failure.
- A retry is not automatically a new logical payment.
- Duplicate delivery is not automatically a new event or transaction.
- Amount/time similarity alone cannot correlate records.
- Unknown event types and conflicting statuses must remain explicit and safe.

## Open questions

Approve identifiers, lifecycle states, correlation precedence, conflict resolution, and whether organizations/workspaces are in MVP. These determine schema constraints and API behavior.
