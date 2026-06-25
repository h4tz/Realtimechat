import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from .models import ChatActivity, Message, PrivateMessage

logger = logging.getLogger(__name__)


class ChatRoomView(LoginRequiredMixin, View):
    def get(self, request, room_name):
        try:
            if not room_name or len(room_name) > 100:
                return HttpResponseBadRequest("Invalid room name")

            user = request.user
            messages = Message.objects.filter(room=room_name).order_by("-timestamp")
            paginator = Paginator(messages, 50)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)

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
                {"room_name": room_name, "messages": [], "user": request.user, "error": "Failed to load room"},
            )


@login_required
def index(request):
    try:
        user = request.user
        recent_rooms = Message.objects.filter(user=user).values("room").distinct()[:5]

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
        return render(request, "chat/minimal_index.html", {"error": "Failed to load rooms"})


@login_required
def room(request, room_name):
    return ChatRoomView.as_view()(request, room_name)


@login_required
def private_chat(request, username):
    try:
        user1 = request.user
        user2 = get_object_or_404(User, username=username)

        if user1 == user2:
            return HttpResponseBadRequest("You cannot chat with yourself")

        messages = PrivateMessage.objects.filter(
            Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
        ).order_by("-timestamp")

        unread_messages = messages.filter(is_read=False, user2=user1)
        for message in unread_messages:
            message.mark_as_read()

        paginator = Paginator(messages, 30)
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
