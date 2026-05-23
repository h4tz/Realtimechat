import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def default_expiry():
    return timezone.now() + timedelta(days=1)


class Message(models.Model):
    """Enhanced Message model with better validation and methods."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_messages"
    )
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(default=default_expiry)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["room", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."

    def save(self, *args, **kwargs):
        if self.pk:  # If message already exists
            self.is_edited = True
            self.edited_at = timezone.now()
        super().save(*args, **kwargs)

    def to_dict(self):
        """Convert message to dictionary for API responses."""
        return {
            "id": str(self.id),
            "room": self.room,
            "user": {
                "id": self.user.id,
                "username": self.user.username,
            },
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }


class PrivateMessage(models.Model):
    """Enhanced PrivateMessage model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(
        User, related_name="sent_messages", on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        User, related_name="received_messages", on_delete=models.CASCADE
    )
    content = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user1", "timestamp"]),
            models.Index(fields=["user2", "timestamp"]),
        ]
        verbose_name = "Private Message"
        verbose_name_plural = "Private Messages"

    def __str__(self):
        return f"{self.user1.username} -> {self.user2.username}: {self.content[:50]}..."

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def to_dict(self):
        """Convert private message to dictionary."""
        return {
            "id": str(self.id),
            "user1": {
                "id": self.user1.id,
                "username": self.user1.username,
            },
            "user2": {
                "id": self.user2.id,
                "username": self.user2.username,
            },
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


class FileMessage(models.Model):
    """Enhanced FileMessage model with better handling."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="chat_files/", max_length=500)
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "File Message"
        verbose_name_plural = "File Messages"

    def __str__(self):
        return f"{self.original_name} by {self.uploaded_by.username}"

    def get_file_size_display(self):
        """Return human-readable file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class MutedUser(models.Model):
    """Muted user functionality."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="muted_users")
    muted_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="muted_by"
    )
    muted_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "muted_user"]
        verbose_name = "Muted User"
        verbose_name_plural = "Muted Users"

    def __str__(self):
        return f"{self.user.username} muted {self.muted_user.username} until {self.muted_until}"

    def is_active(self):
        """Check if mute is still active."""
        return timezone.now() < self.muted_until


class ChatActivity(models.Model):
    """Enhanced ChatActivity model for tracking user activities."""

    ACTION_CHOICES = [
        ("joined", "Joined Room"),
        ("left", "Left Room"),
        ("sent_message", "Sent Message"),
        ("typing", "Typing"),
        ("file_uploaded", "File Uploaded"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_activities"
    )
    room = models.CharField(max_length=100, db_index=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["room", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]
        verbose_name = "Chat Activity"
        verbose_name_plural = "Chat Activities"

    def __str__(self):
        return f"{self.user.username} {self.action} in {self.room}"

    def to_dict(self):
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "user": {
                "id": self.user.id,
                "username": self.user.username,
            },
            "room": self.room,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
