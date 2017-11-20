'''
Created on 16/08/2011

@author: thomas
'''

__all__ = ['utostr', 'print_u']
__version__ = '1.0.0'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

import copy
import random

def n(l, num=100, differs=3):
    full = []
    for i in xrange(num):
        random.shuffle(l)
        if differs:
            keep_shuffling = True
            while keep_shuffling:
                match = False
                for j in xrange(differs):
                    if len(full) > j and l == full[-1 * j]:
                        match = True
                        break
                keep_shuffling = match
                if keep_shuffling:
                    random.shuffle(l)
        full.append(copy.deepcopy(l))
        print ','.join([str(x) for x in l])
    return

#n([1, 2, 3, 4], differs=3)

#n([1, 2, 3,], differs=2)

n([1, 2], differs=0)
