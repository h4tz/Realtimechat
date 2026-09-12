"""Tests for authentication API endpoints."""
import pytest
from django.contrib.auth.models import User

from chat.api import create_tokens, decode_token


# --- Token utility tests ---

@pytest.mark.django_db
class TestTokenUtils:
    def test_create_tokens_returns_both(self, user):
        tokens = create_tokens(user)
        assert "access" in tokens
        assert "refresh" in tokens

    def test_access_token_decodes(self, user):
        tokens = create_tokens(user)
        payload = decode_token(tokens["access"])
        assert payload is not None
        assert payload["sub"] == str(user.id)
        assert payload["username"] == user.username
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_refresh_token_decodes(self, user):
        tokens = create_tokens(user)
        payload = decode_token(tokens["refresh"])
        assert payload is not None
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        assert decode_token("invalid.token.here") is None

    def test_decode_tampered_token(self, user):
        tokens = create_tokens(user)
        tampered = tokens["access"][:-5] + "XXXXX"
        assert decode_token(tampered) is None


# --- Token endpoint tests ---

@pytest.mark.django_db
class TestTokenEndpoint:
    @pytest.mark.asyncio
    async def test_get_token_valid(self, api_client):
        await User.objects.acreate(username="alice", password="pass1234")
        resp = await api_client.post("/api/token/", json={"username": "alice", "password": "pass1234"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

    @pytest.mark.asyncio
    async def test_get_token_invalid_password(self, api_client):
        await User.objects.acreate(username="bob", password="pass1234")
        resp = await api_client.post("/api/token/", json={"username": "bob", "password": "wrong"})
        assert resp.status_code == 401
        assert "error" in resp.json()

    @pytest.mark.asyncio
    async def test_get_token_nonexistent_user(self, api_client):
        resp = await api_client.post("/api/token/", json={"username": "nobody", "password": "pass"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_token_empty_fields(self, api_client):
        resp = await api_client.post("/api/token/", json={"username": "", "password": ""})
        assert resp.status_code == 401


# --- Token refresh endpoint tests ---

@pytest.mark.django_db
class TestTokenRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_refresh_valid(self, api_client, user, refresh_token):
        resp = await api_client.post("/api/token/refresh/", json={"refresh": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, api_client, user, access_token):
        resp = await api_client.post("/api/token/refresh/", json={"refresh": access_token})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, api_client):
        resp = await api_client.post("/api/token/refresh/", json={"refresh": "garbage"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_reuse_token_fails(self, api_client, user, refresh_token):
        resp1 = await api_client.post("/api/token/refresh/", json={"refresh": refresh_token})
        assert resp1.status_code == 200
        resp2 = await api_client.post("/api/token/refresh/", json={"refresh": refresh_token})
        assert resp2.status_code == 401


# --- JWT Auth class tests ---

@pytest.mark.django_db
class TestJWTAuth:
    @pytest.mark.asyncio
    async def test_authenticated_request(self, auth_client):
        resp = await auth_client.get("/api/users/")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_request(self, api_client):
        resp = await api_client.get("/api/users/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token(self, api_client, expired_token):
        api_client.headers["Authorization"] = f"Bearer {expired_token}"
        resp = await api_client.get("/api/users/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_format(self, api_client):
        api_client.headers["Authorization"] = "Bearer not.a.jwt"
        resp = await api_client.get("/api/users/")
        assert resp.status_code == 401
