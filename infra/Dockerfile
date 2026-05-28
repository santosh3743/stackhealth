# Single image that powers both the API and the worker.
# Different CMD per Fly app (see fly.api.toml / fly.worker.toml).

FROM python:3.12-slim AS base

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

# Dependency caching layer
COPY apps/api/pyproject.toml /app/
RUN uv pip install --system -e .[dev] || true

# App source
COPY apps/api /app

# ---------- worker-specific tools ----------
# These are heavy; only installed in the worker image variant.
# When building the API image, you can override with --target api-base to skip them.
FROM base AS worker-base

# Semgrep (Python)
RUN pip install --no-cache-dir semgrep==1.96.0

# Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin v0.57.1

# cloc + radon + lizard + jscpd
RUN apt-get update && apt-get install -y --no-install-recommends cloc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir radon==6.0.1 lizard==1.17.13

# OpenSSF Scorecard binary
RUN curl -sSfL https://github.com/ossf/scorecard/releases/download/v5.0.0/scorecard_5.0.0_linux_amd64.tar.gz \
    | tar -xz -C /usr/local/bin scorecard

# ---------- final API stage (no scanners) ----------
FROM base AS api
CMD ["uvicorn", "stackhealth.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# ---------- final worker stage ----------
FROM worker-base AS worker
CMD ["python", "-m", "stackhealth.worker.main"]
