import itertools
from friendlysam.parts import Model, Part, Process, Storage, ResourceNetwork
import sympy
from friendlysam.optimization.core import *
from friendlysam.optimization.pyomoengine import PyomoEngine

RESOURCE = 0

def main():
    class Producer(Process):
        """docstring for Producer"""
        def __init__(self, param, **kwargs):
            super(Producer, self).__init__(**kwargs)

            self.activity = self.variable('activity', lb=0)

            self.production[RESOURCE] = lambda t: self.activity(t)

            self.cost = lambda t: param(t) * self.activity(t)


    class Consumer(Process):
        """docstring for Consumer"""
        def __init__(self, param, **kwargs):
            super(Consumer, self).__init__(**kwargs)
            
            self.activity = self.variable('activity', lb=0)
            self.consumption[RESOURCE] = lambda t: self.activity(t)
            cons = self.consumption[RESOURCE]

            self += lambda t: (Constraint(cons(t) + cons(t+1) >= param(t)),)


    engine = PyomoEngine()
    m = Model()
    m.engine = engine

    times = range(10)

    p = Producer(lambda t: t ** 2, name='Producer')
    c = Consumer(lambda t: t, name='Consumer')
    s = Storage(RESOURCE, capacity=15, name='Storage')
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p, s)
    rn.add_edge(s, c)
    m.add_part(rn)

    prob = engine.problem()
    prob.constraints = m.constraints(times)

    
    prob.objective = Minimize(sum(p.cost(t) for t in times))
    solution = prob.solve()
    for t in times:
        c.activity.take_value(solution, t)
        p.activity.take_value(solution, t)
        s.volume.take_value(solution, t)
        print(t, p.activity(t), s.volume(t), c.activity(t))
    
if __name__ == '__main__':
    main()