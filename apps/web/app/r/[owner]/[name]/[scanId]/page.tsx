import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { GradeBadge, type Grade } from "@/components/grade-badge";
import { ScoreCard } from "@/components/score-card";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const revalidate = 3600;

type Scan = {
  id: string;
  repo: { owner: string; name: string; stars?: number; language?: string };
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
    const r = await fetch(`${API_BASE}/api/scans/${scanId}/findings?limit=100`, {
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

function qualLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 75) return "Good";
  if (score >= 60) return "Fair";
  if (score >= 40) return "Weak";
  return "Poor";
}

const SEV_ORDER = ["critical", "high", "medium", "low", "info"];

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
          This scan is still <code>{scan.status}</code>. Watch it live at{" "}
          <Link href={`/scan/${scanId}`} className="underline">
            /scan/{scanId.slice(0, 8)}…
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

  const breakdown = (scan.score_breakdown ?? {}) as Record<string, number | string>;
  const completed = scan.completed_at
    ? new Date(scan.completed_at).toLocaleString()
    : "—";

  return (
    <main className="min-h-screen px-6 py-10 max-w-5xl mx-auto">
      <nav className="flex justify-between text-sm mb-8">
        <Link href="/" className="font-semibold tracking-tight">
          Stack<span className="text-indigo-600">Health</span>
        </Link>
        <div className="flex gap-4 text-zinc-500">
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

      <header className="flex flex-col sm:flex-row items-center gap-8 mb-12">
        <GradeBadge grade={grade} size="hero" />
        <div className="text-center sm:text-left">
          <h1 className="text-3xl font-bold">
            {owner}/{name}
          </h1>
          <p className="text-zinc-500 mt-1">
            {scan.repo.language ?? "—"} ·{" "}
            {scan.repo.stars != null ? `${scan.repo.stars.toLocaleString()} ★` : "—"}
          </p>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-5xl font-bold tracking-tight">
              {scan.overall_score}
            </span>
            <span className="text-zinc-500">/ 100</span>
          </div>
          {scan.partial && (
            <p className="mt-2 text-xs text-amber-600">
              Partial scan — some engines couldn&apos;t run:{" "}
              <code>{scan.failure_reason}</code>
            </p>
          )}
        </div>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
        {scan.scores && (
          <>
            <ScoreCard
              label="Security"
              score={scan.scores.security}
              qualitative={qualLabel(scan.scores.security)}
            />
            <ScoreCard
              label="Quality"
              score={scan.scores.quality}
              qualitative={qualLabel(scan.scores.quality)}
            />
            <ScoreCard
              label="Hygiene"
              score={scan.scores.hygiene}
              qualitative={qualLabel(scan.scores.hygiene)}
            />
            <ScoreCard
              label="Community"
              score={scan.scores.community}
              qualitative={qualLabel(scan.scores.community)}
            />
          </>
        )}
      </section>

      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4">Breakdown</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
          {Object.entries(breakdown).map(([k, v]) => (
            <div
              key={k}
              className="flex justify-between border-b border-zinc-200 dark:border-zinc-800 py-1.5"
            >
              <span className="text-zinc-500">{k}</span>
              <span className="font-mono">{String(v)}</span>
            </div>
          ))}
        </div>
      </section>

      {Object.keys(findingsByEngine).length > 0 && (
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-4">Findings</h2>
          {Object.entries(findingsByEngine).map(([engine, items]) => (
            <details
              key={engine}
              className="mb-3 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden"
            >
              <summary className="px-4 py-3 cursor-pointer bg-zinc-50 dark:bg-zinc-900 flex justify-between">
                <span className="font-medium capitalize">{engine}</span>
                <span className="text-zinc-500 text-sm">{items.length} findings</span>
              </summary>
              <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {items
                  .sort(
                    (a, b) =>
                      SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity),
                  )
                  .slice(0, 25)
                  .map((f) => (
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
                            <div className="font-mono text-xs text-zinc-400 mt-1">
                              {f.file_path}
                              {f.line_number ? `:${f.line_number}` : ""}
                            </div>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
              </ul>
            </details>
          ))}
        </section>
      )}

      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4">Reproducibility</h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-y-2 text-sm">
          <dt className="text-zinc-500">Formula version</dt>
          <dd className="font-mono">{scan.formula_version}</dd>
          <dt className="text-zinc-500">Commit SHA</dt>
          <dd className="font-mono">{scan.commit_sha?.slice(0, 12) ?? "—"}</dd>
          <dt className="text-zinc-500">Completed</dt>
          <dd>{completed}</dd>
          <dt className="text-zinc-500">Tool versions</dt>
          <dd className="font-mono text-xs">
            {scan.tool_versions
              ? Object.entries(scan.tool_versions)
                  .map(([k, v]) => `${k}@${v}`)
                  .join(" · ")
              : "—"}
          </dd>
        </dl>
      </section>

      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-3">Embed</h2>
        <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-3 bg-zinc-50 dark:bg-zinc-950">
          <code className="text-xs break-all">
            {`![StackHealth](${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/r/${owner}/${name}/badge.svg)`}
          </code>
        </div>
      </section>

      <footer className="text-xs text-zinc-500 border-t border-zinc-200 dark:border-zinc-800 pt-6">
        <Link href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
          How is this scored?
        </Link>{" "}
        · Formula {scan.formula_version} · Open source
      </footer>
    </main>
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
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide ${
        color[severity] ?? color.info
      }`}
    >
      {severity}
    </span>
  );
}
