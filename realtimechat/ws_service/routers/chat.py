import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..auth import authenticate_user
from ..connection_manager import manager
from ..models import save_message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/chat/{room_name}/")
async def websocket_chat(websocket: WebSocket, room_name: str, token: str):
    """WebSocket endpoint for group chat."""
    # Authenticate
    user = await authenticate_user(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Validate room name
    if not room_name or len(room_name) > 100:
        await websocket.close(code=4002, reason="Invalid room name")
        return

    await websocket.accept()
    room_group = f"chat_{room_name}"

    # Track connection
    await manager.add_connection(room_group, websocket.client.host, {
        "id": user["id"],
        "username": user["username"],
        "websocket": websocket,
    })

    # Subscribe to Redis channel for this room
    await manager.subscribe_room(room_group)

    # Notify room that user joined
    await manager.publish(room_group, {
        "type": "user_joined",
        "user": user["username"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"User {user['username']} connected to room {room_name}")

    try:
        # Listen for Redis messages in background task
        import asyncio

        async def redis_listener():
            if not manager.pubsub:
                return
            async for message in manager.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # Don't echo back to the same user who sent it
                    if data.get("user") != user["username"]:
                        try:
                            await websocket.send_json(data)
                        except Exception:
                            break

        listener_task = asyncio.create_task(redis_listener())

        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content or len(content) > 1000:
                    await websocket.send_json({"type": "error", "message": "Invalid message"})
                    continue

                # Save to database
                saved = await save_message(room_name, user["id"], content)

                # Broadcast to room via Redis
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
        logger.info(f"User {user['username']} disconnected from room {room_name}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        await manager.remove_connection(room_group, websocket.client.host)
        await manager.publish(room_group, {
            "type": "user_left",
            "user": user["username"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await manager.unsubscribe_room(room_group)
