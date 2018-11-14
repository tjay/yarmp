import threading, evdev, serial, re
from mpd import MPDClient
from mpd.base import ConnectionError
from time import time
from select import select
from config import Config

class Event(object):
    __slots__ = ['timestamp', 'type', 'code', 'value']
    def __init__(self, timestamp, type, code, value):
        self.timestamp = timestamp
        self.type = type
        self.code = code
        self.value = value

    def __str__(self):
        msg = 'event at {:f}, code {:02d}, type {:02d}, val {:02d}'
        return msg.format(self.timestamp, self.code, self.type, self.value)

class YarmpMPD:
    def __init__(self):
        self.mpd = MPDClient()
        self.yarmp_connect()

    def yarmp_connect(self):
        self.mpd.connect(Config.mpd_socket)
        self.mpd.idletimeout = None
        self.mpd.timeout = None

    def __getattr__(self, attr):
        if hasattr(self.mpd, attr):
            def wrapper(*args, **kw):
                try:
                    return getattr(self.mpd, attr)(*args, **kw)
                except ConnectionError:
                    self.mpd.connect(Config.mpd_socket)
                    return getattr(self.mpd, attr)(*args, **kw)
            return wrapper
        raise AttributeError(attr)

class Receiver(threading.Thread):
    def __init__(self, queue, name="Receiver"):
        self.stopper = threading.Event()
        self.queue = queue
        super(Receiver, self).__init__(name=name,target=self.receive)
        self.start()

    def receive(self):
        raise NotImplementedError

    def stop(self):
        self.stopper.set()
        self.join()

class EvDevReceiver(Receiver):
    def __init__(self, queue):
        super(EvDevReceiver, self).__init__(queue, name="EvDevReceiver")
    
    @property
    def devices(self):
        try: self.__devices
        except AttributeError:
            self.__devices = {dev.fd: dev for dev in [evdev.InputDevice(fn) for fn in evdev.list_devices()]}
        return self.__devices

    def receive(self):
        while not self.stopper.is_set():
            r, _, _ = select(self.devices, [], [], 0.01)
            for fd in r:
                for e in self.devices[fd].read():
                    self.queue.put(Event(e.timestamp(),self.devices[fd].name,e.type,e.value))

class RfidReceiver(Receiver):

  start_byte = "\x02"
  rescan_timeout = 1.5
  bau_rate = 9600

  def __init__(self, queue):
    self.serial_device = Config.rfid_serial
    self.ids = {}
    super(RfidReceiver, self).__init__(queue, name="RfidReceiver")
    
  def run(self):
    with serial.Serial(self.serial_device, self.bau_rate) as s:
      while not self.stopper.is_set():
        if s.read() == self.start_byte:
          try:
            d = map(lambda x: int(x,16), re.findall('..',s.read(12)))
            chcksm = d[0]
            for pos in range(1, 5):
              chcksm = chcksm ^ d[pos]
            assert chcksm == d[5], "checksum doesn't match"
            id = ''.join('{:02X}'.format(x) for x in d[:5])
            read_time = time()
            if (id in self.ids and read_time > self.ids[id]) or id not in self.ids:
              self.ids[id] = read_time + self.rescan_timeout
              self.queue.put(Event(read_time,Config.rfid_serial,"id",id))
          except Exception as e:
            self.queue.put(Event(read_time,Config.rfid_serial,"error",e.message))