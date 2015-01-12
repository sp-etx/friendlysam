# coding=utf-8

from __future__ import division

from friendlysam.parts import Part


class Storage(Part):
    """docstring for Storage"""
    def __init__(self, resource, capacity=None, maxchange=None, **kwargs):
        super(Storage, self).__init__(**kwargs)
        self.resource = resource
        self.capacity = capacity
        self.maxchange = maxchange

        self.volume = self.variable('volume', lb=0., ub=capacity)

        self += self._maxchange_constraints

    def accumulation(self, t):
        return self.volume(t+1) - self.volume(t)

    @property
    def inputs(self):
        return (self.resource,)

    @property
    def outputs(self):
        return (self.resource,)

    def _maxchange_constraints(self, t):
        acc, maxchange = self.accumulation(t), self.maxchange
        if maxchange is None:
            return ()
        return (
            RelConstraint(acc <= maxchange, 'Max net inflow in {}'.format(self)),
            RelConstraint(-maxchange <= acc, 'Max net outflow from {}'.format(self)))