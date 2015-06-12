# -*- coding: utf-8 -*-

"""
A package for optimization-based modeling and simulation.
"""

import logging
logger = logging.getLogger(__name__)

from friendlysam.util import *
from friendlysam.parts import *
from friendlysam.opt import *
import friendlysam.models

class InsanityError(Exception):
    """Raised when a sanity check fails."""
    pass