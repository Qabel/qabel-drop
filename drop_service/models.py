
from django.db import models
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin


class Drop(ExportModelOperationsMixin('Drop'), models.Model):
    __tablename__ = "drops"

    # SQLAlchemy → Django-ORM port note: the 'id' field is implicitly defined as an integer, auto-increment primary-key

    # check_drop_id enforces exactly 43 ASCII characters
    drop_id = models.CharField(max_length=43)
    message = models.BinaryField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Force un-prefixed table name for compatibility
        db_table = 'drops'
        get_latest_by = 'created_at'

    def __repr__(self):
        return u'<{0} for {1} created at {2} >'.format(self.drop_id, self.message, self.created_at)


class PushSubscription(ExportModelOperationsMixin('PushSubscription'), models.Model):
    SERVICES = (
        ('fcm', 'Firebase Cloud Messaging'),
    )

    service = models.CharField(max_length=20, choices=SERVICES)
    device_id = models.CharField(max_length=100)
    drop_id = models.CharField(max_length=43)
