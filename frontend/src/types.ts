export type Outcome = "confirmed_success" | "confirmed_failure" | "unknown" | "conflict";

export type Evidence = {
  id: string;
  payment_id: string;
  source: string;
  reference: string;
  event_time: string;
  received_time: string;
  event_type: string;
  provider: string;
  authoritative: boolean;
};

export type Attempt = { id: string; request_id: string; requested_time: string; outcome: Outcome; retry_of: string | null };
export type ProviderEvent = { provider: string; id: string; event_type: string; event_time: string; received_time: string | null };
export type Delivery = { id: string; provider: string; event_id: string; received_time: string };

export type Investigation = {
  id: string;
  payment: { id: string; invoice_id: string };
  outcome: Outcome;
  finding: { outcome: Outcome; missing_evidence: string[] };
  missing_evidence: string[];
  attempts: Attempt[];
  events: ProviderEvent[];
  deliveries: Delivery[];
  evidence: Evidence[];
  supporting_evidence: Evidence[];
};

export type InvestigationPage = { count: number; page: number; page_size: number; results: Investigation[] };
export type Health = { status: string; service: string; data_mode: string };

export type CaseState = "open" | "under_review" | "resolved" | "deferred";
export type CaseSummary = { id: string; investigation_id: string; payment_id: string; state: CaseState; payment_outcome: Outcome; updated_at: string };
export type CasePage = { count: number; page: number; page_size: number; results: CaseSummary[] };
export type CaseNote = { id: string; case_id?: string; text: string; actor: string; created_at: string };
export type AuditEvent = { id: string; action: "case_transitioned" | "note_created"; actor: string; created_at: string; previous_state: CaseState | null; new_state: CaseState | null; reason: string | null; note_id: string | null; request_id: string };
export type CaseDetail = CaseSummary & { resolution_reason: string | null; notes: CaseNote[]; audit_events: AuditEvent[] };
export type TransitionResponse = { case: { id: string; state: CaseState; resolution_reason: string | null; payment_outcome: Outcome }; audit_event: AuditEvent };
export type NoteResponse = { note: CaseNote & { case_id: string }; audit_event: AuditEvent };
