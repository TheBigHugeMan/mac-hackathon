# users/api_urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.UserViewSet, basename='users')

urlpatterns = [
    path('me/', views.UserViewSet.as_view({'get': 'me'}), name='api_user_me'),
    path('potential_matches/', views.UserViewSet.as_view({'get': 'potential_matches'}), name='api_potential_matches'),
    path('<int:pk>/swipe_right/', views.UserViewSet.as_view({'post': 'swipe_right'}), name='api_swipe_right'),
    path('<int:pk>/swipe_left/', views.UserViewSet.as_view({'post': 'swipe_left'}), name='api_swipe_left'),
    path('matches/', views.UserViewSet.as_view({'get': 'matches'}), name='api_matches'),
] + router.urls