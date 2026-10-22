import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CaseDetailView, CaseList, HealthBanner, InvestigationDetail, OutcomeBadge } from "./App";
import type { CaseDetail, CasePage, Investigation } from "./types";

afterEach(cleanup);

describe("outcome presentation", () => {
  it.each([
    ["confirmed_success", "Confirmed success"], ["confirmed_failure", "Confirmed failure"],
    ["unknown", "Unknown outcome"], ["conflict", "Conflicting evidence"],
  ] as const)("renders %s with an explicit accessible label", (outcome, label) => {
    render(<OutcomeBadge outcome={outcome} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

describe("health presentation", () => {
  it("shows the backend data mode and SQLite limitation", () => {
    render(<HealthBanner health={{ status: "ok", service: "europilot", data_mode: "sqlite_synthetic" }} />);
    expect(screen.getByText("sqlite_synthetic")).toBeInTheDocument();
    expect(screen.getByText(/Local SQLite synthetic data/)).toBeInTheDocument();
  });

  it("shows an API error instead of a stale healthy banner", () => {
    render(<HealthBanner health={null} error="The API could not be reached." />);
    expect(screen.getByRole("alert")).toHaveTextContent("API unavailable");
    expect(screen.getByRole("alert")).toHaveTextContent("could not be reached");
  });
});

describe("investigation detail readability", () => {
  it("labels retry, evidence provenance, and delivery timestamps separately", () => {
    const item: Investigation = {
      id: "investigation-1",
      payment: { id: "payment-1", invoice_id: "invoice-1" },
      outcome: "unknown",
      finding: { outcome: "unknown", missing_evidence: ["authoritative evidence is missing"] },
      missing_evidence: ["authoritative evidence is missing"],
      attempts: [{ id: "attempt-1", request_id: "request-1", requested_time: "2026-01-01T00:00:00Z", outcome: "unknown", retry_of: null }, { id: "attempt-2", request_id: "request-2", requested_time: "2026-01-02T00:00:00Z", outcome: "unknown", retry_of: "attempt-1" }],
      events: [{ provider: "synthetic", id: "event-1", event_type: "unknown", event_time: "2026-01-03T00:00:00Z", received_time: null }],
      deliveries: [{ id: "delivery-1", provider: "synthetic", event_id: "event-1", received_time: "2026-01-04T00:00:00Z" }],
      evidence: [{ id: "evidence-1", payment_id: "payment-1", source: "synthetic", reference: "event-1", event_time: "2026-01-03T00:00:00Z", received_time: "2026-01-04T00:00:00Z", event_type: "unknown", provider: "synthetic", authoritative: false }],
      supporting_evidence: [],
    };
    render(<InvestigationDetail item={item} onBack={() => undefined} />);
    expect(screen.getByText("Retry of attempt-1")).toBeInTheDocument();
    expect(screen.getAllByText("Requested time")).toHaveLength(2);
    expect(screen.getAllByText("Request ID").length).toBe(2);
    expect(screen.getAllByText("Relationship").length).toBe(2);
    expect(screen.getByText("Event reference")).toBeInTheDocument();
    expect(screen.getByText("delivery-1")).toBeInTheDocument();
    expect(screen.getAllByText("Received time").length).toBeGreaterThan(0);
    expect(screen.getByText(/Receipt time unknown/)).toBeInTheDocument();
  });
});

const caseDetail: CaseDetail = {
  id: "case-1", investigation_id: "investigation-1", payment_id: "payment-1", state: "open", payment_outcome: "unknown", updated_at: "2026-01-05T00:00:00Z", resolution_reason: null,
  notes: [{ id: "note-1", text: "Plain <text>", actor: "synthetic_local_operator", created_at: "2026-01-05T00:00:00Z" }],
  audit_events: [{ id: "audit-1", action: "note_created", actor: "synthetic_local_operator", created_at: "2026-01-05T00:00:00Z", previous_state: null, new_state: null, reason: null, note_id: "note-1", request_id: "request-1" }],
};

describe("case workflow presentation", () => {
  it("renders empty and populated case list states", () => {
    const page: CasePage = { count: 1, page: 1, page_size: 20, results: [caseDetail] };
    render(<CaseList page={page} onSelect={() => undefined} onPage={() => undefined} retry={() => undefined} />);
    expect(screen.getByText("case-1")).toBeInTheDocument();
    expect(screen.getByText("Open")).toBeInTheDocument();
  });

  it("offers only allowed transitions and keeps notes as plain text", () => {
    render(<CaseDetailView item={caseDetail} onBack={() => undefined} onRefresh={async () => undefined} />);
    expect(screen.getByLabelText("New state")).toHaveValue("");
    expect(screen.getByRole("option", { name: "Under review" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Deferred" })).toBeInTheDocument();
    expect(screen.getByText("Plain <text>")).toBeInTheDocument();
    expect(screen.getByLabelText("Reason (optional)")).toHaveAttribute("maxlength", "500");
    expect(screen.getByLabelText("Note")).toHaveAttribute("maxlength", "2000");
    expect(screen.getByText("0/500")).toBeInTheDocument();
    expect(screen.getByText("0/2000")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Note"), { target: { value: "   " } });
    expect(screen.getByRole("button", { name: "Add note" })).toBeDisabled();
  });

  it("keeps pasted input intact for live counters while enforcing native limits", () => {
    render(<CaseDetailView item={caseDetail} onBack={() => undefined} onRefresh={async () => undefined} />);
    const note = "n".repeat(2001);
    fireEvent.change(screen.getByLabelText("Note"), { target: { value: note } });
    expect(screen.getByLabelText("Note")).toHaveValue(note);
    expect(screen.getByText("2001/2000")).toBeInTheDocument();
  });

  it("does not offer state transitions for resolved cases", () => {
    render(<CaseDetailView item={{ ...caseDetail, state: "resolved", resolution_reason: "Done" }} onBack={() => undefined} onRefresh={async () => undefined} />);
    expect(screen.getByText(/no further state transitions/i)).toBeInTheDocument();
    expect(screen.queryByLabelText("New state")).not.toBeInTheDocument();
  });
});
