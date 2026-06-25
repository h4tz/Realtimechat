import jwt
from datetime import datetime, timedelta, timezone

from django.conf import settings


def jwt_token_processor(request):
    """Add JWT token to template context for WebSocket auth."""
    if request.user.is_authenticated:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(request.user.id),
            "username": request.user.username,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return {"ws_token": token}
    return {"ws_token": ""}
