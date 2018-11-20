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
        with open(os.path.join(Config.base_dir,"."+type(self).__name__), 'w') as f:
          log.debug("Save the state of {!r}".format(type(self).__name__))
          cp.dump({state: getattr(self,state) for state in self.states},f)
    except Exception as e:
      log.error("States: _save_states {!r}".format(e.message))
  
  def _load_states(self):
    try: # unpickle in states[] listet vars to class.name-File
      if self.states:
        with open(os.path.join(Config.base_dir,"."+type(self).__name__), 'r') as f:
          for key,value in cp.load(f).items():
            if key in self.states:
              setattr(self,key,value)
    except Exception as e:
      log.error("States: _load_states {!r}".format(e.message))

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
  def __init__(self, rfid):
    self.time = time()
    self.rfid = rfid
    status = mpd.status() # pylint: disable=no-member
    self.track = mpd.currentsong().get("file","") # pylint: disable=no-member
    self.play = status.get("state",None) == "play"
    self.elapsed = status.get("time",0) if not self.track.startswith("http") else 0

class LastUpdatedOrderedFIFODict(OrderedDict):
  def __init__(self, maxsize = 10):
    self.maxsize = maxsize
    super(LastUpdatedOrderedFIFODict, self).__init__()

  def oldest_item(self):
    if self:
      return next(iter(self.items()))

  def newest_item(self):
    if self:
      return next(reversed(self.items()))
  
  def __setitem__(self, key, value):
    if key in self:
      del self[key]
    while len(self) > self.maxsize:
      OrderedDict.popitem(self, last=False)
    OrderedDict.__setitem__(self, key, value)