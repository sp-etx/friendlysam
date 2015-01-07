from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt
from friendlysam.optimization.solvers.pyomo import PyomoSolver

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()

        v = Indexed(lambda t: self.variable(name('x', t), ub=3))

        def activity(t):
            return self.piecewise_affine_arg(name('activity', t), [0, 0.50, 0.75, 1])
        activity = Indexed(activity)
        efficiency = Indexed(lambda t: PwaExpression(activity[t], [.70, .75, .92, .85]))
        self.consumption[fuel] = activity * max_fuel_use
        self.production[power] = Indexed(lambda t: efficiency * self.consumption[fuel][t])
        self.production[heat] = Indexed(lambda t: alpha * self.production[power][t])

        self.constraints += Indexed(lambda t: RelConstraint(activity[t] - activity[t-1] <= 0.1))



x = ProcessA(20)

p = opt.Problem()

times = range(5)
p.constraints = x.constraints(times)
p.sense = opt.Sense.maximize

p.objective = sum([x.production[1](t) for t in times])
p.solver = PyomoSolver()
p.solve()
for t in times:
    print(p._solution[x.v[t]])