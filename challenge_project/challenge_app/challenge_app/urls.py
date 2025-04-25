"""
URL configuration for challenge_app project.

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
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Import RedirectView
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('challenges/', include('challenges.urls')),
    # Add a URL pattern for the root path - redirect to challenges or create a home view
    path('', RedirectView.as_view(url='/challenges/', permanent=True)),
    path('', views.challenges_home, name='challenges_home'),
    path('test-ws/', views.test_websocket, name='test_websocket'),
    # Alternatively, you can create a home view
    # path('', views.home, name='home'),
]