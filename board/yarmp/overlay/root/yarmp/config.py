

class Config:
    mpd_socket='/var/run/mpd.socket'
    states_dir='/storage'
    rfid_tty = "ttyAMA0"
    controls = { 
        'rotary@9' : "Volume",
        'button@a' : "Volume",
        'rotary@1b' : "Track",
        'button@11' : "Track",
        'ttyAMA0' :  "Track"
    }
    volume_default = 20
    volume_min = 0
    volume_max = 100