from django.contrib import admin

from .models import ChatActivity, FileMessage, Message, MutedUser, PrivateMessage


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "content", "timestamp", "is_edited")
    list_filter = ("room", "timestamp", "is_edited")
    search_fields = ("content", "user__username")
    readonly_fields = ("id", "timestamp", "edited_at")


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ("user1", "user2", "content", "timestamp", "is_read")
    list_filter = ("is_read", "timestamp")
    search_fields = ("content", "user1__username", "user2__username")
    readonly_fields = ("id", "timestamp", "read_at")


@admin.register(FileMessage)
class FileMessageAdmin(admin.ModelAdmin):
    list_display = ("original_name", "uploaded_by", "file_size", "mime_type", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("original_name", "uploaded_by__username")
    readonly_fields = ("id", "uploaded_at")


@admin.register(MutedUser)
class MutedUserAdmin(admin.ModelAdmin):
    list_display = ("user", "muted_user", "muted_until", "created_at")
    list_filter = ("created_at",)
    readonly_fields = ("id", "created_at")


@admin.register(ChatActivity)
class ChatActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "room", "action", "timestamp")
    list_filter = ("action", "room", "timestamp")
    search_fields = ("user__username", "room")
    readonly_fields = ("id", "timestamp")
