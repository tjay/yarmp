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
            if not self.queue.empty():
                message = self.queue.get_nowait()
                print message.name, message.value
                if message.name=="exit":
                    self.rfid.join()
                    self.volume.join()
                    self.track.join()
                    exit()

if __name__ == "__main__":
    Yarmp()