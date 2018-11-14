from .config import Config

class Volume(object):
  def __init__(self, event, mpd):
    self.value_range = range(Config.volume_min,Config.volume_max+1)

class Track(object):
  def __init__(self, event, mpd):
    pass