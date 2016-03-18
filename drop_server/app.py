from http.server import HTTPServer
import logging

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from drop_server.backend.monitoring import PrometheusEndpointServer
import prometheus_client

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
with app.app_context():
    db.init_app(current_app)

if app.config.get('PROMETHEUS_ENABLE', False):
    prom_adr = app.config['PROMETHEUS_ADDRESS']
    for port in app.config['PROMETHEUS_PORTS']:
        try:
            httpd = HTTPServer((prom_adr, port), prometheus_client.MetricsHandler)
        except OSError as e:
            print(e)
            continue  # Try next port
        thread = PrometheusEndpointServer(httpd)
        thread.daemon = True
        thread.start()
        logger.info('Serving prometheus on {}:{}'.format(prom_adr, port))
        break
    else:
        raise OSError('No port for prometheus metrics available')
