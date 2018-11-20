import Queue, logging as log, importlib as imp

from .config import Config
from .devices import EvDevReceiver, RfidReceiver
from .utils import Event

class Yarmp(object):
  def __init__(self):
    self.queue = Queue.Queue()
    
    cm = imp.import_module('yarmp.controls')
    controls = { c.lower(): getattr(cm,c,cm.Control)() for c in set(Config.controls.values()) }

    log.debug("Volume {!r}".format(controls["volume"].volume))

    self.evdev_rcv = EvDevReceiver(self.queue)
    self.rfid_rcv = RfidReceiver(self.queue,Config.rfid_tty)
    
    log.debug("Start")

    while 42:
      try:
        event = self.queue.get(timeout=2)
        for c in controls.values(): c.handle(event)
      except Queue.Empty: pass
      except NotImplementedError as e:
        log.error("NotImplementedError %s" % e.message)
      except (KeyboardInterrupt, SystemExit):
        log.error("Exit on UserInterrupt")
        exit(0)