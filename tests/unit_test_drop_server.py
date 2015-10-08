from nose.tools import eq_, raises
import re
from io import BytesIO

from drop_server import *


def test_create_boundary_id():
    id_ = create_boundary_id()
    eq_(len(id_), 12)
    assert not re.search(b'[^-_A-Za-z0-9]', id_)


def test_extract_drop_id():
    id_ = extract_drop_id('/T/ES..T+')
    eq_(id_, 'TEST')


def test_check_drop_id():
    # ok
    assert check_drop_id('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # too short
    assert not check_drop_id('bcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # too long
    assert not check_drop_id('xabcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # illegal character
    assert not check_drop_id('.bcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # non-identity encoding
    assert check_drop_id('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq')
    # missing argument
    assert not check_drop_id(None)
    # incorrect padding
    assert not check_drop_id('x')


def test_decode_record():
    eq_(decode_record(b'1337:TAIL:TEXT'), (1337, b'TAIL:TEXT'))
    eq_(decode_record(b'0:TAIL'), (0, b'TAIL'))


@raises(ValueError)
def test_decode_record_empty():
    decode_record(':TAIL:TEXT')


@raises(ValueError)
def test_decode_record_nonnumber():
    decode_record('HEAD:TAIL')


def test_encode_record():
    eq_(encode_record(0, 'TAIL'), '0:TAIL')
    eq_(encode_record(1337, 'TAIL'), '1337:TAIL')


@raises(TypeError)
def test_encode_record_missing():
    encode_record(None, 'TAIL')


@raises(ValueError)
def test_encode_record_empty():
    encode_record('', 'TAIL')


@raises(ValueError)
def test_encode_record_nonnumber():
    encode_record('HEAD', 'TAIL')


def test_read_postbody_form():
    env = {'CONTENT_TYPE': 'application/x-www-form-urlencoded'}
    env['wsgi.input'] = BytesIO(b'BODY+DATA%3ATEXT')
    eq_(read_postbody(env), None)
    env['wsgi.input'] = BytesIO(b'')
    eq_(read_postbody(env), None)
    env['wsgi.input'] = BytesIO(b'text=BODY+DATA%3ATEXT&moar=text')
    eq_(read_postbody(env), b'BODY DATA:TEXT')
    env['wsgi.input'] = BytesIO(b'moar=text&text=BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY DATA:TEXT')
    env['wsgi.input'] = BytesIO(b'text=first&text=BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY DATA:TEXT')
    env['wsgi.input'] = BytesIO(b'random=BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY DATA:TEXT')


def test_read_postbody_stream():
    env = {'CONTENT_TYPE': 'application/octet-stream'}
    env['wsgi.input'] = BytesIO(b'BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY+DATA%3ATEXT')


def test_read_postbody_multipart():
    env = {'CONTENT_TYPE': 'multipart/form-data; boundary=boundary'}
    env['wsgi.input'] = BytesIO(
        b'--boundary\r\n' +
        b'Content-Disposition: form-data; name="text"\r\n' +
        b'Content-Type: application/octet-stream\r\n' +
        b'\r\n' +
        b'BODY+DATA%3ATEXT' +
        b'\r\n' +
        b'--boundary--\r\n')
    eq_(read_postbody(env), b'BODY+DATA%3ATEXT')

    env['wsgi.input'] = BytesIO(
        b'--boundary\r\n' +
        b'Content-Disposition: form-data; name="NOT_TEXT"\r\n' +
        b'Content-Type: application/octet-stream\r\n' +
        b'\r\n' +
        b'BODY+DATA%3ATEXT' +
        b'\r\n' +
        b'--boundary--\r\n')
    eq_(read_postbody(env), b'BODY+DATA%3ATEXT')


def test_read_postbody_empty():
    env = {'CONTENT_TYPE': ''}
    env['wsgi.input'] = BytesIO(b'BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY+DATA%3ATEXT')


def test_read_postbody_missing():
    env = {}  # no 'CONTENT_TYPE'
    env['wsgi.input'] = BytesIO(b'BODY+DATA%3ATEXT')
    eq_(read_postbody(env), b'BODY+DATA%3ATEXT')


def test_pywsgi_serve():
    import threading
    d = threading.Thread(target=main)
    d.daemon = True
    d.start()
    d.join(1)
    assert d.is_alive()
