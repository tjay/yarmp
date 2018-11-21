import Queue, logging as log, importlib as imp

from .config import Config
from .devices import EvDevReceiver, RfidReceiver

log.basicConfig(level=log.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

queue = Queue.Queue()

cm = imp.import_module('yarmp.controls')
controls = { c.lower(): getattr(cm,c,cm.Control)() for c in set(Config.controls.values()) }

EvDevReceiver(queue)
RfidReceiver(queue,Config.rfid_tty)

log.info("Start")

while 42:
    try:
        event = queue.get(timeout=2)
        for c in controls.values(): c.handle(event)
    except Queue.Empty: pass
    except NotImplementedError as e:
        log.error("NotImplementedError %s" % e.message)
    except (KeyboardInterrupt, SystemExit):
        log.error("Exit on UserInterrupt")
        exit(0)
    except Exception as e:
        log.error("{}: {}".format(type(e).__name__, e))
        exit(1)
