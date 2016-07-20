import time
from contextlib import contextmanager

from prometheus_client import Histogram, Counter

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')


FCM_CALLS = Counter('notify_fcm_calls',
                    'Number of notify_topic_subscribers FCM API calls', ['exception'])


FCM_DURATION = Histogram('notify_fcm_duration',
                         'Time spent in FCM API calls')


@contextmanager
def monitor_duration(metric):
    t0 = time.perf_counter()
    yield
    t1 = time.perf_counter()
    dt = t1 - t0
    metric.observe(dt)
