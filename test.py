import itertools
from friendlysam.parts import Model, Part, Process, Storage, ResourceNetwork
import sympy
from friendlysam.optimization.core import *
from friendlysam.optimization.pyomoengine import PyomoEngine

RESOURCE = 0

def main():
    class Producer(Process):
        """docstring for Producer"""
        def __init__(self, a):
            super(Producer, self).__init__()

            activity = self.variable('activity', lb=0, ub=1)

            self.production[RESOURCE] = lambda t: activity(t) * a


    class Consumer(Process):
        """docstring for Consumer"""
        def __init__(self, b):
            super(Consumer, self).__init__()
            self.b = b
            
            activity = self.variable('activity', lb=0, ub=1)
            self.consumption[RESOURCE] = lambda t: activity(t) * b


    engine = PyomoEngine()
    m = Model()
    m.engine = engine

    n = 10
    prods = [Producer(10+i) for i in range(n)]
    conss = [Consumer(15-i) for i in range(n)]
    stors = [Storage(RESOURCE, capacity=10) for i in range(n)]

    netw = ResourceNetwork(RESOURCE)
    netw.add_nodes(*prods)
    netw.add_nodes(*conss)
    netw.add_nodes(*stors)

    for i in range(n):
        netw.add_edge(prods[i], stors[i])
        netw.add_edge(stors[i], conss[i])

    for i in range(n-1):
        netw.add_edge(stors[i], stors[i+1])


    parts = prods + conss + stors + [netw]
    m.add_part(netw)

    times = range(30)

    prob = engine.problem()
    prob.constraints = set(itertools.chain(*[p.constraints(times) for p in parts]))
    prob.objective = Maximize(sum([conss[i].consumption[RESOURCE](t) for i, t in itertools.product(range(n), times)]))
    print(prob.solve())
    
if __name__ == '__main__':
    main()