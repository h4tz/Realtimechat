import os
from pathlib import Path

# JWT settings (must match Django settings)
# In development (DJANGO_DEBUG=True), falls back to DJANGO_SECRET_KEY.
# In production, JWT_SECRET_KEY must be explicitly set.
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY")
JWT_ALGORITHM = "HS256"

if not DEBUG and not os.environ.get("JWT_SECRET_KEY"):
    raise ValueError(
        "JWT_SECRET_KEY environment variable is required in production. "
        "Set it to a secure random string."
    )

# Database
BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = os.environ.get("SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")

# Server
WS_HOST = os.environ.get("WS_HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("WS_PORT", "8001"))
