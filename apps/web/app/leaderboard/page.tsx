import Link from "next/link";
import type { Metadata } from "next";

import { LogoMark } from "@/components/logo-mark";

const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "Leaderboard — StackHealth",
  description:
    "The highest-graded public repos scored by StackHealth's open formula. Updated every minute.",
};

type Row = {
  scan_id: string;
  owner: string;
  name: string;
  grade?: string | null;
  overall_score?: number | null;
  language?: string | null;
  stars?: number | null;
  completed_at?: string | null;
};

// Mirrors the grade tints used elsewhere — keep the palette consistent.
const GRADE_COLOR: Record<string, string> = {
  "A+": "bg-emerald-500",
  A: "bg-emerald-500",
  "A-": "bg-green-500",
  "B+": "bg-green-500",
  B: "bg-lime-500",
  "B-": "bg-yellow-500",
  "C+": "bg-yellow-500",
  C: "bg-orange-500",
  "C-": "bg-orange-500",
  D: "bg-red-500",
  F: "bg-rose-700",
};

const LANG_FILTERS = [
  "All",
  "Python",
  "TypeScript",
  "JavaScript",
  "Go",
  "Rust",
  "Java",
  "C++",
  "Ruby",
];

const STARS_FILTERS = [
  { label: "All", value: 0 },
  { label: "100+ ★", value: 100 },
  { label: "1k+ ★", value: 1000 },
  { label: "10k+ ★", value: 10_000 },
];

async function fetchTop(
  language: string | undefined,
  minStars: number,
): Promise<Row[]> {
  const lang = language ? `&language=${encodeURIComponent(language)}` : "";
  const url = `${API_BASE}/api/discover/top?limit=50&min_stars=${minStars}${lang}`;
  try {
    const r = await fetch(url, { next: { revalidate: 60 } });
    if (!r.ok) return [];
    const data = await r.json();
    return data.scans ?? [];
  } catch {
    return [];
  }
}

export default async function LeaderboardPage({
  searchParams,
}: {
  searchParams: Promise<{ language?: string; stars?: string }>;
}) {
  const sp = await searchParams;
  const language = sp.language && sp.language !== "All" ? sp.language : undefined;
  const minStars = Number(sp.stars ?? 0) || 0;

  const rows = await fetchTop(language, minStars);

  // Build the `query` object for next/link. Typed-routes refuses raw
  // template-literal hrefs, so we hand it a UrlObject instead.
  const buildQuery = (overrides: {
    language?: string;
    stars?: number;
  }): Record<string, string> => {
    const out: Record<string, string> = {};
    const lang = overrides.language ?? language;
    const stars = overrides.stars ?? (minStars || undefined);
    if (lang && lang !== "All") out.language = String(lang);
    if (stars) out.stars = String(stars);
    return out;
  };

  return (
    <main className="min-h-screen px-6 py-12 max-w-5xl mx-auto">
      <nav className="text-sm mb-10">
        <Link
          href="/"
          className="font-semibold tracking-tight inline-flex items-center gap-2"
        >
          <LogoMark size={20} />
          <span>
            Stack<span className="text-indigo-600">Health</span>
          </span>
        </Link>
        <span className="text-zinc-400 mx-2">/</span>
        <span className="text-zinc-500">Leaderboard</span>
      </nav>

      <header className="mb-10 space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">
          The leaderboard
        </h1>
        <p className="text-zinc-600 dark:text-zinc-300 max-w-2xl">
          The highest-graded public repos scored by{" "}
          <Link href="/methodology" className="underline">
            our open formula
          </Link>
          . Same weights, same engines, every repo. Updated every minute.
        </p>
      </header>

      {/* Filters */}
      <div className="space-y-3 mb-8">
        <FilterRow label="Language">
          {LANG_FILTERS.map((l) => {
            const active =
              (l === "All" && !language) || l === language;
            return (
              <Link
                key={l}
                href={{ pathname: "/leaderboard", query: buildQuery({ language: l }) }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  active
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300 hover:border-indigo-500 hover:text-indigo-600"
                }`}
              >
                {l}
              </Link>
            );
          })}
        </FilterRow>
        <FilterRow label="Stars">
          {STARS_FILTERS.map((f) => {
            const active = f.value === minStars;
            return (
              <Link
                key={f.label}
                href={{ pathname: "/leaderboard", query: buildQuery({ stars: f.value || undefined }) }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  active
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300 hover:border-indigo-500 hover:text-indigo-600"
                }`}
              >
                {f.label}
              </Link>
            );
          })}
        </FilterRow>
      </div>

      {/* Table */}
      {rows.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 px-6 py-16 text-center text-sm text-zinc-500">
          No repos match these filters yet.{" "}
          <Link href="/" className="text-indigo-600 underline">
            Scan one
          </Link>{" "}
          to seed it.
        </div>
      ) : (
        <ol className="rounded-xl border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-200 dark:divide-zinc-800 overflow-hidden bg-white dark:bg-zinc-950">
          {rows.map((scan, i) => (
            <li key={scan.scan_id}>
              <Link
                href={`/r/${scan.owner}/${scan.name}`}
                className="flex items-center gap-4 px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-900/40 transition-colors"
              >
                <span className="w-7 text-sm text-zinc-400 tabular-nums text-right">
                  {i + 1}
                </span>
                <span
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 ${
                    GRADE_COLOR[scan.grade ?? "F"] ?? "bg-zinc-400"
                  }`}
                  aria-label={`Grade ${scan.grade}`}
                >
                  {scan.grade}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate">
                    {scan.owner}/{scan.name}
                  </div>
                  <div className="text-xs text-zinc-500 truncate">
                    {scan.language ?? "—"}
                    {scan.stars != null && scan.stars > 0
                      ? ` · ${scan.stars.toLocaleString()} ★`
                      : ""}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-lg font-semibold tabular-nums">
                    {scan.overall_score ?? "—"}
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400">
                    / 100
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ol>
      )}

      <footer className="mt-10 text-xs text-zinc-500 flex flex-wrap gap-x-4 gap-y-1">
        <span>Top {rows.length} of all scanned repos</span>
        <Link href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
          How is this scored?
        </Link>
        <Link href="/" className="hover:text-zinc-900 dark:hover:text-white">
          Score your repo →
        </Link>
      </footer>
    </main>
  );
}

function FilterRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span className="text-xs uppercase tracking-wider text-zinc-400 w-20 shrink-0">
        {label}
      </span>
      <div className="flex gap-2 flex-wrap">{children}</div>
    </div>
  );
}
