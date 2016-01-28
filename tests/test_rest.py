import datetime
import unittest
from email.utils import format_datetime
import pytz
from flask import current_app
from flask_api import status
from app import app, db
from models import Drop


class DropServerTestCase(unittest.TestCase):
    def setUp(self):
        """Pre-test activities."""
        app.testing = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.init_app(current_app)
            db.metadata.create_all(db.engine)
            self.db = db
            self.app = app.test_client()
            drop = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
            dropfoo = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
            db.session.add(drop)
            db.session.add(dropfoo)
            db.session.commit()

    #######GET
    def test_get_message_from_invalid_drop_id(self):
        response = self.app.get('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == b''

    def test_get_messages(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'].startswith("multipart/mixed; boundary=")
        assert 'Hello World' in response.data.decode()
        assert response.data.decode().count("Hello World") == 1
        assert 'Bar' not in response.data.decode()

    def test_get_messages_empty_drop(self):
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklempty')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data == b''

    def test_get_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})

        assert response.status_code == status.HTTP_200_OK
        print(response.data.decode())
        assert 'Hello World' in response.data.decode()

    def test_get_messages_posted_since_gmt1(self):
        dt = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')) - datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                headers={'If-Modified-Since': format_datetime(dt)})

        assert response.status_code == status.HTTP_200_OK
        print(response.data.decode())
        assert 'Hello World' in response.data.decode()

    def test_get_no_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.data == b''

    def test_get_no_messages_posted_since_gmt1(self):
        dt = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')) + datetime.timedelta(minutes=1)
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                headers={'If-Modified-Since': format_datetime(dt)})
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.data == b''

    ######HEAD
    def test_head_message_from_invalid_drop_id(self):
        response = self.app.head('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == b''

    def test_head_messages(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == b''

    def test_head_messages_empty_drop(self):
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklempty')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data == b''

    def test_head_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(minutes=1)
        print(format_datetime(dt, usegmt=True))
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == b''

    def test_head_no_messages_posted_since(self):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = self.app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response.data == b''

    #######POST
    def test_post_empty_message(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', data=b'',
                                 headers={'Content-Type': 'application/octet-stream'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == b''

    def test_post_no_message(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                 headers={'Content-Type': 'application/octet-stream'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == b''

    def test_post_to_invalid_drop_id(self):
        response = self.app.post('/fail', data=b'Yay', headers={'Content-Type': 'application/octet-stream'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == b''

    def test_post_message_is_too_long(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', data=2574 * b'x',
                                 headers={'Content-Type': 'application/octet-stream'})
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert response.data == b''

    def test_post_message(self):
        response = self.app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost', data=b'Yay',
                                 headers={'Content-Type': 'application/octet-stream'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data == b''
        response = self.app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmpost')
        assert 'Yay' in response.data.decode()
