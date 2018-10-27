#!/bin/sh

set -u
set -e

# Add a console on tty1
#if [ -e ${TARGET_DIR}/etc/inittab ]; then
#    grep -qE '^tty1::' ${TARGET_DIR}/etc/inittab || \
#	sed -i '/GENERIC_SERIAL/a\
#tty1::respawn:/sbin/getty -L  tty1 0 vt100 # HDMI console' ${TARGET_DIR}/etc/inittab
#fi

if [ -e ${TARGET_DIR}/etc/wpa_supplicant.conf ]; then
  sed -i 's/{SSID}/${BR2_TARGET_WLAN_SSID}/' ${TARGET_DIR}/etc/wpa_supplicant.conf
  sed -i 's/{PSK}/${BR2_TARGET_WLAN_PSK}/' ${TARGET_DIR}/etc/wpa_supplicant.conf
fi
