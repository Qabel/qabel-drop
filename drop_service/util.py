
import base64
import re


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
