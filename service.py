from fabric.api import *

@task
def stop(name):
    """Stop a service"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.service_stop_cmd % name)

@task
def start(name):
    """Start a service"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.service_start_cmd % name)

@task
def restart(name):
    """Restart a service"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.service_restart_cmd % name)

@task
def status(name):
    """View status of a service"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.service_status_cmd % name)
