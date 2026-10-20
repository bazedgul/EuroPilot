import { describe, expect, it, vi } from "vitest";
import { ApiError, apiRequestUrl, getInvestigation } from "./api";

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
});
