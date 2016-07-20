import base64
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string

from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

from pyfcm import FCMNotification
from pyfcm.errors import AuthenticationError, FCMServerError, InvalidDataError, InternalPackageError

from .monitoring import FCM_API, monitor_duration
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
    """
    Publish drops through FCM topic messages. The topic is the drop ID.
    """
    SERVICE = 'fcm'
    _logger = logger.getChild('fcm')

    def __init__(self, fcm_notification=None, executor=None):
        if not fcm_notification:
            fcm_notification = FCMNotification(api_key=settings.FCM_API_KEY, proxy_dict=settings.FCM_PROXY)
        self._executor = executor or ThreadPoolExecutor()
        self._push = fcm_notification

    def notify(self, drop):
        self._executor.submit(self._notify, drop)

    def _notify(self, drop):
        data = {
            'drop-id': drop.drop_id,
            'message': base64.b64encode(drop.message).decode(),
        }
        # Alphabet of topics: [a-zA-Z0-9-_.~%]
        # Alphabet of drop IDs: [a-zA-Z0-9-_]
        with monitor_duration(FCM_API, exception='None') as monitor_labels:
            try:
                # The response contains no useful data for topic messages
                # Downstream messages on the other hand include success/failure counts
                self._push.notify_topic_subscribers(topic_name=drop.drop_id, data_message=data)
            except (AuthenticationError, FCMServerError, InvalidDataError, InternalPackageError) as exc:
                monitor_labels['exception'] = type(exc).__name__
                self._logger.exception('notify_topic_subscribes API exception')


class WebSocket:
    def notify(self, drop):
        message = RedisMessage(drop.message)
        self._get_publisher(drop.drop_id).publish_message(message)

    @lru_cache()
    def _get_publisher(self, drop_id):
        return RedisPublisher(broadcast=True, facility=drop_id)


class SubscribeView(CsrfExemptView):
    http_method_names = ['post', 'delete']
