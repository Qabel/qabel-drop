from prometheus_client import Summary, Counter

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')


FCM_CALLS = Counter('notify_fcm_calls',
                    'Number of notify_topic_subscribers FCM API calls', ['exception'])

# We only receive these stats for downstream messages - we intend to use topic messages
#FCM_MESSAGES_PROCESSED = Counter('notify_fcm_messages',
#                                 'Number of messages processed by FCM', ['outcome'])
