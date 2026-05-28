// The colored letter-grade circle. Hero / card / inline variants.
// TODO (Week 3): full styling per docs/10-FRONTEND-PAGES.md visual identity.

import { clsx } from "clsx";

export type Grade =
  | "A+" | "A" | "A-"
  | "B+" | "B" | "B-"
  | "C+" | "C" | "C-"
  | "D"
  | "F";

const COLOR: Record<Grade, string> = {
  "A+": "bg-emerald-500", "A": "bg-emerald-500", "A-": "bg-green-500",
  "B+": "bg-green-500", "B": "bg-lime-500", "B-": "bg-yellow-500",
  "C+": "bg-yellow-500", "C": "bg-orange-500", "C-": "bg-orange-500",
  "D": "bg-red-500",
  "F": "bg-rose-700",
};

export function GradeBadge({
  grade,
  size = "card",
}: {
  grade: Grade;
  size?: "hero" | "card" | "inline";
}) {
  const sizes = {
    hero: "w-32 h-32 text-5xl",
    card: "w-16 h-16 text-2xl",
    inline: "w-8 h-8 text-sm",
  };
  return (
    <div
      role="img"
      aria-label={`Grade ${grade}`}
      className={clsx(
        "rounded-full flex items-center justify-center font-bold text-white",
        COLOR[grade],
        sizes[size],
      )}
    >
      {grade}
    </div>
  );
}
