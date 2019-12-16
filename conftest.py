import datetime
from contextlib import contextmanager
from functools import partial

import pytz

import pytest

from prometheus_client import REGISTRY

from drop_service.models import Drop


class Registry:
    @contextmanager
    def _assert_sample_delta(counter, count):
        get = partial(REGISTRY.get_sample_value, counter)
        before = get() or 0
        yield
        after = get() or 0
        assert before + count == after

    @staticmethod
    def assert_drop_sent(count=1):
        return Registry._assert_sample_delta('drop_messages_delivered_total', count)

    @staticmethod
    def assert_drop_received(count=1):
        return Registry._assert_sample_delta('drop_messages_received_total', count)


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
