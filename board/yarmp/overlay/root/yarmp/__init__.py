import Queue, logging as log, importlib as imp, cPickle as cp, os
from config import Config
import threading
from devices import YarmpMPD, EvDevReceiver, RfidReceiver

class Yarmp:
    def __init__(self):
        self.mpd = YarmpMPD()
        self.queue = Queue.Queue()

        cm = imp.import_module('yarmp.controls')
        self.controls = [ getattr(cm,c,cm.Control)(self.mpd) for c in set(Config.controls.values()) ]

        self.evdev_rcv = EvDevReceiver(self.queue)
        self.rfid_rcv = RfidReceiver(self.queue, Config.rfid_tty)

        log.debug("Start")

        while 42:
            try:
                event = self.queue.get(timeout=1)
                for c in self.controls: c.handle(event)
            except Queue.Empty: pass
            except NotImplementedError as e:
                log.error("NotImplementedError %s" % e.message)
            except (KeyboardInterrupt, SystemExit):
                log.error("Exit on UserInterrupt")
                self.evdev_rcv.stop()
                self.rfid_rcv.stop()
                exit(0)

class States(object):

  states = []

  def __init__(self,save_states_time=3):
    self._load_states()
    self._save_states_time = save_states_time
    self._save_thread = None
    
  def save_state(self):
    if self.states:
      if self._save_thread:
        self._save_thread.cancel()
        self._save_thread.join()
      self._save_thread = threading.Timer(self._save_states_time, self._save_states)
      self._save_thread.start()

  def _save_states(self):
    print type(self).__name__, self.states
    try: # pickle in states[] listet vars to class.name-File
      if self.states:
        with open(os.path.join(Config.states_dir,type(self).__name__), 'w') as f:
          cp.dump({state: getattr(self,state) for state in self.states},f)
    except Exception as e:
      log.debug(e.message)
  
  def _load_states(self):
    try: # unpickle in states[] listet vars to class.name-File
      if self.states:
        with open(os.path.join(Config.states_dir,type(self).__name__), 'r') as f:
          for key,value in cp.load(f).items():
            if key in self.states:
              setattr(self,key,value)
    except: pass

class Control(States):

  def __init__(self, mpd, save_states_time=3):
    self.mpd = mpd
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