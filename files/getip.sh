#!/bin/sh
#
# This returns the first IP address bound to a given FQDN and strips away the
# linefeed. The /etc/hosts file is consulted first, and if no results are
# returned then a DNS request is made. The use of the hosts-file allows
# overriding the IP-address of a given host in cases where results from DNS are
# incorrect for Puppet use. The primary purpose of this script is to return
# IP-addresses for Puppet clients that are less often wrong than the built-in
# $ipaddress fact.
#
# This script can return both IPv4 and IPv6 IP-addresses.
#
# Usage:
#
# getip.sh -4|-6 hostname

# We would prefer to use "ahostsv6" rather than "hosts" as the IPv6 database for
# getent, but older versions of getent don't seem to support it properly.
V4DB="ahostsv4"
V6DB="hosts"

# The following two sections are required to prevent the fqdn of the
# puppetmaster from resolving to a localhost address that might be defined in
# /etc/hosts.
if [ "$2" = "puppet.openvpn.in" ] && [ "$1" = "-4" ]; then
    V4RESULT=`dig +short $2 A|head -n 1|tr -d "\n"`
    echo -n "$V4RESULT"
    exit 0

elif [ "$2" = "puppet.openvpn.in" ] && [ "$1" = "-6" ]; then
    V6RESULT=`dig +short $2 AAAA|head -n 1|tr -d "\n"`
    echo -n "$V6RESULT"
    exit 0

# These two section are for nodes other than the Puppetmaster
elif [ "$2" != "puppet.openvpn.in" ] && [ "$1" = "-4" ]; then

    V4RESULT=`getent $V4DB $2|head -n 1|cut -d " " -f 1|tr -d "\n"`
    echo -n "$V4RESULT"
    exit 0

elif [ "$2" != "puppet.openvpn.in" ] && [ "$1" = "-6" ]; then

    V4RESULT=`getent $V4DB $2|head -n 1|cut -d " " -f 1|tr -d "\n"`
    V6RESULT=`getent $V6DB $2|head -n 1|cut -d " " -f 1|tr -d "\n"`

    # IPv6-only lookups ("ahostsv6") do not work on older versions of getent, so 
    # without this test there's a risk that an IPv4 address is returned as an 
    # IPv6 address.
    if [ "$V4RESULT" = "$V6RESULT" ]; then
        echo -n ""
    else
        echo -n "$V6RESULT"
    fi

    exit 0
fi
