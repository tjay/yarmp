from mpd import MPDClient
client = MPDClient()
client.idletimeout = None
client.connect('/var/run/mpd.socket')
client.clear()
#client.add('http://rbb-fritz-live.cast.addradio.de/rbb/fritz/live/mp3/128/stream.mp3')
client.add('mac.mp3')
client.setvol(18)
client.play(0)
