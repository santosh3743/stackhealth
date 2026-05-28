"""Shallow git clone helper. Hard timeout + size cap.

Security: see docs/12-SECURITY-AND-PRIVACY.md §"Scanning sandbox".
"""

import logging
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from stackhealth.config import settings

log = logging.getLogger(__name__)


class CloneFailed(RuntimeError):
    pass


@contextmanager
def shallow_clone(repo_url: str):
    """Clone `repo_url` into a temporary directory; yield (commit_sha, workdir).

    On exit (success or failure) the tmpdir is deleted.
    Raises CloneFailed on timeout, size-cap breach, or non-zero exit.
    """
    with tempfile.TemporaryDirectory(prefix="sh-scan-") as tmp:
        workdir = Path(tmp) / "repo"
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter",
            f"blob:limit={settings.clone_size_limit_mb}m",
            repo_url,
            str(workdir),
        ]
        log.info("cloning", extra={"repo_url": repo_url})
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=settings.clone_timeout_seconds,
            )
        except subprocess.TimeoutExpired as e:
            raise CloneFailed("clone_timeout") from e
        except subprocess.CalledProcessError as e:
            raise CloneFailed(f"clone_failed: {e.stderr.decode()[:200]}") from e

        commit_sha = subprocess.run(
            ["git", "-C", str(workdir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        yield commit_sha, workdir
