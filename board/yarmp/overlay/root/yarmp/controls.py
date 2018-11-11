import serial, re, time, threading
from .config import Config
from .util import YarmpMPD, Message, EvDevControl

#https://github.com/gvalkov/python-evdev/issues/15#issuecomment-21807699

class Volume(EvDevControl):

  def __init__(self, queue, value = 0):
    self.get_device('rotary@{:x}'.format(Config.volume_gpio))
    self.value_range = [Config.volume_min,Config.volume_max]
    self.value = value
    super(Volume, self).__init__(queue)

  def run(self):
    for event in self.device.read_loop():
      if event.type == 2:
        if self.value + event.value in self.value_range:
          self.queue.put(Message("Volume",self.value + event.value))
    self.queue.put(Message("exit"))

class Track(EvDevControl):
  def __init__(self, queue):
    self.get_device('rotary@{:x}'.format(Config.track_gpio))
    super(Track, self).__init__(queue)

  def run(self):
    for event in self.device.read_loop():
      if event.type == 2:
        self.queue.put(Message("Track",event.value))
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

  def _run(self):
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
          except Exception:
            # TODO error-logger
            pass