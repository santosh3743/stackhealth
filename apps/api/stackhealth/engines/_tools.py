"""Shared helpers for engines that shell out to binaries."""

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class EngineUnavailable(RuntimeError):
    """The engine's binary isn't installed in this environment."""


class EngineFailed(RuntimeError):
    """The engine ran but produced an error we can't interpret as a result."""


def require(binary: str) -> str:
    """Return the resolved path to `binary` or raise EngineUnavailable."""
    found = shutil.which(binary)
    if not found:
        raise EngineUnavailable(f"{binary} not found on PATH")
    return found


def run_capture(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    log.info("run", extra={"cmd": " ".join(cmd[:3]) + ("…" if len(cmd) > 3 else "")})
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
    except subprocess.TimeoutExpired as e:
        raise EngineFailed(f"{cmd[0]} timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise EngineUnavailable(f"{cmd[0]} not found") from e


def tool_version(binary: str, version_flag: str = "--version") -> str | None:
    """Best-effort version string. Returns None if the binary is missing."""
    try:
        binpath = require(binary)
    except EngineUnavailable:
        return None
    try:
        proc = run_capture([binpath, version_flag], timeout=10)
    except EngineFailed:
        return None
    out = (proc.stdout or proc.stderr).strip().splitlines()
    return out[0] if out else None
