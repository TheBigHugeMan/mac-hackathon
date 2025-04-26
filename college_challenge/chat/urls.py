# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:room_id>/', views.chatroom, name='chatroom'),
    path('', views.chat_room_list, name='chat_room_list'),
]