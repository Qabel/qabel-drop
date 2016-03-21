import pytest
from prometheus_client import REGISTRY
from drop_server.app import app as flask_app, db as flask_db
from drop_server.backend.models import Drop
from drop_server.backend import views
from contextlib import contextmanager
from functools import partial


class Registry:
    @contextmanager
    def _by_method(method, status):
        get = partial(REGISTRY.get_sample_value,
                      'drop_request_processing_count',
                      {'method': method, 'status': str(status)})
        before = get()
        if before is None:
            before = 0

        yield
        after = get()
        assert after is not None, 'No request registered with status {}'.format(status)
        assert before + 1 == after

    @staticmethod
    def assert_get_request(status):
        return Registry._by_method('GET', status)

    @staticmethod
    def assert_post_request(status):
        return Registry._by_method('POST', status)

    @staticmethod
    def assert_head_request(status):
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
