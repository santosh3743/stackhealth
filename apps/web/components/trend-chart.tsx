"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

export type TrendPoint = {
  id: string;
  grade: string | null;
  overall_score: number | null;
  security_score: number | null;
  quality_score: number | null;
  hygiene_score: number | null;
  community_score: number | null;
  commit_sha: string | null;
  completed_at: string;
};

const SERIES = [
  { key: "overall_score", label: "Overall", color: "#4f46e5", width: 2.5 },
  { key: "security_score", label: "Security", color: "#10b981", width: 1.5 },
  { key: "quality_score", label: "Quality", color: "#3b82f6", width: 1.5 },
  { key: "hygiene_score", label: "Hygiene", color: "#a855f7", width: 1.5 },
  { key: "community_score", label: "Community", color: "#f59e0b", width: 1.5 },
] as const;

type SeriesKey = (typeof SERIES)[number]["key"];

const W = 720;
const H = 220;
const PAD_L = 32;
const PAD_R = 16;
const PAD_T = 16;
const PAD_B = 32;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function TrendChart({
  owner,
  name,
  history,
  currentScanId,
}: {
  owner: string;
  name: string;
  history: TrendPoint[];
  currentScanId: string;
}) {
  // Show oldest → newest left → right.
  const points = useMemo(
    () =>
      [...history]
        .filter((p) => p.overall_score != null)
        .sort(
          (a, b) =>
            new Date(a.completed_at).getTime() -
            new Date(b.completed_at).getTime(),
        ),
    [history],
  );

  const [hidden, setHidden] = useState<Set<SeriesKey>>(new Set());
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  if (points.length < 2) return null;

  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;

  const xFor = (i: number) =>
    points.length === 1 ? PAD_L + innerW / 2 : PAD_L + (i / (points.length - 1)) * innerW;
  const yFor = (v: number) => PAD_T + innerH * (1 - v / 100);

  const visibleSeries = SERIES.filter((s) => !hidden.has(s.key));

  // Latest values for the legend.
  const latest = points[points.length - 1];

  const hovered = hoverIdx != null ? points[hoverIdx] : null;

  return (
    <section className="px-6 max-w-6xl mx-auto mt-10">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">
          History{" "}
          <span className="text-zinc-500 text-sm font-normal">
            ({points.length} scan{points.length === 1 ? "" : "s"})
          </span>
        </h2>
        <span className="text-xs text-zinc-500">
          Click a series to toggle · click a dot to jump to that scan
        </span>
      </div>

      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 p-4 bg-zinc-50/40 dark:bg-zinc-950/40">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto"
          role="img"
          aria-label={`Score history for ${owner}/${name}, ${points.length} scans`}
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* gridlines: 0, 50, 100 */}
          {[0, 50, 100].map((g) => (
            <g key={g}>
              <line
                x1={PAD_L}
                x2={W - PAD_R}
                y1={yFor(g)}
                y2={yFor(g)}
                stroke="currentColor"
                strokeOpacity="0.08"
                strokeDasharray={g === 50 ? "2 3" : undefined}
              />
              <text
                x={PAD_L - 6}
                y={yFor(g) + 3}
                fontSize="10"
                textAnchor="end"
                className="fill-zinc-400"
              >
                {g}
              </text>
            </g>
          ))}

          {/* hover guide */}
          {hoverIdx != null && (
            <line
              x1={xFor(hoverIdx)}
              x2={xFor(hoverIdx)}
              y1={PAD_T}
              y2={H - PAD_B}
              stroke="currentColor"
              strokeOpacity="0.15"
            />
          )}

          {/* x-axis labels: first, last, and a couple in between if room */}
          {points.map((p, i) => {
            const showLabel =
              i === 0 ||
              i === points.length - 1 ||
              (points.length > 4 && i === Math.floor(points.length / 2));
            if (!showLabel) return null;
            return (
              <text
                key={p.id}
                x={xFor(i)}
                y={H - PAD_B + 16}
                fontSize="10"
                textAnchor={i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"}
                className="fill-zinc-400"
              >
                {formatDate(p.completed_at)}
              </text>
            );
          })}

          {/* invisible hit areas — wide vertical strips for mouse tracking */}
          {points.map((p, i) => {
            const left =
              i === 0 ? PAD_L : (xFor(i - 1) + xFor(i)) / 2;
            const right =
              i === points.length - 1
                ? W - PAD_R
                : (xFor(i) + xFor(i + 1)) / 2;
            return (
              <rect
                key={`hit-${p.id}`}
                x={left}
                y={PAD_T}
                width={Math.max(1, right - left)}
                height={innerH}
                fill="transparent"
                onMouseEnter={() => setHoverIdx(i)}
              />
            );
          })}

          {/* lines */}
          {visibleSeries.map((s) => {
            const d = points
              .map((p, i) => {
                const v = p[s.key];
                if (v == null) return null;
                return `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(1)} ${yFor(v).toFixed(1)}`;
              })
              .filter(Boolean)
              .join(" ");
            return (
              <path
                key={s.key}
                d={d}
                fill="none"
                stroke={s.color}
                strokeWidth={s.width}
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={hidden.size > 0 && s.key !== "overall_score" ? 0.95 : 1}
              />
            );
          })}

          {/* per-scan dots on the overall line — clickable, current scan highlighted */}
          {!hidden.has("overall_score") &&
            points.map((p, i) => {
              const v = p.overall_score;
              if (v == null) return null;
              const isCurrent = p.id === currentScanId;
              const isHovered = hoverIdx === i;
              const r = isCurrent || isHovered ? 5 : 3;
              return (
                <Link
                  key={p.id}
                  href={`/r/${owner}/${name}/${p.id}`}
                  aria-label={`Open scan from ${formatDate(p.completed_at)}, overall ${v}`}
                >
                  <circle
                    cx={xFor(i)}
                    cy={yFor(v)}
                    r={r}
                    fill={isCurrent ? "#4f46e5" : "#fff"}
                    stroke="#4f46e5"
                    strokeWidth={2}
                    className="cursor-pointer"
                  />
                </Link>
              );
            })}
        </svg>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs">
          {SERIES.map((s) => {
            const isHidden = hidden.has(s.key);
            const value = hovered ? hovered[s.key] : latest[s.key];
            return (
              <button
                key={s.key}
                type="button"
                onClick={() =>
                  setHidden((prev) => {
                    const next = new Set(prev);
                    if (next.has(s.key)) next.delete(s.key);
                    else next.add(s.key);
                    return next;
                  })
                }
                className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors ${
                  isHidden ? "opacity-40" : ""
                }`}
              >
                <span
                  className="inline-block w-3 h-0.5 rounded"
                  style={{ backgroundColor: s.color, height: s.width }}
                />
                <span className="text-zinc-600 dark:text-zinc-400">{s.label}</span>
                <span className="tabular-nums font-medium">
                  {value ?? "—"}
                </span>
              </button>
            );
          })}
        </div>

        {/* Hover detail */}
        <div className="mt-2 h-5 text-xs text-zinc-500 tabular-nums">
          {hovered ? (
            <span>
              {formatDate(hovered.completed_at)}
              {hovered.commit_sha && (
                <span className="font-mono ml-2 text-zinc-400">
                  {hovered.commit_sha.slice(0, 7)}
                </span>
              )}
              {hovered.grade && (
                <span className="ml-2">grade {hovered.grade}</span>
              )}
              {hovered.id === currentScanId && (
                <span className="ml-2 text-indigo-500">· this scan</span>
              )}
            </span>
          ) : (
            <span>Latest: {formatDate(latest.completed_at)}</span>
          )}
        </div>
      </div>
    </section>
  );
}
