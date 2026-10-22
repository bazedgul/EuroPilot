import type { CaseDetail, CasePage, Health, Investigation, InvestigationPage, NoteResponse, TransitionResponse } from "./types";

// In Vite development, keep requests same-origin so the configured proxy avoids browser CORS.
// VITE_API_BASE_URL is used as the proxy target by vite.config.ts in that mode.
const baseUrl = (import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? "")).replace(/\/$/, "");

export function apiRequestUrl(path: string): string {
  return `${baseUrl}${path}`;
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string, public readonly code?: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiRequestUrl(path), init);
  } catch {
    throw new ApiError(0, "The API could not be reached. Check that the local backend is running.");
  }
  if (!response.ok) {
    let body: { error?: { code?: string; message?: string } } = {};
    try { body = (await response.json()) as typeof body; } catch { /* Keep the safe fallback below. */ }
    const code = body.error?.code;
    const message = body.error?.message ?? (response.status === 404 ? "The requested investigation was not found." : "The API returned an error.");
    throw new ApiError(response.status, message, code);
  }
  return (await response.json()) as T;
}

export const getHealth = () => request<Health>("/api/health/");
export const listInvestigations = (page: number, pageSize = 10) => request<InvestigationPage>(`/api/v1/investigations/?page=${page}&page_size=${pageSize}`);
export const getInvestigation = (id: string) => request<Investigation>(`/api/v1/investigations/${encodeURIComponent(id)}/`);
export const listCases = (page: number, pageSize = 20) => request<CasePage>(`/api/v1/cases/?page=${page}&page_size=${pageSize}`);
export const getCase = (id: string) => request<CaseDetail>(`/api/v1/cases/${encodeURIComponent(id)}/`);
export const transitionCase = (id: string, requestId: string, targetState: string, reason: string | null) => request<TransitionResponse>(`/api/v1/cases/${encodeURIComponent(id)}/transitions/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: requestId, target_state: targetState, reason }) });
export const createCaseNote = (id: string, requestId: string, note: string) => request<NoteResponse>(`/api/v1/cases/${encodeURIComponent(id)}/notes/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request_id: requestId, text: note }) });
