# chat/api_urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'rooms', views.ChatRoomViewSet, basename='chat_rooms')

urlpatterns = [
    path('rooms/<int:pk>/send_message/', 
         views.ChatRoomViewSet.as_view({'post': 'send_message'}), 
         name='api_send_message'),
] + router.urls