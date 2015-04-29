# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from collections import defaultdict
from itertools import chain

import networkx as nx

import friendlysam as fs
from friendlysam.optimization import Constraint, VariableCollection, namespace
from friendlysam.compat import ignored


class InsanityError(Exception): pass


class ConstraintCollection(object):
    """docstring for ConstraintCollection"""
    def __init__(self, owner):
        super().__init__()
        self._owner = owner
        self._constraint_funcs = set()

    def _prepare(self, constraint, origin_desc):
        if isinstance(constraint, fs.Relation):
            constraint = Constraint(constraint)

        if not isinstance(constraint, Constraint):
            raise ValueError('cannot handle constraint {}'.format(constraint))

        if constraint.origin is None:
            constraint.origin = '{}, {}'.format(self._owner, origin_desc)

        return constraint

    def _func_description(self, func, *indices):
        func_desc = func.__name__
        if len(indices) == 1:
            return '{}({})'.format(func_desc, indices[0])
        else:
            return '{}{}'.format(func_desc, indices)

    def __call__(self, *indices, **kwargs):
        depth = kwargs.get('depth', 'inf')

        constraints = set()

        for func in self._constraint_funcs:
            func_output = func(*indices)
            try:
                func_output = iter(func_output)
            except TypeError: # not iterable
                func_output = (func_output,)

            func_desc = self._func_description(func, *indices)
            constraints.update(self._prepare(item, func_desc) for item in func_output)

        # Subtract 1 from depth. This means we get only this part's constraints
        # if depth=0, etc. It is probably the expected behavior.
        depth = float(depth) - 1
        subparts = self._owner.parts(depth=depth)
        return constraints.union(*[p.constraints(*indices, depth=0) for p in subparts])

    def _add_constraint_func(self, func):
        if not callable(func):
            raise RuntimeError('constraint funcs must be callable but {} is not'.format(func))
        self._constraint_funcs.add(func)

    def add(self, addition):
        try:
            for func in addition:
                self._add_constraint_func(func)
        except TypeError:
            self._add_constraint_func(addition)

    def __iadd__(self, addition):
        self.add(addition)
        return self


class Part(object):
    """docstring for Part"""

    _subclass_counters = defaultdict(int)

    def __init__(self, name=None):
        self._constraints = ConstraintCollection(self)
        self._model = None
        self._subclass_counters[type(self)] += 1
        
        if name is None:
            name = '{}{:04d}'.format(type(self).__name__, self._subclass_counters[type(self)])
        self.name = name

        self._parts = set()

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, value):
        if value is not self._constraints:
            raise AttributeError('you are not allowed to change this one')


    def __str__(self):
        return self.name

    def __getitem__(self, name):
        matches = [part for part in self.parts() if part.name == name]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise KeyError("'{}' has no part '{}'".format(self, name))
        elif len(matches) > 1:
            raise KeyError(
                "'{}' has more than one part '{}'".format(self, name))


    def parts(self, depth='inf'):
        parts = set()
        depth = float(depth)
        if depth >= 0:
            parts.update(self._parts)

        all_parts = parts.union(*(subpart.parts(depth - 1) for subpart in parts))

        return all_parts

    def add_part(self, p):
        if self in p.parts('inf'):
            raise InsanityError(
                ('cannot add {} to {} because it would '
                'generate a cyclic relationship').format(p, self))

        self._parts.add(p)


    def remove_part(self, p):
        with ignored(KeyError):
            self._parts.remove(p)


    def add_parts(self, *parts):
        for p in parts:
            self.add_part(p)

class Node(Part):
    """docstring for Node"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumption = dict()
        self.production = dict()
        self.accumulation = dict()

        self._inflows = set()
        self._outflows = set()

        self._clusters = dict()

        self.constraints += self._all_balance_constraints


    @property
    def inflows(self):
        return self._inflows


    @property
    def outflows(self):
        return self._outflows


    def set_cluster(self, cluster):
        res = cluster.resource
        if res in self._clusters:
            if self._clusters[res] is not cluster:
                raise InsanityError('already in another cluster with that resource!')
            else:
                raise InsanityError('this has already been done')
        else:
            self._clusters[res] = cluster

        if not self in cluster.parts(0):
            cluster.add_part(self)


    def unset_cluster(self, cluster):
        res = cluster.resource
        if not (res in self._clusters and self._clusters[res] is cluster):
            raise InsanityError('cannot unset Cluster {} because it is not set'.format(cluster))        
        del self._clusters[res]
        if self in cluster.parts(0):
            cluster.remove_part(self)


    def cluster(self, resource):
        return self._clusters.get(resource, None)


    def _balance_constraint(self, resource, *indices):
        inflow = sum(flow(*indices) for flow in self._inflows)
        outflow = sum(flow(*indices) for flow in self._outflows)

        lhs = inflow
        rhs = outflow

        if resource in self.production:
            lhs += self.production[resource](*indices)

        if resource in self.consumption:
            rhs += self.consumption[resource](*indices)

        if resource in self.accumulation:
            rhs += self.accumulation[resource](*indices)

        return Constraint(lhs == rhs, desc='Balance constraint (resource={})'.format(resource))
        

    def _all_balance_constraints(self, *indices):
        balance_dicts = (self.consumption, self.production, self.accumulation)
        resources = set(chain(*(d.keys() for d in balance_dicts)))
        resources = list(r for r in resources if r not in self._clusters)
        return set(self._balance_constraint(r, *indices) for r in resources)


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


class ClusterDict(object):
    """docstring for ClusterDict"""
    def __init__(self, owner, attr_name):
        self._owner = owner
        self._attr_name = attr_name
        self._dict = {}

    def __contains__(self, resource):
        for part in self._owner.parts(depth=0):
            if hasattr(part, self._attr_name) and resource in getattr(part, self._attr_name):
                return True

    def __getitem__(self, resource):
        if not resource in self._dict:
            self._dict[resource] = _get_aggr_func(self._owner, self._attr_name, resource)
        return self._dict[resource]


    def keys(self):
        keys = set()
        for part in self._owner.parts(depth=0):
            with ignored(AttributeError):
                keys.update(getattr(part, self._attr_name).keys())
        return keys


class Cluster(Node):
    """docstring for Cluster"""
    
    def __init__(self, *parts, **kwargs):
        self._resource = kwargs.pop('resource')
        super().__init__(**kwargs)
        self.add_parts(*parts)

        self.consumption = ClusterDict(self, 'consumption')
        self.production = ClusterDict(self, 'production')
        self.accumulation = ClusterDict(self, 'accumulation')


    @property
    def resource(self):
        return self._resource


    def add_part(self, part):
        super().add_part(part)
        if not part.cluster(self.resource) is self:
            try:
                part.set_cluster(self) # May raise an exception.
            except InsanityError as e:
                super().remove_part(part) # Roll back on exception.
                raise e


    def remove_part(self, part):
        super().remove_part(part)
        if part.cluster(self.resource) is not None:
            part.unset_cluster(self)


    def cost(self, t):
        return 0

    def state_variables(self, t):
        return tuple()


class Storage(Node):
    """docstring for Storage"""
    def __init__(self, resource, capacity=None, maxchange=None, **kwargs):
        super().__init__(**kwargs)
        self.resource = resource
        self.capacity = capacity
        self.maxchange = maxchange

        with namespace(self):
            self.volume = VariableCollection('volume', lb=0., ub=capacity)
        self.accumulation[resource] = self._accumulation

        self.constraints += self._maxchange_constraints

    def _accumulation(self, *indices):
        if len(indices) == 0:
            raise InsanityError('Storage accumulation needs at least one index. '
                'The first index should represent time.')
        t, other_indices = indices[0], indices[1:]
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
            RelConstraint(acc <= maxchange, 'Max net inflow'),
            RelConstraint(-maxchange <= acc, 'Max net outflow'))


class FlowNetwork(Part):
    """docstring for FlowNetwork"""
    def __init__(self, resource, **kwargs):
        super().__init__(**kwargs)
        self.resource = resource
        self._graph = nx.DiGraph()

        self._flows = dict()

    @property
    def nodes(self):
        return self._graph.nodes()

    @property
    def edges(self):
        return self._graph.edges()

    def remove_part(self, part):
        raise NotImplementedError('need to also remove edges then')

    def connect(self, n1, n2, bidirectional=False):
        edges = self._graph.edges()
            
        if not (n1, n2) in edges:
            self.add_parts(n1, n2)
            self._graph.add_edge(n1, n2)
            name = 'flow ({} --> {})'.format(n1, n2)
            with namespace(self):
                flow = VariableCollection(name, lb=0)
            self._flows[(n1, n2)] = flow
            n1.outflows.add(flow)
            n2.inflows.add(flow)

        if bidirectional and (n2, n1) not in edges:
            self.connect(n2, n1)

    def cost(self, t):
        return 0

    def state_variables(self, *indices):
        return tuple(var(*indices) for var in self._flows)
