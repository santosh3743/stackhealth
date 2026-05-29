# Single image that powers both the API and the worker.
# The two stages (`api` and `worker`) share a Python base; the worker stage
# adds scanner binaries (semgrep, trivy, scorecard, cloc, lizard).
# See infra/docker-compose.prod.yml for how the two stages are wired up.

FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

# OS deps:
#   git        - required by the worker for shallow clones
#   ca-certs   - for HTTPS calls to github.com
#   curl       - used by entrypoint health probes
#   build-essential - for psycopg if installed from source (rare with binary wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy the whole API source (pyproject + package), then install. We could
# split deps from source for better cache, but uv is fast enough on rebuild
# that the simplicity wins. NO `|| true` — a failed install must fail the
# build, otherwise the runtime container errors with "uvicorn not found".
COPY apps/api /app
RUN uv pip install --system -e .

# ---------- worker-specific tools ----------
# These are heavy; only installed in the worker image variant.
# When building the API image, you can override with --target api-base to skip them.
FROM base AS worker-base

# Semgrep (Python) — its opentelemetry instrumentation imports pkg_resources.
# Python 3.12 dropped pkg_resources from stdlib AND setuptools 81+ dropped it
# from setuptools too. Pin to <81 to keep the import path alive.
RUN pip install --no-cache-dir "setuptools<81" semgrep==1.96.0

# Trivy (binary, arch-aware)
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) tv_arch="64bit" ;; \
      arm64) tv_arch="ARM64" ;; \
      *) echo "unsupported arch: $arch" && exit 1 ;; \
    esac; \
    curl -sSfL "https://github.com/aquasecurity/trivy/releases/download/v0.70.0/trivy_0.70.0_Linux-${tv_arch}.tar.gz" \
      | tar -xz -C /usr/local/bin trivy

# cloc + radon + lizard, plus Node + jscpd for duplication detection.
RUN apt-get update \
    && apt-get install -y --no-install-recommends cloc nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir radon==6.0.1 lizard==1.17.13 \
    && npm install -g --no-audit --no-fund jscpd@4.0.5 \
    && npm cache clean --force

# OpenSSF Scorecard binary (arch-aware: amd64 / arm64)
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
      amd64) sc_arch="amd64" ;; \
      arm64) sc_arch="arm64" ;; \
      *) echo "unsupported arch: $arch" && exit 1 ;; \
    esac; \
    curl -sSfL "https://github.com/ossf/scorecard/releases/download/v5.5.0/scorecard_5.5.0_linux_${sc_arch}.tar.gz" \
      | tar -xz -C /usr/local/bin scorecard

# ---------- final API stage (no scanners) ----------
FROM base AS api
CMD ["uvicorn", "stackhealth.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# ---------- final worker stage ----------
FROM worker-base AS worker
CMD ["python", "-m", "stackhealth.worker.main"]
