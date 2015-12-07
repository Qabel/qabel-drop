import datetime

from app import db


class Drop(db.Model):
    __tablename__ = "drops"

    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    drop_id = db.Column('drop_id', db.String)
    message = db.Column('message', db.LargeBinary)
    created_at = db.Column('created_at', db.DateTime, default=datetime.datetime.utcnow())

    def __init__(self, drop_id, message):
        self.drop_id = drop_id
        self.message = message

    def __repr__(self):
        return u'<{0} for {1} created at {2} >'.format(self.drop_id, self.message, self.created_at)
