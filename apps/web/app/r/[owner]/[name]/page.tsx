import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { UrlInput } from "@/components/url-input";

// See report page for why we prefer INTERNAL_API_URL on the server.
const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

async function fetchLatest(owner: string, name: string) {
  try {
    const r = await fetch(`${API_BASE}/api/repos/${owner}/${name}/latest`, {
      next: { revalidate: 60 },
    });
    if (!r.ok) return null;
    return (await r.json()) as { id: string };
  } catch {
    return null;
  }
}

export default async function RepoLatestPage({
  params,
}: {
  params: Promise<{ owner: string; name: string }>;
}) {
  const { owner, name } = await params;
  // Force `headers()` evaluation so this is treated as dynamic at request time.
  await headers();

  const latest = await fetchLatest(owner, name);
  if (latest) {
    redirect(`/r/${owner}/${name}/${latest.id}`);
  }

  // Pre-fill the URL input so the visitor doesn't have to re-type a URL
  // we already know — they arrived here via /r/owner/name (or the
  // github.com→stackhealth.dev URL swap), so click Scan is the only
  // remaining step.
  const githubUrl = `https://github.com/${owner}/${name}`;

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-2xl w-full space-y-6 text-center">
        <h1 className="text-2xl font-semibold">
          {owner}/{name}
        </h1>
        <p className="text-zinc-500">
          We haven&apos;t scanned this repo yet — hit{" "}
          <span className="font-medium">Scan</span> to generate the first
          report. Takes ~30–90 seconds.
        </p>
        <div className="flex justify-center">
          <UrlInput initialUrl={githubUrl} autoFocus />
        </div>
      </div>
    </main>
  );
}
