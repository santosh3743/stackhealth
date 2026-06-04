// Postbuild: chmod the entry point so it runs as a binary.
// tsc preserves the #!/usr/bin/env node shebang from the source.
import { chmodSync, existsSync } from "node:fs";

const bin = new URL("../dist/index.js", import.meta.url);
if (!existsSync(bin)) {
  console.error("dist/index.js not found — did tsc fail?");
  process.exit(1);
}
chmodSync(bin, 0o755);
