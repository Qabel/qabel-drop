from prometheus_client import Summary, Counter
import threading

REQUEST_TIME = Summary('drop_request_processing',
                       'Time spent processing request', ['status', 'method'])

DROP_SAVE_ERROR = Counter('drop_save_message_failed',
                          'Exception when trying to save a drop message')

DROP_SENT = Counter('drop_messages_delivered',
                    'Amount of delivered drop messages')

DROP_RECEIVED = Counter('drop_messages_received',
                        'Amount of received drop messages')


class PrometheusEndpointServer(threading.Thread):
    def __init__(self, httpd, *args, **kwargs):
        self.httpd = httpd
        super().__init__(*args, **kwargs)

    def run(self):
        self.httpd.serve_forever()
