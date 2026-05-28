/**
 * Thin client around the StackHealth API.
 * Spec: docs/09-API-DESIGN.md
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ScanStatus =
  | "queued" | "cloning" | "analyzing" | "scoring" | "complete" | "failed";

export interface ScanSummary {
  scan_id: string;
  status: ScanStatus;
  polling_url: string;
  report_url: string;
}

export interface Scan {
  id: string;
  repo: { owner: string; name: string; stars?: number; language?: string };
  status: ScanStatus;
  formula_version: string;
  commit_sha?: string;
  overall_score?: number;
  grade?: string;
  scores?: {
    security: number;
    quality: number;
    hygiene: number;
    community: number;
  };
  score_breakdown?: Record<string, number>;
  partial?: boolean;
  failure_reason?: string;
  artifacts_url?: string;
  tool_versions?: Record<string, string>;
  created_at: string;
  completed_at?: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.error?.message ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function submitScan(repo_url: string): Promise<ScanSummary> {
  return request<ScanSummary>("/api/scans", {
    method: "POST",
    body: JSON.stringify({ repo_url }),
  });
}

export function getScan(id: string): Promise<Scan> {
  return request<Scan>(`/api/scans/${id}`);
}

export function getLatestForRepo(owner: string, name: string): Promise<Scan> {
  return request<Scan>(`/api/repos/${owner}/${name}/latest`);
}
