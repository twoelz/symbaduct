#! /usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Convert Module.

A collection of conversion or print functions.

"""

# Copyright (c) 2015 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__all__ = ['utostr', 'print_u']
__version__ = '1.0.0'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

import unicodedata
import os


def utostr(txt):
    """Converts an unicode string returning an ascii string"""
    # safer than using str(txt), includes more cases
    if type(txt) == str:
        return txt
    return unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore')


def print_u(txt):
    """Prints a string resulting from an ascii convertion from unicode"""

    print utostr(txt)


def n_uni(some_number, precision=2, sep=None):
    """
    Gets a number, returns a unicode string.

    Uses given precision and formats decimal separator according to language.
    Defaults to brazilian portuguese
    """

    if not sep:
        if 'DECIMAL_SEPARATOR' in os.environ:
            sep = os.environ['DECIMAL_SEPARATOR']
        else:
            # default value
            sep = u'.'
    if isinstance(sep, str):
        sep = unicode(sep)
    text = u'{0:.{1}f}'.format(some_number, precision)
    if sep == u'.':
        return text
    return text.replace(u'.', sep)


def n_str(some_number, precision=2, sep=None):
    """
    Gets a number, returns a regular string.

    Uses given precision and formats decimal separator according to language.
    Defaults to brazilian portuguese
    """
    if not sep:
        if 'DECIMAL_SEPARATOR' in os.environ:
            sep = os.environ['DECIMAL_SEPARATOR']
        else:
            # default value
            sep = '.'
    if not isinstance(sep, str):
        sep = str(sep)
    text = '{0:.{1}f}'.format(some_number, precision)
    if sep == '.':
        return text
    return text.replace('.', sep)

