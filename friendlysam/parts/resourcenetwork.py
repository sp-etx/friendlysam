# coding=utf-8

from __future__ import division

import itertools

import numpy as np
import networkx as nx

from optimization import Variable
from friendlysam.components import Element, Process, Cluster, Storage

class ResourceNetwork(Element):
    """docstring for ResourceNetwork"""
    def __init__(self, resource, **kwargs):
        super(ResourceNetwork, self).__init__(**kwargs)
        self.resource = resource
        self._graph = nx.DiGraph()

        self.flows = dict()
        self._add_opt_setup(self._setup_vars)
        self._add_opt_setup(self._set_all_node_constraints)

    @property
    def nodes(self):
        return self._graph.nodes()

    @property
    def edges(self):
        return self._graph.edges()

    def add_node(self, n):
        self._graph.add_node(n)
        self.add_element(n)

    def add_nodes(self, *nodes):
        map(self.add_node, nodes)

    def add_edge(self, n1, n2, bidirectional=False):
        edges = self._graph.edges()
        nodes = self._graph.nodes()
            
        if not (n1 in nodes and n2 in nodes):
            raise ValueError(
                'At least one of the nodes is not in the network.')
        
        if not (n1, n2) in edges:
            self._graph.add_edge(n1, n2)
            name = 'Flow (' + str(n1) + ', ' + str(n2) + ')'
            self.flows[(n1, n2)] = Variable()

        if bidirectional and (n2, n1) not in edges:
            self.add_edge(n2, n1)

    def _setup_vars(self, opt):
        for f in self.flows.values():
            f.create_in(opt)

    def fix_flows(self, opt, t):
        for flow in self.flows.values():
            flow.fix_from(opt, t)

    def _save_flows(self, group):
        for edge in self.flows:
            flow = self.flows[edge]
            times = flow.fixed_indices
            subgroup = group.create_group('flows/' + repr(edge))
            subgroup.attrs['from'] = repr(edge[0])
            subgroup.attrs['to'] = repr(edge[1])
            subgroup.create_dataset('time', data=np.array(times))
            subgroup.create_dataset('flow',
                data=np.array([flow.get_expr(None, t) for t in times]))

    def _get_inflow_expr(self, opt, node, t):
        in_edges = self._graph.in_edges(nbunch=[node])
        return sum([self.flows[e].get_expr(opt, t) for e in in_edges])

    def _get_outflow_expr(self, opt, node, t):
        out_edges = self._graph.out_edges(nbunch=[node])
        return sum([self.flows[e].get_expr(opt, t) for e in out_edges])

    def _set_all_node_constraints(self, opt):
        node_time_pairs = itertools.product(self.nodes, opt.times)
        constraints = list()
        for (n, t) in node_time_pairs:
            self._set_node_constraint(opt, n, t)

    def _set_node_constraint(self, opt, node, t):
        inflow = self._get_inflow_expr(opt, node, t)
        outflow = self._get_outflow_expr(opt, node, t)

        if isinstance(node, Cluster):
            net_cons = node.get_net_consumption(self.resource, opt, t)
            opt.add_constraint(inflow == outflow + net_cons)

        elif isinstance(node, Storage):
            if node.resource is self.resource:
                accumulation = node.get_accumulation(opt, t)
                opt.add_constraint(inflow == outflow + accumulation)
        
        elif isinstance(node, Process):
            if self.resource in node.inputs:
                consumption = node.consumption[self.resource](opt, t)
            else:
                consumption = 0

            if self.resource in node.outputs:
                production = node.production[self.resource](opt, t)
            else:
                production = 0

            opt.add_constraint(inflow + production == outflow + consumption)

        else:
            raise RuntimeError('node is not supported: ' + repr(node))
