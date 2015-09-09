from fabric.api import *
from fabric.contrib.files import exists
import re

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

        self.release_file = None
        self.has_facter = self.has_program("facter")
        self.has_lsb_release = self.has_program("lsb_release")
        self.lsbdistcodename = self.get_lsbdistcodename()

        # Populate OS-specific parameters
        osfamily = self.get_osfamily()
        if osfamily == 'Debian':
            self.os = Debian()
            self.osfamily = "Debian"
        elif osfamily == 'Ubuntu':
            self.os = Debian()
            self.osfamily = "Debian"
        elif osfamily == 'RedHat':
            self.os = RedHat()
            self.osfamily = "RedHat"

        self.operatingsystem = self.get_operatingsystem()
        self.operatingsystemmajrelease = self.get_operatingsystemmajrelease()
        self.operatingsystemminrelease = self.get_operatingsystemminrelease()


    def has_program(self, name):
        """Check if the node a certain program installed and in PATH"""
        with hide("everything"), settings(warn_only=True):
            if run("which "+name).succeeded:
                return True
            else:
                return False

    def get_fact(self, fact):
        """Get a fact value from facter. Used internally."""
        with hide("everything"):
            return run("facter "+fact)

    def get_release_file_content(self):
        """Get the content of the release file as string"""
        with hide("everything"):
            return run("cat "+self.release_file)

    def get_osfamily(self):
        """Detect operating system family"""
        if self.has_facter:
            return self.get_fact("osfamily")
        elif self.has_lsb_release:
            with hide("everything"):
                return run("lsb_release -is")
        else:
            # While this loop is fairly inefficient, replacing it with a
            # single Fabric run("ls <filelist>") operation is not a panacea,
            # either, as its output may include several files, some of which
            # are preferable. So we'd need a prioritization list to make
            # sense of the output.
            for k, v in self.release_files.iteritems():
                if exists(k):
                    self.release_file = k
                    return self.release_files[k]['osfamily']

            # Could not determine the operating system family
            return ""

    def get_lsbdistcodename(self):
        """Detect lsbdistcodename"""
        # Try facter and fall back to Pythonic detection if Facter is not
        # present
        if self.has_facter:
            return self.get_fact("lsbdistcodename")
        elif self.has_lsb_release:
            with hide("everything"):
                return run("lsb_release -cs")
        else:
            # Facter returns an empty string here as well
            return ""

    def get_operatingsystemrelease(self, maj):
        """Get the operating system release. Used internally."""
        if maj:
            fact = "operatingsystemmajrelease"
            index = 0
        else:
            fact = "operatingsystemminrelease"
            index = 1

        if self.has_facter:
            return self.get_fact(fact)
        elif self.has_lsb_release:
            fullver = re.split(".", run("lsb_release -rs"))
            with hide("everything"):
                return fullver[index]
        else:
            release = self.get_release_file_content()
            if maj:
                return re.split("\.", release)[index][-1:]
            else:
                return re.split("\.", release)[index][-1:]

    def get_operatingsystem(self):
        """Get the operating system name"""
        if self.has_facter:
            return self.get_fact("operatingsystem")
        elif self.has_lsb_release:
            with hide("everything"):
                return run("lsb_release -is")
        else:
            release = self.get_release_file_content()
            return re.split(" ", release)[0]

    def get_operatingsystemmajrelease(self):
        """Get the major version of the operating system"""
        return self.get_operatingsystemrelease(maj=True)

    def get_operatingsystemminrelease(self):
        """Get the minor version of the operating system"""
        return self.get_operatingsystemrelease(maj=False)

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
        self.default_loginshell_config = "/etc/profile"

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
        self.package_install_cmd = "yum -y install %s"
        self.package_autoremove_cmd = "yum autoremove"
        self.package_local_install_cmd = "rpm -ivh %s"
        self.package_installed_cmd = "rpm -qs"
        self.default_shell_config = "/etc/bashrc"
        self.git_package_name = "git"

class Debian(Linux):
    """Parameters for Debian-based operating systems"""
    def __init__(self, *args, **kwargs):
        super(Debian, self).__init__()
        self.package_refresh_cmd = "apt-get update"
        self.package_upgrade_cmd = "apt-get dist-upgrade"
        self.package_install_cmd = "apt-get -y install %s"
        self.package_autoremove_cmd = "apt-get autoremove"
        self.package_local_install_cmd = "dpkg -i %s"
        # Using %s after the single quotes does not seem to work
        self.package_installed_cmd = "dpkg-query -Wf'${db:Status-abbrev}'"
        self.default_shell_config = "/etc/bash.bashrc"
        self.git_package_name = "git"

class Trusty(Debian):
    """Parameters for Ubuntu Trusty (14.04)"""
    def __init__(self, *args, **kwargs):
        super(Trusty, self).__init__()

@task
def test():
    vars = Vars()
    print "osfamily: "+vars.osfamily
    print "operatingsystem: "+vars.operatingsystem
    print "operatingsystemmajrelease: "+vars.operatingsystemmajrelease
    print "operatingsystemminrelease: "+vars.operatingsystemminrelease
    print "lsbdistcodename: "+vars.lsbdistcodename
