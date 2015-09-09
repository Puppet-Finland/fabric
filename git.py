from fabric.api import *
from vars import *

def install():
    """Install Git"""
    import package
    vars = Vars()
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
