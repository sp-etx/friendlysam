from friendlysam.parts.process import Process
import sympy
import friendlysam.optimization as opt

class ProcessA(Process):
    """docstring for ProcessA"""
    def __init__(self, a):
        super(ProcessA, self).__init__()
        #v = self.register_var(name='aoeu', lb=1, ub=2, indexed=True)

        x, y, z = [self.register_var(str(i)) for i in range(3)]
        self.constrain(opt.make_constraints((x,y,z), sos1=True, lb=0, ub=3))

        #self.production[1] = lambda t: v[t] * a
        self.consumption[2] = 1.1*x + 1.10000000000001*y + 0.9*z

        #self.constrain(lambda t: v[t] <= 3)
        #self.constrain(lambda t: sympy.Eq(v[t], 1.5))


x = ProcessA(20)

p = opt.Problem()


p.constraints = x.constraints((20,21))
p.sense = opt.Sense.maximize


p.objective = x.consumption[2]
p.solver = opt.GurobiSolver()
p.solve()
print(p._solution)