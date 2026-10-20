import type { Health, Investigation, InvestigationPage } from "./types";

// In Vite development, keep requests same-origin so the configured proxy avoids browser CORS.
// VITE_API_BASE_URL is used as the proxy target by vite.config.ts in that mode.
const baseUrl = (import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? "")).replace(/\/$/, "");

export function apiRequestUrl(path: string): string {
  return `${baseUrl}${path}`;
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiRequestUrl(path));
  } catch {
    throw new ApiError(0, "The API could not be reached. Check that the local backend is running.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.status === 404 ? "The requested investigation was not found." : "The API returned an error.");
  }
  return (await response.json()) as T;
}

export const getHealth = () => request<Health>("/api/health/");
export const listInvestigations = (page: number, pageSize = 10) => request<InvestigationPage>(`/api/v1/investigations/?page=${page}&page_size=${pageSize}`);
export const getInvestigation = (id: string) => request<Investigation>(`/api/v1/investigations/${encodeURIComponent(id)}/`);
