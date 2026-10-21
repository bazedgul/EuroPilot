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
export type ProviderEvent = { provider: string; id: string; event_type: string; event_time: string; received_time: string };
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
