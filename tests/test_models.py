

from drop_service.models import Drop
from drop_service.util import utc_timestamp


def test_time_granularity(db):
    a = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnfoo', message=b"Bar")
    a.save()
    b = Drop(drop_id='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo', message=b"Hello World")
    b.save()
    dt = utc_timestamp(b.created_at) - utc_timestamp(a.created_at)
    assert dt > 0
