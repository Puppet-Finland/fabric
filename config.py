import ConfigParser

def get(section, key, inifile="settings.ini"):
    """Get a key's value from a inifile"""
    config = ConfigParser.RawConfigParser()
    config.readfp(open(inifile))
    value = config.get(section, key)
    return value
