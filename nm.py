# -*- coding: utf-8 -*-
from fabric.api import *

@task
def add_static_connection(iface, ip, nm, gw, dns):
    """Add a static, secondary ethernet interface"""
    cmd = "nmcli connection"
    sudo("%s modify %s ipv4.addresses %s/%s" % (cmd, iface, ip, nm))
    sudo("%s modify %s ipv4.gateway %s" % (cmd, iface, gw))
    sudo("%s modify %s ipv4.dns %s" % (cmd, iface, dns))
    sudo("%s modify %s ipv4.method manual" % (cmd, iface))
    sudo("%s modify %s connection.autoconnect yes" % (cmd, iface))
    sudo("%s up %s" % (cmd, iface))

