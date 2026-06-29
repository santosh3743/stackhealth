// Mirrors apps/cli/src/api.ts. Inlined here (rather than imported from the
// CLI package) because the bundled Action must be self-contained — the
// runner only has dist/index.js to work with.

const USER_AGENT = "stackhealth-action/0.1.0 (+https://stackhealth.dev)";
const DEFAULT_HEADERS: Record<string, string> = {
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
    language?: string;
    stars?: number;
  };
  status:
    | "queued"
    | "cloning"
    | "analyzing"
    | "scoring"
    | "complete"
    | "failed";
  formula_version: string;
  requested_ref?: string | null;
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
  private readonly headers: Record<string, string>;

  constructor(
    public readonly base: string,
    ciToken?: string,
  ) {
    this.headers = { ...DEFAULT_HEADERS };
    // Sent on every request so a Cloudflare WAF rule can recognise CI
    // traffic and skip the bot challenge that otherwise 403s GitHub
    // Actions runners. Empty/unset = omitted, so behaviour is unchanged
    // when no secret is configured.
    if (ciToken) this.headers["x-stackhealth-ci"] = ciToken;
  }

  async submit(
    repoUrl: string,
    email: string,
    ref?: string,
  ): Promise<ScanCreateResponse> {
    const body: Record<string, string> = {
      repo_url: repoUrl,
      notify_email: email,
    };
    if (ref) body.ref = ref;
    const res = await fetch(`${this.base}/api/scans`, {
      method: "POST",
      headers: { ...this.headers, "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await toError(res);
    return res.json() as Promise<ScanCreateResponse>;
  }

  async get(scanId: string): Promise<ScanRead> {
    const res = await fetch(`${this.base}/api/scans/${scanId}`, {
      headers: this.headers,
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
    /* non-JSON */
  }
  return new ApiError(message, res.status, code);
}

// Poll until the scan reaches a terminal state. Cadence matches the CLI:
// 2s for the first minute, then 4s.
export async function poll(
  client: ApiClient,
  scanId: string,
  timeoutSeconds: number,
  onTick?: (s: ScanRead) => void,
): Promise<ScanRead> {
  const deadline = Date.now() + timeoutSeconds * 1000;
  let interval = 2000;
  let pollCount = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    if (Date.now() > deadline) {
      throw new Error(`Timed out polling scan ${scanId} after ${timeoutSeconds}s`);
    }
    const scan = await client.get(scanId);
    onTick?.(scan);
    if (scan.status === "complete" || scan.status === "failed") return scan;
    if (pollCount++ > 30) interval = 4000;
    await new Promise((r) => setTimeout(r, interval));
  }
}

const GRADES_ORDER = ["F", "D", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"];

export function gradeAtLeast(actual: string | undefined, min: string): boolean {
  if (!actual) return false;
  const ai = GRADES_ORDER.indexOf(actual);
  const mi = GRADES_ORDER.indexOf(min);
  if (ai < 0 || mi < 0) return false;
  return ai >= mi;
}
