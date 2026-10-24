import { FormEvent, useEffect, useRef, useState } from "react";
import { ApiError, createCaseNote, getCase, getHealth, getInvestigation, listCases, transitionCase } from "./api";
import type { CaseDetail, CasePage, CaseState, Health, Investigation, InvestigationPage, Outcome } from "./types";

const outcomeLabels: Record<Outcome, string> = {
  confirmed_success: "Confirmed success",
  confirmed_failure: "Confirmed failure",
  unknown: "Unknown outcome",
  conflict: "Conflicting evidence",
};
const outcomeMarks: Record<Outcome, string> = { confirmed_success: "OK", confirmed_failure: "X", unknown: "?", conflict: "!" };

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  return <span className={`outcome outcome-${outcome}`}><span aria-hidden="true">{outcomeMarks[outcome]}</span>{outcomeLabels[outcome]}</span>;
}

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function formatOptionalTime(value: string | null) {
  return value ? formatTime(value) : "Receipt time unknown";
}

function requestId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `request-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return <div className="state error-state" role="alert"><strong>Unable to load this view.</strong><span>{message}</span><button onClick={retry}>Retry</button></div>;
}

export function HealthBanner({ health, error }: { health: Health | null; error?: string | null }) {
  if (error) return <div className="health-banner health-error" role="alert"><strong>API unavailable</strong><span>{error}</span></div>;
  if (!health) return null;
  return <div className="health-banner"><span className="health-dot" aria-hidden="true" /> Service {health.status} - Data mode: <strong>{health.data_mode}</strong><span>Local SQLite synthetic data; not production persistence.</span></div>;
}

function InvestigationList({ page, onSelect, onPage, retry }: { page: InvestigationPage | null; onSelect: (id: string) => void; onPage: (page: number) => void; retry: () => void }) {
  if (!page) return <div className="state"><span className="spinner" aria-hidden="true" /> Loading investigations…</div>;
  if (page.results.length === 0) return <div className="state"><strong>No investigations found.</strong><span>The synthetic API returned an empty page.</span><button onClick={retry}>Retry</button></div>;
  const hasNext = page.page * page.page_size < page.count;
  return <>
    <div className="investigation-grid">{page.results.map((item) => <button className="investigation-card" key={item.id} onClick={() => onSelect(item.id)}>
      <span className="card-kicker">{item.id}</span><OutcomeBadge outcome={item.outcome} />
      <h2>{item.payment.id}</h2><p>Invoice / payable: {item.payment.invoice_id}</p>
      <span className="card-summary">{item.finding.missing_evidence[0] ?? "Finding supported by available evidence."}</span>
      <span className="card-link">Open investigation -&gt;</span>
    </button>)}</div>
    <div className="pagination"><span>Showing page {page.page} · {page.count} total</span><div><button disabled={page.page <= 1} onClick={() => onPage(page.page - 1)}>Previous</button><button disabled={!hasNext} onClick={() => onPage(page.page + 1)}>Next</button></div></div>
  </>;
}

export function InvestigationDetail({ item, onBack, embedded = false }: { item: Investigation; onBack: () => void; embedded?: boolean }) {
  return <div className={embedded ? "investigation-embedded" : "detail-view"}>{!embedded && <button className="back-button" onClick={onBack}>&lt;- Back to investigations</button>}
    {!embedded && <div className="detail-heading"><div><span className="card-kicker">Investigation {item.id}</span><h1>{item.payment.id}</h1><p>Invoice / payable: {item.payment.invoice_id}</p></div><OutcomeBadge outcome={item.outcome} /></div>}
    <section className="panel finding-panel"><div><span className="section-label">Deterministic finding</span><h2><OutcomeBadge outcome={item.finding.outcome} /></h2></div><div><span className="section-label">Missing evidence</span>{item.finding.missing_evidence.length ? <ul>{item.finding.missing_evidence.map((reason) => <li key={reason}>{reason}</li>)}</ul> : <p>No missing evidence recorded.</p>}</div></section>
    <section className="panel"><span className="section-label">Payment attempts</span><div className="attempt-list">{item.attempts.length ? item.attempts.map((attempt) => <div className="attempt" key={attempt.id}><div className="attempt-main"><span className="field-label">Attempt ID</span><strong className="field-value">{attempt.id}</strong></div><div className="attempt-main"><span className="field-label">Outcome</span><span className="attempt-outcome field-value">{attempt.outcome}</span></div><div className="attempt-meta"><div className="meta-pair"><span className="field-label">Request ID</span><span className="field-value">{attempt.request_id}</span></div><div className="meta-pair"><span className="field-label">Requested time</span><time className="field-value">{formatTime(attempt.requested_time)}</time></div><div className="meta-pair retry-note"><span className="field-label">Relationship</span><span className="field-value">{attempt.retry_of ? `Retry of ${attempt.retry_of}` : "Initial attempt"}</span></div></div></div>) : <p>No attempt data returned.</p>}</div></section>
    <section className="panel"><span className="section-label">Evidence timeline</span><div className="evidence-list">{item.evidence.length ? item.evidence.map((evidence) => <article className="evidence" key={evidence.id}><div className="evidence-title"><div><span className="field-label">Event type</span><strong>{evidence.event_type}</strong></div><span className={evidence.authoritative ? "authority authority-yes" : "authority authority-no"}>{evidence.authoritative ? "Authoritative" : "Non-authoritative"}</span></div><div className="evidence-context"><div><span className="field-label">Source</span><span>{evidence.source}</span></div><div><span className="field-label">Provider</span><span>{evidence.provider ?? "Not specified"}</span></div><div><span className="field-label">Event reference</span><span>{evidence.reference}</span></div></div><dl><div><dt>Provider event time</dt><dd>{formatTime(evidence.event_time)}</dd></div><div><dt>Received time</dt><dd>{formatTime(evidence.received_time)}</dd></div></dl></article>) : <p>No evidence returned.</p>}</div></section>
    <section className="panel"><span className="section-label">Provider events</span><div className="delivery-list">{item.events.length ? item.events.map((event) => <div className="delivery" key={`${event.provider}-${event.id}`}><div><span className="field-label">Event ID</span><strong>{event.id}</strong></div><div><span className="field-label">Type / provider</span><span>{event.event_type} / {event.provider}</span></div><div><span className="field-label">Event and received time</span><time>{formatTime(event.event_time)} / {formatOptionalTime(event.received_time)}</time></div></div>) : <p>No provider events returned.</p>}</div></section>
    <section className="panel"><span className="section-label">Delivery occurrences</span><div className="delivery-list">{item.deliveries.length ? item.deliveries.map((delivery) => <div className="delivery" key={delivery.id}><div><span className="field-label">Delivery ID</span><strong>{delivery.id}</strong></div><div><span className="field-label">Provider event</span><span>{delivery.provider} / {delivery.event_id}</span></div><div><span className="field-label">Received time</span><time>{formatTime(delivery.received_time)}</time></div></div>) : <p>No delivery data returned.</p>}</div></section>
  </div>;
}

const allowedTransitions: Record<CaseState, CaseState[]> = {
  open: ["under_review", "deferred"],
  under_review: ["resolved", "deferred"],
  deferred: ["open", "under_review"],
  resolved: [],
};

const stateLabels: Record<CaseState, string> = { open: "Open", under_review: "Under review", resolved: "Resolved", deferred: "Deferred" };

function caseError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 503 || error.status === 0) return "The operation may still be processing. Retry with the same request when ready.";
    return error.message;
  }
  return "Unexpected API error.";
}

export function CaseList({ page, onSelect, onPage, retry }: { page: CasePage | null; onSelect: (id: string) => void; onPage: (page: number) => void; retry: () => void }) {
  if (!page) return <div className="state"><span className="spinner" aria-hidden="true" /> Loading cases...</div>;
  if (!page.results.length) return <div className="state"><strong>No cases found.</strong><span>Run the approved case backfill before investigating a payment incident.</span><button onClick={retry}>Retry</button></div>;
  const hasNext = page.page * page.page_size < page.count;
  return <>
    <div className="investigation-grid">{page.results.map((item) => <button className="investigation-card" key={item.id} onClick={() => onSelect(item.id)}>
      <span className="card-kicker">{item.id}</span><span className={`outcome outcome-${item.state}`}><span aria-hidden="true">●</span>{stateLabels[item.state]}</span>
      <h2>{item.payment_id}</h2><p>Investigation: {item.investigation_id}</p><span className="card-summary">Payment outcome: {item.payment_outcome.replace(/_/g, " ")}</span><span className="card-link">Open case -&gt;</span>
    </button>)}</div>
    <div className="pagination"><span>Showing page {page.page} · {page.count} total</span><div><button disabled={page.page <= 1} onClick={() => onPage(page.page - 1)}>Previous</button><button disabled={!hasNext} onClick={() => onPage(page.page + 1)}>Next</button></div></div>
  </>;
}

export function CaseDetailView({ item, onBack, onRefresh }: { item: CaseDetail; onBack: () => void; onRefresh: () => Promise<void> }) {
  const [target, setTarget] = useState<CaseState | "">("");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [retry, setRetry] = useState<(() => Promise<void>) | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [investigationLoading, setInvestigationLoading] = useState(true);
  const [investigationError, setInvestigationError] = useState<string | null>(null);
  const [investigationRetryable, setInvestigationRetryable] = useState(false);
  const investigationRequest = useRef(0);
  const reasonRequired = target === "resolved" || target === "deferred";
  const transitions = allowedTransitions[item.state];

  useEffect(() => {
    const request = ++investigationRequest.current;
    setInvestigation(null);
    setInvestigationError(null);
    setInvestigationRetryable(false);
    setInvestigationLoading(true);
    if (typeof item.investigation_id !== "string" || !item.investigation_id.trim()) {
      setInvestigationError("The case does not identify a valid investigation.");
      setInvestigationLoading(false);
      return;
    }
    void getInvestigation(item.investigation_id).then((result) => {
      if (request !== investigationRequest.current) return;
      if (result.id !== item.investigation_id || result.payment.id !== item.payment_id) {
        setInvestigationError("The case investigation relationship could not be validated.");
        return;
      }
      setInvestigation(result);
    }).catch((err) => {
      if (request === investigationRequest.current) {
        setInvestigationError(caseError(err));
        setInvestigationRetryable(err instanceof ApiError && (err.status === 0 || err.status === 503));
      }
    }).finally(() => {
      if (request === investigationRequest.current) setInvestigationLoading(false);
    });
  }, [item.id, item.investigation_id, item.payment_id]);

  const retryInvestigation = () => {
    setInvestigationError(null);
    setInvestigationRetryable(false);
    setInvestigationLoading(true);
    const request = ++investigationRequest.current;
    if (typeof item.investigation_id !== "string" || !item.investigation_id.trim()) {
      setInvestigationError("The case does not identify a valid investigation.");
      setInvestigationLoading(false);
      return;
    }
    void getInvestigation(item.investigation_id).then((result) => {
      if (request !== investigationRequest.current) return;
      if (result.id !== item.investigation_id || result.payment.id !== item.payment_id) {
        setInvestigationError("The case investigation relationship could not be validated.");
        return;
      }
      setInvestigation(result);
    }).catch((err) => {
      if (request === investigationRequest.current) {
        setInvestigationError(caseError(err));
        setInvestigationRetryable(err instanceof ApiError && (err.status === 0 || err.status === 503));
      }
    }).finally(() => {
      if (request === investigationRequest.current) setInvestigationLoading(false);
    });
  };

  const runMutation = async (action: () => Promise<void>, retryable: boolean) => {
    setPending(true); setError(null); setRetry(null);
    try { await action(); await onRefresh(); } catch (err) { setError(caseError(err)); if (retryable && err instanceof ApiError && (err.status === 0 || err.status === 503)) setRetry(() => action); } finally { setPending(false); }
  };
  const submitTransition = (event: FormEvent) => {
    event.preventDefault();
    if (!target) return;
    const id = requestId();
    const normalizedReason = reason.trim() || null;
    void runMutation(() => transitionCase(item.id, id, target, normalizedReason).then(() => undefined), true);
  };
  const submitNote = (event: FormEvent) => {
    event.preventDefault();
    const id = requestId();
    const normalizedNote = note.trim();
    void runMutation(() => createCaseNote(item.id, id, normalizedNote).then(() => undefined), true);
  };
  const retryMutation = () => { if (retry) void runMutation(retry, true); };

  return <div className="detail-view"><button className="back-button" onClick={onBack}>&lt;- Back to cases</button>
    <div className="detail-heading"><div><span className="card-kicker">Case {item.id}</span><h1>{item.payment_id}</h1><p>Investigation: {item.investigation_id}</p></div><span className={`outcome outcome-${item.state}`}>{stateLabels[item.state]}</span></div>
    {error && <div className="state error-state" role="alert"><strong>Unable to complete this case action.</strong><span>{error}</span>{retry && <button onClick={retryMutation} disabled={pending}>Retry same request</button>}</div>}
    <section className="panel finding-panel"><div><span className="section-label">Payment outcome</span><h2><OutcomeBadge outcome={item.payment_outcome} /></h2></div><div><span className="section-label">Resolution reason</span><p>{item.resolution_reason ?? "No resolution reason recorded."}</p></div></section>
    <section className="panel" aria-live="polite"><span className="section-label">Investigation evidence</span>{investigationLoading && <div className="state"><span className="spinner" aria-hidden="true" /> Loading investigation evidence...</div>}{!investigationLoading && investigationError && <div className="state error-state" role="alert"><strong>Unable to load investigation evidence.</strong><span>{investigationError}</span>{investigationRetryable && <button onClick={retryInvestigation}>Retry</button>}</div>}{!investigationLoading && !investigationError && investigation && <InvestigationDetail item={investigation} onBack={() => undefined} embedded />}</section>
    <section className="panel"><span className="section-label">Update case state</span>{transitions.length ? <form className="case-workflow-form" onSubmit={submitTransition}><label htmlFor="case-target">New state</label><select id="case-target" value={target} onChange={(event) => setTarget(event.target.value as CaseState)} disabled={pending}><option value="">Select a state</option>{transitions.map((state) => <option key={state} value={state}>{stateLabels[state]}</option>)}</select><label htmlFor="case-reason">Reason {reasonRequired ? "(required)" : "(optional)"}</label><textarea id="case-reason" value={reason} onChange={(event) => setReason(event.target.value)} maxLength={500} aria-describedby="case-reason-count" disabled={pending} /><span className="character-counter" id="case-reason-count">{reason.length}/500</span><button type="submit" disabled={pending || !target || (reasonRequired && !reason.trim())}>{pending ? "Saving..." : "Save state"}</button></form> : <p>This case is resolved and has no further state transitions in this phase.</p>}</section>
    <section className="panel"><span className="section-label">Add analyst note</span><form className="case-workflow-form" onSubmit={submitNote}><label htmlFor="case-note">Note</label><textarea id="case-note" value={note} onChange={(event) => setNote(event.target.value)} maxLength={2000} aria-describedby="case-note-count" disabled={pending} /><span className="character-counter" id="case-note-count">{note.length}/2000</span><button type="submit" disabled={pending || !note.trim()}>{pending ? "Saving..." : "Add note"}</button></form></section>
    <section className="panel"><span className="section-label">Notes</span>{item.notes.length ? item.notes.map((entry) => <article className="evidence" key={entry.id}><strong>{entry.actor}</strong><time>{formatTime(entry.created_at)}</time><p>{entry.text}</p></article>) : <p>No notes recorded.</p>}</section>
    <section className="panel"><span className="section-label">Audit history</span>{item.audit_events.length ? item.audit_events.map((event) => <article className="evidence" key={event.id}><strong>{event.action}</strong><span>{event.actor} · {formatTime(event.created_at)}</span>{event.new_state && <p>{event.previous_state} → {event.new_state}{event.reason ? ` — ${event.reason}` : ""}</p>}{event.note_id && <p>Note: {event.note_id}</p>}</article>) : <p>No audit events recorded.</p>}</section>
  </div>;
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [page, setPage] = useState<CasePage | null>(null);
  const [selected, setSelected] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const listRequest = useRef(0);
  const detailRequest = useRef(0);

  const loadList = async (pageNumber = currentPage) => { const request = ++listRequest.current; setError(null); setPage(null); try { const result = await listCases(pageNumber); if (request === listRequest.current) setPage(result); } catch (err) { if (request === listRequest.current) setError(caseError(err)); } };
  const select = async (id: string) => { const request = ++detailRequest.current; setDetailLoading(true); setError(null); try { const result = await getCase(id); if (request === detailRequest.current) setSelected(result); } catch (err) { if (request === detailRequest.current) setError(caseError(err)); } finally { if (request === detailRequest.current) setDetailLoading(false); } };
  const refreshSelected = async () => { if (!selected) return; const request = ++detailRequest.current; const result = await getCase(selected.id); if (request === detailRequest.current) setSelected(result); };
  useEffect(() => { void getHealth().then((value) => { setHealth(value); setHealthError(null); }).catch((err) => { setHealth(null); setHealthError(caseError(err)); }); void loadList(1); }, []);
  const changePage = (pageNumber: number) => { setCurrentPage(pageNumber); void loadList(pageNumber); };

  return <div className="app-shell"><header className="topbar"><div className="brand"><span className="brand-mark" aria-hidden="true">E</span><div><strong>EuroPilot</strong><span>Case workflow</span></div></div><span className="read-only">Synthetic data only</span></header><main><HealthBanner health={health} error={healthError} />{selected ? <CaseDetailView item={selected} onBack={() => { setSelected(null); setError(null); }} onRefresh={refreshSelected} /> : <><div className="page-heading"><div><span className="eyebrow">Payment operations</span><h1>Cases</h1><p>Review deterministic payment findings and manage local reconciliation cases.</p></div><span className="scope-note">Local case workflow</span></div>{error ? <ErrorState message={error} retry={() => void loadList(currentPage)} /> : detailLoading ? <div className="state"><span className="spinner" aria-hidden="true" /> Loading case...</div> : <CaseList page={page} onSelect={(id) => void select(id)} onPage={changePage} retry={() => void loadList(currentPage)} />}</>}</main></div>;
}
