import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from ninja import NinjaAPI, Query
from ninja.security import HttpBearer

from .models import Message, PrivateMessage
from .schemas import (
    MessageOut,
    MessageCreate,
    PaginatedMessages,
    PaginatedPrivateMessages,
    PrivateMessageOut,
    RoomCreate,
    RoomOut,
    TokenRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserOut,
)


def create_tokens(user: User) -> dict:
    """Create JWT access and refresh tokens."""
    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    refresh_payload = {
        "sub": str(user.id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=7),
    }
    return {
        "access": jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM),
        "refresh": jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM),
    }


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


class JWTAuth(HttpBearer):
    """JWT authentication for Ninja endpoints."""

    def authenticate(self, request, token: str):
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        try:
            user = User.objects.get(id=int(payload["sub"]))
            return user
        except User.DoesNotExist:
            return None


api = NinjaAPI(auth=JWTAuth())


# --- Auth endpoints (no auth required) ---

@api.post("/token/", response=TokenResponse, auth=None)
def get_token(request, payload: TokenRequest):
    user = authenticate(username=payload.username, password=payload.password)
    if not user:
        return api.create_response(request, {"error": "Invalid credentials"}, status=401)
    tokens = create_tokens(user)
    return TokenResponse(**tokens)


@api.post("/token/refresh/", response=TokenResponse, auth=None)
def refresh_token(request, payload: TokenRefreshRequest):
    data = decode_token(payload.refresh)
    if not data or data.get("type") != "refresh":
        return api.create_response(request, {"error": "Invalid refresh token"}, status=401)
    try:
        user = User.objects.get(id=int(data["sub"]))
    except User.DoesNotExist:
        return api.create_response(request, {"error": "User not found"}, status=401)
    tokens = create_tokens(user)
    return TokenResponse(**tokens)


# --- User endpoints ---

@api.get("/users/", response=list[UserOut])
async def list_users(request):
    users = [user async for user in User.objects.all()]
    return [UserOut(id=u.id, username=u.username) for u in users]


# --- Room endpoints ---

@api.get("/rooms/", response=list[RoomOut])
async def list_rooms(request):
    user = request.auth
    rooms = (
        Message.objects.filter(user=user)
        .values("room")
        .annotate(
            message_count=Count("id"),
            last_message=Max("timestamp"),
        )
        .order_by("-last_message")[:20]
    )
    return [
        RoomOut(room=r["room"], message_count=r["message_count"], last_message=r["last_message"])
        async for r in rooms
    ]


@api.get("/rooms/search/")
async def search_rooms(request, q: str = Query("")):
    if not q.strip():
        return {"rooms": []}
    rooms = [
        r["room"]
        async for r in Message.objects.filter(room__icontains=q).values("room").distinct()[:10]
    ]
    return {"rooms": rooms}


@api.post("/rooms/create/")
async def create_room(request, payload: RoomCreate):
    room_name = payload.room_name.strip()
    if not room_name or len(room_name) > 100:
        return api.create_response(request, {"error": "Invalid room name"}, status=400)

    exists = await Message.objects.filter(room=room_name).aexists()
    if exists:
        return api.create_response(request, {"error": "Room already exists"}, status=400)

    await Message.objects.acreate(
        room=room_name,
        user=request.auth,
        content=f"{request.auth.username} created the room",
    )
    return {"success": True, "room_name": room_name, "redirect_url": f"/chat/{room_name}/"}


# --- Message endpoints ---

@api.get("/rooms/{room_name}/messages/", response=PaginatedMessages)
async def get_messages(request, room_name: str, page: int = 1, per_page: int = 20):
    if not room_name or len(room_name) > 100:
        return api.create_response(request, {"error": "Invalid room name"}, status=400)

    messages = Message.objects.filter(room=room_name).order_by("-timestamp")
    paginator = Paginator(await sync_to_async_list(messages), per_page)
    page_obj = paginator.get_page(page)

    messages_data = [
        MessageOut(
            id=str(m.id),
            room=m.room,
            user=UserOut(id=m.user.id, username=m.user.username),
            content=m.content,
            timestamp=m.timestamp,
            is_edited=m.is_edited,
            edited_at=m.edited_at,
        )
        for m in page_obj.object_list
    ]

    return PaginatedMessages(
        messages=messages_data,
        has_next=page_obj.has_next(),
        has_previous=page_obj.has_previous(),
        current_page=page_obj.number,
        total_pages=paginator.num_pages,
        total_messages=paginator.count,
    )


@api.post("/rooms/{room_name}/messages/", response=MessageOut)
async def send_message(request, room_name: str, payload: MessageCreate):
    content = payload.content.strip()
    if not content or len(content) > 1000:
        return api.create_response(request, {"error": "Invalid message length"}, status=400)

    message = await Message.objects.acreate(
        room=room_name,
        user=request.auth,
        content=content,
    )
    return MessageOut(
        id=str(message.id),
        room=message.room,
        user=UserOut(id=message.user.id, username=message.user.username),
        content=message.content,
        timestamp=message.timestamp,
        is_edited=message.is_edited,
        edited_at=message.edited_at,
    )


# --- Private message endpoints ---

@api.get("/private/{username}/messages/", response=PaginatedPrivateMessages)
async def get_private_messages(request, username: str, page: int = 1, per_page: int = 30):
    try:
        user2 = await User.objects.aget(username=username)
    except User.DoesNotExist:
        return api.create_response(request, {"error": "User not found"}, status=404)

    user1 = request.auth
    messages = PrivateMessage.objects.filter(
        Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
    ).order_by("-timestamp")

    # Mark unread messages as read
    unread = PrivateMessage.objects.filter(is_read=False, user2=user1, user1=user2)
    async for msg in unread:
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        await msg.asave()

    messages_list = await sync_to_async_list(messages)
    paginator = Paginator(messages_list, per_page)
    page_obj = paginator.get_page(page)

    messages_data = [
        PrivateMessageOut(
            id=str(m.id),
            user1=UserOut(id=m.user1.id, username=m.user1.username),
            user2=UserOut(id=m.user2.id, username=m.user2.username),
            content=m.content,
            timestamp=m.timestamp,
            is_read=m.is_read,
            read_at=m.read_at,
        )
        for m in page_obj.object_list
    ]

    return PaginatedPrivateMessages(
        messages=messages_data,
        has_next=page_obj.has_next(),
        has_previous=page_obj.has_previous(),
        current_page=page_obj.number,
        total_pages=paginator.num_pages,
        total_messages=paginator.count,
    )


# --- Helper ---

async def sync_to_async_list(queryset):
    """Evaluate a queryset asynchronously."""
    return [item async for item in queryset]
