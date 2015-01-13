import itertools
from friendlysam.parts import Process, Storage, ResourceNetwork
import sympy
import friendlysam.optimization as opt
from friendlysam.optimization.solvers.pyomo4 import PyomoSolver
#from friendlysam.optimization.solvers.gurobi import GurobiSolver

RESOURCE = 0
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


prod = Producer(10)
cons = Consumer(15)
stor = Storage(RESOURCE, capacity=10)

netw = ResourceNetwork(RESOURCE)
netw.add_nodes(prod, cons, stor)
netw.add_edge(prod, stor)
netw.add_edge(stor, cons)

parts = (prod, cons, stor, netw)

times = range(5)

prob = opt.Problem()
prob.constraints = set(itertools.chain(*[p.constraints(times) for p in parts]))

for c in prob.constraints:
    print(c)


prob.objective = sum([cons.consumption[RESOURCE](t) for t in times])
prob.sense = opt.Sense.maximize
prob.solver = PyomoSolver()
prob.solve()

print(prob.solution)
for part in parts:
    part.replace_symbols(prob.solution, times)

for t in times:
    print(stor.volume(t))

