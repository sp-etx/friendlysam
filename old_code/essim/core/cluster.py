# coding=utf-8

from __future__ import division

from element import Element
from process import Process
from storage import Storage


class Cluster(Element):
    """docstring for Cluster"""
    def __init__(self, *elements, **kwargs):
        super(Cluster, self).__init__(**kwargs)
        self.add_elements(*elements)

    def get_net_consumption(self, res, opt, t):
        terms = list()
        for e in self.elements:
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
                raise RuntimeError('element is not supported: ' + repr(e))

        return sum(terms)
