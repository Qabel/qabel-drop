from nose.tools import eq_
from unittest import SkipTest
from webtest import TestApp
from email.utils import formatdate
from time import sleep, time

import redis_helper
import drop_server


def setUpModule():
    if not redis_helper.startRedisServer():
        raise SkipTest("could not start redis-server")


def tearDownModule():
    redis_helper.stopRedisServer()


def test():
    app = TestApp(drop_server.app)
    app.get('/illegal',
            status=400)
    app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
            status=404)
    app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
             status=404)
    timestamp = time()
    app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
             params='a message',
             headers={'Content-Type': 'application/octet-stream'},
             status=200)
    app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
             status=200)

    r = app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                status=200)
    eq_(r.content_type, 'multipart/mixed')
    assert r.content_length > 0
    r.mustcontain('a message',
                  'Content-Type: application/octet-stream\r\n',
                  'Date: ')

    # space the messages at least one second
    sleep(1)
    app.post('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
             params='second message',
             headers={'Content-Type': 'application/octet-stream'},
             status=200)

    r = app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                 headers={'If-Modified-Since':
                          formatdate(time() + 1, False, True)},
                 status=304)

    r = app.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                 headers={'If-Modified-Since':
                          formatdate(timestamp, False, True)},
                 status=200)

    r = app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                headers={'If-Modified-Since':
                         formatdate(timestamp - 1, False, True)},
                status=200)
    r.mustcontain('a message',
                  'second message')

    r = app.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                headers={'If-Modified-Since':
                         formatdate(timestamp, False, True)},
                status=200)
    r.mustcontain('second message')
    assert not 'a message' in r
