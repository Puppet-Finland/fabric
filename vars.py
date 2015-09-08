from fabric.api import *
from fabric.contrib.files import exists

class Vars:
    """Manage parameters based on the operating system"""

    def __init__(self, *args, **kwargs):
        # Map release files to operating system names and operating system
        # families. This approach has been adapted from
        # facter/operatingsystem/linux.rb and would be redundant _if_ every OS
        # had the lsb_release command at hand out of the box. Note that some
        # operating systems such as Fedora may have several release files, so
        # the most specific need to be at the top. In other words, "Fedora" is
        # more Fedora than RedHat.
        self.release_files = { '/etc/fedora-release': { 'osfamily': 'RedHat' },
                               '/etc/redhat-release': { 'osfamily': 'RedHat' } }

        self. lsbdistcodename = self.get_lsbdistcodename()

        osfamily = self.get_osfamily()

        # Populate OS-specific parameters
        if osfamily == 'Debian':
            self.os = Debian()
            self.osfamily = "Debian"
        elif osfamily == 'Ubuntu':
            self.os = Debian()
            self.osfamily = "Debian"
        elif osfamily == 'RedHat':
            self.os = RedHat()
            self.osfamily = "RedHat"

    def get_osfamily(self):
        """Detect operating system family"""
        with hide("everything"), settings(warn_only=True):
            if run("which facter").succeeded:
                return run("facter osfamily")
            elif run("which lsb_release").succeeded:
                return run("lsb_release -is")
            else:
                # While this loop is fairly inefficient, replacing it with a
                # single Fabric run("ls <filelist>") operation is not a panacea,
                # either, as its output may include several files, some of which
                # are preferable. So we'd need a prioritization list to make
                # sense of the output.
                for k, v in self.release_files.iteritems():
                    if exists(k):
                        return self.release_files[k]['osfamily']

                # Could not determine the operating system family
                return ""

    def get_lsbdistcodename(self):
        """Detect lsbdistcodename"""
        # Try facter and fall back to Pythonic detection if Facter is not
        # present
        with hide("everything"), settings(warn_only=True):
            if run("which facter").succeeded:
                return run("facter lsbdistcodename")
            else:
                # The lsb_release command is not available on RedHat-based operating
                # systems. We can use it on Debian/Ubuntu, though.
                if run("which lsb_release").succeeded:
                   return run("lsb_release -cs")
                else:
                    # Facter returns an empty string here as well
                    return ""

class Linux(object):
    """Parameters for Linux-based operating systems"""
    def __init__(self, *args, **kwargs):
        """Common settings for Linux"""
        if self.has_systemd():
            self.service_start_cmd = "systemctl start %s"
            self.service_stop_cmd = "systemctl stop %s"
            self.service_restart_cmd = "systemctl restart %s"
            self.service_status_cmd = "systemctl status %s"
        else:
            self.service_start_cmd = "service %s start"
            self.service_stop_cmd = "service %s stop"
            self.service_restart_cmd = "service %s restart"
            self.service_status_cmd = "service %s status"

        self.default_shell = "/bin/bash"
        self.default_shell_config = "/etc/bash.bashrc"

    def has_systemd(self):
        """Determine if the operating system uses systemd"""
        with hide("everything"), settings(warn_only=True):
            if run("which systemctl").succeeded:
                return True
            else:
                return False

class RedHat(Linux):
    """Parameters for RedHat-based operating systems"""
    def __init__(self, *args, **kwargs):
        super(RedHat, self).__init__()
        self.package_refresh_cmd = "yum makecache"
        self.package_upgrade_cmd = "yum update"
        self.package_install_cmd = "yum install %s"
        self.package_local_install_cmd = "rpm -i %s"

class Debian(Linux):
    """Parameters for Debian-based operating systems"""
    def __init__(self, *args, **kwargs):
        super(Debian, self).__init__()
        self.package_refresh_cmd = "apt-get update"
        self.package_upgrade_cmd = "apt-get dist-upgrade"
        self.package_install_cmd = "apt-get install %s"
        self.package_autoremove_cmd = "apt-get autoremove"
        self.package_local_install_cmd = "dpkg -i %s"
        # Using %s after the single quotes does not seem to work
        self.package_installed_cmd = "dpkg-query -Wf'${db:Status-abbrev}'"

class Trusty(Debian):
    """Parameters for Ubuntu Trusty (14.04)"""
    def __init__(self, *args, **kwargs):
        super(Trusty, self).__init__()
