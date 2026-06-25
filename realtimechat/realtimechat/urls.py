from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from chat import views
from chat.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("chat/", views.index, name="index"),
    path("chat/<str:room_name>/", views.room, name="room"),
    path("chat/private/<str:username>", views.private_chat, name="private_chat"),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
