import uuid
from datetime import datetime
from email._parseaddr import parsedate_tz
from email.utils import formatdate
from time import mktime
import re
from base64 import b64decode
from flask import Response, request
from flask_api import status
from models import Drop
from app import app, db

MESSAGE_SIZE_LIMIT = 2573  # Octets


@app.route('/<path:drop_id>', methods=['GET', 'HEAD'])
def get_drop_messages(drop_id):
    since_b, since = get_if_modified_since(request)
    if not check_drop_id(drop_id):
        return '', status.HTTP_400_BAD_REQUEST
    drops = db.session.query(Drop).filter(Drop.drop_id == drop_id).all()
    if not drops:
        return '', status.HTTP_204_NO_CONTENT
    if since_b:
        drops = db.session.query(Drop).filter(Drop.drop_id == drop_id, Drop.created_at >= since).all()
        if not drops:
            return '', status.HTTP_304_NOT_MODIFIED
    if request.method == 'GET':
        boundary = str(uuid.uuid4())
        return Response(generate_response(drops, boundary), status=200,
                        content_type='multipart/mixed; boundary="' + boundary + '"')
    else:
        return '', status.HTTP_200_OK


@app.route('/<path:drop_id>', methods=['POST'])
def post_message(drop_id):
    if not check_drop_id(drop_id):
        return '', status.HTTP_400_BAD_REQUEST

    message = request.data
    if message == b'' or message is None:
        return '', status.HTTP_400_BAD_REQUEST
    if len(message) > MESSAGE_SIZE_LIMIT:
        return '', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    try:
        drop = Drop(message=message, drop_id=drop_id)
        db.session.add(drop)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return str(e), status.HTTP_200_OK

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
    return (False, datetime.fromtimestamp(0)) if since is None else (True, datetime(*parsedate_tz(since)[0:7]))


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
