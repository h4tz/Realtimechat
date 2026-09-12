import os

# Set env vars BEFORE any other imports — ws_service.config needs these at import time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realtimechat.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DJANGO_DEBUG", "True")

import jwt
import pytest
import httpx
from datetime import datetime, timedelta, timezone
from django.conf import settings as django_settings
from django.contrib.auth.models import User

from chat.api import api
from chat.models import Message, PrivateMessage


# --- User fixtures ---

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser",
        password="otherpass123",
        email="other@example.com",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        password="adminpass123",
        email="admin@example.com",
    )


# --- Token fixtures ---

@pytest.fixture
def access_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "jti": "test-access-jti",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, django_settings.JWT_SECRET_KEY, algorithm=django_settings.JWT_ALGORITHM)


@pytest.fixture
def refresh_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": "test-refresh-jti",
        "iat": now,
        "exp": now + timedelta(days=7),
    }
    return jwt.encode(payload, django_settings.JWT_SECRET_KEY, algorithm=django_settings.JWT_ALGORITHM)


@pytest.fixture
def expired_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "jti": "test-expired-jti",
        "iat": now - timedelta(hours=25),
        "exp": now - timedelta(hours=1),
    }
    return jwt.encode(payload, django_settings.JWT_SECRET_KEY, algorithm=django_settings.JWT_ALGORITHM)


# --- Message fixtures ---

@pytest.fixture
def message(user):
    return Message.objects.create(
        room="testroom",
        user=user,
        content="Hello, world!",
    )


@pytest.fixture
def private_message(user, other_user):
    return PrivateMessage.objects.create(
        user1=user,
        user2=other_user,
        content="Private hello!",
    )


# --- Client fixtures ---

@pytest.fixture
def api_client():
    """httpx async client wired to the Ninja API via ASGI transport."""
    transport = httpx.ASGITransport(app=api)
    return httpx.AsyncClient(base_url="http://testserver", transport=transport)


@pytest.fixture
def auth_client(api_client, access_token):
    """httpx client with auth header set."""
    api_client.headers["Authorization"] = f"Bearer {access_token}"
    return api_client
