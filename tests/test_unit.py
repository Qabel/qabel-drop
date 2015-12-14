from views import check_drop_id

def test_check_drop_id():
    # ok
    assert check_drop_id('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # too short
    assert not check_drop_id('bcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # too long
    assert not check_drop_id('xabcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # illegal character
    assert not check_drop_id('.bcdefghijklmnopqrstuvwxyzabcdefghijklmnopo')
    # non-identity encoding
    assert check_drop_id('abcdefghijklmnopqrstuvwxyzabcdefghijklmnopq')
    # missing argument
    assert not check_drop_id(None)
    # incorrect padding
    assert not check_drop_id('x')
