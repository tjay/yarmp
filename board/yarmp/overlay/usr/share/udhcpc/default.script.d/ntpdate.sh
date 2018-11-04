#!/bin/sh
case "$1" in
	renew|bound)
		ntpdate -sp 1 fritz.box
	;;
esac
