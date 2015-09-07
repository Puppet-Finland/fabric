from fabric.api import *
from vars import *
from urlparse import urlparse
from vars import *
import os
import re

@task
def is_installed(package):
    """Check if package is installed"""
    vars = Vars()
    # This will work with "package.<extension> and "package"
    package_name = os.path.splitext(package)[0]
    with quiet(), settings(warn_only=True):
        if sudo(vars.os.package_installed_cmd + " " + package_name).failed:
            return False
        else:
            return True

@task
def download_and_install(url):
    """Download a package and install it"""
    vars = Vars()
    with cd("/tmp"):
        parsed = urlparse(url)
        package_file = re.split("/", parsed.path)[1]
        package_name = package_file.rpartition(".")[0]

        if not exists(package_file):
            run("wget "+url)
        if not is_installed(package_name):
            sudo(vars.os.package_local_install_cmd % package_file)

@task
def install(package):
    """Install a package from the repositories"""
    vars = Vars()
    if not is_installed(package):
        sudo(vars.os.package_refresh_cmd)
        sudo(vars.os.package_install_cmd % package)

@task
def upgrade():
    """Install latest (security) updates"""
    vars = Vars()
    sudo(vars.os.package_refresh_cmd)
    sudo(vars.os.package_upgrade_cmd)

@task
def autoremove():
    """Remove obsolete packages, such as unused kernel images"""
    vars = Vars()
    with settings(hide("user", "stdout")):
        sudo(vars.os.package_autoremove_cmd)
