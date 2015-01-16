# coding=utf-8

from __future__ import division

from friendlysam.parts import Part

class Cluster(Part):
    """docstring for Cluster"""
    
    class ClusterDict(object):
        """docstring for ClusterDict"""
        def __init__(self, owner, attr_name):
            super(Cluster.ClusterDict, self).__init__()
            self._owner = owner
            self._attr_name = attr_name
            self._dict = {}

        def __contains__(self, resource):
            for part in self._owner.parts(0):
                if hasattr(part, self._attr_name) and resource in getattr(part, self._attr_name):
                    return True

        def __getitem__(self, resource):
            if not resource in self._dict:
                self._dict[resource] = self._make_func(resource)
            return self._dict[resource]

        def _make_func(self, resource):
            def func(index):
                terms = []
                for part in self._owner.parts(0):
                    attr = getattr(part, self._attr_name)
                    if resource in attr:
                        terms.append(attr[resource](index))
                return sum(terms)
            return func

    def __init__(self, *parts, **kwargs):
        super(Cluster, self).__init__(**kwargs)
        self.add_parts(*parts)

        self.consumption = Cluster.ClusterDict(self, 'consumption')
        self.production = Cluster.ClusterDict(self, 'production')
        self.accumulation = Cluster.ClusterDict(self, 'accumulation')
