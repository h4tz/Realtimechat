"""Tests for chat models."""
import uuid
import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone

from chat.models import (
    Message,
    PrivateMessage,
    FileMessage,
    MutedUser,
    ChatActivity,
    default_expiry,
)


# --- Message model tests ---

@pytest.mark.django_db
class TestMessage:
    def test_create_message(self, user):
        msg = Message.objects.create(room="general", user=user, content="Hello!")
        assert msg.room == "general"
        assert msg.content == "Hello!"
        assert msg.user == user

    def test_uuid_primary_key(self, user):
        msg = Message.objects.create(room="general", user=user, content="Test")
        assert isinstance(msg.id, uuid.UUID)

    def test_default_expiry(self):
        exp = default_expiry()
        assert exp > timezone.now()
        assert exp <= timezone.now() + timedelta(days=1, seconds=5)

    def test_str_representation(self, user):
        msg = Message.objects.create(room="general", user=user, content="A" * 60)
        assert str(msg) == f"{user.username}: {'A' * 50}..."

    def test_save_sets_edited_on_update(self, user):
        msg = Message.objects.create(room="general", user=user, content="Original")
        msg.content = "Edited"
        msg.save()
        msg.refresh_from_db()
        assert msg.is_edited is True
        assert msg.edited_at is not None

    def test_to_dict(self, user):
        msg = Message.objects.create(room="general", user=user, content="Test msg")
        d = msg.to_dict()
        assert d["id"] == str(msg.id)
        assert d["room"] == "general"
        assert d["user"]["id"] == user.id
        assert d["user"]["username"] == user.username
        assert d["content"] == "Test msg"
        assert "timestamp" in d
        assert "is_edited" in d

    def test_ordering(self, user):
        m1 = Message.objects.create(room="general", user=user, content="First")
        m2 = Message.objects.create(room="general", user=user, content="Second")
        msgs = list(Message.objects.all())
        assert msgs[0].content == "Second"
        assert msgs[1].content == "First"

    def test_cascade_delete_user(self, user):
        Message.objects.create(room="general", user=user, content="Test")
        assert Message.objects.count() == 1
        user.delete()
        assert Message.objects.count() == 0

    def test_content_max_length(self, user):
        msg = Message.objects.create(room="general", user=user, content="x" * 1000)
        assert len(msg.content) == 1000


# --- PrivateMessage model tests ---

@pytest.mark.django_db
class TestPrivateMessage:
    def test_create_private_message(self, user, other_user):
        pm = PrivateMessage.objects.create(
            user1=user, user2=other_user, content="Private hello!"
        )
        assert pm.user1 == user
        assert pm.user2 == other_user
        assert pm.content == "Private hello!"
        assert pm.is_read is False
        assert pm.read_at is None

    def test_mark_as_read(self, user, other_user):
        pm = PrivateMessage.objects.create(
            user1=user, user2=other_user, content="Read me"
        )
        assert pm.is_read is False
        pm.mark_as_read()
        pm.refresh_from_db()
        assert pm.is_read is True
        assert pm.read_at is not None

    def test_mark_as_read_idempotent(self, user, other_user):
        pm = PrivateMessage.objects.create(
            user1=user, user2=other_user, content="Idempotent"
        )
        pm.mark_as_read()
        first_read_at = pm.read_at
        pm.mark_as_read()
        pm.refresh_from_db()
        assert pm.read_at == first_read_at

    def test_str_representation(self, user, other_user):
        pm = PrivateMessage.objects.create(
            user1=user, user2=other_user, content="A" * 60
        )
        expected = f"{user.username} -> {other_user.username}: {'A' * 50}..."
        assert str(pm) == expected

    def test_to_dict(self, user, other_user):
        pm = PrivateMessage.objects.create(
            user1=user, user2=other_user, content="Dict test"
        )
        d = pm.to_dict()
        assert d["id"] == str(pm.id)
        assert d["user1"]["username"] == user.username
        assert d["user2"]["username"] == other_user.username
        assert d["content"] == "Dict test"
        assert d["is_read"] is False
        assert d["read_at"] is None

    def test_cascade_delete_user(self, user, other_user):
        PrivateMessage.objects.create(user1=user, user2=other_user, content="Test")
        assert PrivateMessage.objects.count() == 1
        user.delete()
        assert PrivateMessage.objects.count() == 0


# --- FileMessage model tests ---

@pytest.mark.django_db
class TestFileMessage:
    def test_create_file_message(self, user):
        fm = FileMessage.objects.create(
            file="chat_files/test.txt",
            original_name="test.txt",
            file_size=1024,
            mime_type="text/plain",
            uploaded_by=user,
        )
        assert fm.original_name == "test.txt"
        assert fm.file_size == 1024
        assert fm.mime_type == "text/plain"

    def test_str_representation(self, user):
        fm = FileMessage.objects.create(
            file="chat_files/test.txt",
            original_name="test.txt",
            file_size=500,
            uploaded_by=user,
        )
        assert str(fm) == f"test.txt by {user.username}"

    def test_get_file_size_display_bytes(self, user):
        fm = FileMessage.objects.create(
            file="chat_files/small.txt",
            original_name="small.txt",
            file_size=500,
            uploaded_by=user,
        )
        assert fm.get_file_size_display() == "500 B"

    def test_get_file_size_display_kb(self, user):
        fm = FileMessage.objects.create(
            file="chat_files/medium.txt",
            original_name="medium.txt",
            file_size=2048,
            uploaded_by=user,
        )
        assert fm.get_file_size_display() == "2.0 KB"

    def test_get_file_size_display_mb(self, user):
        fm = FileMessage.objects.create(
            file="chat_files/large.txt",
            original_name="large.txt",
            file_size=2 * 1024 * 1024,
            uploaded_by=user,
        )
        assert fm.get_file_size_display() == "2.0 MB"


# --- MutedUser model tests ---

@pytest.mark.django_db
class TestMutedUser:
    def test_create_muted_user(self, user, other_user):
        mu = MutedUser.objects.create(
            user=user,
            muted_user=other_user,
            muted_until=timezone.now() + timedelta(hours=1),
        )
        assert mu.user == user
        assert mu.muted_user == other_user

    def test_is_active_true(self, user, other_user):
        mu = MutedUser.objects.create(
            user=user,
            muted_user=other_user,
            muted_until=timezone.now() + timedelta(hours=1),
        )
        assert mu.is_active() is True

    def test_is_active_false(self, user, other_user):
        mu = MutedUser.objects.create(
            user=user,
            muted_user=other_user,
            muted_until=timezone.now() - timedelta(hours=1),
        )
        assert mu.is_active() is False

    def test_unique_together(self, user, other_user):
        MutedUser.objects.create(
            user=user,
            muted_user=other_user,
            muted_until=timezone.now() + timedelta(hours=1),
        )
        with pytest.raises(Exception):
            MutedUser.objects.create(
                user=user,
                muted_user=other_user,
                muted_until=timezone.now() + timedelta(hours=2),
            )

    def test_str_representation(self, user, other_user):
        until = timezone.now() + timedelta(hours=1)
        mu = MutedUser.objects.create(
            user=user, muted_user=other_user, muted_until=until
        )
        assert str(mu) == f"{user.username} muted {other_user.username} until {until}"


# --- ChatActivity model tests ---

@pytest.mark.django_db
class TestChatActivity:
    def test_create_activity(self, user):
        act = ChatActivity.objects.create(
            user=user, room="general", action="joined"
        )
        assert act.user == user
        assert act.room == "general"
        assert act.action == "joined"
        assert act.details == {}

    def test_all_action_choices(self, user):
        for action, _ in ChatActivity.ACTION_CHOICES:
            act = ChatActivity.objects.create(user=user, room="r", action=action)
            assert act.action == action

    def test_to_dict(self, user):
        act = ChatActivity.objects.create(
            user=user, room="general", action="sent_message", details={"key": "val"}
        )
        d = act.to_dict()
        assert d["user"]["username"] == user.username
        assert d["room"] == "general"
        assert d["action"] == "sent_message"
        assert d["details"] == {"key": "val"}
        assert "timestamp" in d

    def test_str_representation(self, user):
        act = ChatActivity.objects.create(user=user, room="general", action="joined")
        assert str(act) == f"{user.username} joined in general"

    def test_default_details(self, user):
        act = ChatActivity.objects.create(user=user, room="r", action="typing")
        assert act.details == {}
