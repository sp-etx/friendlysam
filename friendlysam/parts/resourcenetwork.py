# coding=utf-8

from __future__ import division

import itertools

import sympy
import networkx as nx

from friendlysam.parts import Part, Process, Cluster, Storage

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

    def _node_balance_constraint(self, node, t):
        in_edges = self._graph.in_edges(nbunch=[node])
        out_edges = self._graph.out_edges(nbunch=[node])
        inflow = sum([self.flows[e](t) for e in in_edges])
        outflow = sum([self.flows[e](t) for e in out_edges])

        desc = 'Balance constraint ({}) for {}'

        if isinstance(node, Cluster):
            lhs = inflow
            rhs = outflow + node.net_consumption(self.resource, t)

        elif isinstance(node, Storage):
            if not node.resource is self.resource:
                return None
            else:
                lhs = inflow
                rhs = outflow + node.accumulation(t)
        
        elif isinstance(node, Process):
            if self.resource in node.inputs:
                consumption = node.consumption[self.resource](t)
            else:
                consumption = 0

            if self.resource in node.outputs:
                production = node.production[self.resource](t)
            else:
                production = 0

            lhs = inflow + production
            rhs = outflow + consumption

        else:
            raise RuntimeError('node is not supported: ' + repr(node))

        return Constraint(lhs == rhs, desc.format(self.resource, node))
        

    def _all_balance_constraints(self, idx):
        constraints = set(self._node_balance_constraint(node, idx) for node in self.nodes)
        constraints.discard(None)
        return constraints