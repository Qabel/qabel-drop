
import datetime
from email.utils import format_datetime

from rest_framework import status


def test_ok(client, drop_messages, registry):
    with registry.assert_drop_sent(count=1):
        response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK


def test_ok_head(client, drop_messages, registry):
    with registry.assert_drop_sent(count=0):
        response = client.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK


def test_invalid_dropid(client, registry):
    with registry.assert_drop_sent(count=0):
        response = client.get('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_no_content(client, db, registry):
    with registry.assert_drop_sent(count=0):
        response = client.get('/xbcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_modified_since(client, drop_messages, registry):
    with registry.assert_drop_sent(count=0):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                              HTTP_IF_MODIFIED_SINCE=format_datetime(dt, usegmt=True))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED


def test_post(client, registry, db):
    with registry.assert_drop_received(count=1):
        response = client.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost', data=b'Yay',
                               content_type='application/octet-stream',
                               HTTP_AUTHORIZATION='Client Qabel')
        assert response.status_code == status.HTTP_200_OK
