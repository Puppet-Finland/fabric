# -*- coding: utf-8 -*-
"""Generic Fabric-commands which should be usable without further configuration"""
from fabric.api import *
from os.path import dirname, split, abspath
import os
import sys
import glob


# Hacking our way into __init__.py of current package
current_dir = dirname(abspath(__file__))
sys_path, package_name = split(current_dir)

sys.path.append(sys_path)
__import__(package_name, globals(), locals(), [], -1)
__package__ = package_name
from . import *

env.roledefs = hostinfo.load_roledefs()
