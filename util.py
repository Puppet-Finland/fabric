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
def ntp_status():
    """Show ntp status"""
    run("/etc/init.d/ntp status")

@task
def install_sudo():
    """Install sudo, if it's not present"""

    # Test if sudo is installed
    with settings(warn_only=True):
        sudo_exists = run("which sudo")
    if sudo_exists.failed:
        run("apt-get install sudo")
