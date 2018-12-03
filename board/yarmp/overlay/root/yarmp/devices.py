import threading, evdev, serial, re, logging as log, json, urllib, os
from time import time
from select import select

from .config import Config
from .utils import Event
import ympd as mpd

class Receiver(threading.Thread):
    def __init__(self, queue, name="Receiver"):
        self.stop_event = threading.Event()
        self.parent = threading.current_thread()
        self.queue = queue
        super(Receiver, self).__init__(name=name, target=self.receive)
        self.start()

    def receive(self):
        raise NotImplementedError

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
        while not self.stop_event.is_set():
            r, _, _ = select(self.devices, [], [], 0.1)
            if not self.parent.is_alive(): self.stop_event.set()
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

class MpdReceiver(Receiver):
    channel = "yarmp"
    devname = os.path.basename(Config.mpd_socket)

    def __init__(self, queue):
        super(MpdReceiver, self).__init__(queue, name="MpdReceiver")
    
    def receive(self):
        # pylint: disable=no-member
        while not self.stop_event.wait(4):
            if not self.parent.is_alive():
                self.stop_event.set()
            if not self.channel in mpd.subscribed_channels:
                mpd.subscribe(self.channel)
                mpd.subscribed_channels.append(self.channel)
            for msg in mpd.readmessages():
                try:
                    read_time = time()
                    if msg.get("channel") == self.channel:
                        j =json.loads(urllib.unquote(msg["message"]))
                        self.queue.put(Event(read_time,self.devname,j["action"],j["value"]))
                except Exception as e:
                    self.queue.put(Event(read_time,self.devname,"error",e.message))

class RfidReceiver(Receiver):

  start_byte = "\x02"
  timeout = 1
  bau_rate = 9600
  re_read = 2.0
  devname = Config.rfid_tty

  def __init__(self, queue):
    self.last = {"id":0}
    super(RfidReceiver, self).__init__(queue, name="RfidReceiver")
    
  def receive(self):
    with serial.Serial(self.devname, self.bau_rate, timeout = self.timeout) as s:
      while not self.stop_event.is_set():
        if not self.parent.is_alive(): self.stop_event.set()
        if s.read() == self.start_byte:
          try:
            read_time = time()
            d = map(lambda x: int(x,16), re.findall('..',s.read(12)))
            chcksm = d[0]
            for pos in range(1, 5):
              chcksm = chcksm ^ d[pos]
            assert chcksm == d[5], "checksum doesn't match"
            id = ''.join('{:02X}'.format(x) for x in d[:5])
            if self.last.get(id,0) + self.re_read < read_time:
                self.queue.put(Event(read_time,os.path.basename(self.devname),"id",id))
                self.last[id] = read_time
          except Exception as e:
            self.queue.put(Event(read_time,os.path.basename(self.devname),"error",e.message))