import asyncio
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
async def websocket_chat(websocket: WebSocket, room_name: str):
    """WebSocket endpoint for group chat."""
    await websocket.accept()

    # Validate room name
    if not room_name or len(room_name) > 100:
        await websocket.close(code=4002, reason="Invalid room name")
        return

    # Wait for auth message as first message (token sent in body, not URL)
    try:
        auth_msg = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except asyncio.TimeoutError:
        await websocket.close(code=4003, reason="Auth timeout")
        return

    if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
        await websocket.close(code=4001, reason="Invalid auth message")
        return

    user = await authenticate_user(auth_msg["token"])
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    room_group = f"chat_{room_name}"
    channel_name = f"user_{user['id']}"

    # Track connection by user_id, not IP
    await manager.add_connection(room_group, channel_name, {
        "id": user["id"],
        "username": user["username"],
        "websocket": websocket,
    })

    # Create a per-connection PubSub instance
    pubsub = manager.create_pubsub()
    listener_task = None

    try:
        # Subscribe to Redis channel for this room
        if pubsub:
            await pubsub.subscribe(room_group)

        # Notify room that user joined
        await manager.publish(room_group, {
            "type": "user_joined",
            "user": user["username"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"User {user['username']} connected to room {room_name}")

        # Listen for Redis messages in background task
        async def redis_listener():
            if not pubsub:
                return
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
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
        # Cancel the listener task
        if listener_task and not listener_task.done():
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        # Cleanup connection
        await manager.remove_connection(room_group, channel_name)
        await manager.publish(room_group, {
            "type": "user_left",
            "user": user["username"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Cleanup per-connection PubSub
        if pubsub:
            try:
                await pubsub.unsubscribe(room_group)
                await pubsub.close()
            except Exception:
                pass
