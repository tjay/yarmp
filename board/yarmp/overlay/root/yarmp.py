# -*- encoding: utf-8 -*-
from __future__ import print_function
from mpd import MPDClient
client = MPDClient()
client.idletimeout = None
client.connect('/var/run/mpd.socket')
client.clear()
client.add('http://rbb-fritz-live.cast.addradio.de/rbb/fritz/live/mp3/128/stream.mp3')
#client.add('mac.mp3')
client.setvol(18)
client.play(0)


import evdev
import select

devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
devices = {dev.fd: dev for dev in devices}

value = int(client.status()['volume'])
print("Value: {0}".format(value))

done = False
while not done:
  r, w, x = select.select(devices, [], [])
  for fd in r:
    for event in devices[fd].read():
      event = evdev.util.categorize(event)
      if isinstance(event, evdev.events.RelEvent):
        value = int(client.status()['volume']) + event.event.value
        client.setvol(value)
        print("Value: {0}".format(value))
      elif isinstance(event, evdev.events.KeyEvent):
        if event.keycode == "KEY_ENTER" and event.eystate == event.key_up:
          done = True
          break
