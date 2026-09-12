"""Tests for private message API endpoints."""
import pytest
from chat.models import PrivateMessage


@pytest.mark.django_db
class TestGetPrivateMessages:
    @pytest.mark.asyncio
    async def test_get_private_messages_empty(self, auth_client, other_user):
        resp = await auth_client.get(f"/api/private/{other_user.username}/messages/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["messages"] == []
        assert data["total_messages"] == 0

    @pytest.mark.asyncio
    async def test_get_private_messages_with_messages(self, auth_client, user, other_user):
        await PrivateMessage.objects.acreate(user1=user, user2=other_user, content="Hi")
        await PrivateMessage.objects.acreate(user1=other_user, user2=user, content="Hello")
        resp = await auth_client.get(f"/api/private/{other_user.username}/messages/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_private_messages_bidirectional(self, auth_client, user, other_user):
        await PrivateMessage.objects.acreate(user1=user, user2=other_user, content="A->B")
        await PrivateMessage.objects.acreate(user1=other_user, user2=user, content="B->A")
        resp = await auth_client.get(f"/api/private/{other_user.username}/messages/")
        contents = [m["content"] for m in resp.json()["messages"]]
        assert "A->B" in contents
        assert "B->A" in contents

    @pytest.mark.asyncio
    async def test_get_private_messages_marks_unread(self, auth_client, user, other_user):
        pm = await PrivateMessage.objects.acreate(
            user1=other_user, user2=user, content="Read me"
        )
        assert pm.is_read is False
        await auth_client.get(f"/api/private/{other_user.username}/messages/")
        await pm.arefresh_from_db()
        assert pm.is_read is True
        assert pm.read_at is not None

    @pytest.mark.asyncio
    async def test_get_private_messages_pagination(self, auth_client, user, other_user):
        for i in range(35):
            await PrivateMessage.objects.acreate(
                user1=user, user2=other_user, content=f"Msg {i}"
            )
        resp = await auth_client.get(
            f"/api/private/{other_user.username}/messages/?page=1&per_page=10"
        )
        data = resp.json()
        assert len(data["messages"]) == 10
        assert data["has_next"] is True
        assert data["total_messages"] == 35

    @pytest.mark.asyncio
    async def test_get_private_messages_user_not_found(self, auth_client):
        resp = await auth_client.get("/api/private/nonexistent/messages/")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_private_messages_requires_auth(self, api_client, other_user):
        resp = await api_client.get(f"/api/private/{other_user.username}/messages/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_private_messages_per_page_capped(self, auth_client, user, other_user):
        for i in range(5):
            await PrivateMessage.objects.acreate(
                user1=user, user2=other_user, content=f"Msg {i}"
            )
        resp = await auth_client.get(
            f"/api/private/{other_user.username}/messages/?per_page=99999"
        )
        assert len(resp.json()["messages"]) <= 100
