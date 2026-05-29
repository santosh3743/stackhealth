// Apple touch icon (180×180) — iOS home-screen icon when someone adds
// stackhealth.dev to their home screen.

import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
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
          gap: 14,
          background: "#4f46e5",
          borderRadius: 40,
          padding: 28,
        }}
      >
        <div
          style={{
            width: "78%",
            height: 18,
            background: "rgba(255,255,255,0.55)",
            borderRadius: 9,
          }}
        />
        <div
          style={{
            width: "100%",
            height: 18,
            background: "rgba(255,255,255,0.85)",
            borderRadius: 9,
          }}
        />
        <div
          style={{
            width: "65%",
            height: 18,
            background: "#ffffff",
            borderRadius: 9,
          }}
        />
      </div>
    ),
    { ...size },
  );
}
