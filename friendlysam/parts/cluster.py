# coding=utf-8

from __future__ import division

from friendlysam.parts import Part, Process, Storage


class Cluster(Part):
    """docstring for Cluster"""
    def __init__(self, *parts, **kwargs):
        super(Cluster, self).__init__(**kwargs)
        self.add_parts(*parts)

    def net_consumption(self, res, t):
        terms = list()
        for part in self.parts(recursion_limit=0):
            if isinstance(part, Cluster):
                terms.append(part.net_consumption(res, t))
            elif isinstance(e, Storage):
                if part.resource is res:
                    terms.append(part.accumulation(t))
            elif isinstance(part, Process):
                if res in e.inputs:
                    terms.append(part.consumption[res](t))
                if res in e.outputs:
                    terms.append(-part.production[res](t))
            else:
                raise RuntimeError('net consumption is not supported for {}'.format(part))

        return sum(terms)
