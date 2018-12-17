#!/bin/sh

chown :555 /dev/input/event* /dev/ttyAMA0 /dev/snd/* /run
chmod g+rw /dev/input/event* /dev/ttyAMA0 /dev/snd/* /run

if [ ! -b  /dev/mmcblk0p3 ]; then
        #parted -a optimal /dev/mmcblk0 mkpart primary 100MB 100%
        parted -a optimal /dev/mmcblk0 mkpart primary 100MB 200MB
        mkfs.ext4 -q -E lazy_itable_init=0,lazy_journal_init=0,root_owner=444:555  /dev/mmcblk0p3
        mount -o rw,noatime,noexec /dev/mmcblk0p3 /storage
        sudo -u yarmp cp -r /storage-template/* /storage
else
        mount -o rw,noatime,noexec /dev/mmcblk0p3 /storage
fi

sudo -u yarmp touch /tmp/mpd.database /tmp/mpd.state
sudo -u yarmp mpd
ympd -u yarmp -h /var/run/mpd.socket &

/sbin/haveged &
