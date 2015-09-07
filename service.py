from fabric.api import *
from vars import *

@task
def stop(name):
    """Stop a service"""
    vars = Vars()
    sudo(vars.os.service_stop_cmd % name)

@task
def start(name):
    """Start a service"""
    vars = Vars()
    sudo(vars.os.service_start_cmd % name)

@task
def restart(name):
    """Restart a service"""
    vars = Vars()
    sudo(vars.os.service_restart_cmd % name)

@task
def status(name):
    """View status of a service"""
    vars = Vars()
    sudo(vars.os.service_status_cmd % name)
