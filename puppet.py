from fabric.api import *
from vars import *
import re
import sys

### Generic puppet tasks
@task
def run_agent(noop="True", onlychanges="True"):
    """Run puppet in normal or no-operation mode"""
    with settings(hide("status"), hide("running")):
        basecommand = "puppet agent --onetime --no-daemonize --verbose --waitforcert 30 --color=false"
        if onlychanges.lower() == "true":
            filtercommand = "| grep -v \"Info:\""
            env.parallel=True
        else:
            filtercommand = ""
            env.parallel=False

        if noop.lower() == "true":
            sudo(basecommand + " --noop" + filtercommand)
        else:
            sudo(basecommand + filtercommand)

@task
@serial
def show_changes():
    """Run puppet on no-operation mode and show changes to be made"""
    sudo("puppet agent --test --noop --waitforcert 30")


### Puppet 3 tasks
@task
def install(master=None, environment='production'):
    """Install puppet agent. Give master's name as the first parameter. If master is not given, env.puppet_master is used."""
    if not master:
        master = getattr(env, 'puppet_master', 'puppet')

    # Get Puppetlabs repo
    os = run('lsb_release -cs')
    puppetlabs_file = "puppetlabs-release-%s.deb" % os
    sudo("wget https://apt.puppetlabs.com/%s -O /root/%s" % (puppetlabs_file, puppetlabs_file))
    sudo("dpkg -i /root/%s" % puppetlabs_file)

    # Install Puppet and Facter
    sudo("apt-get update")
    sudo("apt-get -y install puppet facter")

    sudo("puppet config --section agent set pluginsync true")
    sudo("puppet config --section agent set server %s" % master)
    sudo("puppet config --section agent set environment %s" % environment)

### Puppet 4 tasks
def install_puppetlabs_release_package(pc):
    """Install Puppetlabs apt repo release package"""
    import package
    vars = Vars()
    os = vars.lsbdistcodename
    package.download_and_install("https://apt.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+os+".deb", "puppetlabs-release-pc"+pc)

@task
def setup_agent4(pc="1"):
    """Setup Puppet 4 agent"""
    import package
    install_puppetlabs_release_package(pc)
    package.install("puppet-agent")

@task
def setup_server4(pc="1"):
    """Setup Puppet 4 server"""
    import package
    install_puppetlabs_release_package(pc)
    package.install("puppetserver")

def copy_puppet_conf4():
    """Copy over puppet.conf"""
    remote_puppet_conf = "/etc/puppetlabs/puppet/puppet.conf"
    put("files/puppet.conf", remote_puppet_conf, use_sudo=True, mode="0644")
    sudo("chown root:root "+remote_puppet_conf)
