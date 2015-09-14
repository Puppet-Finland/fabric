from fabric.api import *
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
    import package, vars
    vars = vars.Vars()
    os = vars.lsbdistcodename

    if vars.osfamily == "Debian":
        package.download_and_install("https://apt.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+os+".deb", "puppetlabs-release-pc"+pc)
    elif vars.osfamily == "RedHat":
        if vars.operatingsystem in ["RedHat", "CentOS", "Scientific"]:
            oscode = "el"
        elif vars.operatingsystem == "Fedora":
            oscode = "fedora"
        url="https://yum.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+oscode+"-"+vars.operatingsystemmajrelease+".noarch.rpm"
        package.download_and_install(url, "puppetlabs-release-pc"+pc)

@task
def setup_agent4(pc="1"):
    """Setup Puppet 4 agent"""
    import package
    install_puppetlabs_release_package(pc)
    package.install("puppet-agent")

@task
def setup_server4(domain, pc="1", hostname="puppet", master_conf="files/master.conf", forge_modules=["puppetlabs/stdlib", "puppetlabs/concat", "puppetlabs/firewall", "puppetlabs/apt"]):
    """Setup Puppet 4 server"""
    import package, util, git

    try:
        open(master_conf)
    except IOError:
        print "ERROR: puppetmaster config ("+master_conf+") not found!"
        sys.exit(1)

    install_puppetlabs_release_package(pc)
    package.install("puppetserver")
    copy_puppet_conf4(master_conf)
    util.add_to_path("/opt/puppetlabs/bin")
    util.set_hostname(hostname + "." + domain)
    # "facter fqdn" return a silly name on EC2 without this
    util.add_host_entry("127.0.1.1", hostname, domain)

    for module in forge_modules:
        add_forge_module(module)

    git.install()

def copy_puppet_conf4(localfile="files/agent.conf"):
    """Copy over puppet.conf"""
    remote_puppet_conf = "/etc/puppetlabs/puppet/puppet.conf"
    put(localfile, remote_puppet_conf, use_sudo=True, mode="0644")
    sudo("chown root:root "+remote_puppet_conf)

@task
def add_forge_module(name):
    """Add a forge module"""
    # puppet module list shows dashes instead of slashes due to historic reasons
    listname = name.replace("/", "-")
    with hide("everything"), settings(warn_only=True):
        if sudo("puppet module list --color=false 2> /dev/null|grep "+listname).failed:
            sudo("puppet module install "+name)
