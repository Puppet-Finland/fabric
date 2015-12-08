from fabric.api import *
from urlparse import urlparse
from fabric.contrib.files import exists
import os
import re

@task
def is_installed(package):
    """Check if package is installed"""
    import vars
    vars = vars.Vars()
    # This will work with "package.<extension> and "package"
    package_name = os.path.splitext(package)[0]
    with quiet(), settings(warn_only=True):
        if sudo(vars.os.package_installed_cmd + " " + package_name).failed:
            return False
        else:
            return True

@task
def download_and_install(url, package_name=None, proxy_url=None):
    """Download a package from URL and install it. Use package_name to manually define the name of the installed package and to prevent unnecessary reinstalls."""
    import vars
    vars = vars.Vars()
    with cd("/tmp"):
        parsed = urlparse(url)
        package_file = re.split("/", parsed.path)[1]

        if not package_name:
            package_name = package_file.rpartition(".")[0]

        if not exists(package_file):
            # wget is not universally available out of the box
            if proxy_url: cmd = "curl -Os -x "+proxy_url+" "+url
            else:         cmd = "curl -Os "+url
            run(cmd)
        if not is_installed(package_name):
            sudo(vars.os.package_local_install_cmd % package_file)

@task
def install(package):
    """Install a package from the repositories"""
    import vars
    vars = vars.Vars()
    if not is_installed(package):
        sudo(vars.os.package_refresh_cmd)
        sudo(vars.os.package_install_cmd % package)

@task
def remove(package):
    """Remove a package that may or may not be installed"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.package_remove_cmd % package)


@task
def autoremove():
    """Remove obsolete packages, such as unused kernel images"""
    import vars
    vars = vars.Vars()
    with settings(hide("user", "stdout")):
        sudo(vars.os.package_autoremove_cmd)
