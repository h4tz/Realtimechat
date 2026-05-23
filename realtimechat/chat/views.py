from django.contrib.auth.models import User
from django.shortcuts import render

from .models import Message, PrivateMessage


# Create your views here.
def index(request):
    return render(request, "chat/minimal_index.html")


def room(request, room_name):
    user = request.user
    messages = Message.objects.filter(room=room_name).order_by("-timestamp")[:50]
    return render(
        request,
        "chat/minimal_room.html",
        {"room_name": room_name, "messages": messages, "user": user},
    )


def private_chat(request, username):
    user1 = request.user
    user2 = User.objects.get(username=username)
    messages = PrivateMessage.objects.filter(
        user1__in=[user1, user2], user2__in=[user1, user2]
    )
    return render(request, "chat/private.html", {"user2": user2, "messages": messages})
