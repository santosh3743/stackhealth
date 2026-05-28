"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { submitScan } from "@/lib/api";

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/i;

export function UrlInput() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!GITHUB_URL_RE.test(trimmed)) {
      setError("Paste a github.com/owner/repo URL");
      return;
    }

    setLoading(true);
    try {
      const { scan_id } = await submitScan(trimmed);
      router.push(`/scan/${scan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full max-w-2xl flex flex-col sm:flex-row gap-2"
    >
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
      {error && (
        <p
          role="alert"
          className="text-sm text-red-600 dark:text-red-400 sm:absolute mt-14"
        >
          {error}
        </p>
      )}
    </form>
  );
}
