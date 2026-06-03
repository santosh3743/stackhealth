"use client";

import { useState } from "react";

type Format = "markdown" | "html" | "url";

const LABELS: Record<Format, string> = {
  markdown: "Markdown",
  html: "HTML",
  url: "Image URL",
};

export function EmbedCard({
  owner,
  name,
  apiUrl,
  siteUrl,
}: {
  owner: string;
  name: string;
  apiUrl: string;
  siteUrl: string;
}) {
  const [format, setFormat] = useState<Format>("markdown");
  const [copied, setCopied] = useState(false);

  const badgeUrl = `${apiUrl}/r/${owner}/${name}/badge.svg`;
  const reportUrl = `${siteUrl}/r/${owner}/${name}`;

  const snippets: Record<Format, string> = {
    markdown: `[![StackHealth](${badgeUrl})](${reportUrl})`,
    html: `<a href="${reportUrl}"><img src="${badgeUrl}" alt="StackHealth grade"/></a>`,
    url: badgeUrl,
  };
  const current = snippets[format];

  async function copy() {
    try {
      await navigator.clipboard.writeText(current);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked (Safari private mode, insecure context). Fallback:
      // select the snippet so users can ⌘C. The visible text element is the
      // <code> below — its parent <pre> has user-select enabled by default.
    }
  }

  return (
    <section className="px-6 max-w-6xl mx-auto mt-10">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-lg font-semibold">Embed in your README</h2>
        <span className="text-xs text-zinc-500">
          Always shows the latest grade
        </span>
      </div>

      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-hidden bg-white dark:bg-zinc-950">
        {/* Live preview — anyone reading this readme will see exactly this */}
        <div className="px-4 py-4 flex items-center gap-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-900/40">
          <a
            href={reportUrl}
            className="inline-flex"
            aria-label="View report"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={badgeUrl} alt="StackHealth grade" height={20} />
          </a>
          <span className="text-xs text-zinc-500">
            Live preview · clicks through to this report
          </span>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-200 dark:border-zinc-800">
          {(Object.keys(LABELS) as Format[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFormat(f)}
              className={`px-4 py-2 text-xs font-medium transition-colors ${
                format === f
                  ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px"
                  : "text-zinc-500 hover:text-zinc-800 dark:hover:text-white"
              }`}
            >
              {LABELS[f]}
            </button>
          ))}
        </div>

        {/* Snippet + copy */}
        <div className="relative">
          <pre className="px-4 py-3 text-xs overflow-x-auto bg-zinc-50 dark:bg-zinc-950 m-0">
            <code className="break-all whitespace-pre-wrap">{current}</code>
          </pre>
          <button
            type="button"
            onClick={copy}
            className="absolute top-2 right-2 px-2.5 py-1 text-[11px] font-medium rounded-md bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>

      <p className="mt-3 text-xs text-zinc-500">
        Tip: anyone can score a repo by swapping{" "}
        <code className="font-mono">github.com</code> → {" "}
        <code className="font-mono">stackhealth.dev</code> in the URL.
      </p>
    </section>
  );
}
