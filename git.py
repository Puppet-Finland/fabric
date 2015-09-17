from fabric.api import *
from fabric.contrib.files import exists
import re

@task
def install():
    """Install Git"""
    import package, vars
    vars = vars.Vars()
    package.install(vars.os.git_package_name)

@task
def clone(dir, url, reponame=None, submodule=False):
    """Clone a Git repository as-is or as a submodule"""
    if not reponame:
        temp = re.split("/", url)[-1:][0]
        name = re.split("\.", temp)[0]
    else:
        name = reponame

    with cd(dir):
        if not exists(name):
            if submodule:
                cmd = "git submodule add"
            else:
                cmd = "git clone"
            sudo(cmd+" "+url+" "+name)

@task
def add_submodule(url, basedir, name=None):
    """Add a Git submodule to a directory"""
    if not name:
        # This can handle URL in this format:
        #
        # https://github.com/Puppet-Finland/postgresql.git
        # https://github.com/Puppet-Finland/postgresql
        #
        stripped = re.sub("\.git$", "", url)
        name = re.split("/", stripped)[-1:][0]
        cmd = "git submodule add "+url
    else:
        cmd = "git submodule add "+url+" "+name

    with cd(basedir):
        if not exists(name):
            sudo(cmd)

@task
def add_submodules(basedir, file="files/git-submodules"):
    """Add submodules from url / name pairs listed in a file"""
    with open(file) as modulelist:
        for line in modulelist:
            columns=line.split(" ")
            url=columns[0].rstrip("\n")
            if len(columns) > 1:
                name = columns[1].rstrip("\n")
            else:
                name = None

            add_submodule(url, basedir, name)
