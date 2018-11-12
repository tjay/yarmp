import Queue
from controls import Track, Volume, Rfid
from .util import YarmpMPD

class Yarmp:
    def __init__(self):

        self.queue = Queue.Queue()
        self.rfid = Rfid(self.queue)
        self.volume = Volume(self.queue)
        self.track = Track(self.queue)
        self.mpd = YarmpMPD()
        self.run()

    def run(self):
        self.mpd.add('http://rbb-fritz-live.cast.addradio.de/rbb/fritz/live/mp3/128/stream.mp3')
        #       client.add('mac.mp3')
        self.mpd.setvol(18)
        self.mpd.play(0)
        while 42:
            try:
                message = self.queue.get()
                print message.name, message.value
            except (KeyboardInterrupt, SystemExit):
                print "exit" # wont work :/
                exit(0)


if __name__ == "__main__":
    Yarmp()