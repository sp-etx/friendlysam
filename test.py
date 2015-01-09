from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt
from friendlysam.optimization import Variable, PiecewiseAffineArg
#from friendlysam.optimization.solvers.pyomo import PyomoSolver

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()

        self += Variable('activity', lb=0, ub=1)
        self += PiecewiseAffineArg('y', [0, .4, .6, 1])

        self.production[1] = lambda t: self.activity + self.y



x = ProcessA(20)

p = opt.Problem()

times = range(5)
print(x.constraint_funcs)
p.constraints = x.constraints(times)
p.sense = opt.Sense.maximize
for c in p.constraints:
    print(c)

#p.objective = sum([x.production[1](t) for t in times])
# p.solver = PyomoSolver()
# p.solve()
# for t in times:
#     print(p._solution[x.v[t]])