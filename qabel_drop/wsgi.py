"""
WSGI config for qabel_drop project.

It exposes a WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qabel_drop.settings')

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer

django_app = get_wsgi_application()
websocket_app = uWSGIWebsocketServer()


def application(environ, start_response):
    if environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
        return websocket_app(environ, start_response)
    return django_app(environ, start_response)
