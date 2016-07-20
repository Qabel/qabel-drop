from prometheus_client import Summary, Counter

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')


FCM_CALLS = Counter('notify_fcm_calls',
                    'Number of notify_topic_subscribers FCM API calls', ['exception'])
