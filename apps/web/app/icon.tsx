// Favicon — served as /icon and used by Next.js metadata automatically.
// Image: rounded indigo square with three stacked white bars (the "stack"
// metaphor). Designed to read at 16×16 — bars are thick, square is bold.

import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 3,
          background: "#4f46e5",
          borderRadius: 7,
          padding: 6,
        }}
      >
        <div
          style={{
            width: "85%",
            height: 4,
            background: "rgba(255,255,255,0.55)",
            borderRadius: 2,
          }}
        />
        <div
          style={{
            width: "100%",
            height: 4,
            background: "rgba(255,255,255,0.85)",
            borderRadius: 2,
          }}
        />
        <div
          style={{
            width: "75%",
            height: 4,
            background: "#ffffff",
            borderRadius: 2,
          }}
        />
      </div>
    ),
    { ...size },
  );
}
