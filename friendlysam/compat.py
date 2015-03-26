# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import contextlib

@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass