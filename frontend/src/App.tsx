import { useEffect, useState } from "react";
import { getHealth, getInvestigation, listInvestigations } from "./api";
import type { Health, Investigation, InvestigationPage, Outcome } from "./types";

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

export function InvestigationDetail({ item, onBack }: { item: Investigation; onBack: () => void }) {
  return <div className="detail-view"><button className="back-button" onClick={onBack}>&lt;- Back to investigations</button>
    <div className="detail-heading"><div><span className="card-kicker">Investigation {item.id}</span><h1>{item.payment.id}</h1><p>Invoice / payable: {item.payment.invoice_id}</p></div><OutcomeBadge outcome={item.outcome} /></div>
    <section className="panel finding-panel"><div><span className="section-label">Deterministic finding</span><h2><OutcomeBadge outcome={item.finding.outcome} /></h2></div><div><span className="section-label">Missing evidence</span>{item.finding.missing_evidence.length ? <ul>{item.finding.missing_evidence.map((reason) => <li key={reason}>{reason}</li>)}</ul> : <p>No missing evidence recorded.</p>}</div></section>
    <section className="panel"><span className="section-label">Payment attempts</span><div className="attempt-list">{item.attempts.length ? item.attempts.map((attempt) => <div className="attempt" key={attempt.id}><div className="attempt-main"><span className="field-label">Attempt ID</span><strong className="field-value">{attempt.id}</strong></div><div className="attempt-main"><span className="field-label">Outcome</span><span className="attempt-outcome field-value">{attempt.outcome}</span></div><div className="attempt-meta"><div className="meta-pair"><span className="field-label">Request ID</span><span className="field-value">{attempt.request_id}</span></div><div className="meta-pair retry-note"><span className="field-label">Relationship</span><span className="field-value">{attempt.retry_of ? `Retry of ${attempt.retry_of}` : "Initial attempt"}</span></div></div></div>) : <p>No attempt data returned.</p>}</div></section>
    <section className="panel"><span className="section-label">Evidence timeline</span><div className="evidence-list">{item.evidence.length ? item.evidence.map((evidence) => <article className="evidence" key={evidence.id}><div className="evidence-title"><div><span className="field-label">Event type</span><strong>{evidence.event_type}</strong></div><span className={evidence.authoritative ? "authority authority-yes" : "authority authority-no"}>{evidence.authoritative ? "Authoritative" : "Non-authoritative"}</span></div><div className="evidence-context"><div><span className="field-label">Source</span><span>{evidence.source}</span></div><div><span className="field-label">Provider</span><span>{evidence.provider ?? "Not specified"}</span></div><div><span className="field-label">Event reference</span><span>{evidence.reference}</span></div></div><dl><div><dt>Provider event time</dt><dd>{formatTime(evidence.event_time)}</dd></div><div><dt>Received time</dt><dd>{formatTime(evidence.received_time)}</dd></div></dl></article>) : <p>No evidence returned.</p>}</div></section>
    <section className="panel"><span className="section-label">Delivery occurrences</span><div className="delivery-list">{item.deliveries.length ? item.deliveries.map((delivery) => <div className="delivery" key={delivery.id}><div><span className="field-label">Delivery ID</span><strong>{delivery.id}</strong></div><div><span className="field-label">Provider event</span><span>{delivery.provider} / {delivery.event_id}</span></div><div><span className="field-label">Received time</span><time>{formatTime(delivery.received_time)}</time></div></div>) : <p>No delivery data returned.</p>}</div></section>
  </div>;
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [page, setPage] = useState<InvestigationPage | null>(null);
  const [selected, setSelected] = useState<Investigation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const loadList = async (pageNumber = currentPage) => { setError(null); setPage(null); try { const result = await listInvestigations(pageNumber); setPage(result); } catch (err) { setError(err instanceof Error ? err.message : "Unexpected API error."); } };
  useEffect(() => { void getHealth().then((value) => { setHealth(value); setHealthError(null); }).catch((err) => { setHealth(null); setHealthError(err instanceof Error ? err.message : "The API health check failed."); }); void loadList(1); }, []);
  const select = async (id: string) => { setDetailLoading(true); setError(null); try { setSelected(await getInvestigation(id)); } catch (err) { setError(err instanceof Error ? err.message : "Unexpected API error."); } finally { setDetailLoading(false); } };
  const changePage = (pageNumber: number) => { setCurrentPage(pageNumber); void loadList(pageNumber); };

  return <div className="app-shell"><header className="topbar"><div className="brand"><span className="brand-mark" aria-hidden="true">E</span><div><strong>EuroPilot</strong><span>Investigation desk</span></div></div><span className="read-only">Read-only demo</span></header><main><HealthBanner health={health} error={healthError} />{selected ? <InvestigationDetail item={selected} onBack={() => { setSelected(null); setError(null); }} /> : <><div className="page-heading"><div><span className="eyebrow">Payment operations</span><h1>Investigations</h1><p>Trace uncertain payment outcomes through deterministic evidence.</p></div><span className="scope-note">Synthetic data only</span></div>{error ? <ErrorState message={error} retry={() => void loadList(currentPage)} /> : detailLoading ? <div className="state"><span className="spinner" aria-hidden="true" /> Loading investigation...</div> : <InvestigationList page={page} onSelect={(id) => void select(id)} onPage={changePage} retry={() => void loadList(currentPage)} />}</>}</main></div>;
}
