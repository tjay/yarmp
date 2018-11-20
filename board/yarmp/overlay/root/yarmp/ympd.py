import sys
from mpd import MPDClient
from mpd.base import ConnectionError
from threading import Lock

from .config import Config

_lock = Lock()

class YarmpMPD(object):
    

    def __init__(self):
        self.mpd = MPDClient()
        self.yarmp_connect()

    def yarmp_connect(self):
        self.mpd.connect(Config.mpd_socket)
        self.mpd.idletimeout = None
        self.mpd.timeout = None

    def __getattr__(self, attr):
        if hasattr(self.mpd, attr):
            def wrapper(*args, **kw):
                _lock.acquire() #MPDClient is not threadsafe
                try:
                    return getattr(self.mpd, attr)(*args, **kw)
                except ConnectionError:
                    self.mpd.connect(Config.mpd_socket)
                    return getattr(self.mpd, attr)(*args, **kw)
                finally:
                    _lock.release()
            return wrapper
        raise AttributeError(attr)

sys.modules[__name__] = YarmpMPD()