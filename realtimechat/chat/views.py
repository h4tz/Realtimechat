import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_http_methods

from .models import ChatActivity, Message, PrivateMessage

logger = logging.getLogger(__name__)


class ChatRoomView(LoginRequiredMixin, View):
    """Enhanced chat room view with pagination and error handling."""

    def get(self, request, room_name):
        try:
            # Validate room name
            if not room_name or len(room_name) > 100:
                return HttpResponseBadRequest("Invalid room name")

            # Get user and messages
            user = request.user
            messages = Message.objects.filter(room=room_name).order_by("-timestamp")

            # Add pagination
            paginator = Paginator(messages, 50)  # Show 50 messages per page
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

            # Log user activity
            ChatActivity.objects.create(
                user=user,
                room=room_name,
                action="joined",
                details={"page": page_number},
            )

            context = {
                "room_name": room_name,
                "messages": page_obj.object_list,
                "user": user,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
            }

            return render(request, "chat/minimal_room.html", context)

        except Exception as e:
            logger.error(f"Error loading room {room_name}: {e}")
            return render(
                request,
                "chat/minimal_room.html",
                {
                    "room_name": room_name,
                    "messages": [],
                    "user": request.user,
                    "error": "Failed to load room",
                },
            )


@login_required
def index(request):
    """Enhanced index view with room suggestions and user stats."""
    try:
        user = request.user

        # Get user's recent rooms
        recent_rooms = Message.objects.filter(user=user).values("room").distinct()[:5]

        # Get popular rooms (rooms with most activity in last 24 hours)
        from datetime import timedelta

        from django.db.models import Count

        yesterday = timezone.now() - timedelta(hours=24)
        popular_rooms = (
            Message.objects.filter(timestamp__gte=yesterday)
            .values("room")
            .annotate(message_count=Count("id"))
            .order_by("-message_count")[:10]
        )

        context = {
            "recent_rooms": [room["room"] for room in recent_rooms],
            "popular_rooms": popular_rooms,
            "user": user,
        }

        return render(request, "chat/minimal_index.html", context)

    except Exception as e:
        logger.error(f"Error loading index: {e}")
        return render(
            request, "chat/minimal_index.html", {"error": "Failed to load rooms"}
        )


@login_required
def room(request, room_name):
    """Maintained for backward compatibility."""
    return ChatRoomView.as_view()(request, room_name)


@login_required
def private_chat(request, username):
    """Enhanced private chat view."""
    try:
        user1 = request.user
        user2 = get_object_or_404(User, username=username)

        if user1 == user2:
            return HttpResponseBadRequest("You cannot chat with yourself")

        # Get messages between the two users
        messages = PrivateMessage.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).order_by("-timestamp")

        # Mark messages as read
        unread_messages = messages.filter(is_read=False, user2=user1)
        for message in unread_messages:
            message.mark_as_read()

        # Add pagination
        paginator = Paginator(messages, 30)  # Show 30 messages per page
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context = {
            "user2": user2,
            "messages": page_obj.object_list,
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
        }

        return render(request, "chat/private.html", context)

    except Exception as e:
        logger.error(f"Error loading private chat with {username}: {e}")
        return render(
            request,
            "chat/private.html",
            {"user2": None, "messages": [], "error": "Failed to load chat"},
        )


# API Endpoints
@login_required
def get_room_messages(request, room_name):
    """API endpoint to get room messages with pagination."""
    try:
        if not room_name or len(room_name) > 100:
            return JsonResponse({"error": "Invalid room name"}, status=400)

        page = request.GET.get("page", 1)
        per_page = int(request.GET.get("per_page", 20))

        messages = Message.objects.filter(room=room_name).order_by("-timestamp")
        paginator = Paginator(messages, per_page)
        page_obj = paginator.get_page(page)

        messages_data = [message.to_dict() for message in page_obj.object_list]

        return JsonResponse(
            {
                "messages": messages_data,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_messages": paginator.count,
            }
        )

    except Exception as e:
        logger.error(f"Error getting messages for room {room_name}: {e}")
        return JsonResponse({"error": "Failed to get messages"}, status=500)


@login_required
def get_user_rooms(request):
    """API endpoint to get user's recent rooms."""
    try:
        user = request.user

        # Get user's rooms with message counts
        from django.db.models import Count

        user_rooms = (
            Message.objects.filter(user=user)
            .values("room")
            .annotate(message_count=Count("id"), last_message=Max("timestamp"))
            .order_by("-last_message")[:20]
        )

        return JsonResponse({"rooms": list(user_rooms)})

    except Exception as e:
        logger.error(f"Error getting user rooms: {e}")
        return JsonResponse({"error": "Failed to get rooms"}, status=500)


@login_required
def search_rooms(request):
    """API endpoint to search for rooms."""
    try:
        query = request.GET.get("q", "").strip()

        if not query:
            return JsonResponse({"rooms": []})

        # Search for rooms containing the query
        rooms = (
            Message.objects.filter(room__icontains=query).values("room").distinct()[:10]
        )

        return JsonResponse({"rooms": [room["room"] for room in rooms]})

    except Exception as e:
        logger.error(f"Error searching rooms: {e}")
        return JsonResponse({"error": "Search failed"}, status=500)


@login_required
@require_http_methods(["POST"])
def create_room(request):
    """API endpoint to create a new room."""
    try:
        data = json.loads(request.body)
        room_name = data.get("room_name", "").strip()

        if not room_name or len(room_name) > 100:
            return JsonResponse({"error": "Invalid room name"}, status=400)

        # Check if room already exists
        if Message.objects.filter(room=room_name).exists():
            return JsonResponse({"error": "Room already exists"}, status=400)

        # Create first message to initialize the room
        Message.objects.create(
            room=room_name,
            user=request.user,
            content=f"{request.user.username} created the room",
        )

        return JsonResponse(
            {
                "success": True,
                "room_name": room_name,
                "redirect_url": f"/chat/{room_name}/",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        return JsonResponse({"error": "Failed to create room"}, status=500)
