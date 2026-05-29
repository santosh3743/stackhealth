import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { UrlInput } from "@/components/url-input";

// See report page for why we prefer INTERNAL_API_URL on the server.
const API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

type RecentScan = {
  id: string;
  status: string;
  grade: string | null;
  overall_score: number | null;
  created_at: string;
};

async function fetchRecent(owner: string, name: string): Promise<RecentScan | null> {
  try {
    const r = await fetch(`${API_BASE}/api/repos/${owner}/${name}/recent`, {
      // Recent scan changes frequently (status transitions). Don't cache
      // hard — short revalidate is fine.
      next: { revalidate: 10 },
    });
    if (!r.ok) return null;
    return (await r.json()) as RecentScan;
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

  const recent = await fetchRecent(owner, name);

  // Complete scan exists → straight to the report.
  if (recent?.status === "complete") {
    redirect(`/r/${owner}/${name}/${recent.id}`);
  }

  const githubUrl = `https://github.com/${owner}/${name}`;
  const inProgress =
    recent && ["queued", "cloning", "analyzing", "scoring"].includes(recent.status);

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-2xl w-full space-y-6 text-center">
        <h1 className="text-2xl font-semibold">
          {owner}/{name}
        </h1>

        {inProgress ? (
          <>
            <div className="rounded-xl border border-indigo-300 bg-indigo-50 dark:border-indigo-800/40 dark:bg-indigo-950/30 p-5 space-y-2">
              <p className="text-sm font-medium text-indigo-800 dark:text-indigo-200">
                We&apos;re already scanning this repo right now.
              </p>
              <p className="text-xs text-indigo-700/80 dark:text-indigo-300/80">
                Drop your email below and we&apos;ll notify you the moment the
                report is ready — usually within a few minutes from now.
              </p>
            </div>
          </>
        ) : (
          <p className="text-zinc-500">
            We haven&apos;t scanned this repo yet. Drop your email and we&apos;ll
            send the report when it&apos;s ready — usually 30 seconds, sometimes
            a few minutes for big repos.
          </p>
        )}

        <div className="flex justify-center">
          <UrlInput initialUrl={githubUrl} autoFocus />
        </div>
      </div>
    </main>
  );
}
