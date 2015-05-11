# -*- coding: utf-8 -*-

import doctest

def test_docs():
    failures, tests = doctest.testfile('../../docs/user-guide.rst', optionflags=doctest.ELLIPSIS)
    if failures > 0:
        raise Exception('{} out of {} doctests failed'.format(failures, tests))