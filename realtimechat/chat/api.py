import uuid
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from asgiref.sync import sync_to_async
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

# In-memory store for used refresh token JTIs (clears on server restart)
# For production, use Redis or Django cache backend
_used_refresh_tokens: set[str] = set()
_USED_TOKENS_MAX_SIZE = 10000


def _cleanup_used_tokens():
    """Prevent unbounded growth of used tokens set."""
    if len(_used_refresh_tokens) > _USED_TOKENS_MAX_SIZE:
        # Keep only the most recent half by clearing and letting re-populate
        _used_refresh_tokens.clear()


def create_tokens(user: User) -> dict:
    """Create JWT access and refresh tokens."""
    now = datetime.now(timezone.utc)
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())

    access_payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "jti": access_jti,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    refresh_payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": refresh_jti,
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


def _get_user_sync(user_id: int) -> Optional[User]:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


class JWTAuth(HttpBearer):
    """JWT authentication for Ninja endpoints."""

    async def authenticate(self, request, token: str):
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user = await sync_to_async(_get_user_sync)(int(payload["sub"]))
        return user


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

    # Check if this refresh token has already been used (rotation enforcement)
    jti = data.get("jti")
    if jti and jti in _used_refresh_tokens:
        return api.create_response(request, {"error": "Refresh token already used"}, status=401)

    # Mark the old refresh token as used
    if jti:
        _used_refresh_tokens.add(jti)
        _cleanup_used_tokens()

    try:
        user = User.objects.get(id=int(data["sub"]))
    except User.DoesNotExist:
        return api.create_response(request, {"error": "User not found"}, status=401)

    tokens = create_tokens(user)
    return TokenResponse(**tokens)


# --- User endpoints ---

@api.get("/users/", response=list[UserOut])
async def list_users(request):
    users = await sync_to_async(list)(User.objects.all().values("id", "username"))
    return [UserOut(id=u["id"], username=u["username"]) for u in users]


# --- Room endpoints ---

@api.get("/rooms/", response=list[RoomOut])
async def list_rooms(request):
    user = request.auth
    rooms = await sync_to_async(list)(
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
        for r in rooms
    ]


@api.get("/rooms/search/")
async def search_rooms(request, q: str = Query("")):
    if not q.strip():
        return {"rooms": []}
    rooms = await sync_to_async(list)(
        Message.objects.filter(room__icontains=q).values("room").distinct()[:10]
    )
    return {"rooms": [r["room"] for r in rooms]}


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

    per_page = min(per_page, 100)
    messages = await sync_to_async(list)(
        Message.objects.filter(room=room_name).order_by("-timestamp")
    )
    paginator = Paginator(messages, per_page)
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
    per_page = min(per_page, 100)

    messages = await sync_to_async(list)(
        PrivateMessage.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).order_by("-timestamp")
    )

    # Bulk mark unread messages as read (instead of N+1 individual saves)
    now = datetime.now(timezone.utc)
    await PrivateMessage.objects.filter(
        is_read=False, user2=user1, user1=user2
    ).aupdate(is_read=True, read_at=now)

    paginator = Paginator(messages, per_page)
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
