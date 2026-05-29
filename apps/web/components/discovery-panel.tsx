"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getRecentScans,
  getTopScans,
  type DiscoverScan,
} from "@/lib/api";

type Tab = "recent" | "top";

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

function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 86400 * 30) return `${Math.floor(seconds / 86400)}d ago`;
  return `${Math.floor(seconds / 86400 / 30)}mo ago`;
}

export function DiscoveryPanel() {
  const [tab, setTab] = useState<Tab>("recent");
  const [recent, setRecent] = useState<DiscoverScan[] | null>(null);
  const [top, setTop] = useState<DiscoverScan[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Fire both in parallel — small, cached, cheap.
        const [r, t] = await Promise.all([getRecentScans(10), getTopScans(10)]);
        if (cancelled) return;
        setRecent(r.scans);
        setTop(t.scans);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    }
    load();
    // Refresh every 60s — matches CDN cache TTL on the backend.
    const id = setInterval(load, 60_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const items = tab === "recent" ? recent : top;

  return (
    <aside className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white/40 dark:bg-zinc-950/30 overflow-hidden">
      <div className="flex border-b border-zinc-200 dark:border-zinc-800">
        <button
          type="button"
          onClick={() => setTab("recent")}
          className={`flex-1 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors ${
            tab === "recent"
              ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px"
              : "text-zinc-500 hover:text-zinc-800 dark:hover:text-white"
          }`}
        >
          Recent
        </button>
        <button
          type="button"
          onClick={() => setTab("top")}
          className={`flex-1 px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors ${
            tab === "top"
              ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px"
              : "text-zinc-500 hover:text-zinc-800 dark:hover:text-white"
          }`}
        >
          Leaderboard
        </button>
      </div>

      <div className="px-1 py-1">
        {error ? (
          <p className="px-3 py-6 text-xs text-zinc-500 text-center">
            Couldn&apos;t load. Refresh?
          </p>
        ) : items === null ? (
          <SkeletonRows />
        ) : items.length === 0 ? (
          <p className="px-3 py-6 text-xs text-zinc-500 text-center">
            No scans yet. Be the first.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200/70 dark:divide-zinc-800/70">
            {items.map((scan, i) => (
              <li key={scan.scan_id}>
                <Link
                  href={`/r/${scan.owner}/${scan.name}/${scan.scan_id}`}
                  className="flex items-center gap-3 px-3 py-2.5 hover:bg-zinc-100/70 dark:hover:bg-zinc-900/60 rounded-lg"
                >
                  {tab === "top" && (
                    <span className="w-5 text-xs text-zinc-400 tabular-nums text-right">
                      {i + 1}
                    </span>
                  )}
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 ${
                      GRADE_COLOR[scan.grade ?? "F"] ?? "bg-zinc-400"
                    }`}
                    aria-label={`Grade ${scan.grade}`}
                  >
                    {scan.grade}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">
                      {scan.owner}/{scan.name}
                    </div>
                    <div className="text-[11px] text-zinc-500 truncate">
                      {scan.language ?? "—"}
                      {scan.stars != null && scan.stars > 0
                        ? ` · ${scan.stars.toLocaleString()} ★`
                        : ""}
                      {tab === "recent" && scan.completed_at
                        ? ` · ${timeAgo(scan.completed_at)}`
                        : ""}
                    </div>
                  </div>
                  <span className="text-sm font-semibold tabular-nums text-zinc-700 dark:text-zinc-200">
                    {scan.overall_score ?? "—"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

function SkeletonRows() {
  return (
    <ul className="divide-y divide-zinc-200/70 dark:divide-zinc-800/70">
      {Array.from({ length: 6 }).map((_, i) => (
        <li
          key={i}
          className="flex items-center gap-3 px-3 py-2.5 animate-pulse"
        >
          <span className="w-7 h-7 rounded-full bg-zinc-200 dark:bg-zinc-800" />
          <div className="flex-1 space-y-1.5">
            <div className="h-3 w-2/3 rounded bg-zinc-200 dark:bg-zinc-800" />
            <div className="h-2.5 w-1/3 rounded bg-zinc-200/70 dark:bg-zinc-800/70" />
          </div>
          <div className="w-6 h-4 rounded bg-zinc-200 dark:bg-zinc-800" />
        </li>
      ))}
    </ul>
  );
}
