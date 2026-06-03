import Link from "next/link";

import { DiscoveryPanel } from "@/components/discovery-panel";
import { LogoMark } from "@/components/logo-mark";
import { UrlInput } from "@/components/url-input";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 flex justify-between items-center max-w-7xl w-full mx-auto">
        <div className="font-semibold tracking-tight flex items-center gap-2">
          <LogoMark size={22} />
          <span>
            Stack<span className="text-indigo-600">Health</span>
          </span>
        </div>
        <nav className="flex gap-6 text-sm text-zinc-600 dark:text-zinc-300">
          <Link
            href="/leaderboard"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            Leaderboard
          </Link>
          <Link
            href="/methodology"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            Methodology
          </Link>
          <Link
            href="/about"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            About
          </Link>
          <a
            href="https://github.com/santosh3743/stackhealth"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            GitHub
          </a>
        </nav>
      </header>

      <section className="flex-1 px-6 max-w-7xl w-full mx-auto py-12 lg:py-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 lg:gap-12 items-start">
          {/* Hero — spans 2/3 on desktop */}
          <div className="lg:col-span-2 space-y-8 text-center lg:text-left">
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
                The open code health benchmark
              </h1>
              <p className="text-lg text-zinc-600 dark:text-zinc-300 max-w-xl lg:mx-0 mx-auto">
                Score any public GitHub repo on security, quality, hygiene, and
                community. Fully open formula. Free forever.
              </p>
            </div>

            <UrlInput />

            <p className="text-xs text-zinc-600 dark:text-zinc-400 lg:max-w-xl mx-auto lg:mx-0">
              <span className="font-medium text-zinc-700 dark:text-zinc-300">
                Pro tip:
              </span>{" "}
              replace <code className="font-mono">github.com</code> with{" "}
              <code className="font-mono text-indigo-600">stackhealth.dev</code>{" "}
              in any repo URL to jump straight to its report.
            </p>

            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Formula v1.0 · Free for every public repo · Open source
            </p>

            <div className="pt-2">
              <h2 className="text-sm font-medium text-zinc-500 mb-3 uppercase tracking-wider">
                Try a sample
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <SampleCard repo="fastapi/fastapi" />
                <SampleCard repo="pallets/click" />
                <SampleCard repo="encode/starlette" />
              </div>
            </div>
          </div>

          {/* Sidebar — Recent / Leaderboard */}
          <div className="lg:col-span-1 lg:sticky lg:top-6">
            <DiscoveryPanel />
            <p className="mt-3 px-2 text-[11px] text-zinc-500 dark:text-zinc-500 leading-relaxed">
              Every scan is public. Submitting a URL adds the repo to this
              feed.{" "}
              <Link
                href="/methodology"
                className="underline hover:text-indigo-600"
              >
                Why?
              </Link>
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-8 px-6 text-sm text-zinc-500">
        <div className="max-w-7xl mx-auto flex justify-between">
          <span>StackHealth · open source · MIT</span>
          <Link
            href="/methodology"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            How is this scored?
          </Link>
        </div>
      </footer>
    </main>
  );
}

function SampleCard({ repo }: { repo: string }) {
  return (
    <a
      href={`/r/${repo}`}
      className="border border-zinc-200 dark:border-zinc-800 rounded-lg p-3 hover:border-indigo-500 transition-colors block"
    >
      <div className="font-mono text-sm">{repo}</div>
      <div className="text-xs text-zinc-500 mt-1">View report →</div>
    </a>
  );
}
