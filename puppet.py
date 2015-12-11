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
def setup_agent4(hostname=None, domain=None, pc="1", agent_conf="files/puppet-agent.conf", proxy_url=None, hosts_file=None):
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

    util.add_host_entry(util.get_ip(), hostname, domain)

    # Optionally add hosts from a separate file. This is useful when the IP of
    # the puppetmaster does not match its name in DNS.
    util.add_host_entries(hosts_file)
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
    local_defaults = "files/puppetserver_defaults"
    remote_defaults = "/etc/default/puppetserver"
    modules_dir = basedir+"/code/environments/production/modules"
    hiera_nodes_dir = basedir+"/code/environments/production/hieradata/nodes"

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

    fqdn = "%s.%s" % (hostname, domain)

    # Ensure that clock is correct before doing anything else, like creating SSL 
    # certificates.
    util.set_clock()

    # Start the install
    install_puppetlabs_release_package(pc)
    package.install("puppetserver")
    util.put_and_chown(local_master_conf, remote_master_conf)
    util.put_and_chown(local_hiera_yaml, remote_hiera_yaml)
    util.put_and_chown(local_fileserver_conf, remote_fileserver_conf)
    util.put_and_chown(local_gitignore, remote_gitignore)
    util.put_and_chown(local_defaults, remote_defaults)
    util.add_to_path("/opt/puppetlabs/bin")
    util.set_hostname(hostname + "." + domain)
    # "facter fqdn" return a silly name on EC2 without this
    util.add_host_entry(util.get_ip(), hostname, domain)

    # Copy over template environments
    util.put_and_chown(local_environments, remote_codedir)

    # Generate master node yaml file (fqdn.yaml) and copy it over to remote server
    master_yaml = StringIO()
    make_puppetmaster_yaml(fqdn, util.password(), stream=master_yaml)
    util.put_and_chown(master_yaml, "%s/%s.yaml" % (hiera_nodes_dir, fqdn))

    # Add modules from Puppet Forge. These should in my experience be limited to
    # those which provide new types and providers. In particular puppetlabs'
    # modules which control some daemon (puppetdb, postgresql, mysql) are
    # extremely complex, very prone to breakage and nasty to debug. 
    for module in forge_modules:
        add_forge_module(module)

    # Git setup
    git.install()
    git.init(basedir)
    if not exists(modules_dir):
        sudo("mkdir "+modules_dir)
    git.init(modules_dir)
    git.add_submodules(basedir=modules_dir)
    git.add_all(basedir)
    git.commit(basedir, "Initial commit")

    # Link hieradata and manifests from production to testing. This keeps the
    # testing environment identical to the production environment. The modules
    # directory in testing is separate and may (or may not) contain modules that
    # override or complement those in production.
    util.symlink(remote_codedir+"/environments/production/hieradata", remote_codedir+"/environments/testing/hieradata")
    util.symlink(remote_codedir+"/environments/production/manifests", remote_codedir+"/environments/testing/manifests")

    # Start puppetserver to generate the CA and server certificates/keys
    service.start("puppetserver")

    # Set master FQDN and run agent
    run("puppet config set --section agent server %s" % fqdn)
    run_agent(noop="False")


def make_puppetmaster_yaml(hostname, db_password, stream=None):
    yaml_data = {
        'puppetdb::db_password': db_password,
        'puppetmaster::puppetdb_host': hostname,
        'role': ['puppetserver'],
    }
    return yaml.dump(yaml_data, stream=stream, default_flow_style=False)


@task
@serial
def migrate_node(proxy_url=None):
    """Migrate node from Puppet 3.x to 4.x"""
    import package, puppet, vars
    vars = vars.Vars()
    package.remove("puppet facter")
    sudo("rm -f /etc/apt/sources.list.d/puppetlabs.list")
    if exists("/var/lib/puppet"):
        sudo("mv /var/lib/puppet /var/lib/puppet.old.3")
    if exists("/etc/puppet"):
        sudo("mv /etc/puppet /etc/puppet.old.3")
    puppet.setup_agent4(proxy_url=proxy_url)

    if vars.osfamily == 'Debian':
        package.autoremove()
        puppet.resolve_aptitude_conflicts()

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
