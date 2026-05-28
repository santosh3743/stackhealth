"""Test bootstrap.

Settings is instantiated at import time (config.py:settings) and requires
DATABASE_URL/REDIS_URL. The tests in this suite don't touch the database or
Redis — they only smoke-check FastAPI routes (`/`, `/api/health`) and the
pure-Python formula. We set placeholder values here so Pydantic's required-
field validation passes, with sqlite:// rather than postgres:// to make it
obvious these are not real services.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///not-used-in-tests")
os.environ.setdefault("REDIS_URL", "redis://not-used-in-tests")
