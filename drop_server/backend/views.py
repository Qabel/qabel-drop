import uuid
from datetime import datetime
from email.utils import formatdate
from time import mktime
import sqlalchemy.exc

import dateparser
import re
from base64 import b64decode
from flask import Response, request
from flask_api import status
from time import time
from functools import partial


from drop_server.app import app, db
from drop_server.backend.models import Drop
import drop_server.backend.monitoring as mon

MESSAGE_SIZE_LIMIT = 2573  # Octets


def log_request(start_time, method, status_code):
    time_since = time() - start_time
    mon.REQUEST_TIME.labels({'method': method, 'status': status_code})\
        .observe(time_since)


@app.route('/<path:drop_id>', methods=['GET', 'HEAD'])
def get_drop_messages(drop_id):
    log = partial(log_request, time(), request.method)
    since_b, since = get_if_modified_since(request)
    if not check_drop_id(drop_id):
        log(400)
        return 'Invalid drop id', status.HTTP_400_BAD_REQUEST
    drops = db.session.query(Drop).filter(Drop.drop_id == drop_id).all()
    if not drops:
        log(204)
        return '', status.HTTP_204_NO_CONTENT
    if since_b:
        drops = db.session.query(Drop).filter(Drop.drop_id == drop_id, Drop.created_at >= since).all()
        if not drops:
            log(304)
            return '', status.HTTP_304_NOT_MODIFIED
    if request.method == 'GET':
        log(200)
        mon.DROP_SENT.inc(len(drops))
        boundary = str(uuid.uuid4())
        return Response(generate_response(drops, boundary), status=200,
                        content_type='multipart/mixed; boundary="' + boundary + '"')
    else:
        log(200)
        return '', status.HTTP_200_OK


@app.route('/<path:drop_id>', methods=['POST'])
def post_message(drop_id):
    log = partial(log_request, time(), request.method)
    if not check_drop_id(drop_id):
        log(400)
        return '', status.HTTP_400_BAD_REQUEST

    message = request.data
    authorization_header = request.headers.get('Authorization')
    if authorization_header != 'Client Qabel':
        log(400)
        return 'Bad authorization', status.HTTP_400_BAD_REQUEST
    if message == b'' or message is None:
        log(400)
        return 'No message provided', status.HTTP_400_BAD_REQUEST
    if len(message) > MESSAGE_SIZE_LIMIT:
        log(413)
        return 'Message too large', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    try:
        drop = Drop(message=message, drop_id=drop_id)
        db.session.add(drop)
        db.session.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        mon.DROP_SAVE_ERROR.inc()
        db.session.rollback()
        return str(e), status.HTTP_200_OK
    mon.DROP_RECEIVED.inc()
    return '', status.HTTP_200_OK


def generate_response(drops, boundary):
    bound = str.encode(boundary)
    for drop in drops:
        date = str.encode(str(formatdate(mktime(drop.created_at.timetuple()), localtime=True, usegmt=True)))
        message = drop.message
        yield (b'--' + bound + b'\r\n')
        yield (b'Content-Type: application/octet-stream\r\n')
        yield (b'Date: ' + date + b'\r\n\r\n')
        yield (message + b'\r\n')
    yield (b'--' + bound + b'--\r\n')


def get_if_modified_since(request):
    since = request.headers.get('If-Modified-Since')
    return (False, datetime.fromtimestamp(0)) if since is None else (True, dateparser.parse(since))


def check_drop_id(drop_id):
    """Require a string of 43 randomly generated characters according to
    RFC 4648 Base 64 Encoding with URL and Filename Safe Alphabet."""
    try:
        return (len(drop_id) == 43
                and not re.search(r'[^-_A-Za-z0-9]', drop_id)
                and len(b64decode(drop_id + '=', '-_')) == 32)
    except TypeError:
        return False


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
