import os
from pathlib import Path

# JWT settings (must match Django settings)
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY",
    os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-in-production"),
)
JWT_ALGORITHM = "HS256"

# Database
BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = os.environ.get("SQLITE_PATH", str(BASE_DIR / "realtimechat" / "db.sqlite3"))

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")

# Server
WS_HOST = os.environ.get("WS_HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("WS_PORT", "8001"))
