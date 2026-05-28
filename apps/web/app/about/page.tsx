export const metadata = { title: "About" };

export default function AboutPage() {
  return (
    <main className="min-h-screen px-6 py-16 max-w-2xl mx-auto prose dark:prose-invert">
      <h1>About StackHealth</h1>
      <p>
        StackHealth exists because there is no widely-trusted open standard for
        code health. Lighthouse exists for websites. PageSpeed exists. SSL Labs
        exists. Code does not have its Lighthouse.
      </p>
      <p>
        We aggregate the best open-source analyzers — OpenSSF Scorecard,
        Semgrep, Trivy, and language-native linters — into a single composite
        score with a fully open, versioned formula. Every weight, every
        threshold, every penalty is documented.
      </p>
      <p>
        <strong>Free for public repos. Forever.</strong>
      </p>
    </main>
  );
}
