from fabric.api import *

@task
def remove_cache():
    """Remove apt-cacher-ng caches, which get corrupted quite easily"""
    import service, time
    service.stop("apt-cacher-ng")
    time.sleep(2)
    sudo("rm -rf /var/cache/apt-cacher-ng/*")
    time.sleep(2)
    service.start("apt-cacher-ng")
