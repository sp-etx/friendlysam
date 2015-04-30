.. _user-guide:

User Guide
====================================================================================

You might want to read :ref:`what-friendly-sam-is-for` first.

Now let's get started!

Variables and expressions
----------------------------

In Friendly Sam, each variable is an instance of the ``Variable`` class. Variables can be added, multiplied, subtracted, and so on, to form expressions, including equalities and inequalities.

::

	>>> import friendlysam as fs
	>>> my_var = fs.Variable('x')
	>>> my_var
	<Variable at 0x...: x>
	>>> my_var * 2 + 1
	<Add at 0x...: x * 2 + 1>
	>>> (my_var + 1) * 2
	<Mul at 0x...: (x + 1) * 2>
	>>> my_var * 2 <= 3
	<LessEqual at 0x...: x * 2 <= 3>

In this case, we named the ``Variable`` object ``'x'``. This is nothing more than a string attached to the object, and it does not say anything about the identity of the variable. In principle you can have several ``Variable`` objects with the same name, but that's really confusing and should not be necessary.

::

	>>> my_var = fs.Variable('y')
	>>> my_other_var = fs.Variable('y')
	>>> my_var is my_other_var
	False
	>>> my_var + my_other_var
	<Add at 0x...: y + y>

It is often a good idea to give your variables names you can recognize, because that simplifies debugging when you want to inspect the expressions you have made with the variables. But if you don't want to name variables you don't have to. The variables are then named automatically.

::

	>>> fs.Variable()
	<Variable at 0x...: x1>
	>>> fs.Variable()
	<Variable at 0x...: x2>

There is also a convenient class called ``VariableCollection``. It is a sort of lazy dictionary, which creates variables when you ask for them::

	>>> z = fs.VariableCollection('z')
	>>> z
	<VariableCollection at 0x...: z>
	>>> z(1)
	<Variable at 0x...: z(1)>
	>>> z(1, 'a')
	<Variable at 0x...: z(1, 'a')>
	>>> z()
	<Variable at 0x...: z()>


You can think of ``VariableCollection`` as an indexed variable, but all it really does is to create variables when you call it, and then remember them. As shown above, you can use ``VariableCollection`` with only one index (``x(1)``) or with several (``x(1, 'a')``) or even with zero indices (``x()``). Using zero indices may seem unintuitive, but in some cases it's really convenient as we will show later.

Every index must be hashable. For example, tuples are valid indices, but not lists::
	
	>>> z((3, 1, 4))
	<Variable at 0x...: z((3, 1, 4))>
	>>> z([3, 1, 4])
	Traceback (most recent call last):
	...
	TypeError: unhashable type: 'list'
