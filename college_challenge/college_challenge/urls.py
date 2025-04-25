"""
URL configuration for college_challenge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# college_challenge/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from challenges.views import ChallengeViewSet, TransactionViewSet
from chat.views import ChatRoomViewSet

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'challenges', ChallengeViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'chat-rooms', ChatRoomViewSet, basename='chatroom')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('challenges/', include('challenges.urls')),
    path('chat/', include('chat.urls')),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)