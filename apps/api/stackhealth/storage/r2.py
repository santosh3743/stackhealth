"""Cloudflare R2 (S3-compatible) client for raw scan artifacts."""
import json
from functools import lru_cache

import boto3

from stackhealth.config import settings


@lru_cache
def _client():
    if not (settings.r2_account_id and settings.r2_access_key_id and settings.r2_secret_access_key):
        raise RuntimeError("R2 credentials not configured")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def upload_json(key: str, payload: dict) -> str:
    """Upload `payload` as JSON to R2, return its public URL."""
    body = json.dumps(payload, separators=(",", ":")).encode()
    _client().put_object(
        Bucket=settings.r2_bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
        CacheControl="public, max-age=31536000, immutable",
    )
    return f"{settings.r2_public_url}/{key}"
