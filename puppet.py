from fabric.api import *
from fabric.contrib.files import exists
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
def install_puppetlabs_release_package(pc, proxy_url=None):
    """Install Puppetlabs apt repo release package"""
    import package, vars
    vars = vars.Vars()
    os = vars.lsbdistcodename

    if vars.osfamily == "Debian":
        package.download_and_install("https://apt.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+os+".deb", "puppetlabs-release-pc"+pc, proxy_url=proxy_url)
    elif vars.osfamily == "RedHat":
        if vars.operatingsystem in ["RedHat", "CentOS", "Scientific"]:
            oscode = "el"
        elif vars.operatingsystem == "Fedora":
            oscode = "fedora"
        url="https://yum.puppetlabs.com/puppetlabs-release-pc"+pc+"-"+oscode+"-"+vars.operatingsystemmajrelease+".noarch.rpm"
        package.download_and_install(url, "puppetlabs-release-pc"+pc, proxy_url=proxy_url)

@task
def setup_agent4(hostname=None, domain=None, pc="1", agent_conf="files/puppet-agent.conf", proxy_url=None):
    """Setup Puppet 4 agent"""
    import package, util

    if not hostname:
        hostname = util.get_hostname()
    if not domain:
        domain = util.get_domain()

    install_puppetlabs_release_package(pc, proxy_url=proxy_url)
    package.install("puppet-agent")
    util.put_and_chown(agent_conf, "/etc/puppetlabs/puppet/puppet.conf")
    util.set_hostname(hostname + "." + domain)
    util.add_host_entry("127.0.1.1", hostname, domain)
    util.add_to_path("/opt/puppetlabs/bin")
    run_agent(noop="True", onlychanges="False")

@task
def setup_server4(hostname=None, domain=None, pc="1", forge_modules=["puppetlabs/stdlib", "puppetlabs/concat", "puppetlabs/firewall", "puppetlabs/apt"]):
    """Setup Puppet 4 server"""
    import package, util, git, service

    # Local files to copy over
    basedir = "/etc/puppetlabs"
    local_master_conf = "files/puppet-master.conf"
    remote_master_conf = basedir+"/puppet/puppet.conf"
    local_hiera_yaml = "files/hiera.yaml"
    remote_hiera_yaml = basedir+"/code/hiera.yaml"
    local_fileserver_conf = "files/fileserver.conf"
    remote_fileserver_conf = basedir+"/puppet/fileserver.conf"
    local_environments = "files/environments"
    remote_codedir = basedir+"/code"
    local_gitignore = "files/gitignore"
    remote_gitignore = basedir+"/.gitignore"
    modules_dir = basedir+"/code/environments/production/modules"

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
    util.put_and_chown(local_gitignore, remote_gitignore)
    util.add_to_path("/opt/puppetlabs/bin")
    util.set_hostname(hostname + "." + domain)
    # "facter fqdn" return a silly name on EC2 without this
    util.add_host_entry("127.0.1.1", hostname, domain)

    # Copy over template environments
    util.put_and_chown(local_environments, remote_codedir)

    # Add modules from Puppet Forge. These should in my experience be limited to
    # those which provide new types and providers. In particular puppetlabs'
    # modules which control some daemon (puppetdb, postgresql, mysql) are
    # extremely complex, very prone to breakage and nasty to debug. 
    for module in forge_modules:
        add_forge_module(module)

    # Setup Git
    git.install()
    git.init(basedir)
    if not exists(modules_dir):
        sudo("mkdir "+modules_dir)
    git.init(modules_dir)
    git.add_submodules(basedir=modules_dir)

    # Start puppetserver to generate the CA and server certificates/keys
    service.start("puppetserver")
    run_agent(noop=False)

@task
def add_forge_module(name):
    """Add a forge module"""
    # puppet module list shows dashes instead of slashes due to historic reasons
    listname = name.replace("/", "-")
    with hide("everything"), settings(warn_only=True):
        if sudo("puppet module list --color=false 2> /dev/null|grep "+listname).failed:
            sudo("puppet module install "+name)

@task
def resolve_aptitude_conflicts():
    """Clear package conflicts in aptitude due to Puppet 3->4 migration""" 

    # Installation of Puppetlabs' Puppet 4 packages on top of older Puppet 3 
    # package seems to leave aptitude's package selections in a limbo. In 
    # practice the puppet-agent package from Puppet 4 conflicts with several 
    # other packages that are marked for installation, but no actually 
    # installed. Manually resolving this issue would be tiresome, so better do 
    # it here.
    #
    # The ":" after the package name means that any actions (install, remove, 
    # hold, etc.) set in aptitude are cancelled.
    #
    sudo("aptitude install augeas-lenses: ruby-augeas: libaugeas-ruby1.8: libaugeas-ruby1.9.1: libaugeas0: libaugeas-ruby: puppet: puppet-common: facter:")
