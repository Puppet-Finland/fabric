import ConfigParser

def get(section, key):
    """Get a key's value from settings.ini"""
    config = ConfigParser.RawConfigParser()
    config.readfp(open("settings.ini"))
    value = config.get(section, key)
    return value
