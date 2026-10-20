# Data Model

Status: Proposed conceptual model; schema and migrations are deferred.

Candidate records are: workspace/organization, invoice/payable, logical payment, payment attempt, provider event, event delivery, incident/investigation, evidence item, finding, and audit record. Relationships and constraints must be approved before implementation.

Required integrity considerations include idempotency keys, provider/event identity, decimal monetary fields, UTC timestamps, uniqueness, foreign keys, transaction boundaries, conflict representation, and bounded indexes based on measured queries.

Open questions: tenancy, retention/deletion, payload storage/redaction, event versioning, and audit immutability. No database has been created.
