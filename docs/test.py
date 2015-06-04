import friendlysam as fs

# Create the problem
x = fs.VariableCollection('x', lb=0)
prob = fs.Problem()
prob.objective = fs.Maximize(x(1) + x(2))
prob.add(8 * x(1) + 4 * x(2) <= 11)
prob.add(2 * x(1) + 4 * x(2) <= 5)

# Get a solver and solve the problem
solver = fs.get_solver()
solution = solver.solve(prob)

x(1).value = 0
solution = solver.solve(prob)
print(solution)
x(2).value = 2
try:
    solver.solve(prob)
except fs.ConstraintError as e:
    print(repr(e.constraint))
    print(e.constraint.expr)
