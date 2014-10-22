#!/usr/bin/env python2.7

"""
This software is licenced under the Qabel Public Licence
(QaPL): https://qabel.de/qapl.txt


drop_server.py: Test server for deaddrop protocol.
Uses gevent and redis-py (hiredis is recommended).

Just run this for a cheap example with built-in gevent server.
Enable the keyfile and certfile arguments (last few lines) to try TLS.
Hint:
$ openssl genrsa -out server.key 2048
$ openssl req -new -x509 -nodes -sha1 -key server.key -out server.crt


Maybe use Gunicorn with gevent.pywsgi worker (-k gevent_pywsgi)

Tutorial from http://gunicorn.org/

 $ sudo pip install virtualenv
 $ mkdir ~/environments/
 $ virtualenv ~/environments/drops/
 $ cd ~/environments/drops/
 $ source bin/activate
 (drops) $ pip install -r GITDIR/requirements.txt
 (drops) $ cp GITDIR/drop_server.py .
 (drops) $ ./bin/gunicorn -w 4 drop_server:app

Deploy with uWSGI and Nginx as frontend to
 - check request integrity for security
 - support SSL
 - make it more robust
 - act as load balancers to several wsgi processes in order to scale
"""

# TODO: perhaps alternative in-memory and simple disk backends
# TODO: load and performance monitoring

from __future__ import print_function
import redis
import re
from time import time
from email.utils import parsedate_tz, mktime_tz, formatdate
from base64 import b64encode, b64decode
from urlparse import parse_qs
from cgi import parse_header, parse_multipart
from Crypto import Random

MESSAGES_PER_DROP_LIMIT = 10
MESSAGE_SIZE_LIMIT = 2000  # Octets
MESSAGE_EXPIRE_TIME = 60 * 60 * 24 * 7  # Seconds


def create_boundary_id():
    """Return a string of 12 randomly generated characters according to
    RFC 4648 Base 64 Encoding with URL and Filename Safe Alphabet."""
    return b64encode(Random.new().read(9), '-_')  # no extra padding


def extract_drop_id(path):
    """Extract the Drop-ID from the path argument. Strip all non-Base64
    characters from the given path and return as a joined string."""
    return re.sub(r'[^-_A-Za-z0-9]', '', path)


def check_drop_id(drop_id):
    """Require a string of 43 randomly generated characters according to
    RFC 4648 Base 64 Encoding with URL and Filename Safe Alphabet."""
    try:
        return (len(drop_id) == 43
                and not re.search(r'[^-_A-Za-z0-9]', drop_id)
                and len(b64decode(drop_id + '=', '-_')) == 32)
    except TypeError:
        return False


def decode_record(record):
    timestamp, message = record.split(':', 1)
    return (int(timestamp), message)


def encode_record(timestamp, message):
    int(timestamp)  # raise on bad argument
    return '%s:%s' % (timestamp, message)


def send_multipart(records, start_response):
    boundary = create_boundary_id()
    start_response('200 OK', [('Content-Type',
                               'multipart/mixed; boundary="' + boundary + '"')])
    ret = []
    ret.append('Content-Type: multipart/mixed; boundary="' + boundary + '"\r\n')

    ret.append('\r\n')
    for timestamp, message in records:      
        ret.append('--' + boundary + '\r\n')
        # Content-Transfer-Encoding: binary
        ret.append('Content-Type: application/octet-stream\r\n')
        # format_date_time takes localtime, formats GMT
        ret.append('Date: ' + formatdate(timestamp, False, True) + '\r\n')
        # end headers
        ret.append('\r\n')
        ret.append(message)
        ret.append('\r\n')
    ret.append('--' + boundary + '--\r\n')
    return ret


def read_postbody(env):
    if not 'CONTENT_TYPE' in env:
        # try to get a raw body anyway
        return env['wsgi.input'].read()

    elif env['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
        # decode and split the form
        form = parse_qs(env['wsgi.input'].read())
        if 'text' in form:
            # return the last value for the 'text' key if available
            return form['text'][-1]
        elif len(form):
            # otherwise use a random key
            k, v = form.popitem()
            return v[-1]

    elif env['CONTENT_TYPE'] == 'application/octet-stream':
        return env['wsgi.input'].read()

    elif env['CONTENT_TYPE'].startswith('multipart/form-data'):
        # split the multipart
        ctype, pdict = parse_header(env['CONTENT_TYPE'])
        postvars = parse_multipart(env['wsgi.input'], pdict)
        if 'text' in postvars:
            # return the data for the 'text' part if available
            return postvars['text'][-1]
        elif len(postvars):
            # otherwise use a random key
            k, v = postvars.popitem()
            return v[-1]

    else:
        # try to get a raw body anyway
        return env['wsgi.input'].read()


def app(env, start_response):
    drops = redis.StrictRedis(host='localhost', port=6379, db=0)

    drop_id = extract_drop_id(env['PATH_INFO'])
    if not check_drop_id(drop_id):
        start_response('400 Bad Request', [('Content-Type', 'text/html')])
        return ['<h1>Bad Request</h1>']

    if 'HTTP_IF_MODIFIED_SINCE' in env:
        since = env['HTTP_IF_MODIFIED_SINCE']
        since = mktime_tz(parsedate_tz(since))
    else:
        since = 0

    if env['REQUEST_METHOD'] == 'HEAD':
        record = drops.lindex(drop_id, 0)
        if not record:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return ['<h1>Not Found</h1>']

        timestamp, message = decode_record(record)

        if timestamp <= since:
            start_response('304 Not Modified', [])
            return []

        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['<h1>OK</h1>']

    elif env['REQUEST_METHOD'] == 'GET':
        records = drops.lrange(drop_id, 0, -1)
        if not records:
            start_response('404 Not Found', [('Content-Type', 'text/html')])
            return ['<h1>Not Found</h1>']

        records = [decode_record(record) for record in records]

        if records[0][0] <= since:
            start_response('304 Not Modified', [])
            return []

        records = [record for record in records if record[0] > since]

        return send_multipart(records, start_response)

    elif env['REQUEST_METHOD'] == 'POST':
        message = read_postbody(env)

        if not message:
            start_response('400 Bad Request', [('Content-Type', 'text/html')])
            return ['<h1>Bad REQUEST_METHOD</h1>']

        if len(message) > MESSAGE_SIZE_LIMIT:
            start_response('413 Request Entity Too Large', [('Content-Type', 'text/html')])
            return ['<h1>Request Entity Too Large</h1>']

        now = int(time())
        record = encode_record(now, message)
        # append the message
        drops.lpush(drop_id, record)
        # truncate the list
        drops.ltrim(drop_id, 0, MESSAGES_PER_DROP_LIMIT)
        # set expiration time
        drops.expire(drop_id, MESSAGE_EXPIRE_TIME)

        start_response('200 OK', [('Content-Type', 'text/html')])
        return ["<b>OK</b>"]


def main():
    from gevent import pywsgi

    # change the bind as needed and maybe enable TLS
    server = pywsgi.WSGIServer(('127.0.0.1', 6000),
                               app,
                               # keyfile='server.key',
                               # certfile='server.crt'
                               )

    print('Serving on http://127.0.0.1:6000')

    # to start the server asynchronously, use its start() method;
    # we use blocking serve_forever() here because we have no other jobs
    server.serve_forever()


if __name__ == '__main__':
    main()
