from flask_api import status
import datetime
from email.utils import format_datetime


def test_ok(client, drop_messages, registry):
    with registry.assert_get_request(200):
        response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK


def test_ok_head(client, drop_messages, registry):
    with registry.assert_head_request(200):
        response = client.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_200_OK


def test_invalid_dropid(client, registry):
    with registry.assert_get_request(400):
        response = client.get('/invalid')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_no_content(client, registry):
    with registry.assert_get_request(204):
        response = client.get('/xbcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_modified_since(client, drop_messages, registry):
    with registry.assert_get_request(304):
        dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
        response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                                headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})
        assert response.status_code == status.HTTP_304_NOT_MODIFIED
