import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { EmbedCard } from "@/components/embed-card";
import { GradeBadge, type Grade } from "@/components/grade-badge";
import { LogoMark } from "@/components/logo-mark";

const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export const revalidate = 3600;

type Scan = {
  id: string;
  repo: {
    owner: string;
    name: string;
    stars?: number;
    language?: string;
    default_branch?: string;
    pushed_at?: string;
    license_spdx?: string;
  };
  status: string;
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
  score_breakdown?: Record<string, unknown>;
  partial?: boolean;
  failure_reason?: string;
  artifacts_url?: string;
  tool_versions?: Record<string, string>;
  created_at: string;
  completed_at?: string;
};

type Finding = {
  id: string;
  engine: string;
  severity: string;
  rule_id?: string;
  title: string;
  message?: string;
  file_path?: string;
  line_number?: number;
};

async function fetchScan(scanId: string): Promise<Scan | null> {
  const r = await fetch(`${API_BASE}/api/scans/${scanId}`, {
    next: { revalidate: 3600 },
  });
  if (!r.ok) return null;
  return r.json();
}

async function fetchFindings(scanId: string): Promise<Finding[]> {
  try {
    const r = await fetch(`${API_BASE}/api/scans/${scanId}/findings?limit=200`, {
      next: { revalidate: 3600 },
    });
    if (!r.ok) return [];
    const data = await r.json();
    return data.findings ?? [];
  } catch {
    return [];
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ owner: string; name: string; scanId: string }>;
}): Promise<Metadata> {
  const { owner, name, scanId } = await params;
  const scan = await fetchScan(scanId);
  const grade = scan?.grade ?? "?";
  const score = scan?.overall_score ?? "?";
  return {
    title: `${owner}/${name} — ${grade} (${score})`,
    description: `StackHealth report for ${owner}/${name}: overall ${score}/100, grade ${grade}.`,
  };
}

// ─────────────────────────────────────────────────────────────────────
// helpers

const SEV_ORDER = ["critical", "high", "medium", "low", "info"];

function qualLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 75) return "Good";
  if (score >= 60) return "Fair";
  if (score >= 40) return "Weak";
  return "Poor";
}

function qualColor(score: number): string {
  if (score >= 90) return "text-emerald-500";
  if (score >= 75) return "text-green-500";
  if (score >= 60) return "text-amber-500";
  if (score >= 40) return "text-orange-500";
  return "text-rose-500";
}

function barColor(score: number): string {
  if (score >= 90) return "bg-emerald-500";
  if (score >= 75) return "bg-green-500";
  if (score >= 60) return "bg-amber-500";
  if (score >= 40) return "bg-orange-500";
  return "bg-rose-500";
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function timeAgo(iso?: string): string | null {
  if (!iso) return null;
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 86400 * 30) return `${Math.floor(seconds / 86400)}d ago`;
  if (seconds < 86400 * 365) return `${Math.floor(seconds / 86400 / 30)}mo ago`;
  return `${Math.floor(seconds / 86400 / 365)}y ago`;
}

function failedSet(reason?: string): Set<string> {
  if (!reason) return new Set();
  return new Set(
    reason
      .split(";")
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean),
  );
}

// Hygiene checklist items — names match keys produced by engines/hygiene.py
const HYGIENE_ITEMS: { key: string; label: string; weight: number; info?: string }[] = [
  {
    key: "readme",
    label: "README.md exists & is non-trivial (>300 chars)",
    weight: 15,
    info: "A README at the repo root with at least 300 characters. README.rst and README.markdown also count.",
  },
  {
    key: "license_file",
    label: "LICENSE file",
    weight: 15,
    info: "A LICENSE, LICENSE.md, or COPYING file at the root. Required for anyone to legally use your code.",
  },
  {
    key: "license_osi",
    label: "LICENSE is OSI-approved",
    weight: 5,
    info: "License SPDX matches an OSI-approved one (MIT, Apache-2.0, BSD-3-Clause, GPL-3.0, MPL-2.0, etc.). Detected from GitHub's license API and from the LICENSE body.",
  },
  {
    key: "contributing",
    label: "CONTRIBUTING guide",
    weight: 8,
    info: "CONTRIBUTING.md / CONTRIBUTING.rst at the root (or .github/). Tells outsiders how to file issues and submit PRs.",
  },
  {
    key: "code_of_conduct",
    label: "CODE_OF_CONDUCT",
    weight: 5,
    info: "CODE_OF_CONDUCT.md at the root or in .github/. Sets community behavior norms.",
  },
  {
    key: "security_md",
    label: "SECURITY.md",
    weight: 7,
    info: "SECURITY.md at the root or in .github/. Tells security researchers how to report vulnerabilities responsibly.",
  },
  {
    key: "ci_present",
    label: "CI configured (.github/workflows or .gitlab-ci)",
    weight: 10,
    info: "At least one workflow file in .github/workflows/ (or a .gitlab-ci.yml). Without CI, code lands unverified.",
  },
  {
    key: "ci_pr_trigger",
    label: "CI runs on pull_request",
    weight: 5,
    info: "At least one workflow triggers on `pull_request`. Otherwise CI only runs after merge, which defeats the point.",
  },
  {
    key: "tests_dir",
    label: "Tests directory present",
    weight: 10,
    info: "A tests/, test/, __tests__, or spec/ directory at root — or in any of apps/*, packages/*, services/*, libs/*, modules/*, crates/* for monorepos.",
  },
  {
    key: "gitignore",
    label: ".gitignore",
    weight: 3,
    info: ".gitignore at the root. Cheap signal that the repo is curated rather than dumped.",
  },
  {
    key: "description",
    label: "GitHub description set",
    weight: 5,
    info: "The one-line description shown under the repo name on GitHub. Helps discoverability.",
  },
  {
    key: "topics",
    label: "GitHub topics set",
    weight: 5,
    info: "At least one topic (tag) configured on the repo. Drives GitHub's category browse and search.",
  },
  {
    key: "recent_commit",
    label: "Last commit within 365 days",
    weight: 7,
    info: "Repo's `pushed_at` is within the last year. Older = likely abandoned.",
  },
];

const TEST_SIGNAL_ITEMS: { key: string; label: string; weight: number; info?: string }[] = [
  {
    key: "test_files",
    label: "Tests directory or test files present",
    weight: 40,
    info: "A tests/test/__tests__/spec directory exists at root or in a monorepo workspace. We don't run them — we just look for the structure.",
  },
  {
    key: "ci_test_runner",
    label: "CI invokes a test runner",
    weight: 30,
    info: "A CI workflow file mentions pytest, jest, vitest, mocha, go test, cargo test, mvn test, rspec, or similar. Tests aren't useful if CI doesn't run them.",
  },
  {
    key: "coverage_badge",
    label: "Coverage badge in README",
    weight: 20,
    info: "README contains a codecov.io, coveralls.io, or shields.io coverage badge URL. Public coverage signals commitment to quality.",
  },
  {
    key: "coverage_config",
    label: "codecov.yml / coverage.xml present",
    weight: 10,
    info: "A codecov.yml, .codecov.yml, or coverage.xml file exists at the root. Indicates coverage is actively measured, not just badged.",
  },
];

// ─────────────────────────────────────────────────────────────────────

export default async function ScanReportPage({
  params,
}: {
  params: Promise<{ owner: string; name: string; scanId: string }>;
}) {
  const { owner, name, scanId } = await params;
  const scan = await fetchScan(scanId);
  if (!scan) notFound();

  if (scan.status !== "complete") {
    return (
      <main className="min-h-screen px-6 py-16 max-w-2xl mx-auto text-center space-y-4">
        <h1 className="text-2xl font-semibold">
          {owner}/{name}
        </h1>
        <p className="text-zinc-500">
          This scan is still <code>{scan.status}</code>.{" "}
          <Link href={`/scan/${scanId}`} className="underline">
            Watch progress
          </Link>
          .
        </p>
      </main>
    );
  }

  const grade = (scan.grade ?? "F") as Grade;
  const findings = await fetchFindings(scanId);
  const findingsByEngine = findings.reduce<Record<string, Finding[]>>((acc, f) => {
    (acc[f.engine] ??= []).push(f);
    return acc;
  }, {});

  const bd = (scan.score_breakdown ?? {}) as Record<string, unknown>;
  const failed = failedSet(scan.partial ? scan.failure_reason : undefined);
  const hygieneBd = (bd.hygiene_breakdown ?? {}) as Record<string, number>;
  const testSignalBd = (bd.test_signal_breakdown ?? {}) as Record<string, number>;

  const completed = scan.completed_at
    ? new Date(scan.completed_at).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "—";

  const overallPct = scan.overall_score ?? 0;

  return (
    <main className="min-h-screen pb-16">
      <nav className="px-6 py-5 max-w-6xl w-full mx-auto flex justify-between text-sm">
        <Link
          href="/"
          className="font-semibold tracking-tight flex items-center gap-2"
        >
          <LogoMark size={20} />
          <span>
            Stack<span className="text-indigo-600">Health</span>
          </span>
        </Link>
        <div className="flex gap-5 text-zinc-500">
          <Link href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
            Methodology
          </Link>
          <a
            href={`https://github.com/${owner}/${name}`}
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            View on GitHub →
          </a>
        </div>
      </nav>

      {/* HERO */}
      <section className="px-6 max-w-6xl mx-auto">
        <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/40 dark:bg-zinc-950/40 p-6 sm:p-8 flex flex-col sm:flex-row gap-6 sm:gap-10 items-center sm:items-start">
          <GradeBadge grade={grade} size="hero" />

          <div className="flex-1 w-full space-y-3 text-center sm:text-left">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              {owner}/{name}
            </h1>
            <div className="text-sm text-zinc-500 flex flex-wrap justify-center sm:justify-start items-center gap-x-3 gap-y-1">
              {scan.repo.language && <span>{scan.repo.language}</span>}
              {scan.repo.stars != null && (
                <span>{scan.repo.stars.toLocaleString()} ★</span>
              )}
              {scan.repo.license_spdx && <span>{scan.repo.license_spdx}</span>}
              {scan.repo.default_branch && (
                <a
                  href={`https://github.com/${owner}/${name}/tree/${scan.repo.default_branch}`}
                  className="inline-flex items-center gap-1 rounded-md border border-zinc-200 dark:border-zinc-700 px-1.5 py-0.5 font-mono text-[11px] hover:border-indigo-500 hover:text-indigo-600"
                  title="Branch scanned (default branch at scan time)"
                >
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    aria-hidden
                  >
                    <path d="M9.5 3.25a2.25 2.25 0 113.75 1.674v.351a2.5 2.5 0 01-2.5 2.5h-4a1 1 0 00-1 1v1.151a2.25 2.25 0 11-1.5 0V5.075a2.25 2.25 0 111.5 0v3.586a2.49 2.49 0 011-.211h4a1 1 0 001-1V4.924A2.25 2.25 0 019.5 3.25zM4.25 12a.75.75 0 100 1.5.75.75 0 000-1.5zM3.5 3.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zm8.25-.75a.75.75 0 100 1.5.75.75 0 000-1.5z" />
                  </svg>
                  {scan.repo.default_branch}
                </a>
              )}
              {scan.commit_sha && (
                <a
                  href={`https://github.com/${owner}/${name}/commit/${scan.commit_sha}`}
                  className="font-mono text-xs hover:text-indigo-600"
                  title={`Commit ${scan.commit_sha}`}
                >
                  {scan.commit_sha.slice(0, 8)}
                </a>
              )}
              {scan.repo.pushed_at && (
                <span
                  title={new Date(scan.repo.pushed_at).toLocaleString()}
                >
                  pushed {timeAgo(scan.repo.pushed_at)}
                </span>
              )}
            </div>

            <div>
              <div className="flex items-baseline gap-2 justify-center sm:justify-start">
                <span className="text-5xl font-bold tracking-tight tabular-nums">
                  {scan.overall_score}
                </span>
                <span className="text-zinc-500 text-lg">/ 100</span>
              </div>
              <div className="mt-2 h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
                <div
                  className={`h-full ${barColor(overallPct)} transition-all`}
                  style={{ width: `${overallPct}%` }}
                />
              </div>
            </div>

            {scan.partial && (
              <div className="rounded-lg border border-amber-300/60 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800/40 px-3 py-2 text-xs">
                <span className="font-medium text-amber-700 dark:text-amber-300">
                  Partial scan
                </span>{" "}
                <span className="text-amber-700/80 dark:text-amber-300/80">
                  — engines that didn&apos;t complete:{" "}
                  <code>{scan.failure_reason}</code>. Affected sub-scores use a
                  neutral default; see the dimension breakdowns below.
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* SUB-SCORE CARDS */}
      <section className="px-6 max-w-6xl mx-auto mt-6 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {scan.scores &&
          (
            [
              { label: "Security", value: scan.scores.security, weight: "30%" },
              { label: "Quality", value: scan.scores.quality, weight: "25%" },
              { label: "Hygiene", value: scan.scores.hygiene, weight: "25%" },
              { label: "Community", value: scan.scores.community, weight: "20%" },
            ] as const
          ).map(({ label, value, weight }) => (
            <div
              key={label}
              className="rounded-xl border border-zinc-200 dark:border-zinc-800 p-4"
            >
              <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-zinc-500">
                <span>{label}</span>
                <span>{weight} weight</span>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-3xl font-bold tabular-nums">{value}</span>
                <span className={`text-xs font-medium ${qualColor(value)}`}>
                  {qualLabel(value)}
                </span>
              </div>
              <div className="mt-2 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
                <div
                  className={`h-full ${barColor(value)}`}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          ))}
      </section>

      {/* DIMENSION BREAKDOWNS */}
      <section className="px-6 max-w-6xl mx-auto mt-10 space-y-6">
        <Dimension
          title="Security"
          info="Supply-chain + code security posture. Weighted: 40% OpenSSF Scorecard (CI hardening, branch protection, signed releases, fuzzing…), 40% Semgrep p/security-audit findings, 20% known dependency CVEs from Trivy."
          score={scan.scores?.security}
          weight="30%"
          rows={[
            {
              label: "OpenSSF Scorecard",
              detail: "Aggregate across ~18 supply-chain checks",
              info: "OpenSSF Scorecard runs ~18 checks (Branch-Protection, Code-Review, CI-Tests, Dangerous-Workflow, Dependency-Update-Tool, Fuzzing, License, Maintained, Pinned-Dependencies, SAST, Security-Policy, Signed-Releases, Token-Permissions, Vulnerabilities, Webhooks, etc.). We take the aggregate 0–10, multiply by 10 to get 0–100.",
              value: num(bd.scorecard),
              failed: failed.has("scorecard"),
            },
            {
              label: "Semgrep p/security-audit",
              detail: "LoC-normalised SAST finding density",
              info: "Semgrep runs the p/security-audit ruleset (~150 rules). Each finding is weighted by severity (ERROR×3, WARNING×2, INFO×1), then divided by (LoC/1000+1) so a large repo isn't penalised for the same absolute count. 0 findings = 100; the score drops as density rises.",
              value: num(bd.semgrep),
              failed: failed.has("semgrep"),
            },
            {
              label: "Dependency CVEs (Trivy)",
              detail: "Critical/High/Medium/Low penalty",
              info: "Trivy scans lockfiles + manifests for known CVEs. We start at 100 and subtract: Critical −25, High −10, Medium −3, Low −1. 0 vulns = 100.",
              value: num(bd.dependencies),
              failed: failed.has("trivy"),
            },
          ]}
        />

        <Dimension
          title="Quality"
          info="Internal code quality signals. Weighted: 30% complexity, 25% lint density, 20% duplication, 15% test signal (we look for tests + CI runner + coverage), 10% file size (no mega-files >1000 LoC)."
          score={scan.scores?.quality}
          weight="25%"
          rows={[
            {
              label: "Cyclomatic complexity (lizard)",
              detail: `Avg complexity: ${num(bd.avg_complexity) ?? "—"}`,
              info: "Lizard measures cyclomatic complexity per function (CCN = decision points + 1). We take the repo-wide average. Avg ≤5 = 100, then drops linearly until avg ≥15 = 0. Lower is more readable and easier to test.",
              value: num(bd.complexity),
              failed: failed.has("complexity"),
            },
            {
              label: "Lint density",
              detail: `${num(bd.lint_issues) ?? 0} issues across detected languages`,
              info: "We run the language-native linter on detected languages (ruff for Python, eslint for JS/TS, golangci-lint for Go, etc.) and count issues per 1000 lines. 0 issues = 100. The score drops as issue density rises.",
              value: num(bd.lint_density),
              failed: failed.has("lint"),
            },
            {
              label: "Duplication (jscpd)",
              detail:
                num(bd.duplication_percent) != null
                  ? `${num(bd.duplication_percent)}% duplicated`
                  : "—",
              info: "jscpd detects copy-paste blocks across the codebase using token-level matching (default: ≥50 tokens, ≥5 lines). We exclude node_modules, dist, build, lockfiles, fixtures and *.min.js. 0% duplication = 100; each 1% costs 5 points.",
              value: num(bd.duplication),
              failed: failed.has("duplication"),
            },
            {
              label: "Test signal",
              detail: "See checklist below — we don't run tests, we look for them",
              info: "We don't execute tests (sandbox rule). Instead we score 4 signals: tests directory present (40), CI invokes a test runner (30), coverage badge in README (20), coverage config file at root (10). Total /100. Breakdown below.",
              value: num(bd.test_signal),
              failed: failed.has("test_signal"),
            },
            {
              label: "File size",
              detail: `${num(bd.mega_files) ?? 0} files over 1000 LoC`,
              info: "Count of source files exceeding 1000 lines (per cloc, which excludes blanks and comments). Mega-files are hard to test, review, and modify safely. 0 = 100; each mega-file costs 5 points.",
              value: num(bd.file_size),
              failed: failed.has("cloc"),
            },
          ]}
        >
          <ChecklistBlock
            heading="Test signal breakdown"
            items={TEST_SIGNAL_ITEMS}
            scores={testSignalBd}
            outOf={100}
          />
        </Dimension>

        <Dimension
          title="Hygiene"
          info="OSS housekeeping checklist — 13 binary items totaling 100 points (README, LICENSE, CONTRIBUTING, CoC, SECURITY, CI, PR-triggered CI, tests dir, .gitignore, GH description, GH topics, recent commit). Pure discipline; the easiest dimension to max."
          score={scan.scores?.hygiene}
          weight="25%"
          rows={[]}
        >
          <ChecklistBlock
            heading="Hygiene checklist"
            items={HYGIENE_ITEMS}
            scores={hygieneBd}
            outOf={100}
          />
        </Dimension>

        <Dimension
          title="Community"
          info="Health of the community around the project. Weighted: 35% activity (recency + commit volume), 25% contributors (distinct authors in 365d), 20% popularity (star count, log-scaled), 20% responsiveness (median issue first-response time)."
          score={scan.scores?.community}
          weight="20%"
          rows={[
            {
              label: "Activity",
              detail: "Recency + commits in last 90 days",
              info: "Combines `pushed_at` recency with commit volume. Last commit >365d ago = 0. Last commit 181–365d = 30. Within 180d: 40 + 2×commits-in-90d, capped at 100.",
              value: num(bd.activity),
              failed: failed.has("community"),
            },
            {
              label: "Contributors",
              detail: "Log₂ of distinct authors in last 365 days",
              info: "Distinct authors with at least one commit in the last 365 days. Score = log₂(count + 1) × 25, capped at 100. So 1=25, 3=50, 7=75, 15=100. Logarithmic so a project doesn't need hundreds of contributors to score well.",
              value: num(bd.contributors),
              failed: failed.has("community"),
            },
            {
              label: "Popularity",
              detail: `Log₁₀ of stars (${num(bd.stars) ?? "—"})`,
              info: "Score = log₁₀(stars + 1) × 25, capped at 100. So 100 stars = 50, 1000 stars = 75, 10000 stars = 100. Logarithmic so very early projects aren't punished, but a perfect score requires real adoption.",
              value: num(bd.popularity),
              failed: failed.has("community"),
            },
            {
              label: "Responsiveness",
              detail: "Median time-to-first-response on issues, last 90 days",
              info: "Median hours from issue creation to first non-author comment, sampled from up to 20 issues opened in the last 90 days. <24h = 100, <72h = 80, <168h (1wk) = 60, <720h (30d) = 30, else 0. No issues in 90d = neutral 70.",
              value: num(bd.responsiveness),
              failed: failed.has("community"),
            },
          ]}
        />
      </section>

      {/* SCAN INPUT (LoC + languages) */}
      <section className="px-6 max-w-6xl mx-auto mt-10">
        <h2 className="text-lg font-semibold mb-3">Scan inputs</h2>
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-200 dark:divide-zinc-800 text-sm">
          <Row k="Total lines of code" v={num(bd.loc)?.toLocaleString() ?? "—"} />
          <Row
            k="Languages detected"
            v={
              Array.isArray(bd.languages) && bd.languages.length > 0
                ? (bd.languages as string[]).join(", ")
                : "—"
            }
          />
          <Row k="Stars" v={num(bd.stars)?.toLocaleString() ?? "—"} />
          <Row k="Files over 1000 LoC" v={String(num(bd.mega_files) ?? 0)} />
        </div>
      </section>

      {/* FINDINGS */}
      {Object.keys(findingsByEngine).length > 0 && (
        <section className="px-6 max-w-6xl mx-auto mt-10">
          <h2 className="text-lg font-semibold mb-3">
            Findings{" "}
            <span className="text-zinc-500 text-sm font-normal">
              ({findings.length})
            </span>
          </h2>
          <div className="space-y-3">
            {Object.entries(findingsByEngine).map(([engine, items]) => {
              const sorted = items.sort(
                (a, b) =>
                  SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity),
              );
              return (
                <details
                  key={engine}
                  className="rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden"
                  open={engine !== "hygiene"}
                >
                  <summary className="px-4 py-3 cursor-pointer flex justify-between items-center bg-zinc-50 dark:bg-zinc-900">
                    <span className="font-medium capitalize">{engine}</span>
                    <span className="text-zinc-500 text-xs">
                      {items.length} finding{items.length === 1 ? "" : "s"}
                    </span>
                  </summary>
                  <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
                    {sorted.slice(0, 50).map((f) => (
                      <li key={f.id} className="px-4 py-3 text-sm">
                        <div className="flex items-start gap-3">
                          <SeverityPill severity={f.severity} />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{f.title}</div>
                            {f.message && (
                              <div className="text-zinc-500 text-xs mt-1 line-clamp-2">
                                {f.message}
                              </div>
                            )}
                            {f.file_path && (
                              <div className="font-mono text-xs text-zinc-400 mt-1 truncate">
                                {f.file_path}
                                {f.line_number ? `:${f.line_number}` : ""}
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                    {items.length > 50 && (
                      <li className="px-4 py-3 text-xs text-zinc-500">
                        Showing 50 of {items.length}. Raw output linked below.
                      </li>
                    )}
                  </ul>
                </details>
              );
            })}
          </div>
        </section>
      )}

      {/* REPRODUCIBILITY */}
      <section className="px-6 max-w-6xl mx-auto mt-10">
        <h2 className="text-lg font-semibold mb-3">Reproducibility</h2>
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-200 dark:divide-zinc-800 text-sm">
          <Row k="Formula version" v={<code>{scan.formula_version}</code>} />
          <Row
            k="Branch scanned"
            v={
              scan.repo.default_branch ? (
                <a
                  href={`https://github.com/${owner}/${name}/tree/${scan.repo.default_branch}`}
                  className="font-mono text-xs hover:text-indigo-600"
                >
                  {scan.repo.default_branch}
                </a>
              ) : (
                "—"
              )
            }
          />
          <Row
            k="Commit SHA"
            v={
              scan.commit_sha ? (
                <a
                  href={`https://github.com/${owner}/${name}/commit/${scan.commit_sha}`}
                  className="font-mono text-xs hover:text-indigo-600"
                  title={scan.commit_sha}
                >
                  {scan.commit_sha.slice(0, 12)}…
                </a>
              ) : (
                "—"
              )
            }
          />
          <Row
            k="Last push to repo"
            v={
              scan.repo.pushed_at
                ? `${new Date(scan.repo.pushed_at).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })} (${timeAgo(scan.repo.pushed_at)})`
                : "—"
            }
          />
          <Row k="Completed" v={completed} />
          <Row
            k="Tool versions"
            v={
              scan.tool_versions ? (
                <span className="font-mono text-xs">
                  {Object.entries(scan.tool_versions)
                    .map(([k, v]) => `${k}@${v}`)
                    .join(" · ")}
                </span>
              ) : (
                "—"
              )
            }
          />
        </div>
      </section>

      {/* EMBED */}
      <EmbedCard
        owner={owner}
        name={name}
        apiUrl={
          process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        }
        siteUrl={
          process.env.NEXT_PUBLIC_SITE_URL ?? "https://stackhealth.dev"
        }
      />

      <footer className="px-6 max-w-6xl mx-auto mt-12 pt-6 border-t border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500">
        <Link href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
          How is this scored?
        </Link>{" "}
        · Formula {scan.formula_version} · Open source
      </footer>
    </main>
  );
}

// ─────────────────────────────────────────────────────────────────────
// presentation primitives

function Dimension({
  title,
  info,
  score,
  weight,
  rows,
  children,
}: {
  title: string;
  info?: string;
  score?: number;
  weight: string;
  rows: {
    label: string;
    detail?: string;
    info?: string;
    value: number | null;
    failed?: boolean;
  }[];
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-800">
      <header className="rounded-t-xl px-5 py-3 bg-zinc-50 dark:bg-zinc-900 flex items-center justify-between">
        <h2 className="font-semibold tracking-tight flex items-center gap-2">
          {title}
          {info && <InfoTip text={info} />}
        </h2>
        <div className="flex items-baseline gap-2">
          {score != null && (
            <span className="text-xl font-bold tabular-nums">{score}</span>
          )}
          <span className="text-xs text-zinc-500">/ 100 · weight {weight}</span>
        </div>
      </header>

      {rows.length > 0 && (
        <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {rows.map((r) => (
            <li key={r.label} className="px-5 py-3 text-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-medium flex items-center gap-1.5">
                    {r.label}
                    {r.info && <InfoTip text={r.info} />}
                  </div>
                  {r.detail && (
                    <div className="text-xs text-zinc-500 mt-0.5">{r.detail}</div>
                  )}
                </div>
                <div className="text-right shrink-0">
                  {r.failed ? (
                    <span className="text-xs text-amber-600">⚠ engine skipped</span>
                  ) : r.value != null ? (
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
                        <div
                          className={`h-full ${barColor(r.value)}`}
                          style={{ width: `${r.value}%` }}
                        />
                      </div>
                      <span className="tabular-nums font-medium w-10">
                        {r.value}
                      </span>
                    </div>
                  ) : (
                    <span className="text-zinc-400">—</span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {children && <div className="px-5 py-4 bg-zinc-50/50 dark:bg-zinc-950/40">{children}</div>}
    </div>
  );
}

function ChecklistBlock({
  heading,
  items,
  scores,
}: {
  heading: string;
  items: { key: string; label: string; weight: number; info?: string }[];
  scores: Record<string, number>;
  outOf: number;
}) {
  return (
    <div>
      <div className="text-xs font-medium text-zinc-500 mb-3 uppercase tracking-wider">
        {heading}
      </div>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
        {items.map(({ key, label, weight, info }) => {
          const earned = scores[key] ?? 0;
          const passed = earned > 0;
          return (
            <li key={key} className="flex items-center gap-2">
              {passed ? (
                <span className="w-4 h-4 rounded-full bg-emerald-500 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                  ✓
                </span>
              ) : (
                <span className="w-4 h-4 rounded-full bg-zinc-300 dark:bg-zinc-700 text-zinc-500 text-[10px] font-bold flex items-center justify-center shrink-0">
                  ✗
                </span>
              )}
              <span className={passed ? "" : "text-zinc-500 line-through decoration-zinc-400/50"}>
                {label}
              </span>
              {info && <InfoTip text={info} />}
              <span className="ml-auto text-xs text-zinc-400 tabular-nums">
                {passed ? `+${earned}` : `0 / ${weight}`}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/**
 * Compact, accessible info tooltip. Uses native title for screen readers
 * + a styled hover popover for sighted users. No JS state, no portal —
 * pure CSS group-hover.
 */
function InfoTip({ text }: { text: string }) {
  return (
    <span
      className="relative inline-flex items-center group/info shrink-0"
      tabIndex={0}
      aria-label={text}
    >
      <span
        className="w-3.5 h-3.5 rounded-full border border-zinc-400 dark:border-zinc-500 text-zinc-500 dark:text-zinc-400 text-[9px] font-semibold flex items-center justify-center cursor-help select-none hover:border-zinc-700 hover:text-zinc-700 dark:hover:border-zinc-200 dark:hover:text-zinc-200"
        title={text}
      >
        i
      </span>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-0 top-full mt-2 w-64 max-w-[min(16rem,calc(100vw-2rem))] px-3 py-2 rounded-lg bg-zinc-900 text-zinc-100 dark:bg-zinc-100 dark:text-zinc-900 text-xs font-normal leading-relaxed shadow-lg ring-1 ring-zinc-700/40 dark:ring-zinc-300/40 opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible group-focus/info:opacity-100 group-focus/info:visible transition-opacity z-50 normal-case tracking-normal whitespace-normal text-left"
      >
        {text}
      </span>
    </span>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5">
      <span className="text-zinc-500">{k}</span>
      <span className="text-right">{v}</span>
    </div>
  );
}

function SeverityPill({ severity }: { severity: string }) {
  const color: Record<string, string> = {
    critical: "bg-rose-700 text-white",
    high: "bg-red-500 text-white",
    medium: "bg-amber-500 text-white",
    low: "bg-zinc-400 text-white",
    info: "bg-zinc-300 text-zinc-800",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${
        color[severity] ?? color.info
      }`}
    >
      {severity}
    </span>
  );
}
