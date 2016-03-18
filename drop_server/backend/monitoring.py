from prometheus_client import Summary

REQUEST_TIME = Summary('drop_request_processing',
                       'Time spent processing request', ['status', 'method'])
