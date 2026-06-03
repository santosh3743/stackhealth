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
  notify_enabled?: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    // fetch only throws for network-level failures (DNS, offline, CORS
    // preflight blocked, etc.). HTTP errors fall through to !res.ok below.
    throw new Error(
      "Couldn't reach StackHealth. Check your internet — if the problem persists, it's on us.",
    );
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      const inner = body?.detail?.error?.message ?? body?.error?.message;
      detail = inner ?? body?.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export function submitScan(
  repo_url: string,
  notify_email: string,
): Promise<ScanSummary> {
  return request<ScanSummary>("/api/scans", {
    method: "POST",
    body: JSON.stringify({ repo_url, notify_email }),
  });
}

export function getScan(id: string): Promise<Scan> {
  return request<Scan>(`/api/scans/${id}`);
}

export function setScanNotifyEmail(id: string, email: string): Promise<void> {
  return request<void>(`/api/scans/${id}/notify`, {
    method: "PATCH",
    body: JSON.stringify({ notify_email: email }),
  });
}

export function getLatestForRepo(owner: string, name: string): Promise<Scan> {
  return request<Scan>(`/api/repos/${owner}/${name}/latest`);
}

export interface DiscoverScan {
  scan_id: string;
  owner: string;
  name: string;
  grade?: string | null;
  overall_score?: number | null;
  language?: string | null;
  stars?: number | null;
  completed_at?: string | null;
}

export function getRecentScans(limit = 10): Promise<{ scans: DiscoverScan[] }> {
  return request<{ scans: DiscoverScan[] }>(
    `/api/discover/recent?limit=${limit}`,
  );
}

export function getTopScans(
  limit = 10,
  minStars = 0,
  language?: string,
): Promise<{ scans: DiscoverScan[] }> {
  const lang = language ? `&language=${encodeURIComponent(language)}` : "";
  return request<{ scans: DiscoverScan[] }>(
    `/api/discover/top?limit=${limit}&min_stars=${minStars}${lang}`,
  );
}
