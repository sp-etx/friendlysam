# -*- coding: utf-8 -*-

import doctest
import os

def test_docs():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    docs_dir = os.path.join(this_dir, '../../docs')
    filenames = (f for f in os.listdir(docs_dir) if f.endswith('.rst'))
    for fn in filenames:
        path = os.path.join(docs_dir, fn)
        failures, tests = doctest.testfile(path, optionflags=doctest.ELLIPSIS)
        if failures > 0:
            raise Exception('{} out of {} doctests failed'.format(failures, tests))
