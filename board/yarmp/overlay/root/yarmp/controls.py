import serial, re, time, threading
from .config import Config
from .util import YarmpMPD, Message, EvDevControl

class Volume(EvDevControl):

  def __init__(self, queue):
    self.get_device('rotary@{:x}'.format(Config.volume_gpio))
    self.value_range = [Config.volume_min,Config.volume_max]
    EvDevControl.__init__(self,queue)

  def run(self):
    mpd = YarmpMPD()
    for event in self.device.read_loop():
      if event.type == 2:
        value = int(mpd.status()['volume']) + event.value
        if value in self.value_range:
          print "Volume", value
          mpd.setvol(value)
    self.queue.put(Message("exit"))

class Track(EvDevControl):
  def __init__(self, queue):
    self.get_device('rotary@{:x}'.format(Config.track_gpio))
    EvDevControl.__init__(self,queue)

  def run(self):
    for event in self.device.read_loop():
      if event.type == 2:
        print "Track", event.value
    self.queue.put(Message("exit"))


class Rfid(threading.Thread):

  start_byte = "\x02"
  rescan_timeout = 1.5
  bau_rate = 9600

  def __init__(self, queue):
    self.queue = queue
    self.serial_device = Config.rfid_serial
    self.ids = {}
    threading.Thread.__init__(self)
    self.start()

  def _run(self):
    mpd = YarmpMPD()
    with serial.Serial(self.serial_device, self.bau_rate) as s:
      while True:
        if s.read() == self.startbyte:
          try:
            d = map(lambda x: int(x,16), re.findall('..',s.read(12)))
            chcksm = d[0]
            for pos in range(1, 5):
              chcksm = chcksm ^ d[pos]
            assert chcksm == d[5]
            id = ''.join('{:02X}'.format(x) for x in d[:5])
            # TODO debug-logger
            read_time = time.time()
            if (id in self.ids and read_time > self.ids[id]) or id not in self.ids:
              self.ids[id] = read_time + self.rescan_timeout
              self.queue.put(Message("rfid",self.ids))
              mpd.setvol(int(mpd.status()['volume']) + 1)
          except Exception as e:
            # TODO error-logger
            pass