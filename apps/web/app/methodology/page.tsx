import Link from "next/link";

export const metadata = {
  title: "Methodology",
  description:
    "The open formula behind StackHealth — every weight, threshold, and penalty is documented.",
};

export default function MethodologyPage() {
  return (
    <main className="min-h-screen px-6 py-16 max-w-3xl mx-auto">
      <nav className="text-sm mb-10">
        <Link href="/" className="font-semibold tracking-tight">
          Stack<span className="text-indigo-600">Health</span>
        </Link>
        <span className="text-zinc-400 mx-2">/</span>
        <span className="text-zinc-500">Methodology</span>
      </nav>

      <header className="space-y-3 mb-12">
        <h1 className="text-3xl font-bold">How StackHealth scores a repo</h1>
        <p className="text-zinc-600 dark:text-zinc-300">
          Formula version <code className="font-mono">v1.0</code>. Every weight
          and threshold is defined below. The same formula lives in code at{" "}
          <a
            className="underline"
            href="https://github.com/stackhealth-dev/formula"
          >
            stackhealth-dev/formula
          </a>{" "}
          and runs locally in our worker.
        </p>
      </header>

      <Section title="Overall score">
        <p>
          Each scan produces a 0–100 composite score and an A+ to F letter
          grade. The composite weights four dimensions:
        </p>
        <Table
          rows={[
            ["Security", "30%"],
            ["Quality", "25%"],
            ["Hygiene", "25%"],
            ["Community", "20%"],
          ]}
        />
        <Pre>{`overall = round(
  0.30 * security
+ 0.25 * quality
+ 0.25 * hygiene
+ 0.20 * community
)`}</Pre>
        <p className="text-sm text-zinc-500">
          Grade boundaries: A+ ≥95 · A ≥90 · A- ≥85 · B+ ≥80 · B ≥75 · B- ≥70 ·
          C+ ≥65 · C ≥60 · C- ≥55 · D ≥50 · F &lt;50
        </p>
      </Section>

      <Section title="1. Security (30%)">
        <Table
          rows={[
            ["OpenSSF Scorecard", "40% of security · 12% overall"],
            ["Semgrep p/security-audit", "40% of security · 12% overall"],
            ["Trivy dependency CVEs", "20% of security · 6% overall"],
          ]}
        />
        <p>
          Semgrep findings are LoC-normalised so a 100-finding repo at 1M LoC
          isn&apos;t penalised the same as a 100-finding repo at 1k LoC.
          Dependency CVEs are absolute: one critical vulnerability is one
          critical vulnerability regardless of project size.
        </p>
      </Section>

      <Section title="2. Quality (25%)">
        <Table
          rows={[
            ["Cyclomatic complexity (lizard)", "30% · avg ≤5 → 100"],
            ["Lint density (ruff / eslint / golangci)", "25% · issues per kLoC"],
            ["Code duplication (jscpd)", "20% · 0% dup → 100"],
            ["Test signal (no execution)", "15% · directories + CI runners"],
            ["File size", "10% · penalises files >1000 LoC"],
          ]}
        />
      </Section>

      <Section title="3. Hygiene (25%)">
        <p>A binary checklist. Total possible: 100 points.</p>
        <Table
          rows={[
            ["README.md exists, >300 chars", "15"],
            ["LICENSE present", "15"],
            ["LICENSE is OSI-approved", "5"],
            ["CONTRIBUTING.md", "8"],
            ["CODE_OF_CONDUCT.md", "5"],
            ["SECURITY.md", "7"],
            [".github/workflows/ or .gitlab-ci.yml", "10"],
            ["A workflow triggers on pull_request", "5"],
            ["tests/ directory", "10"],
            [".gitignore", "3"],
            ["Repo description on GitHub", "5"],
            ["Repo topics on GitHub", "5"],
            ["Pushed within last 365 days", "7"],
          ]}
        />
      </Section>

      <Section title="4. Community (20%)">
        <Table
          rows={[
            ["Activity (recent commits)", "35% of community · 7% overall"],
            ["Contributors (last 365d, log2 scale)", "25% · 5% overall"],
            ["Popularity (stars, log10 scale)", "20% · 4% overall"],
            ["Responsiveness (median time-to-first-response)", "20% · 4% overall"],
          ]}
        />
        <p className="text-sm text-zinc-500">
          Popularity is capped at 4% of overall so a repo cannot earn an A just
          by being popular.
        </p>
      </Section>

      <Section title="Reproducibility">
        <p>Every scan stores:</p>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>The formula version (e.g. <code>v1.0</code>)</li>
          <li>Tool versions (<code>semgrep@…</code>, <code>trivy@…</code>, etc.)</li>
          <li>The exact commit SHA that was scanned</li>
          <li>Raw JSON outputs from every analyzer</li>
        </ul>
        <p>
          If you can fetch the raw outputs and the published formula doesn&apos;t
          reproduce the score, that&apos;s a bug we&apos;ll fix.
        </p>
      </Section>

      <Section title="What we do NOT score">
        <p className="text-sm text-zinc-500">
          We deliberately exclude code aesthetics (no AI prose review),
          documentation depth (only README presence), runtime performance,
          stars growth rate, author identity, and language choice. These are
          either gameable, subjective, or unfair across projects.
        </p>
      </Section>

      <Section title="How the formula evolves">
        <p>
          Patch (v1.0 → v1.0.1) — bug fixes only, same inputs → same score.
          Minor (v1.0 → v1.1) — threshold tweaks; old scans aren&apos;t
          re-scored. Major (v1 → v2) — structural changes, always preceded by a
          30-day public RFC.
        </p>
        <p className="text-sm text-zinc-500">
          All changes are pull requests against the public formula repo.
        </p>
      </Section>

      <footer className="text-xs text-zinc-500 border-t border-zinc-200 dark:border-zinc-800 pt-6 mt-10">
        <Link href="/" className="hover:text-zinc-900 dark:hover:text-white">
          ← Back to home
        </Link>
      </footer>
    </main>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const id = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return (
    <section id={id} className="mb-12 space-y-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function Table({ rows }: { rows: [string, string][] }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
      <table className="w-full text-sm">
        <tbody>
          {rows.map(([k, v]) => (
            <tr
              key={k}
              className="border-b border-zinc-200 dark:border-zinc-800 last:border-0"
            >
              <td className="px-4 py-2">{k}</td>
              <td className="px-4 py-2 text-right font-mono text-zinc-500">
                {v}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Pre({ children }: { children: React.ReactNode }) {
  return (
    <pre className="rounded-lg bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 p-4 text-xs overflow-x-auto font-mono">
      {children}
    </pre>
  );
}
