import Queue, logging as log
from controls import Track, Volume
from devices import YarmpMPD, EvDevReceiver, RfidReceiver

class Yarmp:
    def __init__(self):
        self.mpd = YarmpMPD()
        self.queue = Queue.Queue()
        self.serial_receiver = EvDevReceiver(self.queue)
        self.rfid_receiver = RfidReceiver(self.queue)
        log.debug("Start")

        self.mpd.add('http://rbb-fritz-live.cast.addradio.de/rbb/fritz/live/mp3/128/stream.mp3')
        self.mpd.setvol(18)
        self.mpd.play(0)

        while 42:
            try:
                print self.queue.get()
            except (KeyboardInterrupt, SystemExit):
                self.serial_receiver.stop()
                self.rfid_receiver.stop()
                log.info("Exit")
                exit(0)