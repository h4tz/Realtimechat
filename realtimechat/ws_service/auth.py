import jwt
from . import config
from .models import get_user_by_id


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except (jwt.PyJWTError, TypeError):
        return None


async def authenticate_user(token: str) -> dict | None:
    """Validate JWT and return the user dict."""
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return await get_user_by_id(int(user_id))
