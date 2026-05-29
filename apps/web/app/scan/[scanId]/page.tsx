"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";
import { getScan, type Scan } from "@/lib/api";

const PHASES: Record<string, { label: string; pct: number }> = {
  queued: { label: "Queued", pct: 5 },
  cloning: { label: "Cloning repository", pct: 20 },
  analyzing: { label: "Running analyzers", pct: 60 },
  scoring: { label: "Computing scores", pct: 90 },
  complete: { label: "Complete", pct: 100 },
  failed: { label: "Failed", pct: 100 },
};

export default function ScanProgressPage({
  params,
}: {
  params: Promise<{ scanId: string }>;
}) {
  const { scanId } = use(params);
  const router = useRouter();
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const started = Date.now();
    const tick = setInterval(() => setElapsed((Date.now() - started) / 1000), 250);

    async function poll() {
      try {
        const data = await getScan(scanId);
        if (cancelled) return;
        if (data.status === "complete") {
          // Hard navigate so we never flash this page after the scan finishes.
          // router.replace can occasionally lose a tick if the report page
          // does its own data fetching during navigation.
          window.location.replace(
            `/r/${data.repo.owner}/${data.repo.name}/${data.id}`,
          );
          return;
        }
        setScan(data);
        if (data.status === "failed") {
          return;
        }
        setTimeout(poll, 2000);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Polling failed");
      }
    }
    poll();
    return () => {
      cancelled = true;
      clearInterval(tick);
    };
  }, [scanId, router]);

  const phase = scan ? PHASES[scan.status] : PHASES.queued;
  const isInProgress = scan
    ? !["complete", "failed"].includes(scan.status)
    : true;
  const reportUrl =
    typeof window !== "undefined" && scan?.repo
      ? `${window.location.origin}/r/${scan.repo.owner}/${scan.repo.name}/${scan.id}`
      : "";

  async function copyUrl() {
    if (!reportUrl) return;
    try {
      await navigator.clipboard.writeText(reportUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-lg w-full space-y-6">
        {isInProgress && (
          // Email is required at submit, so every in-progress scan has a
          // notification target. Lead with the calmer "we'll email you"
          // confirmation; the progress bar below is for users who choose
          // to stay on the page anyway.
          <div className="rounded-xl border border-emerald-300 bg-emerald-50 dark:border-emerald-800/40 dark:bg-emerald-950/30 p-5 text-center space-y-2">
            <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500 text-white text-lg font-bold">
              ✓
            </div>
            <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
              All set — we&apos;ll email you when it&apos;s done.
            </p>
            <p className="text-xs text-emerald-700/80 dark:text-emerald-300/80">
              You can close this tab now. The scan keeps running and your
              report will be in your inbox within a few minutes.
            </p>
          </div>
        )}

        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold">
            {scan?.repo
              ? `${scan.repo.owner}/${scan.repo.name}`
              : "Preparing scan…"}
          </h1>
          <p className="text-sm text-zinc-500">{phase.label}</p>
        </div>

        <div className="h-2 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
          <div
            className="h-full bg-indigo-600 transition-all duration-700"
            style={{ width: `${phase.pct}%` }}
          />
        </div>

        <div className="flex justify-between text-xs text-zinc-500 font-mono">
          <span>{Math.floor(elapsed)}s elapsed</span>
          <span>scan {scanId.slice(0, 8)}…</span>
        </div>

        {scan?.status === "failed" ? (
          <div className="rounded-lg border border-red-300 bg-red-50 dark:bg-red-950 p-4 text-sm">
            <p className="font-medium text-red-700 dark:text-red-300">
              Scan failed
            </p>
            <p className="text-red-600 dark:text-red-400 mt-1">
              {scan.failure_reason ?? "Unknown error"}
            </p>
          </div>
        ) : (
          // Bookmark URL — handy as a permalink even when email is set,
          // so the user can return to the same page from another device.
          isInProgress && reportUrl && (
            <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 space-y-2">
              <p className="text-xs text-zinc-500">
                Bookmark or share the report URL — it&apos;ll point to your
                results when they&apos;re ready.
              </p>
              <div className="flex gap-2 items-stretch">
                <input
                  readOnly
                  value={reportUrl}
                  onFocus={(e) => e.currentTarget.select()}
                  className="flex-1 min-w-0 px-2 py-1.5 text-xs font-mono rounded border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950"
                />
                <button
                  type="button"
                  onClick={copyUrl}
                  className="px-3 py-1.5 text-xs font-medium rounded bg-indigo-600 hover:bg-indigo-700 text-white whitespace-nowrap"
                >
                  {copied ? "Copied ✓" : "Copy"}
                </button>
              </div>
            </div>
          )
        )}

        {error && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950 p-4 text-sm">
            <p className="font-medium text-amber-700 dark:text-amber-300">
              Polling problem
            </p>
            <p className="text-amber-600 dark:text-amber-400 mt-1">{error}</p>
          </div>
        )}

        <p className="text-center text-xs text-zinc-400">
          Scans usually take 30–90 seconds — sometimes a few minutes for
          repos we&apos;ve never seen.
        </p>
      </div>
    </main>
  );
}
