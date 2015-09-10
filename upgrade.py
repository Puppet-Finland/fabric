from fabric.api import *

@task
def simple():
    """Install latest (security) updates"""
    import vars
    vars = vars.Vars()
    sudo(vars.os.package_refresh_cmd)
    sudo(vars.os.package_upgrade_cmd)

@parallel
def get_update_status():
    """Return update information for a node"""
    security_updates = sudo("facter -p security_updates")
    updates = sudo("facter -p updates")
    reboot_required = sudo("facter -p reboot_required")
    output = "|False|"+updates+"|"+security_updates+"|"+reboot_required+"|"
    return output

def select_entries(all_entries, question):
    """Return a subset of a list based on user's decisions"""
    if all_entries:
        print question+" ([a]ll/[s]elect/[N]one)"
        input = "invalid"
        while input not in ("a", "s", "n", ""):
            input = raw_input().lower()
        entries = []
        if input == "a":
            entries = all_entries
            return entries
        elif input == "s":
            for entry in all_entries:
                add_entry = raw_input("Add "+entry+"? (y/N) ").lower()
                if add_entry == "y": entries.append(entry)
            return entries
        elif input in ("n", ""):
            return entries

@task
@runs_once
def interactive():
    """Manage security updates"""
    from util import isTrue

    # Initialize update status dictionary
    update_status = {}

    with hide("everything"):
        results = execute(get_update_status)
        # We need to empty env.roles or it will be "inherited" by subsequent 
        # Fabric execute statements. This is undesirable because we only want to 
        # run (further) commands on nodes which have been explicitly selected.
        env.roles = []

    for host in results:
        try:
            data = results[host].lstrip("|").rstrip("|").split("|")
            tempdict = {}
            tempdict['kernel_upgradable'] = isTrue(data[0])
            tempdict['updates'] = int(data[1])
            tempdict['security_updates'] = int(data[2])
            tempdict['needs_reboot'] = isTrue(data[3])
            update_status[host] = tempdict
            del tempdict
        # Host was not accessible
        except AttributeError:
            update_status[host] = False
        except IndexError:
            update_status[host] = False

    # Initialize temporary hosts lists
    inaccessible_hosts = []
    hosts_with_updates = []
    hosts_needing_reboot = []
    hosts_to_update = []
    hosts_to_reboot = []

    print "Updates".rjust(44)
    print "Host".ljust(30)+" Kernel Total Security   Reboot"
    print

    for host in update_status:

        if not update_status[host]:
            inaccessible_hosts.append(host)
            print "%s  %s" % (host.ljust(30), "<Data unavailable>")
        else:
            if update_status[host]['updates'] > 0: hosts_with_updates.append(host)
            if update_status[host]['needs_reboot']: hosts_needing_reboot.append(host)

            print "%s  %s   %s      %s     %s" % (host.ljust(30),\
                                                  str(update_status[host]['kernel_upgradable']).rjust(5),\
                                                  str(update_status[host]['updates']).rjust(3),\
                                                  str(update_status[host]['security_updates']).rjust(3),\
                                                  str(update_status[host]['needs_reboot']).rjust(3))
    print

    # Give the option to install updates
    if hosts_with_updates:
        selected_hosts = select_entries(hosts_with_updates, "Install security updates?")
        if selected_hosts:
            do_update = raw_input("Commence update? (y/N)").lower()
            if do_update == "y":
                env.hosts = selected_hosts
                execute(do_upgrade)
