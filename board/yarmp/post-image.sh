#!/bin/bash

set -e

BOARD_DIR="$(dirname $0)"
BOARD_NAME="$(basename ${BOARD_DIR})"
GENIMAGE_CFG="${BOARD_DIR}/genimage-${BOARD_NAME}.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

cat << __EOF__ > "${BINARIES_DIR}/rpi-firmware/config.txt"

kernel=zImage
device_tree=bcm2708-rpi-0-w.dtb
disable_overscan=1

gpu_mem_256=100
gpu_mem_512=100
gpu_mem_1024=100

dtparam=i2c=on,i2s=on,spi=on

dtoverlay=pi3-miniuart-bt
dtparam=audio=off
dtoverlay=pi3-disable-bt
dtoverlay=justboom-dac
dtoverlay=rotary-encoder,pin_a=5,pin_b=6,relative_axis=1
dtoverlay=gpio-key,gpio=13,keycode=28,label="ENTER"
gpu_mem=16

hdmi_group=2
hdmi_mode=4
hdmi_force_mode=1
edid_content_type=0
hdmi_blanking=2

arm_freq_min=400

__EOF__



rm -rf "${GENIMAGE_TMP}"

genimage                           \
	--rootpath "${TARGET_DIR}"     \
	--tmppath "${GENIMAGE_TMP}"    \
	--inputpath "${BINARIES_DIR}"  \
	--outputpath "${BINARIES_DIR}" \
	--config "${GENIMAGE_CFG}"

exit $?
