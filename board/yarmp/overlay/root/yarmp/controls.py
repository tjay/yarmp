import logging as log, os, threading, re, subprocess as sub
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
    self.last_volume_fx = None
    super(Volume, self).__init__()
    if self.volume in range(Config.volume_min,Config.volume_min+10) + range(Config.volume_max-10,Config.volume_max): #dont start silent/loud
      self.volume = Config.volume_default
  
  def button_up(self,e):
    if getattr(self,"button_down_last",e.time) + 0.1 < e.time:
      if self.volume > 0: 
        self.mute = self.volume # save last state
        self.volume = 0
      else: # resume last state
        self.volume = self.mute if self.mute else Config.volume_default
        self.mute = False

  def button_down(self,e):
    self.button_down_last = e.time
    log.debug("Volume.button_down")
  
  def rotary(self,e):
    if not self.mute:
      self.volume += e.value

  def volume_fx(self,volume):
    value=volume/10
    if value <> self.last_volume_fx:
      with open(os.devnull, 'w') as dn:
        sub.Popen(["aplay","{!s}/fx/{!s}.wav".format(Config.base_dir,value)],stdout=dn,stderr=dn)
    self.last_volume_fx = value

  @property
  def volume(self):
    return int(mpd.status()['volume'])

  # this will set the last Volume on init
  @volume.setter
  def volume(self, value):
    if value in self.volume_range:
      self.volume_fx(value)
      mpd.setvol(value)

class Track(Control):

  states = ["last_rfids"]

  def __init__(self):
    self.check_play_state()
    self.last_rfids = LastUpdatedOrderedFIFODict(maxsize=10)
    self.rcl={"skip_time":time()-5,"timer":None, 1L:[], -1L:[]} # rotary positive / negative time list
    super(Track, self).__init__()

  ### events #############

  def button_up(self,e):
    log.debug("Track.button_up")
    if getattr(self,"button_down_last",e.time) + 1 < e.time:
      log.debug("Track Seek to Playlist(0,0)")
      mpd.seek(0,0)
      mpd.play(0)
    elif(getattr(self,"button_down_last",e.time) + 0.1 < e.time):
      log.debug("Track Toggle Pause")
      mpd.pause()

  def button_down(self,e):
    self.button_down_last = e.time
    log.debug("Track.button_down")
  
  def rotary(self,e):

    try:
      self.rcl["timer"].cancel()
      self.rcl["timer"].join()
    except:pass
    
    self.rcl[e.value*-1] = []
    self.rcl[e.value].append(e.time)
    avg_tick = 99
    clear_time = 0.2

    if len(self.rcl[e.value]) > 1:
      deltas = [b-a for a, b in zip(self.rcl[e.value][:-1], self.rcl[e.value][1:])]
      avg_tick = sum(deltas)/len(deltas)
    
    # skip track on fast roll
    if e.time - self.rcl["skip_time"] > 0.5 and len(self.rcl[e.value]) > 4 and avg_tick < 0.09:
      self.skip(e.value) # skip +-
      self.rcl["skip_time"] = e.time
      clear_time = 1
    # seek track on slow roll
    elif e.time - self.rcl["skip_time"] > 2 and  0.10 <= avg_tick <= 1:  # seek +-
      self.seek(e.value)
      clear_time = 0.5

    # clear tick-list if we make a pause
    self.rcl["timer"] = threading.Timer(clear_time, self.clear_rcl, args=(e.value,))
    self.rcl["timer"].start()


  def id(self,e):
    log.debug("Track: card_id {:s}".format(e.value))
    # TODO make *bling*
    current_rfid = self.last_rfids.newest_key()
    log.debug("Track: current RFID {!r}".format(current_rfid))
    if current_rfid:
      self.last_rfids[current_rfid] = self.track_state
      if not self.last_rfids.is_newest(e.value):
        if  e.value in self.last_rfids and \
            self.last_rfids[e.value].timestamp + 120 > time():
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

  def clear_rcl(self,value):
    del self.rcl[value][:]

  def seek(self, value):
    log.debug("Track: seek {!r}".format(value))
    status = self.track_state
    pos = float(status.elapsed)+5*value
    if getattr(status,"duration",None):
      duration = float(status.duration)
      if 0 < pos < duration:
        mpd.seekid(status.songid,pos)
      elif int(status.playlistlength)>1:
        self.skip(value)
    elif int(status.playlistlength)>1:
      self.skip(value)

  def skip(self,value):
    log.debug("Track: skip {!r}".format(value))
    if int(self.track_state.playlistlength)>1:
      #sound
      if value > 0: mpd.next()
      else: mpd.previous()

  @property
  def track_state(self):
    rfid = self.last_rfids.newest_key()
    if rfid:
      self.last_rfids[rfid] = TrackState(rfid)
    return TrackState(rfid)
  
  @setInterval(10)
  def check_play_state(self):
    status = self.track_state
    if status.state == "play" and getattr(status,"duration",None):
      # save state only on play
      self.save_state(atcall=True)
  
  def start_playback(self,rfid, resume=False):
    playlist = None
    for pl in mpd.listplaylists():
      match = re.search("^RFID-{!s}".format(rfid),pl)
      if match:
        playlist = match.group()
        break
    if playlist:
      mpd.clear()
      mpd.load(playlist)
      if resume:
        track_state = self.last_rfids[rfid]
        if getattr(track_state,"duration",None):
          mpd.seekid(track_state.songid,float(track_state.elapsed)-5)
        else:
          mpd.seekid(track_state.songid,0)
        mpd.play(track_state.songid)
      else:
        mpd.play(0)
    else:
      #sound
      log.debug("Track: RFID {!r} unknown.".format(rfid))