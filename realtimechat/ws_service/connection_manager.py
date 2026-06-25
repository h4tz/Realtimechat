import json
import logging
from typing import Optional

import redis.asyncio as redis

from .config import REDIS_URL

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and Redis pub/sub for broadcasting."""

    def __init__(self):
        self.active_connections: dict[str, dict[str, dict]] = {}  # room -> {channel_name: user_info}
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(REDIS_URL, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis:
            await self.redis.close()

    async def subscribe_room(self, room: str):
        """Subscribe to a Redis channel for a room."""
        if self.pubsub:
            await self.pubsub.subscribe(room)
            logger.info(f"Subscribed to room channel: {room}")

    async def unsubscribe_room(self, room: str):
        """Unsubscribe from a Redis channel."""
        if self.pubsub:
            await self.pubsub.unsubscribe(room)

    async def publish(self, room: str, message: dict):
        """Publish a message to a Redis channel."""
        if self.redis:
            await self.redis.publish(room, json.dumps(message))

    async def add_connection(self, room: str, channel_name: str, user_info: dict):
        """Track an active connection."""
        if room not in self.active_connections:
            self.active_connections[room] = {}
        self.active_connections[room][channel_name] = user_info

    async def remove_connection(self, room: str, channel_name: str):
        """Remove an active connection."""
        if room in self.active_connections:
            self.active_connections[room].pop(channel_name, None)
            if not self.active_connections[room]:
                del self.active_connections[room]

    async def get_room_users(self, room: str) -> list[dict]:
        """Get all users in a room."""
        if room in self.active_connections:
            return list(self.active_connections[room].values())
        return []

    async def get_user_room(self, channel_name: str) -> Optional[str]:
        """Find which room a channel belongs to."""
        for room, connections in self.active_connections.items():
            if channel_name in connections:
                return room
        return None


manager = ConnectionManager()
