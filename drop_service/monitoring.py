import time
from contextlib import contextmanager

from prometheus_client import Summary, Counter

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')


FCM_API = Summary('notify_fcm_api',
                  'Number and duration of notify_topic_subscribers FCM API calls', ['exception'])


@contextmanager
def monitor_duration(metric, **labels):
    t0 = time.perf_counter()
    yield labels
    t1 = time.perf_counter()
    dt = t1 - t0
    metric.labels(labels).observe(dt)
