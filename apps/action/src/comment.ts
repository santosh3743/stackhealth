// Builds the sticky PR comment body. Marker lets us find-and-update on
// re-runs instead of stacking new comments every push.

import type { ScanRead } from "./api.js";

export const COMMENT_MARKER = "<!-- stackhealth-action -->";

interface RenderArgs {
  base: ScanRead;
  head: ScanRead;
  baseRepoSlug: string;
  headRepoSlug: string;
  baseRef: string;
  headRef: string;
  siteBase: string;
}

const SUB_DIMENSIONS = ["security", "quality", "hygiene", "community"] as const;

export function renderComment(a: RenderArgs): string {
  const baseGrade = a.base.grade ?? "?";
  const headGrade = a.head.grade ?? "?";
  const baseScore = a.base.overall_score ?? 0;
  const headScore = a.head.overall_score ?? 0;
  const delta = headScore - baseScore;
  const deltaCell = formatDelta(delta);

  const baseReport = `${a.siteBase}/r/${a.base.repo.owner}/${a.base.repo.name}/${a.base.id}`;
  const headReport = `${a.siteBase}/r/${a.head.repo.owner}/${a.head.repo.name}/${a.head.id}`;

  const lines: string[] = [];
  lines.push(COMMENT_MARKER);
  lines.push("### StackHealth grade");
  lines.push("");
  lines.push(`| | Base \`${a.baseRef}\` | This PR \`${a.headRef}\` | Δ |`);
  lines.push("|---|---|---|---|");
  lines.push(
    `| **Overall** | ${gradeCell(baseGrade, baseScore)} | ${gradeCell(headGrade, headScore)} | ${deltaCell} |`,
  );

  if (a.base.scores && a.head.scores) {
    for (const dim of SUB_DIMENSIONS) {
      const b = a.base.scores[dim];
      const h = a.head.scores[dim];
      const d = h - b;
      lines.push(
        `| ${capitalise(dim)} | ${b} | ${h} | ${formatDelta(d, /* compact= */ true)} |`,
      );
    }
  }

  lines.push("");

  if (a.base.partial || a.head.partial) {
    lines.push("> ⚠️ One side ran with partial engine output — score may shift on re-scan.");
    lines.push("");
  }

  if (a.head.failure_reason) {
    lines.push(`> ❌ PR scan note: \`${escapeMd(a.head.failure_reason)}\``);
    lines.push("");
  }

  lines.push(
    `[Base report](${baseReport}) · [PR report](${headReport}) · [Methodology](${a.siteBase}/methodology)`,
  );
  lines.push("");
  lines.push(
    `<sub>Formula ${a.head.formula_version} · ${a.head.repo.owner}/${a.head.repo.name}@\`${(a.head.commit_sha ?? "").slice(0, 7)}\` vs ${a.base.repo.owner}/${a.base.repo.name}@\`${(a.base.commit_sha ?? "").slice(0, 7)}\`</sub>`,
  );
  return lines.join("\n");
}

function gradeCell(grade: string, score: number): string {
  return `**${grade}** ${score}`;
}

function formatDelta(delta: number, compact = false): string {
  if (delta === 0) return compact ? "·" : "± 0";
  const sign = delta > 0 ? "+" : "";
  const emoji = delta > 0 ? "✅ " : "⚠️ ";
  return `${compact ? "" : emoji}${sign}${delta}`;
}

function capitalise(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function escapeMd(s: string): string {
  return s.replace(/[`*_~|<>]/g, " ").slice(0, 200);
}
