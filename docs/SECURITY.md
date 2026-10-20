# Security and Privacy

Status: Proposed baseline; no audit performed.

Use server-side authentication and authorization, tenant/object isolation where applicable, input/schema validation, safe errors, least privilege, bounded pagination/filtering, timeouts and bounded retries, and database constraints. Treat imported events, invoice text, notes, and logs as untrusted data. Do not log secrets or unnecessary sensitive payloads.

AI must receive minimum necessary sanitized evidence. External content must not become instructions. AI has no unrestricted database, shell, payment, or privileged API access; output is untrusted until validated.

Open approvals: threat model, tenancy, retention/deletion, classification of sensitive data, audit requirements, deployment controls, and security test scope. No secrets or real customer data are introduced here.
