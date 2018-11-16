from .config import Config
import logging as log
from yarmp import Control

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

  @volume.setter
  def volume(self, value):
    if value in self.volume_range:
      self.mpd.setvol(value)

class Track(Control):

  def __init__(self, mpd):
    super(Track, self).__init__(mpd)

  def button_up(self,e):
    log.debug("Track.button_up")

  def button_down(self,e):
    log.debug("Track.button_down")
  
  def rotary(self,e):
    log.debug("Track.rotary")

class Card(Control):

  states = ["rfid"]

  def __init__(self, mpd):
    super(Card, self).__init__(mpd)

  def id(self,e):
    log.debug("Card.id {:s}".format(e.value))
    self.rfid = e.value