
from unittest.mock import MagicMock

from pyfcm import FCMNotification
from pyfcm.errors import AuthenticationError

from drop_service.notify import FCM


def test_fcm_basic(drop_messages):
    drop1, drop2 = drop_messages
    api = MagicMock(spec=FCMNotification)()

    fcm = FCM(api)
    fcm.notify(drop1)

    data_message = {
        'message': 'SGVsbG8gV29ybGQ=',
        'drop-id': 'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo'
    }
    api.notify_topic_subscribers.assert_called_once_with(topic_name=drop1.drop_id, data_message=data_message)


def test_fcm_doesnt_explode(drop_messages):
    drop1, drop2 = drop_messages
    api = MagicMock(spec=FCMNotification)()
    api.notify_topic_subscribers.side_effect = AuthenticationError('Well that didn\'t work!')

    fcm = FCM(api)
    fcm.notify(drop1)
