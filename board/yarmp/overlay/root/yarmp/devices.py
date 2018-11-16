import threading, evdev, serial, re, logging as log
from mpd import MPDClient
from mpd.base import ConnectionError
from time import time
from select import select
from config import Config

class Event(object):
    __slots__ = ['time', 'device', 'function', 'value']
    def __init__(self, time, device, function, value):
        self.time = time
        self.device = device
        self.function = function
        self.value = value

    def __str__(self):
        msg = 'event at {:f}, code {!r}, type {!r}, val {!r}'
        return msg.format(self.time, self.device, self.function, self.value)

class YarmpMPD:
    __slots__ = ['mpd']
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
    __slots__ = ['stop_event','queue']
    def __init__(self, queue, name="Receiver"):
        self.stop_event = threading.Event()
        self.queue = queue
        super(Receiver, self).__init__(name=name, target=self.receive)
        self.start()

    def receive(self):
        raise NotImplementedError

    def stop(self):
        self.stop_event.set()
        self.join()

class EvDevReceiver(Receiver):
    __slots__ = ['devices']
    def __init__(self, queue):
        super(EvDevReceiver, self).__init__(queue, name="EvDevReceiver")
    
    @property
    def devices(self):
        try: self.__devices 
        except AttributeError:
            self.__devices = {dev.fd: dev for dev in [evdev.InputDevice(fn) for fn in evdev.list_devices()]}
        return self.__devices

    def receive(self):
        while not self.stop_event.is_set():
            r, _, _ = select(self.devices, [], [], 0.1)
            for fd in r:
                for e in self.devices[fd].read():
                    event = evdev.util.categorize(e)
                    if isinstance(event, evdev.events.RelEvent):
                        self.queue.put(Event(e.timestamp(),self.devices[fd].name,"rotary",e.value))
                    if isinstance(event, evdev.events.KeyEvent):
                        if event.keystate == event.key_up:
                            self.queue.put(Event(e.timestamp(),self.devices[fd].name,"button_up",e.value))
                        if event.keystate == event.key_down:
                            self.queue.put(Event(e.timestamp(),self.devices[fd].name,"button_down",e.value))

class RfidReceiver(Receiver):
  __slots__ = ['devname']

  start_byte = "\x02"
  timeout = 1
  bau_rate = 9600

  def __init__(self, queue, devname):
    self.devname = devname
    super(RfidReceiver, self).__init__(queue, name="RfidReceiver")
    
  def receive(self):
    with serial.Serial("/dev/%s"%self.devname, self.bau_rate, timeout = self.timeout) as s:
      while not self.stop_event.is_set():
        if s.read() == self.start_byte:
          try:
            read_time = time()
            d = map(lambda x: int(x,16), re.findall('..',s.read(12)))
            chcksm = d[0]
            for pos in range(1, 5):
              chcksm = chcksm ^ d[pos]
            assert chcksm == d[5], "checksum doesn't match"
            id = ''.join('{:02X}'.format(x) for x in d[:5])
            self.queue.put(Event(read_time,self.devname,"id",id))
          except Exception as e:
            self.queue.put(Event(read_time,self.devname,"error",e.message))