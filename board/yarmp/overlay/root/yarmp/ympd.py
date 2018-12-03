import sys, logging as log, re
from mpd import MPDClient
from mpd.base import ConnectionError
from threading import Lock

from .config import Config

class YarmpMPD(object):
    
    _lock = Lock()  
    _reconnect = ConnectionError
    _log = log
    _re = re

    def __init__(self,socket):
        self.socket = socket
        self.mpd = MPDClient()
        self.mpd.idletimeout = None
        self.mpd.timeout = None
        self.subscribed_channels = []
        self.mpd.connect(socket)


    def load_playlist(self,rfid,source=None):
        playlist = self.find_playlist(rfid)
        if playlist:
            self.clear()
            if source and len(self.listplaylist(source)):
                self.rm(playlist)
                self.load(source)
                self.save(playlist)
            else:
                self.load(playlist)
            return playlist

    def find_playlist(self,rfid):
        for pl in self.listplaylists():
            match = self._re.search("^RFID-{!s}.*".format(rfid),pl['playlist'])
            if match:
                return match.group()

    def __getattr__(self, attr):
        if hasattr(self.mpd, attr):
            def wrapper(*args, **kw):
                self._lock.acquire() #MPDClient is not threadsafe
                try:
                    return getattr(self.mpd, attr)(*args, **kw)
                except self._reconnect:
                    self.mpd.connect(self.socket)
                    self.subscribed_channels = []
                    return getattr(self.mpd, attr)(*args, **kw)
                except Exception as e:
                    self._log.error("{}: {}".format(type(e).__name__, e))
                finally:
                    self._lock.release()
            return wrapper
        raise AttributeError(attr)

sys.modules[__name__] = YarmpMPD(Config.mpd_socket)