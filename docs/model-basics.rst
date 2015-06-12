Model basics: Parts and constraints
======================================

Interconnected parts
-----------------------

Friendly Sam is made for optimization-based modeling of interconnected parts, producing and consuming various resources. For example, an urban energy system may have grids for district heating, electric power, fossil gas, etc. Consumers, producers and storages are connected to each other through the grid. Friendly Sam is made with this type of models in mind. Friendly Sam models make heavy use of the :class:`~friendlysam.parts.Part` class and its subclasses like :class:`~friendlysam.parts.Node`, :class:`~friendlysam.parts.FlowNetwork`, :class:`~friendlysam.parts.Cluster`, :class:`~friendlysam.parts.Storage`, etc. We will introduce these in due time, but first a few general things about :class:`~friendlysam.parts.Part`.

Parts have indexed constraints
-------------------------------

A :class:`~friendlysam.parts.Part` typically represents something physical, like a heat consumer or a power grid. You can attach indexed constraints to a part :class:`~friendlysam.parts.Part`. This is probably easiest to explain with a concrete example (:class:`~friendlysam.parts.Node` is a type of :class:`~friendlysam.parts.Part`)::

    >>> from friendlysam import Node, namespace, VariableCollection
    >>> class ChocolateFactory(Node):
    ...     def __init__(self):
    ...         with namespace(self):
    ...             self.production['chocolate'] = VariableCollection('production')
    ...         self.constraints += self.more_than_last
    ...
    ...     def more_than_last(self, t):
    ...         last = self.step_time(t, -1)
    ...         return self.production['chocolate'](t) >= self.production['chocolate'](last)
    ...

OK, what happens above is the following: We define ``ChocolateFactory`` as a typ