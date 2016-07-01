import datetime
from contextlib import contextmanager
from functools import partial

import pytz

import pytest

from prometheus_client import REGISTRY

from drop_service.models import Drop


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


@pytest.fixture
def drop_messages(db):
    drop = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
    dropfoo = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
    dropfoo.created_at = datetime.datetime(year=2016, month=1, day=1, tzinfo=pytz.UTC)
    drop.save()
    dropfoo.save()
    return drop, dropfoo
