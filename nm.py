# -*- coding: utf-8 -*-
from fabric.api import *

@task
def add_static_connection(ifname, ip, nm, gw, dns, never_default="TRUE"):
    """Add a static, secondary ethernet interface"""
    cmd = "nmcli connection"
    sudo("%s modify %s ipv4.addresses %s/%s" % (cmd, ifname, ip, nm))
    sudo("%s modify %s ipv4.gateway %s" % (cmd, ifname, gw))
    sudo("%s modify %s ipv4.dns %s" % (cmd, ifname, dns))
    sudo("%s modify %s ipv4.method manual" % (cmd, ifname))
    sudo("%s modify %s ipv4.never-default %s" % (cmd, ifname, never_default))
    sudo("%s modify %s connection.autoconnect yes" % (cmd, ifname))
    sudo("%s up %s" % (cmd, ifname))

@task
def add_static_bridge(bridge_ifname, ip, nm, gw, dns, never_default="TRUE", slave_ifnames=[]):
    """Add a bridge interface with static IP and attach interfaces to it"""
    cmd = "nmcli connection"
    bridge_con_name = "bridge-%s" % bridge_ifname
    sudo("%s add type bridge con-name %s ifname %s" % (cmd, bridge_con_name, bridge_ifname))
    sudo("%s modify %s bridge.stp no" % (cmd, bridge_con_name))
    sudo("%s modify %s ipv4.addresses %s/%s" % (cmd, bridge_con_name, ip, nm))
    sudo("%s modify %s ipv4.gateway %s" % (cmd, bridge_con_name, gw))
    sudo("%s modify %s ipv4.dns %s" % (cmd, bridge_con_name, dns))
    sudo("%s modify %s ipv4.method manual" % (cmd, bridge_con_name))
    sudo("%s modify %s ipv4.never-default %s" % (cmd, bridge_con_name, never_default))
    sudo("%s modify %s connection.autoconnect yes" % (cmd, bridge_con_name))

    # Add slave interfaces to the bridge
    for slave_ifname in slave_ifnames:
        slave_con_name = "bridge-slave-%s" % (slave_ifname)
        sudo("%s add type bridge-slave con-name %s ifname %s master %s" % (cmd, slave_con_name, slave_ifname, bridge_con_name))

    sudo("%s up %s" % (cmd, bridge_con_name))

