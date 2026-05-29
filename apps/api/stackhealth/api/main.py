"""FastAPI app entrypoint.

Run with:
    uv run uvicorn stackhealth.api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stackhealth import __version__
from stackhealth.api.routes import badge, discover, health, repos, scans
from stackhealth.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.env,
            traces_sample_rate=0.1,
        )
    yield


app = FastAPI(
    title="StackHealth API",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
app.include_router(badge.router, tags=["badge"])
app.include_router(discover.router, tags=["discover"])


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "stackhealth-api", "version": __version__, "docs": "/api/docs"}
