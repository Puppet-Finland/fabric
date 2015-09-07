# Fabric

This repository contains fairly general-purpose fabfiles and related data 
intended for use with [Fabric](http://www.fabfile.org/). Fabric is essentially a 
SSH in a for loop on steroids written in Python. For full usage documentation 
see the [Fabric homepage](http://www.fabfile.org/).

Note that Fabric is not a viable replacement for real configuration management 
systems such as Puppet, except for very trivial cases. Trying to do 
configuration management with Fabric will very quickly just result in one 
reinventing Puppet resources in Python.

# Configuring Puppet/Hiera

To make use of automatically generated roledefs youn will first need to 
configure Hiera. Add the categories you want to your site.pp:

    $role = hiera('role', undef)
    $importance = hiera('importance', undef)
    $connectivity = hiera('connectivity', undef)
    $admin = hiera('admin', undef)

Then define these settings for each node (or a group of nodes) in its yaml file. 
For example db1.domain.com might have this in it:

    role: db
    importance: high
    admin: jack

The generate_roledefs() task will produce env.roledefs from the yaml files. 
Adding the categories to hiera.yaml allows grouping the nodes in Puppet also:

    ---
    :backends:
    - yaml
    :yaml:
        :datadir: /etc/puppet/environments/%{::environment}/hiera
    :hierarchy:
        - "nodes/%{::fqdn}"
        - "connectivity/%{::connectivity}"
        - "importance/%{::importance}"
        - "roles/%{::role}"
        - "lsbdistcodename/%{::lsbdistcodename}"
        - "osfamily/%{::osfamily}"
        - common

# Setting up Fabric

First install Fabric according to it's documentation. Then clone this repository 
and copy *settings.ini.sample* to *settings.ini*. Edit *settings.ini* it so that 
it looks like this:

    [puppet]
    puppet_tags = role, importance, admin, connectivity

It may be useful to then create a Fabric configuration file, $HOME/.fabricrc, 
with contents such as this:

    user = my_remote_ssh_username
    warn_only = True
    skip_bad_hosts = True

Unfortunately these settings seem to override those given on the command-line, 
so the usefulness of .fabricrc is somewhat limited.

# Managing roles / host groups

Fabric has a concept of "roles" which are actually just arbitrary groupings of 
hosts. Here groups are based on things such as *role*, *importance*, 
*connectivity* and *admin* (see puppet_tags in *settings.ini*, above). These 
groups are populated from Hiera data on the Puppetmaster, so that the same 
groupings can be used for Puppet and Fabric.

To update the locally cached role definitions do

    $ fab -Hpuppet.domain.com generate_roledefs

This will fetch role information from Hiera and store it in a serialized Python 
dictionary, *roledefs.pickle*. This local copy of the role definitions can then 
be updated as necessary. Although fetching the most current nodelist from Hiera 
on every Fabric run would certainly be doable, it would probably be a much 
bigger hassle in the long run for the user than periodically updating the local 
host/role cache .

To list active nodes and roles, do

    $ fab show_hostinfo
    [localhost] Executing task 'show_hostinfo'
    Roles:
        admin_joe:
            www1.domain.com
            www2.domain.com
    --- snip ---
        role_db:
            db1.domain.com
            db2.domain.com
    
    Done.

Tasks can be run on specified groups of hosts by specifying a matching category 
name and value joined by underscore , e.g.

    $ fab -Rrole_db uptime
    $ fab -Rrole_wwww deploy
    $ fab -Radmin_jack upgrade

A special role, *role_any*, includes all hosts. This is solely to allow easily 
running tasks on all hosts when necessary.

# Common Fabric tasks

## List available commands/tasks:

    $ fab -l

## Restart a service

    $ fab -Hsomehost -p<password> service.restart:name=ntp

## Install security updates to a few nodes

    $ fab -Hsomehost,otherhost -p<password> package.upgrade

## Clean up unused packages

    $ fab -Hsomehost.openvpn.in -p<password> package.autoremove

## Run Puppet Agent

Sometimes running Puppet manually is useful. First do a parallel dry-run:

    $ fab -Rimportance_critical -p<password> puppet.run_agent

If there are suspicious-looking changes on some nodes, show the changes that 
would be made (slow, runs in serial):

    $ fab -Hsomehost -p<password> puppet.show_changes

Finally do the real run:

    $ fab -Rimportance_critical -p puppet.run_agent:noop=False

# Bugs

## Imports need to be inside defs

If imports are placed at the top of the Python files, the task hierarchy gets 
messed up. See message for commit e0d3d79 for details.

## Operating system variables are constantly redefined

Currently each method has to individually (re)determine the OS-specific 
variables. This is suboptimal if a task calls many methods which also need to 
runnable by themselves, i.e. Fabric tasks.

# TODO

* Generate a list of tags directly from Hiera by parsing manifests/site.pp
