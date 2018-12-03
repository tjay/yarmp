class Config(object):
    
    mpd_socket='/var/run/mpd.socket'
    base_dir='/storage'
    rfid_tty = "/dev/ttyAMA0"

    playlist_options = '/storage/playlists.json'

    # Hardware to Class Mapping
    controls = { 
        'rotary@9' : "Volume",
        'button@a' : "Volume",
        'rotary@1b' : "Track",
        'button@11' : "Track", 
        'ttyAMA0' :  "Track", # RFID Reader on Serial
        'mpd.socket' : "Mpd" # MPD Channel messages to YARMP
    }

    volume_default = 40
    volume_min = 0
    volume_max = 100