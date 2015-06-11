Flow networks: Nodes and resources
===================================

.. warning::

    This tutorial only teaches the very basics of how to use Friendly Sam. To learn more, follow the links into the code reference of :class:`~friendlysam.parts.Node`, :class:`~friendlysam.parts.FlowNetwork`, etc.

Friendly Sam makes it easy to formulate optimization problems with flow networks. Let's begin with an example.

An example
------------

Custom types of nodes should typically be created by subclassing :class:`~friendlysam.parts.Node`, like this::

    >>> from friendlysam import Node, VariableCollection, namespace
    >>> class PowerPlant(Node):
    ...     def __init__(self):
    ...         with namespace(self):
    ...             x = VariableCollection('output')
    ...         self.production['power'] = x
    ...
    >>> class Consumer(Node):
    ...     def __init__(self, demand):
    ...         self.consumption['power'] = lambda time: demand[time]
    ...

We have now defined a ``PowerPlant`` class inheriting :class:`~friendlysam.parts.Node`, and a ``Consumer`` class, also inheriting :class:`~friendlysam.parts.Node`. The power plant has its ``production['power']`` equal to a :class:`~friendlysam.opt.VariableCollection`, and the consumer has ``consumption['power']`` equal to the value found in the argument ``demand``. Let's create instances and test them:

    >>> power_plant = PowerPlant()
    >>> power_plant.production['power'](3)
    <friendlysam.opt.Variable at 0x...: PowerPlant0001.output(3)>

    >>> power_demand = [25, 30, 33, 29, 27]
    >>> consumer = Consumer(power_demand)
    >>> consumer.consumption['power'](3)
    29

Let's now connect the two nodes:

    >>> from friendlysam import FlowNetwork
    >>> power_grid = FlowNetwork('power', name='Power grid')
    >>> power_grid.connect(power_plant, consumer)
    >>> power_grid.children == {power_plant, consumer}
    True

The ``Consumer`` instance and the ``PowerPlant`` instance were added to the power grid, and can now be found as :attr:`~friendlysam.parts.Part.children` of the :class:`~friendlysam.parts.FlowNetwork`.

.. note::

    In this example, we use the key ``'power'`` in a few different places. Whatever we put as a key in a :attr:`~friendlysam.parts.Node.production` or :attr:`~friendlysam.parts.Node.consumption` dictionary, or a similar place, is called a **resource**. You are not limited to strings like ``'power'`` but could use any hashable type: numbers, tuples, most other objects, etc.

Now let's look at something less obvious:

    >>> for part in [consumer, power_plant, power_grid]:
    ...     for constraint in part.constraints.make(3):
    ...         print(constraint.long_description)
    ...         print(constraint.expr)
    ...         print()
    ...
    <friendlysam.opt.Constraint at 0x...>
    Description: Balance constraint (resource=power)
    Origin: CallTo(func=<bound method Consumer.balance_constraints of <Consumer at 0x...: Consumer0001>>, index=3, owner=<Consumer at 0x...: Consumer0001>)
    Power grid.flow(PowerPlant0001-->Consumer0001)(3) == 29
    <BLANKLINE>
    <friendlysam.opt.Constraint at 0x...>
    Description: Balance constraint (resource=power)
    Origin: CallTo(func=<bound method PowerPlant.balance_constraints of ...>, index=3, owner=<PowerPlant at 0x...: PowerPlant0001>)
    PowerPlant0001.output(3) == Power grid.flow(PowerPlant0001-->Consumer0001)(3)
    <BLANKLINE>

The :meth:`~friendlysam.parts.FlowNetwork.connect` call creates a flow between two nodes, and it adds this flow to the appropriate :attr:`~friendlysam.parts.Node.outflows` or :attr:`~friendlysam.parts.Node.inflows` on those two nodes. Each :class:`~friendlysam.parts.Node` can then formulate its own balance constraints.

Of course, we could now add these constraints to an optimization problem, just like any other constraint.

.. note::

    A :class:`~friendlysam.parts.Node` instance will always produce balance constraints for each of its :attr:`~friendlysam.parts.Node.resources`. Let's say we had not connected the ``PowerPlant`` instance to the consumer, then its balance constraint would be ``PowerPlant0001.output(3) == 0``. (Try it yourself!)



Node
------------------------------------


How balance constraints are made
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here are a few simple rules for how balance constraints are made:

    * Each :class:`~friendlysam.parts.Node` has the five dictionaries :attr:`~friendlysam.parts.Node.consumption`, :attr:`~friendlysam.parts.Node.production`, :attr:`~friendlysam.parts.Node.accumulation`, :attr:`~friendlysam.parts.Node.inflows`, and :attr:`~friendlysam.parts.Node.outflows`.

    * Whatever you decide to put as a key in any of these dictionaries is called a **resource**.

    * For each resource present in any of the dictionaries, the :class:`~friendlysam.parts.Node` produces balance constraints like this:

        **(sum of inflows) + production = consumption + accumulation + (sum of outflows)**

    * The constraints of the node are accessed by calling something like

        >>> index = 3
        >>> constraints = power_plant.constraints.make(index)

      The index is passed on to the functions: ``production[resource](index)``, ``consumption[resource](index)``, etc. You can use any function or object as ``production[resource]``, ``consumption[resource]``, etc, as long as it is callable. The index can be any hashable object.


Custom names
^^^^^^^^^^^^^^^

You can name your :class:`~friendlysam.parts.Node` instances if you want something more personal than ``PowerPlant0001``. Just set the property :attr:`~friendlysam.parts.Part.name`, for example in the ``__init__`` function, like this:

    >>> class CHPPlant(Node):
    ...     def __init__(self, name=None):
    ...         if name:
    ...             self.name = name
    ...         ...
    >>> chp_plant = CHPPlant(name='Rya KVV')
    >>> chp_plant.name == str(chp_plant) == 'Rya KVV'
    True


FlowNetwork
-------------------------

A :class:`~friendlysam.parts.FlowNetwork` essentially does two things: It creates the variable collections representing flows in the network, and it modifies the :attr:`~friendlysam.parts.Node.inflows` and :attr:`~friendlysam.parts.Node.outflows` of nodes when you call :meth:`~friendlysam.parts.FlowNetwork.connect`.

Unidirectional by default
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connections are unidirectional, so when you ``connect(node1, node2)`` things can flow from ``node1`` to ``node2``. Make the opposite connection if you want a bidirectional flow, or use this shorthand:

    >>> power_grid.connect(power_plant, consumer, bidirectional=True)


Flow restrictions
^^^^^^^^^^^^^^^^^^^

To limit the flow between two nodes, get the flow :class:`~friendlysam.opt.VariableCollection` and set its upper bound :attr:`~friendlysam.opt.VariableCollection.ub`::

    >>> flow = power_grid.get_flow(power_plant, consumer)
    >>> flow
    <friendlysam.opt.VariableCollection at 0x...: Power grid.flow(PowerPlant0001-->Consumer0001)>
    >>> flow.ub = 40


Clusters and multi-area models
--------------------------------

A cluster is fully connected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes we are not interested in making a full network model specifying all the flows between different nodes. The :class:`~friendlysam.parts.Cluster` class is a handy type of :class:`~friendlysam.parts.Node` for that. It is a type of node that can contain other nodes, and it essentially acts like a fully connected network, where all nodes are connected to all others.

When a :class:`~friendlysam.parts.Node` is put in a :class:`~friendlysam.parts.Cluster`, the child :class:`~friendlysam.parts.Node` will no longer make balance constraints, and instead the :class:`~friendlysam.parts.Cluster` creates an aggregated balance constraint, summing up the ``production``, ``consumption`` and ``accumulation`` of its contained :attr:`~friendlysam.parts.Part.children`.

    >>> from friendlysam import Cluster
    >>> power_plant = PowerPlant()
    >>> consumer = Consumer(power_demand)
    >>> power_cluster = Cluster(power_plant, consumer, resource='power', name='Power cluster')
    >>> for part in power_cluster.descendants_and_self:
    ...     for constraint in part.constraints.make(2):
    ...         print(constraint.long_description)
    ...         print(constraint.expr)
    ...
    <friendlysam.opt.Constraint at 0x...>
    Description: Balance constraint (resource=power)
    Origin: CallTo(func=<bound method Cluster.balance_constraints ...>, index=2, owner=<Cluster at 0x...: Power cluster>)
    PowerPlant0002.output(2) == 33


Multi-area models
^^^^^^^^^^^^^^^^^^

A :class:`~friendlysam.parts.Cluster` instance can be used like any other :class:`~friendlysam.parts.Node`, for example in a :class:`~friendlysam.parts.FlowNetwork`. This is a simple way of making a multi-area model of, say, a district heating system. Let's say the system has a few areas with significant flow restrictions between them. Then create a flow network with interconnected clusters, something like this::

    area_A == Cluster(*nodes_in_area_A, resource='heat')
    area_B == Cluster(*nodes_in_area_B, resource='heat')
    area_C == Cluster(*nodes_in_area_C, resource='heat')
    
    heat_grid = FlowNetwork('heat')
    heat_grid.connect(area_A, area_B, bidirectional=True, capacity=ab)
    heat_grid.connect(area_A, area_C, bidirectional=True, capacity=ac)
    heat_grid.connect(area_B, area_C, bidirectional=True, capacity=bc)
