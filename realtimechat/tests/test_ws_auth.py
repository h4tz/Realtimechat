"""Tests for WebSocket authentication."""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User
from django.conf import settings

from ws_service.auth import decode_token, authenticate_user


class TestDecodeToken:
    def test_decode_valid_token(self, user):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "type": "access",
            "exp": now + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        result = decode_token(token)
        assert result is not None
        assert result["sub"] == str(user.id)

    def test_decode_invalid_token(self):
        assert decode_token("invalid.token") is None

    def test_decode_expired_token(self, user):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "type": "access",
            "exp": now - timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        assert decode_token(token) is None

    def test_decode_tampered_signature(self, user):
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user.id), "type": "access", "exp": now + timedelta(hours=1)}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        tampered = token[:-10] + "XXXXXXXX"
        assert decode_token(tampered) is None

    def test_decode_wrong_secret(self, user):
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user.id), "type": "access", "exp": now + timedelta(hours=1)}
        token = jwt.encode(payload, "wrong-secret", algorithm=settings.JWT_ALGORITHM)
        assert decode_token(token) is None


@pytest.mark.django_db
class TestAuthenticateUser:
    @pytest.mark.asyncio
    async def test_authenticate_valid_token(self, user):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "type": "access",
            "exp": now + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        result = await authenticate_user(token)
        assert result is not None
        assert result["id"] == user.id
        assert result["username"] == user.username

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self):
        result = await authenticate_user("bad-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_missing_sub(self):
        now = datetime.now(timezone.utc)
        payload = {"type": "access", "exp": now + timedelta(hours=1)}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        result = await authenticate_user(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self):
        now = datetime.now(timezone.utc)
        payload = {"sub": "99999", "type": "access", "exp": now + timedelta(hours=1)}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        result = await authenticate_user(token)
        assert result is None
