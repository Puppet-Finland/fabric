# -*- coding: utf-8 -*-
import os
import glob

__all__ = [ os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__)+"/*.py") if not os.path.basename(f) == "fabfile.py"]

#import util
#import puppet
