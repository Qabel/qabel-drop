import datetime
from email.utils import format_datetime
from json import loads

from django.conf import settings
from django.test import Client, TestCase

from rest_framework import status

import pytz

from drop_service.models import Drop
from drop_service.util import utc_timestamp


def err(body: bytes):
    return loads(body.decode('utf-8')).get('error')


class DropServerTestCase(TestCase):
    def setUp(self):
        """Pre-test activities."""
        self.app = Client()
        self.drop = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
        self.dropfoo = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
        self.dropfoo.created_at = datetime.datetime(year=2016, month=1, day=1, tzinfo=pytz.UTC)
        self.drop.save()
        self.dropfoo.save()

    #######GET
    def test_get_message_from_invalid_drop_id(self):
        response = self.app.get('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid drop id' == err(response.content)

    def test_get_messages(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'].startswith("multipart/mixed; boundary=")
        assert 'Hello World' in response.content.decode()
        assert response.content.decode().count("Hello World") == 1
        assert 'Bar' not in response.content.decode()

    def test_get_messsages_contains_headers(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo')
        assert response['Last-Modified'] == "Fri, 01 Jan 2016 00:00:00 GMT"
        assert 'X-Qabel-Latest' in response

    def test_get_messages_empty_drop(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklempty')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

    def test_get_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_IF_MODIFIED_SINCE=format_datetime(dt, usegmt=True))

        assert response.status_code == status.HTTP_200_OK
        assert 'Hello World' in response.content.decode()

    def test_get_messages_posted_since_qabel(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_X_QABEL_NEW_SINCE=str(utc_timestamp(self.dropfoo.created_at)))

        assert response.status_code == status.HTTP_200_OK
        body = response.content.decode()
        assert 'Hello World' in body
        assert 'Bar' not in body

    def test_get_qabel_round_trip(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK
        latest = response['X-Qabel-Latest']
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_X_QABEL_NEW_SINCE=latest)
        assert response.status_code == status.HTTP_304_NOT_MODIFIED

    def test_get_messages_posted_since_gmt1(self):
        dt = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')) - datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_IF_MODIFIED_SINCE=format_datetime(dt))

        assert response.status_code == status.HTTP_200_OK
        assert 'Hello World' in response.content.decode()

    def test_get_no_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_IF_MODIFIED_SINCE=format_datetime(dt, usegmt=True))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.content == b''

    def test_get_no_messages_posted_since_qabel(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_X_QABEL_NEW_SINCE=str(utc_timestamp(self.drop.created_at) + 1))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.content == b''

    def test_get_no_messages_posted_since_gmt1(self):
        dt = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')) + datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                HTTP_IF_MODIFIED_SINCE=format_datetime(dt))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.content == b''

    ######HEAD
    def test_head_message_from_invalid_drop_id(self):
        response = self.app.head('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content == b''

    def test_head_messages(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b''

    def test_head_messages_empty_drop(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklempty')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

    def test_head_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=1)
        print(format_datetime(dt, usegmt=True))
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 HTTP_IF_MODIFIED_SINCE=format_datetime(dt, usegmt=True))

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b''

    def test_head_messages_posted_since_qabel(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 HTTP_X_QABEL_NEW_SINCE=str(utc_timestamp(self.dropfoo.created_at)))
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b''

    def test_head_no_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 HTTP_IF_MODIFIED_SINCE=format_datetime(dt, usegmt=True))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.content == b''

    def test_head_no_messages_posted_since_etag(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 HTTP_X_QABEL_NEW_SINCE=str(utc_timestamp(self.drop.created_at) + 1))
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.content == b''

    #######POST
    def test_post_empty_message(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', data=b'',
                                 content_type='application/octet-stream',
                                 HTTP_AUTHORIZATION='Client Qabel')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert err(response.content) == 'No message provided'

    def test_post_to_invalid_drop_id(self):
        response = self.app.post('/fail', data=b'Yay',
                                 content_type='application/octet-stream',
                                 HTTP_AUTHORIZATION='Client Qabel')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert err(response.content) == 'Invalid drop id'

    def test_post_message_is_too_long(self):
        too_long = settings.MESSAGE_SIZE_LIMIT + 1
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', data=too_long * b'x',
                                 content_type='application/octet-stream',
                                 HTTP_AUTHORIZATION='Client Qabel')
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert err(response.content) == 'Message too large'

    def test_post_message(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost', data=b'Yay',
                                 content_type='application/octet-stream',
                                 HTTP_AUTHORIZATION='Client Qabel')
        assert response.status_code == status.HTTP_200_OK
        assert response.content == b''
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost')
        assert 'Yay' in response.content.decode()

    def test_post_message_without_headers(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost', data=b'Yay',
                                 content_type='application/octet-stream')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert err(response.content) == 'Bad authorization'
