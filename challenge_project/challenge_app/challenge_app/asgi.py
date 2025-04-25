"""
ASGI config for challenge_app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import challenges.routing  
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'challenge_app.settings')
django.setup()

application = ProtocolTypeRouter({
    # Serve traditional HTTP requests by Django
    'http': get_asgi_application(),

    # Add WebSocket support:
    'websocket': AuthMiddlewareStack(
        URLRouter(
            challenges.routing.websocket_urlpatterns
        )
    ),
})

