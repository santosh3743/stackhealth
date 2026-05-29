"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { submitScan } from "@/lib/api";

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/i;
// RFC-ish; the backend is the source of truth, this is just a UX prefilter.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * URL submit form.
 *
 * Email is **required** to submit. Every scan needs a notification
 * target so the user can walk away from the polling page — most scans
 * take 30s to several minutes and we don't want to make people babysit
 * a progress bar.
 *
 * @param initialUrl Pre-fills the repo URL. Used when arriving from
 *   `/r/owner/name` so the visitor doesn't re-type a URL we already know.
 * @param autoFocus Focus the URL input on mount.
 */
export function UrlInput({
  initialUrl = "",
  autoFocus = false,
}: {
  initialUrl?: string;
  autoFocus?: boolean;
} = {}) {
  const router = useRouter();
  const [url, setUrl] = useState(initialUrl);
  const [email, setEmail] = useState("");
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
    if (!trimmedEmail) {
      setError("Email is required — we'll send the report there when it's ready");
      return;
    }
    if (!EMAIL_RE.test(trimmedEmail)) {
      setError("That doesn't look like a valid email");
      return;
    }

    setLoading(true);
    try {
      const { scan_id } = await submitScan(trimmedUrl, trimmedEmail);
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
          autoFocus={autoFocus}
          required
          className="flex-1 px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-base focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="your@email.com (we'll email the report here)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
          required
          className="flex-1 px-4 py-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-base focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {loading ? "Scanning…" : "Scan & email me"}
        </button>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </form>
  );
}
