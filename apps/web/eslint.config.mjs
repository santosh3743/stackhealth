// Flat config for ESLint 10 + Next.js 16.
// eslint-config-next v16 ships native flat-config arrays — no FlatCompat
// needed. Earlier we tried FlatCompat and hit a circular-ref bug in the
// legacy shim against the v16 plugin shape.

import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const config = [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  {
    ignores: [".next/**", "node_modules/**", "next-env.d.ts"],
  },
];

export default config;
