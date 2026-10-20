import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HealthBanner, InvestigationDetail, OutcomeBadge } from "./App";
import type { Investigation } from "./types";

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
      attempts: [{ id: "attempt-1", request_id: "request-1", outcome: "unknown", retry_of: null }, { id: "attempt-2", request_id: "request-2", outcome: "unknown", retry_of: "attempt-1" }],
      deliveries: [{ id: "delivery-1", provider: "synthetic", event_id: "event-1", received_time: "2026-01-04T00:00:00Z" }],
      evidence: [{ id: "evidence-1", payment_id: "payment-1", source: "synthetic", reference: "event-1", event_time: "2026-01-03T00:00:00Z", received_time: "2026-01-04T00:00:00Z", event_type: "unknown", provider: "synthetic", authoritative: false }],
      supporting_evidence: [],
    };
    render(<InvestigationDetail item={item} onBack={() => undefined} />);
    expect(screen.getByText("Retry of attempt-1")).toBeInTheDocument();
    expect(screen.getAllByText("Request ID").length).toBe(2);
    expect(screen.getAllByText("Relationship").length).toBe(2);
    expect(screen.getByText("Event reference")).toBeInTheDocument();
    expect(screen.getByText("delivery-1")).toBeInTheDocument();
    expect(screen.getAllByText("Received time").length).toBeGreaterThan(0);
  });
});
