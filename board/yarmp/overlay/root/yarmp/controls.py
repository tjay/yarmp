from .config import Config
import logging as log
from yarmp import Control

class Volume(Control):

  def __init__(self, mpd):
    self.value_range = range(Config.volume_min,Config.volume_max+1)
    super(Volume, self).__init__(mpd)

  def button_up(self,e):
    log.debug("Volume.button_up")

  def button_down(self,e):
    log.debug("Volume.button_down")
  
  def rotary(self,e):
    log.debug("Volume.rotary")

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

  def __init__(self, mpd):
    super(Card, self).__init__(mpd)

  def id(self,e):
    log.debug("Card.id")
