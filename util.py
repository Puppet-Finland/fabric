# -*- coding: utf-8 -*-
from fabric.api import *
from fabric.contrib.files import exists
from datetime import datetime

import random
import re
import os

def getisotime():
    """Convenience method to get current UTC time in yyyymmddhhmm format"""
    ct = datetime.utcnow()
    return ct.strftime("%Y%m%d%H%M")

@task
def set_clock():
    """Set clock on the server using ntpdate"""
    import package
    package.install("ntpdate")
    sudo("ntpdate 0.fi.pool.ntp.org 1.fi.pool.ntp.org 2.fi.pool.ntp.org")

@task
@parallel
def uname():
    """Show kernel version"""
    run("uname -a")

@task
@parallel
def uptime():
    """Show system uptime"""
    with hide("everything"):
        output = run("uptime")
	print env.host + ": "+output

@task
def df():
    """Check available disk space"""
    run("df -h")

@task
def install_sudo():
    """Install sudo, if it's not present"""
    import vars
    vars = vars.Vars()
    with settings(warn_only=True):
        if run("which sudo").failed:
            run(vars.os.package_install_cmd % "sudo")

@task
def put_and_chown(localfile, remotefile, mode="0644", owner="root", group="root", overwrite=True):
    """Put a file to remote server and chown it"""
    # Configure the exists() check and chown differently depending on whether
    # we're copying over a file or a directory.
    with hide("everything"), settings(warn_only=True):
        if isinstance(localfile, basestring) and \
                local("test -d "+localfile).succeeded:
            target = remotefile+"/"+os.path.basename(localfile)
            chown_cmd = "chown -R"
        else:
            target = remotefile
            chown_cmd = "chown"

    # Only copy things that are not already there
    if not exists(target) or overwrite:
        put(localfile, remotefile, use_sudo=True, mode=mode)
        sudo(chown_cmd+" "+owner+":"+group+" "+remotefile)

@task
def add_host_entry(ip, hostname, domain):
    """Add an entry to /etc/hosts"""
    host_line = ip+" "+hostname+"."+domain+" "+hostname

    # Only add entry if it does not exist already. We don't want warnings about
    # grep not finding the entry, as that's to be expected.
    with hide("warnings"), settings(warn_only=True):
        if run("grep \""+host_line+"\" /etc/hosts").failed:
            sudo("echo "+host_line+" >> /etc/hosts")

@task
def add_host_entries(hosts_file=None):
    """Add entries from local hosts file to a remote hosts file"""
    from fabric.contrib.files import append
    if hosts_file:
        try:
            hosts = open(hosts_file)
            for line in hosts:
                append("/etc/hosts", line.rstrip("\n"), use_sudo=True)
        except IOError:
            print "ERROR: defined hosts file is missing!"

@task
def symlink(source, target, use_sudo=True):
    """Make a symbolic link"""

    # Some older versions of Fabric do not have the is_link method 
    try:
        from fabric.contrib.files import is_link
        is_a_link = is_link(target)
    except ImportError:
        with settings(hide("everything"), warn_only=True):
            if run("test -L "+target).failed:
	        is_a_link = False
            else:
                is_a_link = True

    if not is_a_link:
        cmd = "ln -s "+source+" "+target
        if use_sudo:
            sudo(cmd)
        else:
            run(cmd)

def get_hostname():
    """Get hostname part of the current host"""
    return re.split("\.", env.host)[0]

def get_domain():
    """Get domain part of the current host"""
    domain=""
    for item in re.split("\.", env.host)[1:]:
        domain = domain + "." + item
    return domain.lstrip(".")

@task
def set_hostname(hostname):
    """Set hostname"""
    with hide("everything"), settings(warn_only=True):
        if run("grep "+hostname+" /etc/hostname").failed:
            sudo("echo "+hostname+" > /etc/hostname")
        if not hostname == run("hostname"):
            sudo("hostname "+hostname)

@task
def add_to_path(path):
    """Add a new directory to PATH for the default shell"""
    from fabric.contrib.files import append
    import vars
    vars = vars.Vars()
    for file in [ vars.os.default_shell_config, vars.os.default_loginshell_config ]:
        append(file, "export PATH=$PATH:"+path, use_sudo=True)

def get_ip():
    """Get first non-local ip address"""
    with hide("everything"):
        ip_addresses = run('hostname -I').split(' ')
    return ip_addresses[0]

@task
def reboot(really='no'):
    """Reboot the machine. Use reboot:really=YES to actually reboot."""

    if really == 'YES':
        sudo("shutdown -r now")
    else:
        print("Use reboot:really=YES to actually reboot")


def password():
    """Creates a random password string"""
    chars = "abcdefghijklmnopqsrtuvwxyzABCDEFGHIJKLMNOPQSRTUVWXYZ"\
            "123456890!#%&-_*<>+=()"
    return ''.join(random.sample(chars, 15))


def isTrue(s):
    """Convert a Yes into True and everything else into False"""
    return s == "Yes"
