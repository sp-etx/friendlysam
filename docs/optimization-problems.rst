Optimization problems
======================

Creating a problem
-------------------------

We use Friendly Sam to formulate MILP problems. The optimization library could be extended to allow other types of problems, too, but this is what is supported today.

Now, let's begin with a full example of an optimization problem.

    >>> import friendlysam as fs
    >>> 
    >>> # Create the problem
    >>> x = fs.VariableCollection('x')
    >>> prob = fs.Problem()
    >>> prob.objective = fs.Maximize(x(1) + x(2))
    >>> prob.add(8 * x(1) + 4 * x(2) <= 11)
    >>> prob.add(2 * x(1) + 4 * x(2) <= 5)
    >>> 
    >>> # Get a solver and solve the problem
    >>> solver = fs.get_solver()
    >>> solution = solver.solve(prob)
    >>> type(solution)
    <class 'dict'>
    >>> solution[x(1)]
    1.0
    >>> solution[x(2)]
    0.75

The solver does not in any way affect the problem or the variables. It just reads the problem, solves it and handles back a ``dict`` with your `Variable` objects as keys and their solutions as values.

If you set the ``value`` of some variables, those will be inserted into the problem before solving it:

    >>> x(1).value = 0
    >>> solution = solver.solve(prob)
    >>> solution
    {<friendlysam.opt.Variable at 0x...: x(2)>: 1.25}
    >>> x(1) in solution
    False

``x(1)`` is not in the solution, because you already set its value, so it was handled like a number by the solver.

Debugging constraints
----------------------

Now let's add another constraint:

    >>> x(1).value = 0
    >>> prob.add(1 <= x(1))
    >>> solver.solve(prob)
    Traceback (most recent call last):
    ...
    friendlysam.opt.ConstraintError: The expression in <Constraint: Ad hoc constraint> evaluates to False, so the problem is infeasible.

In this case it's obvious why the problem could not be solved. But for argument's sake, let's say we didn't know which constraint was causing a problem. The error message was not too helpful, but the :class:`~friendlysam.opt.ConstraintError` luckily also contains a reference to the constraint that failed, so we can pick it out like this:

    >>> try:
    ...     solver.solve(prob)
    ... except fs.ConstraintError as e:
    ...     failed_constraint = e.constraint
    ...     print(repr(failed_constraint))
    ...     print(repr(failed_constraint.expr))
    ...     print(failed_constraint.expr)
    ...     print(failed_constraint.desc)
    ...     print(failed_constraint.origin)
    ... 
    <friendlysam.opt.Constraint at 0x...>
    <friendlysam.opt.LessEqual at 0x...>
    1 <= x(1)
    Ad hoc constraint
    None

OK, that's helpful! We got the problematic constraint out. And there are a few things you should note.

    1. The type of the failed constraint is :class:`friendlysam.opt.Constraint`. It was automatically created when we added a :class:`friendlysam.opt.LessEqual` constraint to the problem, and its sole purpose is to wrap the inequality ``1 <= x(1)`` and to add some metadata.

    2. The :class:`~friendlysam.opt.Constraint` object contains the :class:`~friendlysam.opt.LessEqual` object that we added to the problem.

    3. The :class:`~friendlysam.opt.Constraint` object contains also a description ``desc`` and a variable called ``origin`` which is supposed to say something about where the constraint comes from.

.. note::

    There is a quicker way of printing out some info about a constraint: :attr:`~friendlysam.opt.Constraint.long_description`:

        >>> print(failed_constraint.long_description)
        <friendlysam.opt.Constraint at 0x...>
        Description: Ad hoc constraint
        Origin: None

If you want to make your model easier to debug, you can use :class:`~friendlysam.opt.Constraint` instances with custom description and/or origin, like in this stupid example:

    >>> from friendlysam import Constraint
    >>> def constr(var, parameter):
    ...     return var / 42 >= parameter
    >>> for i in range(5):
    ...     expr = constr(x(i), i)
    ...     origin = (constr, x(i), i)
    ...     prob += Constraint(expr, desc='Some description', origin=origin)
    ...

Different ways to add constraints
-----------------------------------

.. note::
    In the examples above, we added constraints like this::

        >>> prob.add(8 * x(1) + 4 * x(2) <= 11)
        >>> prob += Constraint(expr, desc='Some description', origin=origin)

    These two methods are equivalent, so just choose the syntax you like best.

    You can also send an iterable (even a generator), and the items in the iterable can also be iterables, e.g::

        >>> prob += ([constr(x(i), i), constr(x(i+1), i)] for i in range(5))

    See the documentation for :meth:`~friendlysam.opt.Problem.add` for all the details.

Special ordered sets
----------------------

Friendly Sam also supports special ordered sets. You specify them as a sort of constraint: Check out :class:`~friendlysam.opt.SOS1` and :class:`~friendlysam.opt.SOS2`.