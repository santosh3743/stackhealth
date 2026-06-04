// Tiny ANSI helpers — no kleur/chalk dependency to keep `npx stackhealth`
// instant. We honour NO_COLOR (https://no-color.org) and disable colors
// when stdout isn't a TTY (e.g. piped to `jq`).

import type { ScanRead } from "./api.js";

const ENABLE =
  process.stdout.isTTY === true && process.env.NO_COLOR === undefined;

const wrap = (open: number, close: number) => (s: string) =>
  ENABLE ? `\x1b[${open}m${s}\x1b[${close}m` : s;

export const bold = wrap(1, 22);
export const dim = wrap(2, 22);
export const red = wrap(31, 39);
export const green = wrap(32, 39);
export const yellow = wrap(33, 39);
export const blue = wrap(34, 39);
export const magenta = wrap(35, 39);
export const cyan = wrap(36, 39);
export const gray = wrap(90, 39);

// Same palette as the web GradeBadge so the CLI matches what users see online.
export function colorForGrade(grade: string | undefined | null): (s: string) => string {
  if (!grade) return gray;
  if (grade.startsWith("A")) return green;
  if (grade.startsWith("B")) return cyan;
  if (grade.startsWith("C")) return yellow;
  if (grade === "D") return red;
  return red;
}

const GRADES_ORDER = ["F", "D", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"];

export function gradeAtLeast(actual: string | undefined, min: string): boolean {
  if (!actual) return false;
  const ai = GRADES_ORDER.indexOf(actual);
  const mi = GRADES_ORDER.indexOf(min);
  if (ai < 0 || mi < 0) return false;
  return ai >= mi;
}

export function renderReport(scan: ScanRead, reportUrl: string): string {
  const out: string[] = [];
  const repo = `${scan.repo.owner}/${scan.repo.name}`;
  const grade = scan.grade ?? "?";
  const tint = colorForGrade(scan.grade);
  const score = scan.overall_score ?? "—";

  out.push("");
  out.push(`  ${bold(repo)}`);
  out.push(
    `  ${tint(bold(grade.padEnd(3)))} ${bold(String(score))}${dim("/100")}` +
      (scan.partial ? "  " + yellow("(partial)") : ""),
  );
  out.push("");

  if (scan.scores) {
    const row = (label: string, val: number) =>
      `    ${label.padEnd(10)} ${bar(val)}  ${String(val).padStart(3)}${dim("/100")}`;
    out.push(row("Security", scan.scores.security));
    out.push(row("Quality", scan.scores.quality));
    out.push(row("Hygiene", scan.scores.hygiene));
    out.push(row("Community", scan.scores.community));
    out.push("");
  }

  if (scan.failure_reason) {
    out.push(`  ${yellow("note")} ${scan.failure_reason}`);
    out.push("");
  }

  out.push(`  ${dim("Report:")}   ${blue(reportUrl)}`);
  if (scan.commit_sha) {
    out.push(`  ${dim("Commit:")}   ${scan.commit_sha.slice(0, 7)}`);
  }
  out.push(`  ${dim("Formula:")}  ${scan.formula_version}`);
  out.push("");

  return out.join("\n");
}

function bar(value: number, width = 20): string {
  const filled = Math.round((Math.max(0, Math.min(100, value)) / 100) * width);
  const empty = width - filled;
  const tint =
    value >= 80 ? green : value >= 60 ? cyan : value >= 40 ? yellow : red;
  return tint("█".repeat(filled)) + dim("·".repeat(empty));
}
