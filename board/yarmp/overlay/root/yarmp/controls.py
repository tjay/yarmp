from .config import Config
import logging as log, os
from yarmp import Control, TrackState
from time import time
from collections import OrderedDict

class LastUpdatedOrderedFIFODict(OrderedDict):
  def __init__(self, maxsize = 10):
    self.maxsize = maxsize
    super(LastUpdatedOrderedFIFODict, self).__init__()

  def oldest_item(self):
    return next(iter(self.items()))

  def newest_item(self):
    return next(reversed(self.items()))
  
  def __setitem__(self, key, value):
    if key in self:
      del self[key]
    while len(self) > self.maxsize:
      OrderedDict.popitem(self, last=False)
    OrderedDict.__setitem__(self, key, value)


class Volume(Control):

  states =["volume"]

  volume_range = range(Config.volume_min,Config.volume_max+1)

  def __init__(self, mpd):
    self.mute = False
    super(Volume, self).__init__(mpd)
    if self.volume == 0: #dont start silent
      self.volume = Config.volume_default
  
  def button_up(self,e):
    if not self.mute: # save last state
      self.mute = self.volume
      self.volume = 0
    else: # resume last state
      self.volume = self.mute
      self.mute = False

  def button_down(self,e):
    pass
  
  def rotary(self,e):
    if not self.mute:
      self.volume += e.value

  @property
  def volume(self):
    return int(self.mpd.status()['volume'])

  # this will set the last Volume on init
  @volume.setter
  def volume(self, value):
    if value in self.volume_range:
      self.mpd.setvol(value)

class Track(Control):

  states = ["track_state"]

  def __init__(self, mpd):
    self.last_rfids = LastUpdatedOrderedFIFODict(maxsize=10)
    super(Track, self).__init__(mpd, save_loop_time=10)

  ### events #############

  def button_up(self,e):
    log.debug("Track.button_up")
    if getattr(self,"button_down_last",e.time) + 3 < e.time:
      log.debug("Track Pos0")
      #self.mpd.seek(0,0)
    else:
      log.debug("Track Pause")
      #self.mpd.pause()

  def button_down(self,e):
    self.button_down_last = e.time
    log.debug("Track.button_down")
  
  def rotary(self,e):
    log.debug("Track.rotary")

  def id(self,e):
    log.debug("Card.id {:s}".format(e.value))
    current_rfid, _ = self.last_rfids.newest_item()
    if current_rfid <> e.value:
      # TODO make *bling*
      if self.track_state:
        self.last_rfids[current_rfid] = self.track_state
      # resume old state?
      if e.value in self.last_rfids:
        # TODO: config resume Time
        if self.last_rfids[e.value]["time"] + 60 > time():
          # resume
          log.debug("Track: Resume RFID {!r}".format(e.value))
      else:
        # start play rfid
        log.debug("Track: Start RFID {!r}".format(e.value))

  #####################################

  @property
  def track_state(self):
    current_rfid, _ = self.last_rfids.newest_item()
    return TrackState(current_rfid,self.mpd)
  
  # this will set the last Track on init
  @track_state.setter
  def track_state(self,v):
    self.last_rfids[v.rfid] = v
    if v.play:
      log.debug("Track: Resume after Boot {!r}".format(v.rfid))
    



