import logging as log, os, threading, re, json
from time import time

from .utils import setInterval, LastUpdatedOrderedFIFODict, TrackState, Control, States, fx
from .config import Config
import ympd as mpd

# pylint: disable=no-member

class Volume(Control,States):

  states =["volume"]

  volume_range = range(Config.volume_min,Config.volume_max+1)

  def __init__(self):
    self.mute = False
    self.last_volume_fx = None
    super(Volume, self).__init__()
    if self.volume in range(Config.volume_min,Config.volume_min+10) + range(Config.volume_max-10,Config.volume_max+5): #dont start silent/loud
      self.volume = Config.volume_default
      self.save_state(atcall=True)
  
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
      fx(value)
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

class Track(Control,States):

  states = ["last_playlists"]

  def __init__(self):
    self.check_play_state()
    self.last_playlists = LastUpdatedOrderedFIFODict(maxsize=50)
    self.rcl={"skip_time":time()-5,"timer":None, 1L:[], -1L:[]} # rotary positive / negative time list
    super(Track, self).__init__()

  ### events #############

  def button_up(self,e):
    log.debug("Track.button_up")
    if getattr(self,"button_down_last",e.time) + 1 < e.time:
      log.debug("Track Seek to Playlist(0,0)")
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
    log.debug("Track: RFID {:s}".format(e.value))
    playlist_options = mpd.load_playlist_options(e.value)
    playlist, name = mpd.find_playlist(e.value)

    mpd.sendmessage("ympd","RFID_OPTIONS:"+json.dumps({"rfid":e.value,"name":name,"options":playlist_options}))
    current_playlist = self.last_playlists.newest_key()
    log.debug("Track: current Playlist {!r}".format(current_playlist))
    if current_playlist:
      self.last_playlists[current_playlist] = self.track_state
      if not self.last_playlists.is_newest(playlist):
        if playlist in self.last_playlists and \
            (self.last_playlists[playlist].timestamp + 120 > time()
            or playlist_options.get("resume")):
          log.debug("Track: Resume Playlist {!r}".format(playlist))
          self.start_playback(playlist,playlist_options,resume=True)
        else:
          log.debug("Track: Start Playlist {!r}".format(playlist))
          self.start_playback(playlist,playlist_options)
      else:
        log.debug("Track: Playlist {!r} is currenty loaded.".format(playlist))
        track_state = self.track_state
        if track_state.state in ["pause","stop"]:
          self.start_playback(playlist,playlist_options,resume=True)
    elif playlist:
      # start play playlist
      log.debug("Track: Start Playlist {!r}".format(playlist))
      self.start_playback(playlist,playlist_options)
    else:
      fx("error")
      log.debug("Track: RFID {!r} unknown.".format(e.value))

  #####################################

  def clear_rcl(self,value):
    del self.rcl[value][:]

  def seek(self, value):
    log.debug("Track: seek {!r}".format(value))
    status = self.track_state
    if status.state != "play":
      return
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
    status = self.track_state
    if status.state != "play": return
    if int(status.playlistlength)>1:
      fx("next")
      if value > 0: mpd.next()
      else: mpd.previous()

  @property
  def track_state(self):
    playlist = self.last_playlists.newest_key()
    if playlist:
      self.last_playlists[playlist] = TrackState(playlist)
    return TrackState(playlist)
  
  @setInterval(10)
  def check_play_state(self):
    status = self.track_state
    if status.state == "play" and getattr(status,"duration",None):
      # save state only on play
      self.save_state(atcall=True)
  
  def start_playback(self,playlist,playlist_options,resume=False):
    mpd.load_playlist(playlist,source=playlist_options.get("url"))
    if resume:
      track_state = self.last_playlists[playlist]
      if getattr(track_state,"song",None):
        if getattr(track_state,"duration",None):
          mpd.seek(track_state.song,float(track_state.elapsed)-5)
        else:
          mpd.play(track_state.song)
      else:
        mpd.play(0)
    else:
      mpd.play(0)
    # set saved playback options
    for mode in ["single","repeat","random","crossfade"]:
      getattr(mpd,mode)( 1 if playlist_options.get(mode) else 0)
    fx("rfid")
    self.last_playlists[playlist] = TrackState(playlist)

class Mpd(Control):

  def __init__(self):
    super(Mpd, self).__init__()

  def set_rfid_options(self,e):
    if isinstance(e.value,dict) :
      rfid = e.value.get("rfid",None)
      options = e.value.get("options",None)
      if rfid and isinstance(options,dict):
        mpd.save_playlist_options(rfid,options)