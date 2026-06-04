#!/usr/bin/env node
// stackhealth — score any public GitHub repo from the terminal.
// Usage:
//   stackhealth <owner/repo>
//   stackhealth fastapi/fastapi --email me@example.com
//   stackhealth pallets/click --json | jq .grade
//   stackhealth pallets/click --min-grade B   # exit nonzero if below B

import { ApiClient, ApiError, parseRepoArg, type ScanRead } from "./api.js";
import {
  blue,
  bold,
  colorForGrade,
  cyan,
  dim,
  gradeAtLeast,
  gray,
  red,
  renderReport,
  yellow,
} from "./render.js";

interface Args {
  repo?: string;
  ref?: string;
  email?: string;
  json: boolean;
  minGrade?: string;
  apiBase: string;
  siteBase: string;
  timeoutSeconds: number;
  help: boolean;
  version: boolean;
  badge: boolean;
  noWait: boolean;
}

const VERSION = "0.2.0";

const HELP = `${bold("stackhealth")} — score any public GitHub repo against the open StackHealth formula.

${bold("Usage")}
  $ stackhealth <owner/repo> [options]

${bold("Examples")}
  $ stackhealth fastapi/fastapi
  $ stackhealth pallets/click --json | jq .grade
  $ stackhealth my-org/my-repo --min-grade B    # exit 1 if grade < B

${bold("Options")}
  --email <addr>      Email for scan-complete notification (or set $STACKHEALTH_EMAIL).
                      Required by the API on first scan; remembered for repeat runs.
  --json              Print the full scan as JSON. No colors, no spinner.
  --min-grade <G>     Exit non-zero if the resulting grade is below G (e.g. B, A-).
                      Useful in CI: \`stackhealth . --min-grade B || exit 1\`.
  --ref <branch|tag>  Score a specific branch or tag instead of the repo's
                      default branch (e.g. --ref v8.0.0, --ref release/2.x).
  --no-wait           Submit the scan and exit immediately with the scan_id and
                      report URL. No polling. Use for fire-and-forget triggers.
  --badge             Print the README badge markdown for this repo and exit.
                      No scan is submitted; the badge always reflects the latest
                      grade once one exists.
  --api <url>         Override API base (default: https://api.stackhealth.dev).
  --site <url>        Override site base (default: https://stackhealth.dev).
  --timeout <secs>    Give up polling after N seconds (default: 600).
  -h, --help          Show this help.
  -v, --version       Show version.

Reports stay at https://stackhealth.dev/r/<owner>/<repo>.
Formula: https://stackhealth.dev/methodology · v${VERSION}
`;

function parseArgs(argv: string[]): Args {
  const args: Args = {
    json: false,
    apiBase: process.env.STACKHEALTH_API ?? "https://api.stackhealth.dev",
    siteBase: process.env.STACKHEALTH_SITE ?? "https://stackhealth.dev",
    email: process.env.STACKHEALTH_EMAIL,
    timeoutSeconds: 600,
    help: false,
    version: false,
    badge: false,
    noWait: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case "-h":
      case "--help":
        args.help = true;
        break;
      case "-v":
      case "--version":
        args.version = true;
        break;
      case "--json":
        args.json = true;
        break;
      case "--badge":
        args.badge = true;
        break;
      case "--no-wait":
      case "--nowait":
        args.noWait = true;
        break;
      case "--ref":
        args.ref = argv[++i];
        break;
      case "--email":
        args.email = argv[++i];
        break;
      case "--min-grade":
        args.minGrade = argv[++i];
        break;
      case "--api":
        args.apiBase = argv[++i];
        break;
      case "--site":
        args.siteBase = argv[++i];
        break;
      case "--timeout":
        args.timeoutSeconds = Number(argv[++i]);
        break;
      default:
        if (a.startsWith("--")) {
          throw new Error(`Unknown flag: ${a}`);
        }
        if (args.repo) {
          throw new Error(
            `Too many positional args. Expected one repo, got "${args.repo}" and "${a}".`,
          );
        }
        args.repo = a;
    }
  }
  return args;
}

// Spinner that updates the same line. Silent when not on a TTY (CI logs).
class Spinner {
  private frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
  private idx = 0;
  private timer: NodeJS.Timeout | null = null;
  private current = "";

  constructor(private readonly enabled: boolean) {}

  start(text: string): void {
    this.current = text;
    if (!this.enabled) return;
    process.stderr.write("\x1b[?25l"); // hide cursor
    this.timer = setInterval(() => {
      const frame = this.frames[this.idx++ % this.frames.length];
      process.stderr.write(`\r  ${cyan(frame)} ${this.current}     `);
    }, 80);
  }

  update(text: string): void {
    this.current = text;
  }

  stop(finalLine?: string): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    if (this.enabled) {
      process.stderr.write("\r\x1b[K\x1b[?25h"); // clear line, show cursor
    }
    if (finalLine) process.stderr.write(finalLine + "\n");
  }
}

async function poll(
  client: ApiClient,
  scanId: string,
  timeoutSeconds: number,
  onTick: (s: ScanRead) => void,
): Promise<ScanRead> {
  const deadline = Date.now() + timeoutSeconds * 1000;
  // Backend rate-limits aggressive polling. 2s is the same cadence the web
  // app uses (see scan/[id]/page.tsx). After 60s we slow to 4s to be kind.
  let interval = 2000;
  let pollCount = 0;
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  while (true) {
    if (Date.now() > deadline) {
      throw new Error(
        `Timed out after ${timeoutSeconds}s. The scan may still complete — see https://stackhealth.dev/r/${scanId}`,
      );
    }
    const scan = await client.get(scanId);
    onTick(scan);
    if (scan.status === "complete" || scan.status === "failed") return scan;
    if (pollCount++ > 30) interval = 4000;
    await new Promise((r) => setTimeout(r, interval));
  }
}

const STATUS_LABEL: Record<ScanRead["status"], string> = {
  queued: "queued · waiting for worker",
  cloning: "cloning repo",
  analyzing: "running 7 engines (security, quality, hygiene, community…)",
  scoring: "computing final score",
  complete: "complete",
  failed: "failed",
};

async function main(): Promise<number> {
  let args: Args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (e) {
    process.stderr.write(red("Error: ") + (e as Error).message + "\n\n");
    process.stderr.write(HELP);
    return 2;
  }

  if (args.help) {
    process.stdout.write(HELP);
    return 0;
  }
  if (args.version) {
    process.stdout.write(`stackhealth ${VERSION}\n`);
    return 0;
  }
  if (!args.repo) {
    process.stderr.write(HELP);
    return 2;
  }

  let parsed: ReturnType<typeof parseRepoArg>;
  try {
    parsed = parseRepoArg(args.repo);
  } catch (e) {
    process.stderr.write(red("Error: ") + (e as Error).message + "\n");
    return 2;
  }

  // --badge: print the README snippet and exit. No API call needed —
  // the badge route always serves the latest grade for the repo.
  if (args.badge) {
    const badgeUrl = `${args.apiBase}/r/${parsed.owner}/${parsed.name}/badge.svg`;
    const reportUrl = `${args.siteBase}/r/${parsed.owner}/${parsed.name}`;
    process.stdout.write(`[![StackHealth](${badgeUrl})](${reportUrl})\n`);
    return 0;
  }

  if (!args.email) {
    process.stderr.write(
      red("Error: ") +
        "an email is required by the API.\n" +
        dim(
          "       pass --email you@example.com, or set $STACKHEALTH_EMAIL once and forget it.\n",
        ),
    );
    return 2;
  }

  const client = new ApiClient(args.apiBase);
  const spinner = new Spinner(!args.json && process.stderr.isTTY === true);

  const refSuffix = args.ref ? ` @ ${args.ref}` : "";
  spinner.start(
    `Submitting ${bold(`${parsed.owner}/${parsed.name}`)}${refSuffix} for scoring…`,
  );
  let submitted;
  try {
    submitted = await client.submit(parsed.url, args.email, args.ref);
  } catch (e) {
    spinner.stop();
    return handleApiError(e);
  }

  spinner.update(`Scan ${gray(submitted.scan_id)} ${STATUS_LABEL.queued}`);

  // --no-wait: submit and exit immediately. Useful for CI gates that don't
  // need the score inline (separate job will poll, or use the GH Action).
  if (args.noWait) {
    spinner.stop();
    const reportUrl = `${args.siteBase}${submitted.report_url}`;
    if (args.json) {
      process.stdout.write(
        JSON.stringify({ ...submitted, report_url: reportUrl }, null, 2) + "\n",
      );
    } else {
      process.stdout.write(
        `\n  ${bold(`${parsed.owner}/${parsed.name}`)} queued\n` +
          `  ${dim("scan_id:")} ${submitted.scan_id}\n` +
          `  ${dim("status:")}  ${submitted.status}\n` +
          `  ${dim("report:")}  ${blue(reportUrl)}\n\n`,
      );
    }
    return 0;
  }

  let scan: ScanRead;
  try {
    scan = await poll(client, submitted.scan_id, args.timeoutSeconds, (s) => {
      spinner.update(`${STATUS_LABEL[s.status] ?? s.status}`);
    });
  } catch (e) {
    spinner.stop();
    return handleApiError(e);
  }
  spinner.stop();

  const reportUrl = `${args.siteBase}/r/${parsed.owner}/${parsed.name}/${submitted.scan_id}`;

  if (args.json) {
    process.stdout.write(
      JSON.stringify({ ...scan, report_url: reportUrl }, null, 2) + "\n",
    );
  } else {
    process.stdout.write(renderReport(scan, reportUrl));
  }

  if (scan.status === "failed") return 1;
  if (args.minGrade && !gradeAtLeast(scan.grade, args.minGrade)) {
    if (!args.json) {
      const tint = colorForGrade(scan.grade);
      process.stderr.write(
        `  ${yellow("✗")} grade ${tint(scan.grade ?? "?")} is below threshold ${bold(args.minGrade)}\n\n`,
      );
    }
    return 1;
  }
  return 0;
}

function handleApiError(e: unknown): number {
  if (e instanceof ApiError) {
    process.stderr.write(red(`API error (${e.status}): `) + e.message + "\n");
    if (e.code) process.stderr.write(dim(`  code: ${e.code}\n`));
    if (e.status === 429) {
      process.stderr.write(
        dim("  Rate limit: 5 scans / IP / hour. Try again in a few minutes.\n"),
      );
    }
    return 1;
  }
  process.stderr.write(red("Error: ") + (e as Error).message + "\n");
  return 1;
}

main().then(
  (code) => process.exit(code),
  (e) => {
    process.stderr.write(red("Unexpected: ") + (e as Error).stack + "\n");
    process.exit(1);
  },
);
