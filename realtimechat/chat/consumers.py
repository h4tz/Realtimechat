import json
import logging
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .models import Message

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()


def get_private_room_name(user1, user2):
    """Generate consistent private room name for two users."""
    return f"private_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"


class ChatConsumer(AsyncWebsocketConsumer):
    """Improved WebSocket consumer for chat functionality."""

    async def connect(self):
        """Handle WebSocket connection with improved error handling."""
        try:
            # Check authentication
            if not self.scope.get("user") or not self.scope["user"].is_authenticated:
                logger.warning("Unauthenticated user attempted to connect")
                await self.close(code=4000, reason="Authentication required")
                return

            self.user = self.scope["user"]
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"chat_{self.room_name}"
            self.user_status = "online"

            # Validate room name
            if (
                not self.room_name
                or not isinstance(self.room_name, str)
                or len(self.room_name) > 100
            ):
                logger.warning(f"Invalid room name: {self.room_name}")
                await self.close(code=4001, reason="Invalid room name")
                return

            # Add to room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            # Notify other users that this user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_joined",
                    "user": self.user.username,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.info(f"User {self.user.username} connected to room {self.room_name}")

        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self.close(code=5000, reason="Internal server error")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            if hasattr(self, "room_group_name"):
                # Notify other users that this user left
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_left",
                        "user": self.user.username,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                await self.channel_layer.group_discard(
                    self.room_group_name, self.channel_name
                )
                logger.info(
                    f"User {self.user.username} disconnected from room {self.room_name}"
                )
        except Exception as e:
            logger.error(f"Disconnection error: {e}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages with improved validation."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "message")

            if message_type == "typing":
                await self.handle_typing(text_data_json)
            elif message_type == "message":
                await self.handle_message(text_data_json)
            else:
                await self.send_error("Invalid message type")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self.send_error("Message processing failed")

    async def handle_typing(self, data):
        """Handle typing indicator messages."""
        try:
            is_typing = data.get("typing", False)
            if not isinstance(is_typing, bool):
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing.indicator",
                    "user": self.user.username,
                    "is_typing": is_typing,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Typing handling error: {e}")

    async def handle_message(self, data):
        """Handle chat messages with validation and persistence."""
        try:
            message = data.get("message", "").strip()

            # Validate message
            if not message or len(message) > 1000:
                await self.send_error("Invalid message length")
                return

            # Save message to database
            await self.save_message(message)

            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": message,
                    "user": self.user.username,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": self.user.id,
                },
            )

        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await self.send_error("Failed to send message")

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database asynchronously."""
        try:
            message = Message.objects.create(
                room=self.room_name, user=self.user, content=content
            )
            logger.debug(f"Message saved: {message.id}")
            return message
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise

    async def send_error(self, error_message):
        """Send error message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": error_message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

    # WebSocket event handlers
    async def chat_message(self, event):
        """Handle chat message broadcasts."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": event["message"],
                    "user": event["user"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def typing_indicator(self, event):
        """Handle typing indicator broadcasts."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user": event["user"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    async def user_joined(self, event):
        """Handle user joined notifications."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "user": event["user"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def user_left(self, event):
        """Handle user left notifications."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "user": event["user"],
                    "timestamp": event["timestamp"],
                }
            )
        )


class PrivateChatConsumer(ChatConsumer):
    """Improved private chat consumer."""

    async def connect(self):
        """Handle private chat connection."""
        try:
            if not self.scope.get("user") or not self.scope["user"].is_authenticated:
                await self.close(code=4000, reason="Authentication required")
                return

            user1 = self.scope["user"]
            username = self.scope["url_route"]["kwargs"]["username"]

            # Validate target user
            if not username or username == user1.username:
                await self.close(code=4001, reason="Invalid target user")
                return

            user2 = await database_sync_to_async(User.objects.get)(username=username)
            self.room_name = get_private_room_name(user1, user2)
            self.room_group_name = f"chat_{self.room_name}"

            # Add to room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

            logger.info(
                f"Private chat started between {user1.username} and {user2.username}"
            )

        except User.DoesNotExist:
            await self.close(code=4002, reason="User not found")
        except Exception as e:
            logger.error(f"Private chat connection error: {e}")
            await self.close(code=5000, reason="Internal server error")
