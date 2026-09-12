"""Tests for message API endpoints."""
import pytest
from chat.models import Message


@pytest.mark.django_db
class TestGetMessages:
    @pytest.mark.asyncio
    async def test_get_messages_empty_room(self, auth_client):
        resp = await auth_client.get("/api/rooms/general/messages/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["messages"] == []
        assert data["total_messages"] == 0

    @pytest.mark.asyncio
    async def test_get_messages_with_messages(self, auth_client, user):
        for i in range(5):
            await Message.objects.acreate(room="general", user=user, content=f"Msg {i}")
        resp = await auth_client.get("/api/rooms/general/messages/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 5
        assert data["total_messages"] == 5

    @pytest.mark.asyncio
    async def test_get_messages_pagination(self, auth_client, user):
        for i in range(25):
            await Message.objects.acreate(room="general", user=user, content=f"Msg {i}")
        resp = await auth_client.get("/api/rooms/general/messages/?page=1&per_page=10")
        data = resp.json()
        assert len(data["messages"]) == 10
        assert data["has_next"] is True
        assert data["has_previous"] is False
        assert data["total_pages"] == 3
        assert data["current_page"] == 1

    @pytest.mark.asyncio
    async def test_get_messages_page_2(self, auth_client, user):
        for i in range(25):
            await Message.objects.acreate(room="general", user=user, content=f"Msg {i}")
        resp = await auth_client.get("/api/rooms/general/messages/?page=2&per_page=10")
        data = resp.json()
        assert len(data["messages"]) == 10
        assert data["has_previous"] is True

    @pytest.mark.asyncio
    async def test_get_messages_per_page_capped(self, auth_client, user):
        for i in range(5):
            await Message.objects.acreate(room="general", user=user, content=f"Msg {i}")
        resp = await auth_client.get("/api/rooms/general/messages/?per_page=99999")
        data = resp.json()
        assert len(data["messages"]) <= 100

    @pytest.mark.asyncio
    async def test_get_messages_requires_auth(self, api_client):
        resp = await api_client.get("/api/rooms/general/messages/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message(self, auth_client, user):
        resp = await auth_client.post(
            "/api/rooms/general/messages/", json={"content": "Hello!"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Hello!"
        assert data["user"]["username"] == user.username
        assert data["room"] == "general"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, auth_client):
        resp = await auth_client.post(
            "/api/rooms/general/messages/", json={"content": ""}
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_whitespace_only(self, auth_client):
        resp = await auth_client.post(
            "/api/rooms/general/messages/", json={"content": "   "}
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_too_long(self, auth_client):
        resp = await auth_client.post(
            "/api/rooms/general/messages/", json={"content": "x" * 1001}
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_trims_whitespace(self, auth_client):
        resp = await auth_client.post(
            "/api/rooms/general/messages/", json={"content": "  trimmed  "}
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "trimmed"

    @pytest.mark.asyncio
    async def test_send_message_creates_in_db(self, auth_client, user):
        await auth_client.post("/api/rooms/testroom/messages/", json={"content": "DB check"})
        assert await Message.objects.filter(room="testroom", content="DB check").aexists()

    @pytest.mark.asyncio
    async def test_send_message_requires_auth(self, api_client):
        resp = await api_client.post(
            "/api/rooms/general/messages/", json={"content": "No auth"}
        )
        assert resp.status_code == 401
