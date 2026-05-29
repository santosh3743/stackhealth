// The icon paired with the "StackHealth" wordmark in headers and footers.
// Same visual language as app/icon.tsx and app/apple-icon.tsx.

export function LogoMark({ size = 22 }: { size?: number }) {
  const r = size / 4.5;
  const gap = Math.max(1.5, size * 0.08);
  const barHeight = Math.max(2, size * 0.11);

  return (
    <div
      role="img"
      aria-label="StackHealth"
      style={{
        width: size,
        height: size,
        background: "#4f46e5",
        borderRadius: r,
      }}
      className="inline-flex flex-col items-center justify-center shrink-0"
    >
      <span
        style={{
          width: "78%",
          height: barHeight,
          background: "rgba(255,255,255,0.55)",
          borderRadius: barHeight / 2,
          marginBottom: gap,
        }}
      />
      <span
        style={{
          width: "100%",
          height: barHeight,
          background: "rgba(255,255,255,0.85)",
          borderRadius: barHeight / 2,
          marginBottom: gap,
        }}
      />
      <span
        style={{
          width: "65%",
          height: barHeight,
          background: "#ffffff",
          borderRadius: barHeight / 2,
        }}
      />
    </div>
  );
}
