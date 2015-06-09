Flow networks: Nodes and resources
===================================

Friendly Sam makes it easy to formulate optimization problems with flow networks. A central tool for this is the :class:`~friendlysam.opt.Node` class. Let's begin with an example::

    >>> from friendlysam import Node, VariableCollection
    >>> n = Node(name='Power plant')
    >>> fuel_use = VariableCollection('fuel')
    >>> efficiency = 0.5
    >>> n.production['power'] = lambda time: efficiency * fuel_use(time)
    >>> time = 42
    >>> for c in n.constraints(time):
    ...     print(c.long_description)
    ...     print(c.expr)
    ...
    <friendlysam.opt.Constraint at 0x...>
    Description: Balance constraint (resource=power)
    Origin: CallTo(func=<bound method Node.balance_constraints of <Node at 0x...: Power plant>>, index=42)
    0.5 * fuel(42) == 0

Let's go through what happened here.

    1. First we created a :class:`~friendlysam.opt.Node` instance with the name ``'Power plant'``.

    2. We then created a function returning an expression, and set it as the ``'power'`` item of a dictionary ``production`` on the :class:`~friendlysam.opt.Node`.

    3. The :class:`~friendlysam.opt.Node` created a balance constraint constraint using our power production function.

In essence, this is what the :class:`~friendlysam.opt.Node` class does: It keeps track of a ``production`` function (and also ``accumulation`` and ``consumption`` as we soon shall see) and it creates balance constraints.


