// Thin HTTP client over the public StackHealth API.
// Mirrors apps/web/lib/api.ts so the CLI behaves like the website would.

const DEFAULT_BASE = "https://api.stackhealth.dev";

// Identify ourselves so we show up cleanly in API logs and Cloudflare
// analytics — and so any future server-side rule can route by client.
const USER_AGENT = "stackhealth-cli/0.1.0 (+https://stackhealth.dev)";

const DEFAULT_HEADERS: HeadersInit = {
  "user-agent": USER_AGENT,
  accept: "application/json",
};

export interface ScanCreateResponse {
  scan_id: string;
  status: string;
  polling_url: string;
  report_url: string;
}

export interface ScanRead {
  id: string;
  repo: {
    owner: string;
    name: string;
    stars?: number;
    language?: string;
    license_spdx?: string;
  };
  status:
    | "queued"
    | "cloning"
    | "analyzing"
    | "scoring"
    | "complete"
    | "failed";
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
  partial?: boolean;
  failure_reason?: string;
  tool_versions?: Record<string, string>;
  created_at: string;
  completed_at?: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
  }
}

export class ApiClient {
  constructor(public readonly base: string = DEFAULT_BASE) {}

  async submit(repoUrl: string, email: string): Promise<ScanCreateResponse> {
    const res = await fetch(`${this.base}/api/scans`, {
      method: "POST",
      headers: { ...DEFAULT_HEADERS, "content-type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, notify_email: email }),
    });
    if (!res.ok) throw await toError(res);
    return res.json() as Promise<ScanCreateResponse>;
  }

  async get(scanId: string): Promise<ScanRead> {
    const res = await fetch(`${this.base}/api/scans/${scanId}`, {
      headers: DEFAULT_HEADERS,
    });
    if (!res.ok) throw await toError(res);
    return res.json() as Promise<ScanRead>;
  }
}

async function toError(res: Response): Promise<ApiError> {
  let message = res.statusText;
  let code: string | undefined;
  try {
    const body = (await res.json()) as {
      detail?: { error?: { code?: string; message?: string }; message?: string };
      error?: { code?: string; message?: string };
    };
    const inner = body?.detail?.error ?? body?.error;
    if (inner?.message) message = inner.message;
    if (inner?.code) code = inner.code;
    else if (typeof body?.detail === "string") message = body.detail;
  } catch {
    /* non-JSON body */
  }
  return new ApiError(message, res.status, code);
}

// Parses "owner/repo", a full github URL, or a stackhealth report URL.
export function parseRepoArg(input: string): { owner: string; name: string; url: string } {
  const s = input.trim().replace(/\.git\/?$/, "").replace(/\/$/, "");
  const patterns = [
    /^https?:\/\/github\.com\/([\w.-]+)\/([\w.-]+)$/i,
    /^https?:\/\/stackhealth\.dev\/(?:r\/)?([\w.-]+)\/([\w.-]+)$/i,
    /^([\w.-]+)\/([\w.-]+)$/,
  ];
  for (const re of patterns) {
    const m = re.exec(s);
    if (m) {
      const [, owner, name] = m;
      return {
        owner,
        name,
        url: `https://github.com/${owner}/${name}`,
      };
    }
  }
  throw new Error(
    `Could not parse "${input}". Use "owner/repo" or a github.com URL.`,
  );
}
