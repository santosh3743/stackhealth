"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";
import { getScan, setScanNotifyEmail, type Scan } from "@/lib/api";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
  const [emailDraft, setEmailDraft] = useState("");
  const [emailSaving, setEmailSaving] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSaved, setEmailSaved] = useState(false);

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

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault();
    setEmailError(null);
    const trimmed = emailDraft.trim();
    if (!EMAIL_RE.test(trimmed)) {
      setEmailError("That doesn't look like a valid email");
      return;
    }
    setEmailSaving(true);
    try {
      await setScanNotifyEmail(scanId, trimmed);
      setEmailSaved(true);
      setScan((s) => (s ? { ...s, notify_enabled: true } : s));
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "Could not save email");
    } finally {
      setEmailSaving(false);
    }
  }

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
          // Shareable / bookmark URL block — only while the scan is still
          // in progress. Once it's complete, we redirect (in `poll()` above).
          isInProgress && reportUrl && (
            <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 space-y-2">
              <p className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                You can close this tab and come back later
              </p>
              <p className="text-xs text-zinc-500">
                The scan continues running. Bookmark or copy this URL — your
                report will be here when it&apos;s done.
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

              {/* Email opt-in / opt-out */}
              <div className="pt-3 mt-1 border-t border-zinc-200 dark:border-zinc-800">
                {scan?.notify_enabled || emailSaved ? (
                  <p className="text-xs text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                    <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 text-white text-[9px] font-bold flex items-center justify-center">
                      ✓
                    </span>
                    We&apos;ll email you when the scan finishes.
                  </p>
                ) : (
                  <form onSubmit={submitEmail} className="space-y-1.5">
                    <p className="text-xs text-zinc-600 dark:text-zinc-400">
                      Or get notified by email when it&apos;s ready:
                    </p>
                    <div className="flex gap-2 items-stretch">
                      <input
                        type="email"
                        inputMode="email"
                        autoComplete="email"
                        placeholder="you@example.com"
                        value={emailDraft}
                        onChange={(e) => setEmailDraft(e.target.value)}
                        disabled={emailSaving}
                        className="flex-1 min-w-0 px-2 py-1.5 text-xs rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                      <button
                        type="submit"
                        disabled={emailSaving || !emailDraft}
                        className="px-3 py-1.5 text-xs font-medium rounded border border-zinc-300 dark:border-zinc-700 hover:border-indigo-500 hover:text-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {emailSaving ? "Saving…" : "Notify me"}
                      </button>
                    </div>
                    {emailError && (
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {emailError}
                      </p>
                    )}
                  </form>
                )}
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
          Scans usually take 30–90 seconds — sometimes up to 3 minutes for repos
          we&apos;ve never seen.
        </p>
      </div>
    </main>
  );
}
