import sys, logging as log, re, json
from mpd import MPDClient
from mpd.base import ConnectionError
from threading import Lock

from .config import Config

class YarmpMPD(object):
    
    _lock = Lock()  
    _reconnect = ConnectionError
    _log = log
    _re = re
    _json = json
    _config = Config
    _default_options = {"url":"","resume":False,"repeat":False,"single":False,"crossfade":False,"random":False,"new":True}

    def __init__(self,socket):
        self.socket = socket
        self.mpd = MPDClient()
        self.mpd.idletimeout = None
        self.mpd.timeout = None
        self.subscribed_channels = []
        self.mpd.connect(socket)

    def load_playlist_options(self,rfid):
        try:
            with open(self._config.playlist_options,'r') as f:
                data = self._json.load(f)
        except: data = dict()
        return data.get(rfid,self._default_options)

    def save_playlist_options(self,rfid,options):
        try:
            with open(self._config.playlist_options,'r') as f:
                data = self._json.load(f)
        except: data = dict()
        options.pop("name",None)
        options.pop("new",None)
        with open(self._config.playlist_options,'w') as f:
            data[rfid] = options
            self._log.debug("Mpd: write playlist_options {!r} {!r}".format(rfid,options))
            self._json.dump(data,f,indent=2,separators=(',', ': ')) 


    def load_playlist(self,rfid,source=None):
        playlist, name = self.find_playlist(rfid)
        if playlist:
            self.clear()
            if source:
                new_playlist = self.listplaylist(source)
                if new_playlist and len(new_playlist):
                    self.rm(playlist)
                    self.load(source)
                    self.save(playlist)
                else:
                    self.load(playlist)
            else:
                self.load(playlist)
            return playlist, name
        return None, None

    def find_playlist(self,rfid):
        for pl in self.listplaylists():
            match = self._re.search("^RFID-{!s}-*(.+)*".format(rfid),pl['playlist'])
            if match:
                return match.group(), match.group(1)
        return None, None

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