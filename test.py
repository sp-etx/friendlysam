import itertools
from friendlysam.model import Model, Node, Storage, Cluster, ResourceNetwork
from friendlysam.optimization.core import *
from friendlysam.optimization.pyomoengine import PyomoEngine

RESOURCE = 0

def main():
    class Producer(Node):
        """docstring for Producer"""
        def __init__(self, param, **kwargs):
            super(Producer, self).__init__(**kwargs)

            self.activity = self.variable('activity', lb=0)

            self.production[RESOURCE] = lambda t: self.activity(t)

            self.cost = lambda t: param(t) * self.activity(t)


    class Consumer(Node):
        """docstring for Consumer"""
        def __init__(self, param, **kwargs):
            super(Consumer, self).__init__(**kwargs)
            
            self.activity = self.variable('activity', lb=0)
            self.consumption[RESOURCE] = lambda t: self.activity(t)
            cons = self.consumption[RESOURCE]

            self += lambda t: (Constraint(cons(t) >= param(t)),)


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
    prob.constraints = m.constraints('inf', *times)

    
    prob.objective = Minimize(sum(p.cost(t) for t in times))
    solution = prob.solve()
    for t in times:
        c.activity.take_value(solution, t)
        p.activity.take_value(solution, t)
        s.volume.take_value(solution, t)
        print(t, p.activity(t), s.volume(t), c.activity(t))


    engine = PyomoEngine()
    m = Model()
    m.engine = engine

    times = range(10)

    p1 = Producer(lambda t: 0.5 * (t + 1) ** 2, name='Producer 1')
    p2 = Producer(lambda t: (t + 1) ** 2, name='Producer 2')
    c = Consumer(lambda t: t, name='Consumer')
    s = Storage(RESOURCE, capacity=10, name='Storage')
    cluster = Cluster(p2, c, s)
    rn = ResourceNetwork(RESOURCE)
    rn.add_edge(p1, cluster)
    rn += lambda t: (Constraint(rn.flows[(p1, cluster)](t) <= 3.3),)

    m.add_part(rn)

    s.volume[0] = 1.3
    print(s.volume(0))

    prob = engine.problem()
    prob.constraints = m.constraints('inf', *times)

    
    prob.objective = Minimize(sum(p1.cost(t) + p2.cost(t) for t in times))
    solution = prob.solve()

    
    for t in times:
        c.activity.take_value(solution, t)
        p1.activity.take_value(solution, t)
        p2.activity.take_value(solution, t)
        s.volume.take_value(solution, t)
        print(t, p1.activity(t), p2.activity(t), s.volume(t), c.activity(t))
    
if __name__ == '__main__':
    main()