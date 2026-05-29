"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { submitScan } from "@/lib/api";

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/i;
// RFC-ish; the backend is the source of truth, this is just a UX prefilter.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function UrlInput() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [emailExpanded, setEmailExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmedUrl = url.trim();
    const trimmedEmail = email.trim();

    if (!GITHUB_URL_RE.test(trimmedUrl)) {
      setError("Paste a github.com/owner/repo URL");
      return;
    }
    if (trimmedEmail && !EMAIL_RE.test(trimmedEmail)) {
      setError("That doesn't look like a valid email");
      return;
    }

    setLoading(true);
    try {
      const { scan_id } = await submitScan(
        trimmedUrl,
        trimmedEmail || undefined,
      );
      router.push(`/scan/${scan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="w-full max-w-2xl space-y-3">
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="url"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          placeholder="https://github.com/owner/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
          className="flex-1 px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-base focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Scanning…" : "Scan"}
        </button>
      </div>

      {/* Optional email — collapsed by default so the hero stays clean. */}
      {emailExpanded ? (
        <div className="flex flex-col sm:flex-row gap-2 items-start">
          <input
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="you@example.com (optional — we'll email when it's done)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            className="flex-1 px-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="button"
            onClick={() => {
              setEmail("");
              setEmailExpanded(false);
            }}
            className="text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-white px-2 py-2"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setEmailExpanded(true)}
          className="text-xs text-zinc-500 hover:text-indigo-600 underline-offset-2 hover:underline"
        >
          + Notify me by email when it&apos;s ready
        </button>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </form>
  );
}
