# coding=utf-8

from __future__ import division

from friendlysam.parts import Process


class Storage(Process):
    """docstring for Storage"""
    def __init__(self, resource, capacity=None, maxchange=None, **kwargs):
        super(Storage, self).__init__(**kwargs)
        self.resource = resource
        self.capacity = capacity
        self.maxchange = maxchange

        self.volume = self.variable('volume', lb=0., ub=capacity)
        self.accumulation[resource] = lambda t: self.volume(t+1) - self.volume(t)

        self += self._maxchange_constraints

    def _maxchange_constraints(self, t):
        acc, maxchange = self.accumulation[self.resource](t), self.maxchange
        if maxchange is None:
            return ()
        return (
            RelConstraint(acc <= maxchange, 'Max net inflow in {}'.format(self)),
            RelConstraint(-maxchange <= acc, 'Max net outflow from {}'.format(self)))