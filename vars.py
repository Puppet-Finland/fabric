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

        osfamily = self.get_osfamily()
        lsbdistcodename = self.get_lsbdistcodename()

        # Populate OS-specific parameters
        if osfamily == 'Debian': self.os = Debian(osfamily, lsbdistcodename)
        elif osfamily == 'RedHat': self.os = RedHat(osfamily, lsbdistcodename)

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
                    # Facter return an empty string here as well
                    return ""

class Linux(object):
    """Parameters for Linux-based operating systems"""
    def __init__(self, osfamily, lsbdistcodename, *args, **kwargs):
        self.osfamily = osfamily
        self.lsbdistcodename = lsbdistcodename

class RedHat(Linux):
    """Parameters for RedHat-based operating systems"""
    def __init__(self, osfamily, lsbdistcodename, *args, **kwargs):
        super(RedHat, self).__init__(osfamily, lsbdistcodename)
        self.package_refresh_cmd = "yum makecache"
        self.package_upgrade_cmd = "yum update"
        self.package_install_cmd = "yum install %s"

class Debian(Linux):
    """Parameters for Debian-based operating systems"""
    def __init__(self, osfamily, lsbdistcodename, *args, **kwargs):
        super(Debian, self).__init__(osfamily, lsbdistcodename)
        self.package_refresh_cmd = "apt-get update"
        self.package_upgrade_cmd = "apt-get dist-upgrade"
        self.package_install_cmd = "apt-get install %s"

class Trusty(Debian):
    """Parameters for Ubuntu Trusty (14.04)"""
    def __init__(self, osfamily, lsbdistcodename, *args, **kwargs):
        super(Trusty, self).__init__(osfamily, lsbdistcodename)

