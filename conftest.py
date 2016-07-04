import datetime
from contextlib import contextmanager
from functools import partial

import pytz

import pytest

from prometheus_client import REGISTRY

from drop_service.models import Drop


@pytest.fixture
def drop_messages(db):
    drop = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
    dropfoo = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
    dropfoo.created_at = datetime.datetime(year=2016, month=1, day=1, tzinfo=pytz.UTC)
    drop.save()
    dropfoo.save()
    return drop, dropfoo
