from mpd import MPDClient
from mpd.base import ConnectionError
import threading, evdev
from ..config import Config

class Message:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value

class YarmpMPD:
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
                try:
                    return getattr(self.mpd, attr)(*args, **kw)
                except ConnectionError:
                    self.mpd.connect(Config.mpd_socket)
                    return getattr(self.mpd, attr)(*args, **kw)
            return wrapper
        raise AttributeError(attr)

class EvDevControl(threading.Thread):

  def __init__(self, queue):
    self.queue = queue
    threading.Thread.__init__(self)
  
  def get_device(self, device_name):
    self.device = None
    for fn in evdev.list_devices():
      self.device = evdev.InputDevice(fn)
      if self.device.name == device_name:
        break
    assert self.device and self.device.name == device_name, "%s not found" % device_name

  def run(self):
    self.queue.put(Message("exit"))