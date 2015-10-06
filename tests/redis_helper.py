from subprocess import Popen, PIPE
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
from time import sleep

proc = None


def startRedisServer():
    # s.a. https://github.com/jamesls/fakeredis
    global proc
    try:
        # run the redis-server as a subprocess:
        proc = Popen(['redis-server', '--save', '""'], stdout=PIPE)
        # outs, errs = proc.communicate(timeout=...) is Py 3.x only
        # set the O_NONBLOCK flag of stdout file descriptor:
        flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
    except:
        return False
    outs = b''
    timeout = 5
    while timeout > 0 and not b'ready to accept connections' in outs:
        sleep(0.1)
        timeout -= 0.1
        try:
            outs += read(proc.stdout.fileno(), 1024)
        except OSError:
            # exception if there is no data
            pass
    if timeout > 0:
        return True
    else:
        proc.terminate()
        return False


def stopRedisServer():
    proc.terminate()
