#!/bin/bash

set -e

BOARD_DIR="$(dirname $0)"
BOARD_NAME="$(basename ${BOARD_DIR})"
GENIMAGE_CFG="${BOARD_DIR}/genimage-${BOARD_NAME}.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

cat << __EOF__ > "${BINARIES_DIR}/rpi-firmware/config.txt"

kernel=zImage
device_tree=bcm2708-rpi-0-w.dtb
disable_splash=1
boot_delay=0

arm_freq_min=600
gpu_mem=15
start_x=0

dtparam=i2c=on,i2s=on
dtparam=audio=off

dtoverlay=pi3-miniuart-bt
dtoverlay=justboom-dac
dtoverlay=rotary-encoder,pin_a=5,pin_b=6,relative_axis=1
dtoverlay=gpio-key,gpio=13,keycode=28,label="ENTER"


__EOF__

#root=/dev/mmcblk0p2 rootwait console=tty1 console=ttyAMA0,115200 
#root=/dev/mmcblk0p2 rootwait quiet
cat << __EOF__ > "${BINARIES_DIR}/rpi-firmware/cmdline.txt"
root=/dev/mmcblk0p2 rootfstype=squashfs rootwait ro quiet
__EOF__


rm -rf "${GENIMAGE_TMP}"

genimage                           \
	--rootpath "${TARGET_DIR}"     \
	--tmppath "${GENIMAGE_TMP}"    \
	--inputpath "${BINARIES_DIR}"  \
	--outputpath "${BINARIES_DIR}" \
	--config "${GENIMAGE_CFG}"

exit $?
