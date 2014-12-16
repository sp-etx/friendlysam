# coding=utf-8

from __future__ import division

from friendlysam.parts import Part, Process, Storage


class Cluster(Part):
    """docstring for Cluster"""
    def __init__(self, *parts, **kwargs):
        super(Cluster, self).__init__(**kwargs)
        self.add_parts(*parts)

    def get_net_consumption(self, res, opt, t):
        terms = list()
        for e in self.parts:
            if isinstance(e, Cluster):
                terms.append(e.get_net_consumption(res, opt, t))
            elif isinstance(e, Storage):
                if e.resource is res:
                    terms.append(e.get_accumulation(opt, t))
            elif isinstance(e, Process):
                if res in e.inputs:
                    terms.append(e.consumption[res](opt, t))
                if res in e.outputs:
                    terms.append(-e.production[res](opt, t))
            else:
                raise RuntimeError('part is not supported: ' + repr(e))

        return sum(terms)
