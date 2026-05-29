// Default OG card for the site (1200×630). Used when someone shares
// stackhealth.dev itself. Report pages override this with their own
// dynamic OG showing the scanned repo's score.

import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt =
  "StackHealth — the open code health benchmark for any GitHub repo";

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#0a0a0a",
          color: "#ffffff",
          display: "flex",
          padding: 80,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {/* Left column: brand mark + copy */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              fontSize: 38,
              fontWeight: 600,
              letterSpacing: -1,
              display: "flex",
              alignItems: "center",
              gap: 18,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                background: "#4f46e5",
                borderRadius: 14,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                padding: 12,
                gap: 6,
              }}
            >
              <div
                style={{
                  width: "78%",
                  height: 6,
                  background: "rgba(255,255,255,0.6)",
                  borderRadius: 3,
                }}
              />
              <div
                style={{
                  width: "100%",
                  height: 6,
                  background: "rgba(255,255,255,0.9)",
                  borderRadius: 3,
                }}
              />
              <div
                style={{
                  width: "65%",
                  height: 6,
                  background: "#ffffff",
                  borderRadius: 3,
                }}
              />
            </div>
            <span>
              Stack<span style={{ color: "#818cf8" }}>Health</span>
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div
              style={{
                fontSize: 70,
                fontWeight: 700,
                letterSpacing: -2,
                lineHeight: 1.05,
              }}
            >
              The open code health benchmark.
            </div>
            <div
              style={{
                fontSize: 28,
                color: "#a1a1aa",
                lineHeight: 1.4,
                maxWidth: 640,
              }}
            >
              Score any public GitHub repo on security, quality, hygiene,
              and community. Fully open formula. Free forever.
            </div>
          </div>

          <div
            style={{
              fontSize: 22,
              color: "#71717a",
              display: "flex",
              gap: 24,
            }}
          >
            <span>Formula v1.0</span>
            <span>·</span>
            <span>stackhealth.dev</span>
          </div>
        </div>

        {/* Right: visual — example grade badge */}
        <div
          style={{
            width: 280,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            gap: 16,
            marginLeft: 60,
          }}
        >
          <div
            style={{
              width: 220,
              height: 220,
              borderRadius: 999,
              background: "#22c55e",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 110,
              fontWeight: 800,
              letterSpacing: -3,
            }}
          >
            A
          </div>
          <div style={{ fontSize: 24, color: "#a1a1aa" }}>92 / 100</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
