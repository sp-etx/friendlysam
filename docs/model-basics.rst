Model basics: Parts and constraints
======================================

Interconnected parts
-----------------------

Friendly Sam is made for optimization-based modeling of interconnected parts, producing and consuming various resources. For example, an urban energy system may have grids for district heating, electric power, fossil gas, etc. Consumers, producers, storages and other parts are connected to each other through these grids. To describe these relations, Friendly Sam models make heavy use of the :class:`~friendlysam.parts.Part` class and its subclasses like :class:`~friendlysam.parts.Node`, :class:`~friendlysam.parts.FlowNetwork`, :class:`~friendlysam.parts.Cluster`, :class:`~friendlysam.parts.Storage`, etc. We will introduce these in due time, but first a few general things about :class:`~friendlysam.parts.Part`.

Parts have indexed constraints
-------------------------------

A :class:`~friendlysam.parts.Part` typically represents something physical, like a heat consumer or a power grid. You can attach **constraint functions** to parts. Constraint functions are probably easiest to explain with a concrete example::

    >>> from friendlysam import Part, namespace, VariableCollection
    >>> class ChocolateFactory(Part):
    ...     def __init__(self):
    ...         with namespace(self):
    ...             self.output = VariableCollection('output')
    ...         self.constraints += self.more_than_last
    ...
    ...     def more_than_last(self, time):
    ...         last = self.step_time(time, -1)
    ...         return self.output(last) <= self.output(time)
    ...

OK, what happens above is the following: We define ``ChocolateFactory`` as a subclass of :class:`~friendlysam.parts.Part`. Upon setup, in ``__init__()``, we add a constraint function called ``more_than_last``, which defines the (admittedly bizarre) rule that the factory may never decrease its output from one time step to the next.

In Friendly Sam's vocabulary, the ``time`` argument in the example above is called an **index**. Our typical use case for indexing is a discrete time model, where each hour, day, year, or whatever time period, is an index of the model, and each constraint "belongs" to a time step just like in the silly example above.

Going back to the example, we can get the constraints out by making a ``ChocolateFactory`` instance and calling ``constraints.make()`` with an index:

    >>> chocolate_factory = ChocolateFactory() # Create an instance
    >>> constraints = chocolate_factory.constraints.make(47)
    >>> constraints
    {<friendlysam.opt.Constraint at 0x...>}
    >>> for c in constraints:
    ...     print(c.expr)
    ...
    ChocolateFactory0001.output(46) <= ChocolateFactory0001.output(47)

The result of ``constraints.make(47)`` is a set with one single constraint in it, saying that output at "time" 47 must be greater than or equal to output at "time" 46.

.. note::

    In the example above, we wrote ``last = self.step_time(time, -1)`` instead of just ``last = t-1``. This is because :class:`~friendlysam.parts.Part` has a bunch of nice functions to help out with time indexing. Read the API documentation for :meth:`~friendlysam.parts.Part.step_time`. Also check out :meth:`~friendlysam.parts.Part.times` and :meth:`~friendlysam.parts.Part.times_between`. For example, because we used ``step_time(...)``, we can easily change the time representation of our chocolate factory like this::

        >>> from pandas import Timestamp, Timedelta
        >>> chocolate_factory.time_unit = Timedelta('6h')
        >>> constraints = chocolate_factory.constraints.make(Timestamp('2015-06-10 18:00'))
        >>> for c in constraints:
        ...     print(c.expr)
        ...
        ChocolateFactory0001.output(2015-06-10 12:00:00) <= ChocolateFactory0001.output(2015-06-10 18:00:00)


Advanced indexing
-------------------

Indexing is really just a way to organize constraints in groups that belong together. When we have a whole bunch of parts, to get all the constraints that belong together, we can do things like this:

    >>> from itertools import chain
    >>> parts = Part(), Part(), Part() # Put something more useful here...
    >>> some_index = 'could be anything'
    >>> constraints = set.union(*(p.constraints.make(some_index) for p in parts))

Indexing is typically used to represent time, but it is really up to you to decide what an index means, and what to use as indices. We call it "index" rather than "time" because it is something more general than a representation of time. In fact, any hashable object can be used as an index, so you can do all sorts of complicated things. Examples of indexing can be found in the docs for :meth:`~friendlysam.parts.Part.step_time`. Also check out :meth:`~friendlysam.parts.Part.times` and :meth:`~friendlysam.parts.Part.times_between`.

Friendly Sam currently has no mechanism for using constraint functions without indices. If you want to make a static model and really don't need indexing, then just use some common index like ``None`` or ``0`` for everything. (Or come up with a better solution and `discuss it with us on GitHub <https://github.com/sp-etx/friendlysam/issues>`_.)

In the next section :ref:`nodes_networks_clusters` you will also see how indexing is used to represent time in flow networks.   
