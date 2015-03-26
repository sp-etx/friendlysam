from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import super
from future import standard_library
standard_library.install_aliases()
import itertools
from friendlysam.model import Node, Storage, Cluster, ResourceNetwork
from friendlysam.optimization import *
from friendlysam.optimization.pyomoengine import PyomoProblem

RESOURCE = 0

def main():
    class Producer(Node):
        """docstring for Producer"""
        def __init__(self, param, **kwargs):
            super(Producer, self).__init__(**kwargs)

            self.activity = self.variable_collection('activity', lb=0)

            self.production[RESOURCE] = lambda t: self.activity[t]

            self.cost = lambda t: param(t) * self.activity[t]


    class Consumer(Node):
        """docstring for Consumer"""
        def __init__(self, param, **kwargs):
            super(Consumer, self).__init__(**kwargs)
            
            self.activity = self.variable_collection('activity', lb=0)
            self.consumption[RESOURCE] = lambda t: self.activity[t]
            cons = self.consumption[RESOURCE]

            self += lambda t: (Constraint(cons(t) >= param(t)),)


    times = range(10)

    p = Producer(lambda t: t ** 2, name='Producer')
    c = Consumer(lambda t: t, name='Consumer')
    s = Storage(RESOURCE, capacity=15, name='Storage')
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p, s)
    rn.add_edge(s, c)

    prob = PyomoProblem()
    prob.constraints = rn.constraints('inf', *times)

    
    prob.objective = Minimize(sum(p.cost(t) for t in times))
    solution = prob.solve()
    for t in times:
        c.activity[t].take_value(solution)
        p.activity[t].take_value(solution)
        s.volume[t].take_value(solution)
        print(t, p.activity[t].value, s.volume[t].value, c.activity[t].value)


    times = range(10)

    p1 = Producer(lambda t: 0.5 * (t + 1) ** 2, name='Producer 1')
    p2 = Producer(lambda t: (t + 1) ** 2, name='Producer 2')
    c = Consumer(lambda t: t, name='Consumer')
    s = Storage(RESOURCE, capacity=10, name='Storage')
    cluster = Cluster(p2, c, s)
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p1, cluster)
    rn += lambda t: (Constraint(rn.flows[(p1, cluster)][t] <= 3.3),)


    s.volume[0].value = 1.3
    print(s.volume[0])

    prob = PyomoProblem()
    prob.constraints = rn.constraints('inf', *times)

    
    prob.objective = Minimize(sum(p1.cost(t) + p2.cost(t) for t in times))
    solution = prob.solve()

    
    for t in times:
        c.activity[t].take_value(solution)
        p1.activity[t].take_value(solution)
        p2.activity[t].take_value(solution)
        #s.volume[t].take_value(solution)
        print(t, p1.activity[t].value, p2.activity[t].value, 
            #s.volume[t].value, 
            c.activity[t].value)
    
if __name__ == '__main__':
    main()
