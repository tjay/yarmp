import Queue, logging as log, importlib as imp
from config import Config
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

class Control(object):
  def __init__(self, mpd):
    self.mpd = mpd

  def error(self,e):
    log.error(e.value)

  def handle(self, event):
    if event.device not in Config.controls:
      raise NotImplementedError(event.device)
    if Config.controls[event.device] == type(self).__name__:
      if hasattr(self,event.function):
        getattr(self,event.function)(event)
      else:
        raise NotImplementedError("{!r}{!r}".format(type(self).__name__,event.function))
    elif type(self).__name__ == "Control":
        raise NotImplementedError(Config.controls[event.device])