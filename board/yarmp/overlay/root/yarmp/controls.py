import logging as log, os
from time import time

from .utils import setInterval, LastUpdatedOrderedFIFODict, TrackState, Control
from .config import Config
import ympd as mpd

# pylint: disable=no-member

class Volume(Control):

  states =["volume"]

  volume_range = range(Config.volume_min,Config.volume_max+1)

  def __init__(self):
    self.mute = False
    super(Volume, self).__init__()
    if self.volume in range(0,5) + range(90,100): #dont start silent/loud
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
    return int(mpd.status()['volume'])

  # this will set the last Volume on init
  @volume.setter
  def volume(self, value):
    if value in self.volume_range:
      mpd.setvol(value)

class Track(Control):

  states = ["last_rfids"]

  def __init__(self):
    self.check_play_state()
    self.last_rfids = LastUpdatedOrderedFIFODict(maxsize=10)
    super(Track, self).__init__()

  ### events #############

  def button_up(self,e):
    log.debug("Track.button_up")
    if getattr(self,"button_down_last",e.time) + 2 < e.time:
      log.debug("Track Pos0")
      mpd.seek(0,0)
    else:
      log.debug("Track Pause")
      mpd.pause()

  def button_down(self,e):
    self.button_down_last = e.time
    log.debug("Track.button_down")
  
  def rotary(self,e):
    log.debug("Track.rotary")

  def id(self,e):
    log.debug("Track: card_id {:s}".format(e.value))
    # TODO make *bling*
    current_rfid = self.last_rfids.newest_key()
    log.debug("Track: current Track {!r}".format(current_rfid))
    if current_rfid:
      self.last_rfids[current_rfid] = self.track_state
      if not self.last_rfids.is_newest(e.value):
        if  e.value in self.last_rfids and \
            self.last_rfids[e.value].time + 60 > time():
          # resume old state?
          log.debug("Track: Resume RFID {!r}".format(e.value))
          self.start_playback(e.value,resume=True)
        else:
          log.debug("Track: Start RFID {!r}".format(e.value))
          self.start_playback(e.value)
      else:
        # do nothing
        # TODO Resume / Restart / Unpause
        log.debug("Track: RFID {!r} is currenty playing.".format(e.value))
    else:
      # start play rfid
      log.debug("Track: Start RFID {!r}".format(e.value))
      self.start_playback(e.value)

  #####################################

  @property
  def track_state(self):
    if self.last_rfids:
      current_rfid, _ = self.last_rfids.newest_item()
      return TrackState(current_rfid)
  
  @track_state.setter
  def track_state(self,v):
    self.last_rfids[v.rfid] = v
  
  @setInterval(10)
  def check_play_state(self):
    status = mpd.status()
    log.debug(status)
    if status.get("state",None) == "play":
      # save state only on play
      self.save_state(atcall=True)
  
  def start_playback(self,rfid, resume=False):
    rfids = {"08008BDC09" : "http://rbb-fritz-live.cast.addradio.de/rbb/fritz/live/mp3/128/stream.mp3"}
    if rfid in rfids:
      mpd.clear()
      mpd.add(rfids[rfid])
      mpd.play(0)
      self.track_state = TrackState(rfid)
    else:
      log.debug("Track: RFID {!r} unknown.".format(rfid))
