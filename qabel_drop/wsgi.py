"""
WSGI config for qabel_drop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qabel_drop.settings")

try:
    import uwsgi

    from drop_service.wsasync import application as _ws_application, uri_re

    _django_application = get_wsgi_application()

    def application(env, start_response):
        if uri_re.fullmatch(env['PATH_INFO']):
            return _ws_application(env, start_response)
        return _django_application(env, start_response)

except ImportError:
    application = get_wsgi_application()
