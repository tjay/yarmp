import Queue, logging as log, importlib as imp, cPickle as cp, os, threading
from config import Config
from time import time
from devices import YarmpMPD, EvDevReceiver, RfidReceiver, Event

class Yarmp(object):
  def __init__(self):
    self.mpd = YarmpMPD()
    self.queue = Queue.Queue()

    cm = imp.import_module('yarmp.controls')
    controls = { c.lower(): getattr(cm,c,cm.Control)(self.mpd) for c in set(Config.controls.values()) }

    log.debug("Volume {!r}".format(controls["volume"].volume))

    self.evdev_rcv = EvDevReceiver(self.queue)
    self.rfid_rcv = RfidReceiver(self.queue, Config.rfid_tty)
    
    log.debug("Start")

    while 42:
      try:
        event = self.queue.get(timeout=2)
        for c in controls.values(): c.handle(event)
      except Queue.Empty:
        if controls["track"].track_state.play:
          # save the state only if we are playing sth
          controls["track"].set_save_loop(10)
        else:
          controls["track"].set_save_loop(0)
      except NotImplementedError as e:
        log.error("NotImplementedError %s" % e.message)
      except (KeyboardInterrupt, SystemExit):
        log.error("Exit on UserInterrupt")
        self.evdev_rcv.stop()
        self.rfid_rcv.stop()
        exit(0)

class TrackState(object):
  def __init__(self, rfid, mpd):
    status = mpd.status()
    self.time = time()
    self.rfid = rfid
    self.track = mpd.currentsong()
    self.play = status["state"] == "play"
    self.elapsed = status["time"] if not self.track.startswith("http") else 0

class States(object):

  states = []

  def __init__(self,save_states_time=3, save_loop_time = 0):
    self._load_states()
    self._save_states_time = save_states_time
    self._looping_time = save_loop_time
    self._save_thread = None
    
  def save_state(self, looping = False):
    if looping:
      save_states_time = self._looping_time
    if self.states:
      if self._save_thread:
        self._save_thread.cancel()
        # Do we need this?
        self._save_thread.join()
      self._save_thread = threading.Timer(save_states_time, self._save_states)
      self._save_thread.start()

  def set_save_loop(self,save_loop_time):
    self._looping_time = save_loop_time

  def _save_states(self):
    try: # pickle in states[] listed vars to class.name-File
      if self.states:
        with open(os.path.join(Config.base_dir,"."+type(self).__name__), 'w') as f:
          log.debug("Save the state of {!r}".format(type(self).__name__))
          cp.dump({state: getattr(self,state) for state in self.states},f)
        if self._looping_time > 0:
          self.save_state(looping=True)
    except Exception as e:
      log.error(e.message)
  
  def _load_states(self):
    try: # unpickle in states[] listet vars to class.name-File
      if self.states:
        with open(os.path.join(Config.base_dir,"."+type(self).__name__), 'r') as f:
          for key,value in cp.load(f).items():
            if key in self.states:
              setattr(self,key,value)
    except: pass

class Rfid(object):
  pass


class Control(States):

  def __init__(self, mpd, save_states_time=3, save_loop_time=0):
    self.mpd = mpd
    super(Control, self).__init__(
      save_states_time=save_states_time,
      save_loop_time = save_loop_time
    )

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