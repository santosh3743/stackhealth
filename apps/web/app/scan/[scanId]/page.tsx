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

  useEffect(() => {
    let cancelled = false;
    const started = Date.now();
    const tick = setInterval(() => setElapsed((Date.now() - started) / 1000), 250);

    async function poll() {
      try {
        const data = await getScan(scanId);
        if (cancelled) return;
        setScan(data);
        if (data.status === "complete") {
          router.replace(`/r/${data.repo.owner}/${data.repo.name}/${data.id}`);
          return;
        }
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

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-lg w-full space-y-6">
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

        {scan?.status === "failed" && (
          <div className="rounded-lg border border-red-300 bg-red-50 dark:bg-red-950 p-4 text-sm">
            <p className="font-medium text-red-700 dark:text-red-300">
              Scan failed
            </p>
            <p className="text-red-600 dark:text-red-400 mt-1">
              {scan.failure_reason ?? "Unknown error"}
            </p>
          </div>
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
          Scans usually take 30–90 seconds.
        </p>
      </div>
    </main>
  );
}
