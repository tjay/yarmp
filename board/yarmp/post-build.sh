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
  sed -i 's/{SSID}/'$(grep -oP '(?<=^BR2_TARGET_WLAN_SSID=").+(?="$)' ${BR2_CONFIG})'/' ${TARGET_DIR}/etc/wpa_supplicant.conf
  sed -i 's/{PSK}/'$(grep -oP '(?<=^BR2_TARGET_WLAN_PSK=").+(?="$)' ${BR2_CONFIG})'/' ${TARGET_DIR}/etc/wpa_supplicant.conf
fi

rm -f ${TARGET_DIR}/etc/init.d/S20urandom
rm -f ${TARGET_DIR}/etc/init.d/S95mpd


[ -h "${TARGET_DIR}/etc/dropbear" ] && rm -f ${TARGET_DIR}/etc/dropbear
if [ ! -f "${TARGET_DIR}/etc/dropbear/dropbear_rsa_host_key" ]; then
  mkdir -p ${TARGET_DIR}/etc/dropbear
  dropbearkey -t rsa -f ${TARGET_DIR}/etc/dropbear/dropbear_rsa_host_key 
  dropbearkey -t dss -f ${TARGET_DIR}/etc/dropbear/dropbear_dss_host_key
  dropbearkey -t ecdsa -f ${TARGET_DIR}/etc/dropbear/dropbear_ecdsa_host_key
fi
