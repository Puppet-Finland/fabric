"""Convert Hiera data into env.roledefs"""
from fabric.api import *
import sys
import pickle
import re

@serial
@task
def generate():
    """Generate a list of hosts and roles based on Hiera data"""
    import config

    # Ensure that we're running in the correct local directory
    try:
        fabfile = open("fabfile.py", "r")
    except IOError:
        print("ERROR: you must run this command in the directory where fabfile.py resides!")
        sys.exit(1)

    try:
        tagstring = config.get("puppet", "puppet_tags")
        nodes_dir = config.get("puppet", "nodes_dir")
    except:
        print("ERROR: unable to load settings from settings.ini!")
        sys.exit(1)

    # Generate the search pattern for tags
    tags = re.split(",", tagstring.replace(" ", ""))
    maxsep = len(tags)-1

    if not tagstring:
        print "ERROR: settings.ini: puppet_tags has no value!"
        sys.exit(1)
    else:
        sepcount = 0
        pattern = "^("
        for tag in tags:
            if sepcount < maxsep:
                pattern = pattern + tag + "|"
            else:
                pattern = pattern + tag + ")"
            sepcount = sepcount + 1

    print "NOTICE: using pattern "+pattern+" for parsing Hiera tags"

    # The env.roledefs dictionary is already loaded from fabfile.py and needs
    # to be emptied before regenerating it or duplicate entries will get
    # generated.
    env.roledefs = {}

    # Fetch latest node data from the Puppetmaster
    with hide("everything"):
        if run("test -d "+nodes_dir).failed:
            print "ERROR: unable to load Hiera data from remote server!"
            sys.exit(1)
        with cd(nodes_dir):
            output = run("grep -E \""+pattern+"\" *.yaml")

    # Add to role that includes all hosts. We can't use env.hosts because
    # it's contents are loaded on every execution.
    env.roledefs['role_any'] = []

    # Convert the textual data from the Puppetmaster into env.roledefs
    for entry in re.split("\r\n", output.replace(".yaml", "")):
        info = re.split(":+", entry.replace(" ", ""))

        # <server.domain.com>
        nodename = info[0]

        # role_<somerole>
        rolestring = info[1]+"_"+info[2]

        # Add current role if it does not exist in env.roledefs
        if rolestring not in env.roledefs:
            env.roledefs[rolestring] = [nodename]

        # Add host to role_any and role_<somerole> if not yet present 
        for role in ['role_any', rolestring]:
            if nodename not in env.roledefs[role]:
                env.roledefs[role].append(nodename)

    # Pickle the env.roledefs dictionary for offline loading. This avoids having
    # to fetch the node data before every invocation of Fabric. The pickled
    # roledefs are stored in version control to ease sharing.
    with open('roledefs.pickle', 'wb') as roledefs:
        pickle.dump(env.roledefs, roledefs)

    print
    print "Successfully generated and pickled env.roledefs. Next you have to add this"
    print "to your main fabfile.py:"
    print
    print "    env.roledefs = hostinfo.load_roledefs()"
    print
    print "This will ensure that the roledefs are actually used."

@task
@serial
@runs_once
@hosts('localhost')
def show():
    '''Display contents of env.roledefs'''
    env.roledefs = load_roledefs()
    print "Roles:"
    for role in sorted(env.roledefs):
        print "  "+role+": "
        for member in sorted(env.roledefs[role]):
            print "    "+member

def load_roledefs():
    '''Unpickle and return env.roledefs'''
    try:
        with open("roledefs.pickle", "rb") as roledefs:
            return pickle.load(roledefs)
    except IOError:
        return None
