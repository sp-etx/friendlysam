from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()
        v = self.make_var(name='x')

        self.production[1] = lambda t: v * a
        self.consumption[2] = lambda t: v

        self.add_constraint(lambda t: v >= 0)
        self.add_constraint(lambda t: v <= 3)


x = ProcessA(20)


p = opt.Problem()
for c in x.constraints(1):
    p.constraints.add(c)

p.objective = sympy.Symbol('v')
p.solver = opt.GurobiSolver()
p.solve()