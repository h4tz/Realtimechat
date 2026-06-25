import aiosqlite

from .config import SQLITE_PATH


async def get_user_by_id(user_id: int) -> dict | None:
    """Fetch a user from Django's auth_user table."""
    async with aiosqlite.connect(SQLITE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, username FROM auth_user WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_by_username(username: str) -> dict | None:
    """Fetch a user by username."""
    async with aiosqlite.connect(SQLITE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, username FROM auth_user WHERE username = ?", (username,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_id_pair(username: str) -> tuple[int, int] | None:
    """Get (user1_id, user2_id) pair for private chat, ordered consistently."""
    from .auth import decode_token  # avoid circular
    # This is called from WS handler which already has the current user
    pass


async def save_message(room: str, user_id: int, content: str) -> dict:
    """Insert a message into chat_message and return it."""
    import uuid
    from datetime import datetime, timezone

    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    expiry = datetime.now(timezone.utc).replace(
        day=datetime.now(timezone.utc).day + 1
    ).isoformat()

    async with aiosqlite.connect(SQLITE_PATH) as db:
        await db.execute(
            """INSERT INTO chat_message (id, room, user_id, content, timestamp, expires_at, is_edited, edited_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, room, user_id, content, now, expiry, 0, None),
        )
        await db.commit()

    user = await get_user_by_id(user_id)
    return {
        "id": msg_id,
        "room": room,
        "user": {"id": user_id, "username": user["username"] if user else "unknown"},
        "content": content,
        "timestamp": now,
        "is_edited": False,
    }


async def save_private_message(user1_id: int, user2_id: int, content: str) -> dict:
    """Insert a private message and return it."""
    import uuid
    from datetime import datetime, timezone

    # Order user IDs consistently for the pair
    uid1, uid2 = (min(user1_id, user2_id), max(user1_id, user2_id))

    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(SQLITE_PATH) as db:
        await db.execute(
            """INSERT INTO chat_privatemessage (id, user1_id, user2_id, content, timestamp, is_read, read_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, uid1, uid2, content, now, 0, None),
        )
        await db.commit()

    user1 = await get_user_by_id(user1_id)
    user2 = await get_user_by_id(user2_id)
    return {
        "id": msg_id,
        "user1": {"id": uid1, "username": user1["username"] if user1 else "unknown"},
        "user2": {"id": uid2, "username": user2["username"] if user2 else "unknown"},
        "content": content,
        "timestamp": now,
        "is_read": False,
    }
