# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import map
from builtins import dict
from builtins import super
from future import standard_library
standard_library.install_aliases()

import networkx as nx

from friendlysam.optimization import Constraint
from friendlysam.model import Part

class Node(Part):
    """docstring for Node"""
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.consumption = dict()
        self.production = dict()
        self.accumulation = dict()


def _get_aggr_func(owner, attr_name, resource):
    def aggregation(*indices):

        terms = []
        for part in owner.parts(0):
            func_dict = getattr(part, attr_name)
            if resource in func_dict:
                func = func_dict[resource]
                term = func(*indices)
                terms.append(term)

        return sum(terms)

    return aggregation

class Cluster(Node):
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
                self._dict[resource] = _get_aggr_func(self._owner, self._attr_name, resource)
            return self._dict[resource]


    def __init__(self, *parts, **kwargs):
        super(Cluster, self).__init__(**kwargs)
        self.add_parts(*parts)

        self.consumption = Cluster.ClusterDict(self, 'consumption')
        self.production = Cluster.ClusterDict(self, 'production')
        self.accumulation = Cluster.ClusterDict(self, 'accumulation')


class Storage(Node):
    """docstring for Storage"""
    def __init__(self, resource, capacity=None, maxchange=None, **kwargs):
        super(Storage, self).__init__(**kwargs)
        self.resource = resource
        self.capacity = capacity
        self.maxchange = maxchange

        self.volume = self.variable_collection('volume', lb=0., ub=capacity)
        self.accumulation[resource] = self._accumulation

        self += self._maxchange_constraints

    def _accumulation(self, t, *other_indices):
        if len(other_indices) > 0:
            next_index = (t+1,) + other_indices
            this_index = (t,) + other_indices
        else:
            next_index = t+1
            this_index = t
        return self.volume(next_index) - self.volume(this_index)

    def _maxchange_constraints(self, *indices):
        acc, maxchange = self.accumulation[self.resource](*indices), self.maxchange
        if maxchange is None:
            return ()
        return (
            RelConstraint(acc <= maxchange, 'Max net inflow in {}'.format(self)),
            RelConstraint(-maxchange <= acc, 'Max net outflow from {}'.format(self)))


class ResourceNetwork(Node):
    """docstring for ResourceNetwork"""
    def __init__(self, resource, **kwargs):
        super(ResourceNetwork, self).__init__(**kwargs)
        self.resource = resource
        self._graph = nx.DiGraph()

        self.flows = dict()

        self.consumption[resource] = _get_aggr_func(self, 'consumption', resource)
        self.production[resource] = _get_aggr_func(self, 'production', resource)
        self.accumulation[resource] = _get_aggr_func(self, 'accumulation', resource)

        self += self._all_balance_constraints

    @property
    def nodes(self):
        return self._graph.nodes()

    @property
    def edges(self):
        return self._graph.edges()

    def add_node(self, n):
        self._graph.add_node(n)
        self.add_part(n)

    def add_nodes(self, *nodes):
        map(self.add_node, nodes)

    def add_edge(self, n1, n2, bidirectional=False):
        edges = self._graph.edges()
        nodes = self._graph.nodes()

        if not n1 in nodes:
            self.add_part(n1)

        if not n2 in nodes:
            self.add_part(n2)
            
        if not (n1, n2) in edges:
            self._graph.add_edge(n1, n2)
            name = 'flow ({} --> {})'.format(n1, n2)
            self.flows[(n1, n2)] = self.variable_collection(name, lb=0)

        if bidirectional and (n2, n1) not in edges:
            self.add_edge(n2, n1)

    def _node_balance_constraint(self, node, *indices):

        in_edges = self._graph.in_edges(nbunch=[node])
        out_edges = self._graph.out_edges(nbunch=[node])
        inflow = sum([self.flows[edge](*indices) for edge in in_edges])
        outflow = sum([self.flows[edge](*indices) for edge in out_edges])

        desc = 'Balance constraint ({}) for {}'

        resource = self.resource

        lhs = inflow
        rhs = outflow

        if resource in node.production:
            lhs += node.production[resource](*indices)

        if resource in node.consumption:
            rhs += node.consumption[resource](*indices)

        if resource in node.accumulation:
            rhs += node.accumulation[resource](*indices)

        return Constraint(lhs == rhs, desc.format(self.resource, node))
        

    def _all_balance_constraints(self, *indices):
        constraints = set(self._node_balance_constraint(node, *indices) for node in self.nodes)
        return constraints