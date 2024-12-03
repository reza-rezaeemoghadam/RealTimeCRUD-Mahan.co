"""
ASGI config for src project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

application = get_asgi_application()
"""
ASGI config for src project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
# Importing extra modules
import os

# Importing django modules
from django.core.asgi import get_asgi_application

# Importing channel modules
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Import routes
from rt_crud.routing import ws_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http":django_asgi_app,
    'websocket':
        AuthMiddlewareStack(
            URLRouter(
                ws_urlpatterns
            ),
        ),
})
