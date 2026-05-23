from django.urls import path
from . import views

# HTTP URL patterns for API endpoints
urlpatterns = [
    path('rooms/', views.get_user_rooms, name='get_user_rooms'),
    path('rooms/search/', views.search_rooms, name='search_rooms'),
    path('rooms/create/', views.create_room, name='create_room'),
    path('rooms/<str:room_name>/messages/', views.get_room_messages, name='get_room_messages'),
]