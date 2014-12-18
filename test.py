from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()
        v = self.register_var(name='aoeu', lb=1, ub=2, indexed=True)
        # x, y, z = [self.register_var() for i in range(3)]
        # opt.make_constraints((x,y,z), sos1=True, lb=0)

        self.production[1] = lambda t: v[t] * a
        self.consumption[2] = lambda t: v[t]

        self.constrain(lambda t: v[t] <= 3)


x = ProcessA(20)

p = opt.Problem()


p.constraints = x.constraints((20,))


p.objective = x.consumption[2](20)
p.solver = opt.GurobiSolver()
p.solve()