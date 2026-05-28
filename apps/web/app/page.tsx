import { UrlInput } from "@/components/url-input";

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-5 flex justify-between items-center max-w-6xl w-full mx-auto">
        <div className="font-semibold tracking-tight">
          Stack<span className="text-indigo-600">Health</span>
        </div>
        <nav className="flex gap-6 text-sm text-zinc-600 dark:text-zinc-300">
          <a href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
            Methodology
          </a>
          <a href="/about" className="hover:text-zinc-900 dark:hover:text-white">
            About
          </a>
          <a
            href="https://github.com/stackhealth-dev/stackhealth"
            className="hover:text-zinc-900 dark:hover:text-white"
          >
            GitHub
          </a>
        </nav>
      </header>

      <section className="flex-1 flex flex-col items-center justify-center px-6 max-w-3xl mx-auto text-center gap-8 py-20">
        <div className="space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            The open code health benchmark
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-300 max-w-xl mx-auto">
            Score any public GitHub repo on security, quality, hygiene, and
            community. Fully open formula. Free forever.
          </p>
        </div>

        <UrlInput />

        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Formula v1.0 · Free for every public repo · Open source
        </p>
      </section>

      <section className="border-t border-zinc-200 dark:border-zinc-800 py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-semibold mb-8">Try a sample</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <SampleCard repo="fastapi/fastapi" />
            <SampleCard repo="expressjs/express" />
            <SampleCard repo="rust-lang/rust" />
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-8 px-6 text-sm text-zinc-500">
        <div className="max-w-6xl mx-auto flex justify-between">
          <span>StackHealth · open source · MIT</span>
          <a href="/methodology" className="hover:text-zinc-900 dark:hover:text-white">
            How is this scored?
          </a>
        </div>
      </footer>
    </main>
  );
}

function SampleCard({ repo }: { repo: string }) {
  return (
    <a
      href={`/r/${repo}`}
      className="border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 hover:border-indigo-500 transition-colors"
    >
      <div className="font-mono text-sm">{repo}</div>
      <div className="text-xs text-zinc-500 mt-1">View report →</div>
    </a>
  );
}
