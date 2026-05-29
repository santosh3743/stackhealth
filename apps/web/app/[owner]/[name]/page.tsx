// The "github.com → stackhealth.dev" URL swap.
//
//   stackhealth.dev/pallets/click   →   /r/pallets/click   →   latest scan
//
// Next.js routing precedence is: explicit literal segments > dynamic. So
// `/methodology`, `/about`, `/r/...`, `/scan/...`, `/icon`, `/apple-icon`,
// and `/opengraph-image` are all matched by their own files first; this
// catch-all only fires for genuinely two-segment paths.
//
// We still guard against `[owner]` accidentally matching one of our
// reserved words (e.g. `stackhealth.dev/methodology/foo` has two segments
// and would otherwise be treated as a scan of `methodology/foo`).

import { notFound, redirect } from "next/navigation";

// Anything here must NEVER be treated as a GitHub owner.
const RESERVED_OWNERS = new Set([
  "r",
  "scan",
  "methodology",
  "about",
  "api",
  "icon",
  "apple-icon",
  "opengraph-image",
  "favicon.ico",
  "robots.txt",
  "sitemap.xml",
  "_next",
]);

// GitHub usernames + repo names: alphanumeric, dash, underscore, dot.
// Length and leading-char rules are stricter, but we leave that to the
// downstream API (which calls api.github.com to confirm the repo).
const GH_NAME_RE = /^[A-Za-z0-9._-]+$/;

export default async function GithubSwapPage({
  params,
}: {
  params: Promise<{ owner: string; name: string }>;
}) {
  const { owner, name } = await params;

  if (RESERVED_OWNERS.has(owner.toLowerCase())) notFound();
  if (!GH_NAME_RE.test(owner) || !GH_NAME_RE.test(name)) notFound();

  redirect(`/r/${owner}/${name}`);
}
