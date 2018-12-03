#!/bin/sh

#get the gateway - assume that we have there a ntp server
gateway=$(ip r | awk '$1 == "default" {print $3}')

case "$1" in
	renew|bound)
		ntpdate -sp 1 $gateway
	;;
esac
