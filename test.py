import itertools
from friendlysam.parts import Process, Storage, ResourceNetwork
import sympy
import friendlysam.optimization as opt

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

    times = range(30)

    prob = opt.Problem()
    prob.constraints = set(itertools.chain(*[p.constraints(times) for p in parts]))
    prob.objective = sum([conss[i].consumption[RESOURCE](t) for i, t in itertools.product(range(n), times)])
    prob.sense = opt.Sense.maximize
    prob.solve()
    # times = range(29)
    # prob.constraints = set(itertools.chain(*[p.constraints(times) for p in parts]))
    # prob.objective = sum([conss[i].consumption[RESOURCE](t) for i, t in itertools.product(range(n), times)])
    prob.solve()

    #print(prob.solution)
    for part in parts:
        part.replace_symbols(prob.solution, times)

    for t in times:
        print(stors[0].volume(t))

if __name__ == '__main__':
    main()