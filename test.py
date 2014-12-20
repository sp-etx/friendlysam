from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt
from friendlysam.optimization.solvers.gurobi import GurobiSolver

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()
        #v = self.register_var(name='aoeu', lb=1, ub=2, indexed=True)

        # x, y, z = [self.variable(str(i)) for i in range(3)]
        # self.constrain(opt.make_constraints((x,y,z), sos1=True, lb=0, ub=3))

        v = self.variable_collection('arne', ub=3)
        self.v = v
        self.production[1] = lambda t: v[t] * a
        self.constrain(lambda t: v[t] * 1.1 <= v[t-1])
        # self.consumption[2] = 1.1*x + 1.10000000000001*y + 0.9*z

        #self.constrain(lambda t: v[t] <= 3)
        #self.constrain(lambda t: sympy.Eq(v[t], 1.5))



x = ProcessA(20)

p = opt.Problem()

times = range(40)
p.constraints = x.constraints(times)
p.sense = opt.Sense.maximize


p.objective = sum([x.production[1](t) for t in times])
p.solver = GurobiSolver()
p.solve()
for t in times:
    print(p._solution[x.v[t]])