#! /usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Decimals Module.

Functions and classes for handling decimal numbers.

'''

# Copyright (c) 2015 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details


__version__ = '1.0.0'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

try:
    import cdecimal as decimal
    from cdecimal import Decimal
except ImportError:
    print 'cdecimal not found, using standard (slower) decimal module'
    import decimal
    from decimal import Decimal

# all further rounding for decimal class is rounded up
decimal.getcontext().rounding = decimal.ROUND_UP

## example use:
#pi = Decimal('3.1415926535897931')
#round_pi = pi.quantize(Decimal('.01'))
#print round_pi
#3.14
