"""
ASGI config for AfanChatServer project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
import os
import sys
from pathlib import Path

import django
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from config import routing
from mymiddleware.ChannelsMiddleWare import JwtAuthMiddleWare

# This allows easy placement of apps within the interior
# projectmodel directory.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "AfanChatServer"))

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()
# Apply ASGI middleware here.

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        # "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns)))
        "websocket": AllowedHostsOriginValidator(JwtAuthMiddleWare(URLRouter(routing.websocket_urlpatterns)))
    }
)
