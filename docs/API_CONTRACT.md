# API Contract

Status: Proposed outline; no endpoints implemented.

The future API should expose read-only investigation and evidence views plus approved synthetic-event ingestion. It must define authentication, authorization, versioning, pagination, bounded filters, idempotency, stable success/error envelopes, validation, and object-level access before implementation.

No public path, field, status, or provider contract is approved. Proposed future resource areas: investigations, payments/attempts, evidence, findings, and synthetic events. AI explanation requests must be explicitly advisory and must return provenance/validation status.

Owner approval is required for endpoint names, schemas, authentication, tenancy, and mutation semantics.
