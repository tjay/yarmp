import threading, logging as log, os, cPickle as cp
from time import sleep, time
from collections import OrderedDict
import ympd as mpd

from .config import Config

class Event(object):
  __slots__ = ['time', 'device', 'function', 'value']
  def __init__(self, time, device, function, value):
    self.time = time
    self.device = device
    self.function = function
    self.value = value

  def __str__(self):
    msg = 'event at {:f}, code {!r}, type {!r}, val {!r}'
    return msg.format(self.time, self.device, self.function, self.value)

def setInterval(interval):
  def decorator(function):
    def wrapper(*args, **kwargs):
      stopped = threading.Event()
      def loop(parent): # executed in another thread
        wait = 0.5
        wait_intervals = 0
        assert interval > 0
        while not stopped.wait(wait): # until stopped
          wait_intervals+=wait
          if not parent.is_alive():
            stopped.set()
          if wait_intervals >= interval:
            wait_intervals = 0
            function(*args, **kwargs)
      t = threading.Thread(target=loop,name="SaveLoop",args=(threading.current_thread(),))
      t.start()
    return wrapper
  return decorator

class States(object):

  states = []

  def __init__(self,save_states_time=3):
    self._load_states()
    self._save_states_time = save_states_time
    self._save_thread = None
    
  def save_state(self,atcall=False):
    if self.states:
      if self._save_thread:
        self._save_thread.cancel()
        self._save_thread.join()
      if atcall:
        self._save_states()
      else:
        self._save_thread = threading.Timer(self._save_states_time, self._save_states)
        self._save_thread.name="SaveTimer"
        self._save_thread.start()

  def _save_states(self):
    try: # pickle in states[] listed vars to class.name-File
      if self.states:
        with open(os.path.join(Config.base_dir,"."+type(self).__name__.lower()), 'w') as f:
          log.debug("Save the state of {!r}".format(type(self).__name__.lower()))
          cp.dump({state: getattr(self,state) for state in self.states},f)
    except Exception as e:
      log.error("{}: {}".format(type(e).__name__, e))
  
  def _load_states(self):
    try: # unpickle in states[] listet vars to class.name-File
      if self.states:
        with open(os.path.join(Config.base_dir,"."+type(self).__name__.lower()), 'r') as f:
          for key,value in cp.load(f).items():
            if key in self.states:
              setattr(self,key,value)
    except Exception as e:
      log.error("{}: {}".format(type(e).__name__.lower(), e))

class Control(States):

  def __init__(self, save_states_time=3):
    super(Control, self).__init__(save_states_time=save_states_time)

  def error(self,e):
    log.error(e.value)

  def handle(self, event):
    if event.device not in Config.controls:
      raise NotImplementedError(event.device)
    if Config.controls[event.device] == type(self).__name__:
      if hasattr(self,event.function):
        getattr(self,event.function)(event)
        self.save_state()
      else:
        raise NotImplementedError("{!r}{!r}".format(type(self).__name__,event.function))
    elif type(self).__name__ == "Control":
        raise NotImplementedError(Config.controls[event.device])

class TrackState(object):
  def __init__(self, rfid=None):
    self.timestamp = time()
    self.rfid = rfid
    for k,v in mpd.status().items(): # pylint: disable=no-member
      setattr(self,k,v)

class LastUpdatedOrderedFIFODict(OrderedDict):
  def __init__(self, maxsize = 10):
    self.maxsize = maxsize
    super(LastUpdatedOrderedFIFODict, self).__init__()

  def oldest_value(self):
    if self:
      return next(iter(self.values()))

  def oldest_key(self):
    if self:
      return next(iter(self.keys()))

  def newest_value(self):
    if self:
      return next(reversed(self.values()))

  def newest_key(self):
    if self:
      return next(reversed(self.keys()))
  
  def is_newest(self,key):
    return self.newest_key() == key

  def is_oldest(self,key):
    return self.oldest_key() == key
  
  def __setitem__(self, key, value):
    if key in self:
      del self[key]
    while len(self) > self.maxsize:
      OrderedDict.popitem(self, last=False)
    OrderedDict.__setitem__(self, key, value)