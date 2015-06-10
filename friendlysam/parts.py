# -*- coding: utf-8 -*-

import sys
import logging
logger = logging.getLogger(__name__)

from collections import defaultdict, namedtuple
from itertools import chain

import networkx as nx

import friendlysam as fs
from friendlysam.opt import Constraint, VariableCollection, namespace
from friendlysam.compat import ignored


class InsanityError(Exception): pass


class ConstraintCollection(object):
    """docstring for ConstraintCollection"""
    def __init__(self, owner):
        super().__init__()
        self._owner = owner
        self._constraint_funcs = set()

    _origin_tuple = namedtuple('CallTo', ['func', 'index'])

    def __call__(self, index, **kwargs):
        constraints = set()

        for func in self._constraint_funcs:
            origin = self._origin_tuple(func=func, index=index)
            func_output = func(index)
            try:
                func_output = iter(func_output)
            except TypeError: # not iterable
                func_output = (func_output,)

            for constraint in func_output:
                if isinstance(constraint, fs.Relation):
                    constraint = Constraint(constraint)

                if constraint.origin is None:
                    constraint.origin = origin

                constraints.add(constraint)

        return constraints

    def _add_constraint_func(self, func):
        if not callable(func):
            raise ValueError('constraint funcs must be callable but {} is not'.format(func))
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

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._subclass_counters[type(self)] += 1
        self._constraints = ConstraintCollection(self)
        self._parts = set()
        self.time_unit = 1
        self.name = '{}{:04d}'.format(type(self).__name__, self._subclass_counters[type(self)])
        return self

    def __init__(self, name=None):
        if name is not None:
            self.name = name


    def step_time(self, index, step):
        return index + self.time_unit * step

    def iter_times(self, start, *range_args):
        for step in range(*range_args):
            yield self.step_time(start, step)

    def times(self, start, *range_args):
        return tuple(self.iter_times(start, *range_args))

    def iter_times_between(self, start, end):
        """Only works if time is orderable!!"""
        time = start
        while time <= end:
            yield time
            time = self.step_time(time, 1)

    def times_between(self, start, end):
        """Only works if time is orderable!!"""
        return tuple(self.iter_times_between(start, end))

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, value):
        if value is not self._constraints:
            raise AttributeError('you are not allowed to change this one')

    def __repr__(self):
        if self.name:
            return '<{} at {}: {}>'.format(self.__class__.__name__, hex(id(self)), self)
        else:
            return '<{} at {} (unnamed)>'.format(self.__class__.__name__, hex(id(self)))

    def __str__(self):
        return self.name


    def find(self, name):
        matches = [part for part in self.descendants_and_self if part.name == name]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            raise ValueError("'{}' has no part '{}'".format(repr(self), name))
        elif len(matches) > 1:
            raise ValueError(
                "'{}' has more than one part '{}'".format(repr(self), name))


    def parts(self, depth='inf', include_self=True):
        parts = set()
        depth = float(depth)

        if depth >= 1:
            parts.update(self._parts)

        parts.update(*(subpart.parts(depth=depth - 1, include_self=False) for subpart in parts))

        if include_self:
            parts.add(self)

        return parts

    @property    
    def children(self):
        return self.parts(depth=1, include_self=False)

    @property
    def children_and_self(self):
        return self.parts(depth=1, include_self=True)

    @property
    def descendants(self):
        return self.parts(depth='inf', include_self=False)

    @property
    def descendants_and_self(self):
        return self.parts(depth='inf', include_self=True)


    def add_part(self, p):
        if self in p.descendants_and_self:
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


    def state_variables(self, index):
        msg = "{} has not defined state_variables".format(repr(self))
        raise AttributeError(msg).with_traceback(sys.exc_info()[2])

class Node(Part):
    """docstring for Node"""

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self.consumption = dict()
        self.production = dict()
        self.accumulation = dict()
        self.inflows = defaultdict(set)
        self.outflows = defaultdict(set)
        self._clusters = dict()

        self.constraints += self.balance_constraints

        return self


    def set_cluster(self, cluster):
        res = cluster.resource
        if res in self._clusters:
            if self._clusters[res] is not cluster:
                raise InsanityError('already in another cluster with that resource!')
            else:
                raise InsanityError('this has already been done')
        else:
            self._clusters[res] = cluster

        if not self in cluster.children:
            cluster.add_part(self)


    def unset_cluster(self, cluster):
        res = cluster.resource
        if not (res in self._clusters and self._clusters[res] is cluster):
            raise InsanityError('cannot unset Cluster {} because it is not set'.format(cluster))        
        del self._clusters[res]
        if self in cluster.children:
            cluster.remove_part(self)


    def cluster(self, resource):
        return self._clusters.get(resource, None)


    def _balance_constraint(self, resource, index):
        inflow = fs.Sum(flow(index) for flow in self.inflows[resource])
        outflow = fs.Sum(flow(index) for flow in self.outflows[resource])

        lhs = inflow
        rhs = outflow

        if resource in self.production:
            lhs += self.production[resource](index)

        if resource in self.consumption:
            rhs += self.consumption[resource](index)

        if resource in self.accumulation:
            rhs += self.accumulation[resource](index)

        return Constraint(fs.Eq(lhs, rhs), desc='Balance constraint (resource={})'.format(resource))


    @property
    def resources(self):
        balance_dicts = (self.consumption, self.production, self.accumulation)
        return set(chain(*(d.keys() for d in balance_dicts)))

    def balance_constraints(self, index):
        # Enforce balance constraints for all resources, except those resources
        # which this node is in a cluster for. The cluster instead makes an aggregated
        # balance constraint for those.
        resources_to_be_balanced = (r for r in self.resources if r not in self._clusters)
        return set(self._balance_constraint(r, index) for r in resources_to_be_balanced)


class Cluster(Node):
    """docstring for Cluster"""
    
    def __init__(self, *parts, resource=None, name=None):
        super().__init__(name=name)
        if resource is None:
            msg = '{} is not a valid resource'.format(resource)
            raise ValueError(msg).with_traceback(sys.exc_info()[2])
        self._resource = resource
        self.add_parts(*parts)

        self.consumption[self._resource] = self._get_aggr_func('consumption')
        self.production[self._resource] = self._get_aggr_func('production')
        self.accumulation[self._resource] = self._get_aggr_func('accumulation')


    def _get_aggr_func(self, attr_name):
        # attr_name is the attribute to aggregate, like "production", "consumption", or "accumulation"
        def aggregation(index):
            terms = []
            for part in self.children:
                func_dict = getattr(part, attr_name)
                if self._resource in func_dict:
                    func = func_dict[self._resource]
                    try:
                        term = func(index)
                        terms.append(term)
                    except TypeError as e:
                        if callable(func):
                            raise
                        else:
                            msg = 'The node {} has a non-callable value of {}[{}]: {}'.format(
                                part,
                                attr_name,
                                self._resource,
                                repr(func))

                            raise TypeError(msg) from e

            return fs.Sum(terms)

        return aggregation


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
                raise


    def remove_part(self, part):
        super().remove_part(part)
        if part.cluster(self.resource) is not None:
            part.unset_cluster(self)


    def state_variables(self, t):
        return tuple()


class Storage(Node):
    """docstring for Storage"""
    def __init__(self, resource, capacity=None, maxchange=None, name=None):
        super().__init__(name=None)
        self.resource = resource
        self.capacity = capacity
        self.maxchange = maxchange

        with namespace(self):
            self.volume = VariableCollection('volume', lb=0., ub=capacity)
        self.accumulation[resource] = self._accumulation

        self.constraints += self._maxchange_constraints

    def _accumulation(self, index):
        return self.volume(self.step_time(index, 1)) - self.volume(index)

    def _maxchange_constraints(self, index):
        acc, maxchange = self.accumulation[self.resource](index), self.maxchange
        if maxchange is None:
            return ()
        return (
            RelConstraint(acc <= maxchange, 'Max net inflow'),
            RelConstraint(-maxchange <= acc, 'Max net outflow'))

    def state_variables(self, index):
        return {self.volume(index)}


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
            n1.outflows[self.resource].add(flow)
            n2.inflows[self.resource].add(flow)

        if bidirectional and (n2, n1) not in edges:
            self.connect(n2, n1)

    def state_variables(self, index):
        return tuple(var(index) for var in self._flows.values())
