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

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-lg w-full space-y-6 text-center">
        <h1 className="text-2xl font-semibold">
          {owner}/{name}
        </h1>
        <p className="text-zinc-500">
          We haven&apos;t scanned this repo yet. Submit it to generate the first
          report.
        </p>
        <UrlInput />
      </div>
    </main>
  );
}
