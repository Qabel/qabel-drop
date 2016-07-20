
import base64
import datetime
import re
from concurrent.futures import Future

from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


def check_drop_id(drop_id):
    """
    Require a string of 43 randomly generated characters according to
    RFC 4648 Base 64 Encoding with URL and Filename Safe Alphabet.
    """
    try:
        return (len(drop_id) == 43
                and not re.search(r'[^-_A-Za-z0-9]', drop_id)
                and len(base64.b64decode(drop_id + '=', '-_')) == 32)
    except TypeError:
        return False


def set_last_modified(response, modification_date):
    response['Last-Modified'] = modification_date.strftime("%a, %d %b %Y %H:%M:%S GMT")


def utc_timestamp(datetime_obj):
    """Return float UTC timestamp for *datetime_obj*."""
    return datetime_obj.replace(tzinfo=datetime.timezone.utc).timestamp()


class CsrfExemptView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SynchronousExecutor:
    def submit(self, callable, *args, **kwargs):
        future = Future()
        future.set_running_or_notify_cancel()  # synchronous, can't be canceled
        try:
            future.set_result(callable(*args, **kwargs))
        except Exception as exc:
            future.set_exception(exc)
        return future
