# -*- coding: utf-8 -*-
from fabric.api import *

from datetime import datetime

def getisotime():
    """Convenience method to get current UTC time in yyyymmddhhmm format"""
    ct = datetime.utcnow()
    return ct.strftime("%Y%m%d%H%M")

@task
def uname():
    """Show kernel version"""
    run("uname -a")

@task
def df():
    """Check available disk space"""
    run("df -h")

@task
def install_sudo():
    """Install sudo, if it's not present"""
    vars = Vars()
    with settings(warn_only=True):
        if run("which sudo").failed:
            run(vars.os.package_install_cmd % "sudo")

@task
def add_host_entry(ip, hostname, domain):
    """Add an entry to /etc/hosts"""
    host_line = ip+" "+hostname+"."+domain+" "+hostname

    # Only add entry if it does not exist already. We don't want warnings about
    # grep not finding the entry, as that's to be expected.
    with hide("warnings"):
        if run("grep \""+host_line+"\" /etc/hosts").failed:
            sudo("echo "+host_line+" >> /etc/hosts")
