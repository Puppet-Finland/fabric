# -*- coding: utf-8 -*-
from fabric.api import *

@task
def bootstrap(puppetmaster=''):
    """Bootstrap an Ubuntu 14.04 host on Upcloud"""
    from . import util, puppet

    util.install_sudo()

    fqdn = run('hostname -f')
    hostname = run('hostname -s')

    ipaddress = run("/sbin/ifconfig eth0 | grep 'inet ' | awk -F'[: ]+' '{ print $4 }'")

    hosts_line = "%s %s %s" % (ipaddress, fqdn, hostname)
    sudo("sed -i '/127.0.1.1/d' /etc/hosts")
    with settings(warn_only=True):
        grep = run("grep \"%s\" /etc/hosts" % hosts_line)
    if grep.failed:
        sudo("echo %s >> /etc/hosts" % hosts_line)

    puppet.install(puppetmaster)
    puppet.run_agent()
