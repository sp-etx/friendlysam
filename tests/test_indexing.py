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
            self.production[RESOURCE] = lambda t: self.activity[t]
        else:
            self.activity = self.variable('activity', lb=0)
            self.production[RESOURCE] = lambda: self.activity


class Consumer(Node):
    """docstring for Consumer"""
    def __init__(self, consumption, indexed=True, **kwargs):
        super(Consumer, self).__init__(**kwargs)
        
        if indexed:
            self.activity = self.variable_collection('activity', lb=0)
            self.consumption[RESOURCE] = lambda t: self.activity[t]
            self += lambda t: (Constraint(self.consumption[RESOURCE](t) == consumption(t)),)
        else:
            self.activity = self.variable('activity', lb=0)
            self.consumption[RESOURCE] = lambda: self.activity
            self += lambda: (Constraint(self.consumption == consumption),)


def approx(a, b):
    return abs(a-b) <= ABSTOL


def test_indexed():
    times = tuple(range(10))
    consumption = lambda t: t * 1.5
    
    p = Producer(indexed=True)
    c = Consumer(consumption, indexed=True)
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p, c)

    prob = PyomoProblem()
    prob.constraints = rn.constraints('inf', *times)
    
    prob.objective = Minimize(p.production[RESOURCE](times[0]))
    
    solution = prob.solve()
    for t in times:
        c.activity[t].take_value(solution)
        p.activity[t].take_value(solution)

    for t in times:
        assert approx(p.production[RESOURCE](t).evaluate({}), c.consumption[RESOURCE](t).evaluate({}))


if __name__ == '__main__':
    test_indexed()