#!/bin/sh

case "$1" in
	renew|bound)
		#get the gateway - assume that we have there a ntp server
		ntpdate -sp 1 $(ip r | awk '$1 == "default" {print $3}')
	;;
esac
