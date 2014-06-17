from nose.tools import eq_
from unittest import SkipTest
from webtest import TestApp
from email.utils import formatdate
from subprocess import Popen, PIPE
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
from time import sleep, time

import drop_server

proc = None


def setUpModule():
    # s.a. https://github.com/jamesls/fakeredis
    global proc
    try:
        # run the redis-server as a subprocess:
        proc = Popen(['redis-server', '--save', '""'], stdout=PIPE)
        # outs, errs = proc.communicate(timeout=...) is Py 3.x only
        # set the O_NONBLOCK flag of stdout file descriptor:
        flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
    except:
        raise SkipTest("could not start redis-server")
    outs = ''
    timeout = 5
    while timeout > 0 and not 'ready to accept connections' in outs:
        sleep(0.1)
        timeout -= 0.1
        try:
            outs += read(proc.stdout.fileno(), 1024)
        except OSError:
            # exception if there is no data
            pass
    if not timeout > 0:
        proc.terminate()
        raise SkipTest("could not start redis-server")


def tearDownModule():
    proc.terminate()


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
