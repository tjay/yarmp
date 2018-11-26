import sys, logging as log
from mpd import MPDClient
from mpd.base import ConnectionError
from threading import Lock

from .config import Config

class YarmpMPD(object):
    
    _lock = Lock()  
    _reconnect = ConnectionError
    _log = log

    def __init__(self,socket):
        self.socket = socket
        self.mpd = MPDClient()
        self.mpd.idletimeout = None
        self.mpd.timeout = None
        self.mpd.connect(socket)

    def __getattr__(self, attr):
        if hasattr(self.mpd, attr):
            def wrapper(*args, **kw):
                self._lock.acquire() #MPDClient is not threadsafe
                try:
                    return getattr(self.mpd, attr)(*args, **kw)
                except self._reconnect:
                    self.mpd.connect(self.socket)
                    return getattr(self.mpd, attr)(*args, **kw)
                except Exception as e:
                    self._log.error("{}: {}".format(type(e).__name__, e))
                finally:
                    self._lock.release()
            return wrapper
        raise AttributeError(attr)

sys.modules[__name__] = YarmpMPD(Config.mpd_socket)