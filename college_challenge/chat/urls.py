# chat/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:room_id>/', views.chatroom, name='chatroom'),
]