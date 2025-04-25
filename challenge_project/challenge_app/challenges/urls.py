# challenge_app/challenges/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Add your challenge app URL patterns here
    path('test-ws/', views.test_websocket, name='test_websocket'),
    # Other URL patterns
]