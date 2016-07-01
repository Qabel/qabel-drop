from prometheus_client import Summary, Counter

# Remove this? It's a bit redundant with django-prometheus around which generates very similar stats (among other things).
REQUEST_TIME = Summary('drop_request_processing',
                       'Time spent processing request', ['status', 'method'])

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')
