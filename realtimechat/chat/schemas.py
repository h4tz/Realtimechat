from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Auth ---

class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access: str
    refresh: str


class TokenRefreshRequest(BaseModel):
    refresh: str


# --- User ---

class UserOut(BaseModel):
    id: int
    username: str


# --- Message ---

class MessageOut(BaseModel):
    id: str
    room: str
    user: UserOut
    content: str
    timestamp: datetime
    is_edited: bool
    edited_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    content: str


# --- Private Message ---

class PrivateMessageOut(BaseModel):
    id: str
    user1: UserOut
    user2: UserOut
    content: str
    timestamp: datetime
    is_read: bool
    read_at: Optional[datetime] = None


# --- Room ---

class RoomCreate(BaseModel):
    room_name: str


class RoomOut(BaseModel):
    room: str
    message_count: int
    last_message: datetime


# --- Pagination ---

class PaginatedMessages(BaseModel):
    messages: list[MessageOut]
    has_next: bool
    has_previous: bool
    current_page: int
    total_pages: int
    total_messages: int


class PaginatedPrivateMessages(BaseModel):
    messages: list[PrivateMessageOut]
    has_next: bool
    has_previous: bool
    current_page: int
    total_pages: int
    total_messages: int
