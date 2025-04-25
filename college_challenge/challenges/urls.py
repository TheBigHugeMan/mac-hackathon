# challenges/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.challenge_list, name='challenges'),
    path('create/<int:match_id>/', views.create_challenge, name='create_challenge'),
    path('<int:pk>/', views.challenge_detail, name='challenge_detail'),
]