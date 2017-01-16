import re
import sys

from django.conf import settings

try:
    import uwsgi
except ImportError:
    print('This module (%s) can only run in an uwsgi worker.' % __name__, file=sys.stderr)
    sys.exit(1)

import redis

import gevent.select

from . import monitoring

uri_re = re.compile(r'^/(?P<drop_id>[-_A-Za-z0-9]+)/ws$')


def application(env, start_response):
    # At this point the server received a valid WebSocket Upgrade request,
    # and routed the request to this pseudo-WSGI app,
    # but has not yet send any response.

    def bad(why):
        start_response('400 Bad request (' + why + ')', [])

    if 'HTTP_SEC_WEBSOCKET_KEY' not in env:
        return bad('Missing Sec-WebSocket-Key header')

    match = uri_re.fullmatch(env['REQUEST_URI'])
    if not match:
        return bad('Invalid/missing drop ID')

    drop_id = match.group('drop_id')

    # This uWSGI utility function sends the HTTP/101 Switching Protocols response
    # (it doesn't need *start_response*, because it directly accesses the requests'
    # output socket).
    uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))

    redis_conn = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    channel = redis_conn.pubsub()
    channel.subscribe(settings.REDIS_PREFIX + drop_id)

    websocket_fd = uwsgi.connection_fd()
    redis_fd = channel.connection._sock.fileno()

    print('wsfd/rfd', websocket_fd, redis_fd)

    monitoring.WEBSOCKET_CONNECTIONS.inc()

    try:
        while True:
            rable, wable, xfd = gevent.select.select([websocket_fd, redis_fd], [], [], 2)
            print('selected', rable)
            if not rable:
                # When the select times out, we do a non-blocking receive. This triggers a check
                # in uWSGI whether a PING should be send. It also handles various housekeeping
                # tasks, like closing the connection and stuff like that.
                # We don't really care what the client has to say.
                uwsgi.websocket_recv_nb()
                continue

            for fd in rable:
                if fd == websocket_fd:
                    uwsgi.websocket_recv_nb()
                elif fd == redis_fd:
                    # This is a reading block, but that's okay since we previously polled for
                    # readability on the redis FD, so the server is sending us a message.
                    msg = channel.handle_message(channel.parse_response())
                    if msg['type'] != 'message':
                        print('Unexpected Redis message type:', msg['type'])
                        continue
                    uwsgi.websocket_send_binary(msg['data'])
                    monitoring.WEBSOCKET_MESSAGES.inc()
    finally:
        monitoring.WEBSOCKET_CONNECTIONS.dec()
        try:
            redis_conn.connection_pool.disconnect()
        except:
            pass
