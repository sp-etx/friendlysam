# coding=utf-8

from __future__ import division

import itertools

import sympy
import networkx as nx

from friendlysam.parts import Part

from friendlysam.optimization.core import Constraint

class ResourceNetwork(Part):
    """docstring for ResourceNetwork"""
    def __init__(self, resource, **kwargs):
        super(ResourceNetwork, self).__init__(**kwargs)
        self.resource = resource
        self._graph = nx.DiGraph()

        self.flows = dict()

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
            self.flows[(n1, n2)] = self.variable(name, lb=0)

        if bidirectional and (n2, n1) not in edges:
            self.add_edge(n2, n1)

    def _node_balance_constraint(self, node, index):
        in_edges = self._graph.in_edges(nbunch=[node])
        out_edges = self._graph.out_edges(nbunch=[node])
        inflow = sum([self.flows[edge](index) for edge in in_edges])
        outflow = sum([self.flows[edge](index) for edge in out_edges])

        desc = 'Balance constraint ({}) for {}'

        resource = self.resource

        lhs = inflow
        rhs = outflow

        if resource in node.production:
            lhs += node.production[resource](index)

        if resource in node.consumption:
            rhs += node.consumption[resource](index)

        if resource in node.accumulation:
            rhs += node.accumulation[resource](index)

        return Constraint(lhs == rhs, desc.format(self.resource, node))
        

    def _all_balance_constraints(self, index=None):
        constraints = set(self._node_balance_constraint(node, index) for node in self.nodes)
        return constraints