import base64
import logging
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string

from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

from pyfcm import FCMNotification
from pyfcm.errors import AuthenticationError, FCMServerError, InvalidDataError, InternalPackageError

from .monitoring import FCM_CALLS
from .models import PushSubscription
from .util import CsrfExemptView


logger = logging.getLogger('drop_service.notify')


def get_notificators():
    """Return list of configured notificator instances."""
    notificators = []
    for class_path in settings.PUSH_NOTIFICATORS:
        cls = import_string(class_path)
        notificators += cls(),
    return notificators


class FCM:
    SERVICE = 'fcm'
    _logger = logger.getChild('fcm')

    def __init__(self):
        self._push = FCMNotification(api_key=settings.FCM_API_KEY, proxy_dict=settings.FCM_PROXY)

    def notify(self, drop):
        data = {
            'drop-id': drop.drop_id,
            'message': base64.b64encode(drop.message).decode(),
        }
        # Alphabet of topics: [a-zA-Z0-9-_.~%]
        # Alphabet of drop IDs: [a-zA-Z0-9-_]
        try:
            # The response contains no useful data for topic messages
            # Downstream messages on the other hand include success/failure counts
            self._push.notify_topic_subscribers(topic_name=drop.drop_id, data_message=data)
        except (AuthenticationError, FCMServerError, InvalidDataError, InternalPackageError) as exc:
            FCM_CALLS.labels({'exception': type(exc).__name__}).inc()
            self._logger.exception()
        else:
            FCM_CALLS.labels({'exception': 'None'}).inc()


class WebSocket:
    def notify(self, drop):
        message = RedisMessage(drop.message)
        self._get_publisher(drop.drop_id).publish_message(message)

    @lru_cache()
    def _get_publisher(self, drop_id):
        return RedisPublisher(broadcast=True, facility=drop_id)


class SubscribeView(CsrfExemptView):
    http_method_names = ['post', 'delete']
