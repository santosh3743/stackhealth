"""RQ worker entrypoint.

Run with:
    uv run python -m stackhealth.worker.main

On macOS the default fork-based worker crashes because of libobjc fork safety.
We set OBJC_DISABLE_INITIALIZE_FORK_SAFETY before any imports that might touch
Foundation, and additionally use SimpleWorker which runs jobs in-process — no
fork at all. This is fine for a single-tenant deploy; Fly.io scales horizontally.
"""

import os
import sys

os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

import logging

from redis import Redis
from rq import Queue, SimpleWorker

from stackhealth.config import settings

QUEUE_NAME = "stackhealth"


def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    conn = Redis.from_url(settings.redis_url)
    queue = Queue(QUEUE_NAME, connection=conn)
    worker = SimpleWorker([queue], connection=conn)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
