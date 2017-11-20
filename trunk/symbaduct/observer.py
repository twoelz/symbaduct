#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Symbaduct

Observer
'''

# symbaduct observer
# Copyright (c) 2017 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

import sys
import imp

# the following way to import is to avoid creating bytecode file (.pyc) for client
sys.dont_write_bytecode = True
imp.load_source('client', 'client.py')

from client import *

if __name__ == '__main__':
    set_obs_on()

    import traceback
    try:
        main()
    except:
        traceback.print_exc()
        if stout:
            stout.close()