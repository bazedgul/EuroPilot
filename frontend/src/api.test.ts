import { describe, expect, it, vi } from "vitest";
import { ApiError, apiRequestUrl, createCaseNote, getInvestigation, listCases, transitionCase } from "./api";

describe("API client", () => {
  it("uses same-origin API paths in Vite development", () => {
    expect(apiRequestUrl("/api/health/")).toBe("/api/health/");
  });

  it("converts network failures into a safe user-facing error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network detail")));
    await expect(getInvestigation("missing")).rejects.toEqual(expect.objectContaining({ name: "ApiError", status: 0, message: expect.stringContaining("could not be reached") }));
  });

  it("does not expose server error bodies as implementation details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("secret stack trace", { status: 500 })));
    await expect(getInvestigation("one")).rejects.toBeInstanceOf(ApiError);
    await expect(getInvestigation("one")).rejects.toHaveProperty("message", "The API returned an error.");
  });

  it("uses the case endpoints and sends the locked mutation payloads", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ count: 0, page: 1, page_size: 20, results: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ case: {}, audit_event: {} }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ note: {}, audit_event: {} }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    await listCases(1);
    await transitionCase("case-1", "request-1", "deferred", "reason");
    await createCaseNote("case-1", "request-2", "note");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/cases/?page=1&page_size=20");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toEqual({ request_id: "request-1", target_state: "deferred", reason: "reason" });
    expect(JSON.parse(fetchMock.mock.calls[2][1].body as string)).toEqual({ request_id: "request-2", text: "note" });
  });

  it("preserves documented retryable API errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: "concurrency_retryable", message: "Retry" } }), { status: 503 })));
    await expect(createCaseNote("case-1", "request-1", "note")).rejects.toEqual(expect.objectContaining({ status: 503, code: "concurrency_retryable", message: "Retry" }));
  });
});
