import pytest
from prometheus_client import REGISTRY
from drop_server.app import app as flask_app, db as flask_db
from drop_server.backend.models import Drop
from drop_server.backend import views


class Registry:

    @staticmethod
    def _by_method(method, status):
        return REGISTRY.get_sample_value('drop_request_processing_count',
                                         {'method': method, 'status': str(status)})

    @staticmethod
    def get_requests(status):
        return Registry._by_method('GET', status)

    @staticmethod
    def post_requests(status):
        return Registry._by_method('POST', status)

    @staticmethod
    def head_requests(status):
        return Registry._by_method('HEAD', status)


@pytest.fixture
def registry():
    return Registry


@pytest.fixture(scope='session')
def app():
    app = flask_app
    app.testing = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


@pytest.fixture
def db(app):
    with app.app_context():
        flask_db.init_app(app)
        flask_db.metadata.create_all(flask_db.engine)
    return flask_db


@pytest.fixture
def drop_messages(app, db):
    with app.app_context():
        drop = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
        dropfoo = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
        db.session.add(drop)
        db.session.add(dropfoo)
        db.session.commit()
        return [drop, dropfoo]
