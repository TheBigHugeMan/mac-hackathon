# challenges/api_urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.ChallengeViewSet)

urlpatterns = [
    path('create_challenge/', views.ChallengeViewSet.as_view({'post': 'create_challenge'}), name='api_create_challenge'),
    path('<int:pk>/accept_challenge/', views.ChallengeViewSet.as_view({'post': 'accept_challenge'}), name='api_accept_challenge'),
    path('<int:pk>/execute_challenge/', views.ChallengeViewSet.as_view({'post': 'execute_challenge'}), name='api_execute_challenge'),
] + router.urls