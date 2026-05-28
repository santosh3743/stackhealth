"""Common FastAPI dependencies."""
from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from stackhealth.database import SessionLocal


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client_ip(request: Request) -> str | None:
    # Honor X-Forwarded-For (Fly.io / Cloudflare) but only the leftmost.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


# Re-exports
__all__ = ["get_db", "get_client_ip", "Depends"]
