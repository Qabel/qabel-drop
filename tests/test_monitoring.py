from flask_api import status
import datetime
from email.utils import format_datetime


def test_ok(client, drop_messages, registry):
    response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    assert response.status_code == status.HTTP_200_OK
    assert registry.get_requests(200) == 1


def test_ok_head(client, drop_messages, registry):
    response = client.head('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    assert response.status_code == status.HTTP_200_OK
    assert registry.head_requests(200) == 1


def test_invalid_dropid(client, registry):
    response = client.get('/invalid')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert registry.get_requests(400) == 1


def test_no_content(client, registry):
    response = client.get('/xbcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert registry.get_requests(204) == 1


def test_modified_since(client, drop_messages, registry):
    dt = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=1)
    response = client.get('/abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo',
                            headers={'If-Modified-Since': format_datetime(dt, usegmt=True)})
    assert response.status_code == status.HTTP_304_NOT_MODIFIED
    assert registry.get_requests(304) == 1
