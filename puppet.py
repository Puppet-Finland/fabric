from fabric.api import *
import sys

### Generic puppet tasks
@task
def run_agent(noop="True", onlychanges="True"):
    """Run puppet in normal or no-operation mode"""
    with settings(hide("status"), hide("running")):
        basecommand = "puppet agent --onetime --no-daemonize --verbose --waitforcert 30 --color=false --no-splay"
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
def setup_agent4(hostname=None, domain=None, pc="1", agent_conf="files/puppet-agent.conf"):
    """Setup Puppet 4 agent"""
    import package, util

    if not hostname:
        hostname = util.get_hostname()
    if not domain:
        domain = util.get_domain()

    install_puppetlabs_release_package(pc)
    package.install("puppet-agent")
    util.put_and_chown(agent_conf, "/etc/puppetlabs/puppet/puppet.conf")
    util.set_hostname(hostname + "." + domain)
    util.add_host_entry("127.0.1.1", hostname, domain)
    util.add_to_path("/opt/puppetlabs/bin")
    run_agent(noop="True", onlychanges="False")

@task
def setup_server4(hostname=None, domain=None, pc="1", forge_modules=["puppetlabs/stdlib", "puppetlabs/concat", "puppetlabs/firewall", "puppetlabs/apt"]):
    """Setup Puppet 4 server"""
    import package, util, git

    # Local files to copy over
    local_master_conf = "files/puppet-master.conf"
    remote_master_conf = "/etc/puppetlabs/puppet/puppet.conf"
    local_hiera_yaml = "files/hiera.yaml"
    remote_hiera_yaml = "/etc/puppetlabs/code/hiera.yaml"
    local_fileserver_conf = "files/fileserver.conf"
    remote_fileserver_conf = "/etc/puppetlabs/puppet/fileserver.conf"

    # Verify that all the local files are in place
    try:
        open(local_master_conf)
        open(local_hiera_yaml)
    except IOError:
        print "ERROR: some local config files were missing!"
        sys.exit(1)

    # Autodetect hostname and domain from env.host, if they're not overridden
    # with method parameters
    if not hostname:
        hostname = util.get_hostname()
    if not domain:
        domain = util.get_domain()

    # Start the install
    install_puppetlabs_release_package(pc)
    package.install("puppetserver")
    util.put_and_chown(local_master_conf, remote_master_conf)
    util.put_and_chown(local_hiera_yaml, remote_hiera_yaml)
    util.put_and_chown(local_fileserver_conf, remote_fileserver_conf)
    util.add_to_path("/opt/puppetlabs/bin")
    util.set_hostname(hostname + "." + domain)
    # "facter fqdn" return a silly name on EC2 without this
    util.add_host_entry("127.0.1.1", hostname, domain)

    # Add modules from Puppet Forge. These should in my experience be limited to
    # those which provide new types and providers. In particular puppetlabs'
    # modules which control some daemon (puppetdb, postgresql, mysql) are
    # extremely complex, very prone to breakage and nasty to debug. 
    for module in forge_modules:
        add_forge_module(module)

    # Add Git submodules
    git.install()

@task
def add_forge_module(name):
    """Add a forge module"""
    # puppet module list shows dashes instead of slashes due to historic reasons
    listname = name.replace("/", "-")
    with hide("everything"), settings(warn_only=True):
        if sudo("puppet module list --color=false 2> /dev/null|grep "+listname).failed:
            sudo("puppet module install "+name)
