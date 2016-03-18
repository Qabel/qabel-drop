from flask_api import status


def test_invalid_dropid(client, registry):
    response = client.get('/invalid')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
