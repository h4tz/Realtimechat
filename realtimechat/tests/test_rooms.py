"""Tests for room API endpoints."""
import pytest
from chat.models import Message


@pytest.mark.django_db
class TestListRooms:
    @pytest.mark.asyncio
    async def test_list_rooms_empty(self, auth_client):
        resp = await auth_client.get("/api/rooms/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_rooms_with_messages(self, auth_client, user):
        await Message.objects.acreate(room="general", user=user, content="Hi")
        await Message.objects.acreate(room="random", user=user, content="Hey")
        resp = await auth_client.get("/api/rooms/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_rooms_max_20(self, auth_client, user):
        for i in range(25):
            await Message.objects.acreate(room=f"room_{i}", user=user, content=f"msg_{i}")
        resp = await auth_client.get("/api/rooms/")
        assert len(resp.json()) == 20

    @pytest.mark.asyncio
    async def test_list_rooms_requires_auth(self, api_client):
        resp = await api_client.get("/api/rooms/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestSearchRooms:
    @pytest.mark.asyncio
    async def test_search_rooms(self, auth_client, user):
        await Message.objects.acreate(room="general", user=user, content="Hi")
        await Message.objects.acreate(room="gaming", user=user, content="Play")
        resp = await auth_client.get("/api/rooms/search/?q=gen")
        assert resp.status_code == 200
        assert "general" in resp.json()["rooms"]

    @pytest.mark.asyncio
    async def test_search_rooms_empty_query(self, auth_client, user):
        await Message.objects.acreate(room="general", user=user, content="Hi")
        resp = await auth_client.get("/api/rooms/search/?q=")
        assert resp.status_code == 200
        assert resp.json()["rooms"] == []

    @pytest.mark.asyncio
    async def test_search_rooms_whitespace_query(self, auth_client, user):
        await Message.objects.acreate(room="general", user=user, content="Hi")
        resp = await auth_client.get("/api/rooms/search/?q=%20%20")
        assert resp.json()["rooms"] == []

    @pytest.mark.asyncio
    async def test_search_no_results(self, auth_client, user):
        await Message.objects.acreate(room="general", user=user, content="Hi")
        resp = await auth_client.get("/api/rooms/search/?q=nonexistent")
        assert resp.json()["rooms"] == []


@pytest.mark.django_db
class TestCreateRoom:
    @pytest.mark.asyncio
    async def test_create_room(self, auth_client):
        resp = await auth_client.post("/api/rooms/create/", json={"room_name": "newroom"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["room_name"] == "newroom"
        assert "/chat/newroom/" in data["redirect_url"]

    @pytest.mark.asyncio
    async def test_create_room_trims_whitespace(self, auth_client):
        resp = await auth_client.post("/api/rooms/create/", json={"room_name": "  spaced  "})
        assert resp.status_code == 200
        assert resp.json()["room_name"] == "spaced"

    @pytest.mark.asyncio
    async def test_create_room_empty_name(self, auth_client):
        resp = await auth_client.post("/api/rooms/create/", json={"room_name": ""})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_room_too_long(self, auth_client):
        resp = await auth_client.post("/api/rooms/create/", json={"room_name": "x" * 101})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_room_duplicate(self, auth_client, user):
        await Message.objects.acreate(room="existing", user=user, content="Hi")
        resp = await auth_client.post("/api/rooms/create/", json={"room_name": "existing"})
        assert resp.status_code == 400
        assert "already exists" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_create_room_requires_auth(self, api_client):
        resp = await api_client.post("/api/rooms/create/", json={"room_name": "room"})
        assert resp.status_code == 401
