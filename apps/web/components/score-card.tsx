// Sub-score card. Used for Security / Quality / Hygiene / Community.

export function ScoreCard({
  label,
  score,
  qualitative,
}: {
  label: string;
  score: number;
  qualitative: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 text-center">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="text-3xl font-bold mt-1">{score}</div>
      <div className="text-xs text-zinc-500 mt-1">{qualitative}</div>
    </div>
  );
}
