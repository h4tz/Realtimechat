import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..auth import authenticate_user
from ..connection_manager import manager
from ..models import get_user_by_username, save_private_message

logger = logging.getLogger(__name__)
router = APIRouter()


def get_private_room_name(user1_id: int, user2_id: int) -> str:
    """Generate consistent private room name for two users."""
    return f"private_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"


@router.websocket("/ws/private/{target_username}/")
async def websocket_private_chat(websocket: WebSocket, target_username: str, token: str):
    """WebSocket endpoint for private chat."""
    # Authenticate current user
    user = await authenticate_user(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Look up target user
    target = await get_user_by_username(target_username)
    if not target:
        await websocket.close(code=4002, reason="User not found")
        return

    if user["id"] == target["id"]:
        await websocket.close(code=4003, reason="Cannot chat with yourself")
        return

    await websocket.accept()

    # Generate consistent private room name
    room_name = get_private_room_name(user["id"], target["id"])
    room_group = f"private_{room_name}"

    # Track connection
    await manager.add_connection(room_group, websocket.client.host, {
        "id": user["id"],
        "username": user["username"],
        "websocket": websocket,
    })

    # Subscribe to Redis channel
    await manager.subscribe_room(room_group)

    logger.info(f"Private chat started between {user['username']} and {target['username']}")

    try:
        import asyncio

        async def redis_listener():
            if not manager.pubsub:
                return
            async for message in manager.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if data.get("user") != user["username"]:
                        try:
                            await websocket.send_json(data)
                        except Exception:
                            break

        listener_task = asyncio.create_task(redis_listener())

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content or len(content) > 1000:
                    await websocket.send_json({"type": "error", "message": "Invalid message"})
                    continue

                # Save to database
                saved = await save_private_message(user["id"], target["id"], content)

                # Broadcast via Redis
                await manager.publish(room_group, {
                    "type": "message",
                    "user": user["username"],
                    "content": content,
                    "timestamp": saved["timestamp"],
                    "id": saved["id"],
                })

            elif msg_type == "typing":
                is_typing = data.get("is_typing", False)
                await manager.publish(room_group, {
                    "type": "typing",
                    "user": user["username"],
                    "is_typing": is_typing,
                })

    except WebSocketDisconnect:
        logger.info(f"Private chat ended between {user['username']} and {target['username']}")
    except Exception as e:
        logger.error(f"Private WebSocket error: {e}")
    finally:
        await manager.remove_connection(room_group, websocket.client.host)
        await manager.unsubscribe_room(room_group)
