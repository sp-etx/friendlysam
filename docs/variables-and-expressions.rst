
Now that you know :ref:`what-friendly-sam-is-for`, let's get started!

Variables and expressions
==========================

In Friendly Sam, each variable is an instance of the ``Variable`` class. Let's create one:

    >>> from friendlysam import Variable
    >>> my_var = Variable('x')
    >>> my_var
    <friendlysam.opt.Variable at 0x...: x>
    >>> print(my_var)
    x

Variables can be added, multiplied, subtracted, and so on, to form expressions, including equalities and inequalities.

::

    >>> expressions = [
    ...     my_var * 2 + 1,
    ...     (my_var + 1) * 2,
    ...     my_var * 2 <= 3
    ... ]
    >>> for expr in expressions:
    ...     expr
    <friendlysam.opt.Add at 0x...>
    <friendlysam.opt.Mul at 0x...>
    <friendlysam.opt.LessEqual at 0x...>
    >>> 
    >>> for expr in expressions:
    ...     print(expr)
    x * 2 + 1
    (x + 1) * 2
    x * 2 <= 3

.. warning::
    The operator ``==`` is reserved for checking object similarity, just like we are used to in Python. To create the relation "x equals y", use ``Eq``:

    ::
    
        >>> from friendlysam import Eq
        >>> my_var == 1
        False
        >>> print(Eq(my_var, 1))
        x == 1

There is also a nice ``Sum`` operation you should use for large sums. Using the built-in ``sum()`` will create a deeply nested and very inefficient tree of ``Add`` objects.

    >>> from friendlysam import Sum
    >>> many_terms = [my_var * i for i in range(100)]
    >>> Sum(many_terms)
    <friendlysam.opt.Sum at 0x...>
    >>> sum(many_terms)
    <friendlysam.opt.Add at 0x...>


Names don't mean anything
--------------------------

In the example above, we named the ``Variable`` object ``'x'``. This is nothing more than a string attached to the object, and it does not say anything about the identity of the variable. In principle you can have several ``Variable`` objects with the same name, but that's really confusing and should not be necessary.

::

    >>> my_var = Variable('y')
    >>> my_other_var = Variable('y')
    >>> my_var == my_other_var
    False
    >>> print(my_var + my_other_var)
    y + y

It is often a good idea to give your variables names you can recognize, because that simplifies debugging when you want to inspect the expressions you have made with the variables. But if you don't want to name variables you don't have to. The variables are then named automatically.

::

    >>> Variable()
    <friendlysam.opt.Variable at 0x...: x1>
    >>> Variable()
    <friendlysam.opt.Variable at 0x...: x2>


VariableCollection is like an indexed Variable
--------------------------------------------------

There is also a convenient class called ``VariableCollection``. It is a sort of lazy dictionary, which creates variables when you ask for them::

    >>> from friendlysam import VariableCollection
    >>> z = VariableCollection('z')
    >>> z
    <friendlysam.opt.VariableCollection at 0x...: z>
    >>> z(1)
    <friendlysam.opt.Variable at 0x...: z(1)>
    >>> z((1, 'a'))
    <friendlysam.opt.Variable at 0x...: z((1, 'a'))>
    >>> z(None)
    <friendlysam.opt.Variable at 0x...: z(None)>


You can think of ``VariableCollection`` as an indexed variable, but all it really does is to create variables when you call it, and then remember them.

The index must be hashable. For example, tuples are valid indices, but not lists::
    
    >>> z((3, 1, 4))
    <friendlysam.opt.Variable at 0x...: z((3, 1, 4))>
    >>> z([3, 1, 4])
    Traceback (most recent call last):
    ...
    TypeError: unhashable type: 'list'


Variables can be named in a namespace, like this::

    >>> from friendlysam import namespace
    >>> with namespace('cheese'):
    ...     cheese1 = Variable('gorgonzola')
    ...     cheese2 = VariableCollection('ricotta')
    ... 
    >>> cheese1
    <friendlysam.opt.Variable at 0x...: cheese.gorgonzola>
    >>> cheese2
    <friendlysam.opt.VariableCollection at 0x...: cheese.ricotta>

The namespace doesn't affect the function of a variable in any way. It only prepends a string representation of whatever object to the variable name, so you can also do things like this::

    >>> with namespace(dict()):
    ...     Variable('x')
    ... 
    <friendlysam.opt.Variable at 0x...: {}.x>


Variables can have values
--------------------------

You can assign a value to a variable. The variable will still work in expressions:

    >>> x = Variable('x')
    >>> x.value = 39
    >>> expression = x + 3
    >>> expression
    <friendlysam.opt.Add at 0x...>
    >>> print(expression)
    x + 3

The difference is that you can now evaluate expressions. But note that the expression object is unchanged.

    >>> float(expression)
    42.0
    >>> print(expression)
    x + 3

You can change or delete the value:

    >>> x.value = 0.5
    >>> int(expression)
    3
    >>> float(expression)
    3.5
    >>> expression.value
    3.5
    >>> del x.value
    >>> float(expression)
    Traceback (most recent call last):
    ...
    friendlysam.opt.NoValueError: cannot get a numeric value: x + 3 evaluates to x + 3

And it works for relations, too:

    >>> x.value = 10
    >>> (x <= 12).value
    True


Expressions are immutable
--------------------------

Expressions are hashed by structure: If they do the same thing, they hash and compare equal. This also means they are considered equal e.g. as ``dict`` keys.

    >>> expr1 = x * 2
    >>> expr2 = x * 2
    >>> expr1 is expr2 # Different objects!
    False
    >>> expr1 == expr2 # But similar
    True
    >>> d = dict()
    >>> d[expr1] = 'some value'
    >>> d[expr2]
    'some value'

Expressions are immutable, meaning that their state can never be changed. In the example above, ``expr1 == expr2`` and that will always be true. Two expressions are interchangeable if (and only if) they compare equal. For any purpose, in any situation, ``expr1`` will always do the same thing as ``expr2``.

However, as you saw above, the result of ``float(expr1)`` may vary depending on whether variables in the expression have values. Let's look a little bit closer:

    >>> x.value = 3
    >>> expression = x + 39
    >>> float(expression)
    42.0
    >>> x.value = 100
    >>> another_expression = x + 39
    >>> expression == another_expression
    True
    >>> float(expression)
    139.0
    >>> float(another_expression)
    139.0

This is pretty much analogous to a tuple of mutable objects. The tuple itself may never change, but its contents may:

    >>> a = [1, 2, 3]
    >>> my_tuple = (a, 'something')
    >>> my_tuple
    ([1, 2, 3], 'something')
    >>> a[:] = ['changed'] # Only changing the contents of the list
    >>> another_tuple = (a, 'something')
    >>> my_tuple == another_tuple
    True
    >>> my_tuple
    (['changed'], 'something')
    >>> another_tuple
    (['changed'], 'something')


Behind ``value`` is ``evaluate()``
------------------------------------

You might want to know what is happening behind the scenes when you ask for ``expression.value`` or ``float(expression)``. In that case, check out the method :meth:`~friendlysam.opt.Operation.evaluate`.

