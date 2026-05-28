import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "StackHealth — the open code health benchmark",
    template: "%s · StackHealth",
  },
  description:
    "Score any public GitHub repository on security, quality, hygiene, and community — with a fully open, versioned formula.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  openGraph: {
    title: "StackHealth — the open code health benchmark",
    description:
      "Paste a GitHub URL. Get a score. Share the report. Formula is fully open.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
