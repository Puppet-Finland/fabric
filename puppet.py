from fabric.api import *
from fabric.contrib.files import exists
import sys
from StringIO import StringIO

try:
    import yaml
except ImportError:
    print "NOTICE: setup_master4 task requires PyYaml package (python-yaml in Debian)"

### Generic puppet tasks
@task
def run_agent(noop="True", onlychanges="True", environment=None):
    """Run puppet in normal or no-operation mode"""
    with settings(hide("status"), hide("running")):
        basecommand = "puppet agent --onetime --no-daemonize --verbose --waitforcert 30 --color=false --no-splay"
        if environment:
            basecommand = basecommand + " --environment "+environment
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
def show_changes(environment=None):
    """Run puppet on no-operation mode and show changes to be made"""
    cmd = "puppet agent --test --noop --waitforcert 30"

    if environment:
        cmd = cmd + " --environment "+environment

    sudo(cmd)

### Puppet 5 tasks
def install_puppetlabs_release_package(proxy_url=None):
    """Install Puppetlabs apt repo release package"""
    import package, vars
    vars = vars.Vars()
    os = vars.lsbdistcodename

    if vars.osfamily == "Debian":
        package.download_and_install("https://apt.puppetlabs.com/puppet-release-"+os+".deb", "puppet-release", proxy_url=proxy_url)
    elif vars.osfamily == "RedHat":
        if vars.operatingsystem in ["RedHat", "CentOS", "Scientific"]:
            oscode = "el"
        elif vars.operatingsystem == "Fedora":
            oscode = "fedora"
        url="https://yum.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+oscode+"-"+vars.operatingsystemmajrelease+".noarch.rpm"
        package.download_and_install(url, "puppetlabs-release-pc"+pc, proxy_url=proxy_url)

@task
def setup_agent5(hostname=None, domain=None, agent_conf="files/puppet-agent5.conf", puppetserver=None, proxy_url=None, hosts_file=None):
    """Setup Puppet 5 agent"""
    import package, util, config

    if not hostname:
        hostname = util.get_hostname()
    if not domain:
        domain = util.get_domain()

    install_puppetlabs_release_package(proxy_url=proxy_url)
    package.install("puppet-agent")

    # Use puppetserver value from setting.ini file if none is given on the
    # command-line. If that fails use the default.
    if not puppetserver:
        try:    puppetserver = config.get("puppet", "puppetserver")
        except: puppetserver = None

    # Add a customized puppet.conf
    util.put_and_chown(agent_conf, "/etc/puppetlabs/puppet/puppet.conf")
    if puppetserver: server = puppetserver
    else:            server = "puppet.%s" % domain
    sudo("puppet config set --section agent server %s" % server)

    util.set_hostname(hostname + "." + domain)
    util.add_host_entry(util.get_ip(), hostname, domain)

    # Optionally add hosts from a separate file. This is useful when the IP of
    # the puppetmaster as seen from the Puppet agent node does not match its
    # name in DNS.
    util.add_host_entries(hosts_file)
    util.add_to_path("/opt/puppetlabs/bin")
    run_agent(noop="False", onlychanges="False")

@task
def run_agent5(noop="True", onlychanges="True", environment=None):
    """Run puppet in normal or no-operation mode"""
    with settings(hide("status"), hide("running")):
        basecommand = "puppet agent --onetime --no-daemonize --verbose --waitforcert 30 --color=false --no-splay"
        if environment:
            basecommand = basecommand + " --environment "+environment
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


