from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
with app.app_context():
    db.init_app(current_app)
