from itertools import chain
from nose.tools import raises
from friendlysam.model import Node, Storage, Cluster, ResourceNetwork
from friendlysam.optimization import *
from friendlysam.optimization.pyomoengine import PyomoProblem

RESOURCE = 0
ABSTOL = 1e-6

class Producer(Node):
    def __init__(self, indexed=True, **kwargs):
        super(Producer, self).__init__(**kwargs)

        if indexed:
            self.activity = self.variable_collection('activity', lb=0)
            self.production[RESOURCE] = self.activity
        else:
            self.activity = self.variable('activity', lb=0)
            self.production[RESOURCE] = lambda: self.activity


class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, consumption, indexed=True, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        if indexed:
            self.activity = self.variable_collection('activity', lb=0)
            self.consumption[RESOURCE] = self.activity
            self += lambda t: (Constraint(self.consumption[RESOURCE](t) == consumption(t)),)
        else:
            self.activity = self.variable('activity', lb=0)
            self.consumption[RESOURCE] = lambda: self.activity
            self += lambda: (Constraint(self.consumption[RESOURCE]() == consumption),)


def approx(a, b):
    return abs(a-b) <= ABSTOL

def test_indexed():
    times = tuple(range(10))
    consumption = lambda t: t * 1.5
    
    p = Producer(indexed=True)
    s = Storage(RESOURCE, capacity=0)
    c = Consumer(consumption, indexed=True)
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p, s)
    rn.add_edge(s, c)

    prob = PyomoProblem()
    prob.constraints = tuple(chain(*(rn.constraints('inf', t) for t in times)))
    
    prob.objective = Minimize(p.production[RESOURCE](times[0]))
    
    solution = prob.solve()
    for t in times:
        c.activity(t).take_value(solution)
        p.activity(t).take_value(solution)

    for t in times:
        assert approx(p.production[RESOURCE](t).evaluate({}), c.consumption[RESOURCE](t).evaluate({}))

def test_not_indexed():
    consumption = 3
    
    p = Producer(indexed=False)
    c = Consumer(consumption, indexed=False)
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p, c)

    prob = PyomoProblem()
    prob.constraints = rn.constraints('inf')
    
    prob.objective = Minimize(p.production[RESOURCE]())
    
    solution = prob.solve()
    c.activity.take_value(solution)
    p.activity.take_value(solution)

    assert approx(p.production[RESOURCE]().evaluate(), consumption)
    assert approx(c.consumption[RESOURCE]().evaluate(), consumption)
    
@raises(TypeError)
def test_not_indexed_w_storage():
    s = Storage(RESOURCE)
    s.constraints('inf')

if __name__ == '__main__':
    test_indexed()