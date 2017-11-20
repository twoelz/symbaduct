#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Lineages

common code
'''

# Copyright (c) 2015 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'
__all__ = ['is_valid_ip', 'validate_config', 'shared', 'HOST', 'PORT', 'MAX_PORT', 'LOCALTIME', 'LANG', 'DECIMAL_SEPARATOR', 'CSV_SEPARATOR']

import sys

if __name__ == '__main__':
    sys.exit()

import os
import time
import re

# add dependency (configobj)
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                'res',
                                'scripts',
                                'dependencies',
                                'configobj'))
from configobj import ConfigObj
from configobj import flatten_errors
from validate import Validator


# DIR is up two folders
DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    '..'))

LOCALTIME = '%04d-%02d-%02d-%02d-%02d-%02d'%time.localtime()[0:6]


def is_valid_ip(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

def validate_config(a_config, set_copy=False):
    '''Validates a ConfigObj instance.

    If errors are found, throws exception and reports errors.
    '''
    error = False
    error_message_list = []
    res = a_config.validate(Validator(), preserve_errors=True, copy=set_copy)
    for entry in flatten_errors(a_config, res):
        section_list, key, error = entry
        if key is not None:
            section_list.append(key)
        else:
            section_list.append('[missing section]')
        section_string = ', '.join(section_list)
        if not error:
            error = 'Missing value or section.'
        error_message = ''.join([section_string, ' = ', str(error)])
        error_message_list.append(error_message)
    if error:
        error_messages = '; '.join(error_message_list)
        print error_messages
        raise Exception(error_messages)
    if not res:
        error = '{0} invalid\n'.format(os.path.split(a_config.filename)[1])
        raise Exception(error)

# load & validate config
shared = ConfigObj(infile=os.path.join(DIR, 'config', 'shared.ini'),
                   configspec=os.path.join(DIR, 'config', 'spec', 'spec_shared.ini'))

validate_config(shared)

# set constants
HOST = shared['host']
PORT = shared['port']
MAX_PORT = 65535
LANG = shared['language']
DECIMAL_SEPARATOR = shared['decimal separator']
CSV_SEPARATOR = shared['csv separator']

#create directory structure
if not os.path.exists(os.path.join(DIR, 'output')):
    os.mkdir(os.path.join(DIR, 'output'))
if not os.path.exists(os.path.join(DIR, 'output', 'log')):
    os.mkdir(os.path.join(DIR, 'output', 'log'))



