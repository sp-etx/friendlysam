# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
import sys
import operator
from functools import reduce

from contextlib import contextmanager
from itertools import chain
from enum import Enum
import numbers

import friendlysam as fs
from friendlysam.compat import ignored
from friendlysam.common import short_default_repr

_namespace_string = ''

def _prefix_namespace(s):
    global _namespace_string
    if _namespace_string == '':
        return str(s)
    return '{}.{}'.format(_namespace_string, s)

@contextmanager
def namespace(name):
    """Context manager for prefixing variable names.

    Examples:

        >>> with namespace('dimensions'):
        ...     w = Variable('width')
        ...     h = VariableCollection('heights')
        ...
        >>> w
        <friendlysam.opt.Variable at 0x...: dimensions.width>
        >>> h(3)
        <friendlysam.opt.Variable at 0x...: dimensions.heights(3)>
    """
    global _namespace_string
    old = _namespace_string
    _namespace_string = str(name)
    yield
    _namespace_string = old


def get_solver(engine='pulp', options=None):
    """Get a solver object.

    Args:
        engine (str, optional): Which engine to use.
        options (dict, optional): Parameters to the engine constructor.

            If ``engine == 'pulp'``, the engine is created using
            ``PulpSolver(options)``. See 
            :class:`~friendlysam.solvers.pulpengine.PulpSolver` constructor
            for details.

    """
    if options is None:
        options = {}

    if engine == 'pulp':            
        from friendlysam.solvers.pulpengine import PulpSolver
        return PulpSolver(options)

class SolverError(Exception):
    """A generic exception raised by a solver instance."""
    pass
        
class NoValueError(AttributeError):
    """Raised when a variable or expression has no value."""
    pass

class Domain(Enum):
    """Domain of a variable.

    :class:`Variable` and :class:`VariableCollection` support these
    domains passed in with the ``domain`` keyword argument of the
    constructor.

    Examples:

        >>> for d in Domain:
        ...     print(d)
        ...
        Domain.real
        Domain.integer
        Domain.binary

        >>> s = get_solver()
        >>> prob = Problem()
        >>> x = Variable('x', domain=Domain.integer)
        >>> prob.objective = Minimize(x)
        >>> prob += (x >= 41.5)
        >>> solution = s.solve(prob)
        >>> solution[x] == 42
        True

    """
    real = 0
    integer = 1
    binary = 2


class Operation(object):
    """An operation on some arguments.

    This is a base class. Concrete examples:

    Arithmetic operations:

        * Addition: :class:`Add`
        * Subtraction: :class:`Sub`
        * Multiplication: :class:`Mul`
        * Summation: :class:`Sum`

    Relations:

        * Less than (``<``): :class:`Less`
        * Less or equal (``<=``): :class:`LessEqual`
        * Equals: :class:`Eq`

    Note:
        The :class:`Variable` class and the arithmetic operation classes have
        overloaded operators which create :class:`Operation` instances. For example:

            >>> x = Variable('x')
            >>> isinstance(x * 2, Operation)
            True
            >>> x + 1
            <friendlysam.opt.Add at 0x...>

    """

    def __new__(cls, *args):
        obj = super().__new__(cls)
        obj._args = args
        obj._key = (cls,) + args
        return obj

    @classmethod
    def create(cls, *args):
        """Classmethod to create a new object.

        This method is the default evaluator function used in :meth:`evaluate`.
        Usually you don't want to use this function, but instead the constructor.

        Args:
            *args: The arguments the operation operates on.

        Examples:
            >>> x = Variable('x')
            >>> args = (2, x)
            >>> Add.create(*args) == 2 + x
            True
            >>> LessEqual.create(*args) == (2 <= x)
            True

        """
        return cls.__new__(cls, *args)

    def __hash__(self):
        return hash(self._key)

    def __eq__(self, other):
        return type(self) == type(other) and self._key == other._key

    @property
    def args(self):
        """This property holds the arguments of the operation.

        See also :meth:`create`.

        Examples:

            >>> x, y = Variable('x'), Variable('y')
            >>> expr = x + y
            >>> expr
            <friendlysam.opt.Add at 0x...>
            >>> expr.args == (x, y)
            True

            >>> (x + y) * 2
            <friendlysam.opt.Mul at 0x...>
            >>> _.args
            (<friendlysam.opt.Add at 0x...>, 2)

        """
        return self._args
    
    def evaluate(self, replace=None, evaluators=None):
        """Evaluate the expression recursively.

        Evaluating an expression:

            1. Get an evaluating function. If the class of the present expression
            is in the :obj:`evaluators` dict, use that. Otherwise, take the :meth:`create`
            classmethod of the present expression class.

            2. Evaluate all the arguments. For each argument ``arg``, first try to replace
            it by looking for ``replace[arg]``. If it's not there, try to evaluate it
            by calling ``arg.evaluate()`` with the same arguments supplied to this call.
            If ``arg.evaluate()`` is not present, leave the argument unchanged.

            3. Run the evaluating function ``func(*evaluated_args)`` and return the result.

        Args:
            replace (dict, optional): Replacements for arguments. Arguments matching keys
                will be replaced by specified values.
            evaluators (dict, optional): Evaluating functions to use instead of the default
                (which is the :meth:`create` classmethod of the argument's class). An argument
                whose ``__class__`` equals a key will be evaluated with the specified function.

        Examples:

            >>> x = VariableCollection('x')
            >>> expr = x(1) + x(2)
            >>> print(expr.evaluate())
            x(1) + x(2)
            >>> expr.evaluate(replace={x(1): 10, x(2): 20})
            <friendlysam.opt.Add at 0x...>
            >>> print(_)
            10 + 20
            >>> expr.evaluate(replace={x(1): 10, x(2): 20}, evaluators=fs.CONCRETE_EVALUATORS)
            30

        """
        if evaluators is None:
            evaluators = {}
        if replace is None:
            replace = {}
        evaluated_args = []
        for arg in self.args:
            try:
                evaluated = replace[arg]
            except KeyError:
                try:
                    evaluated = arg.evaluate(replace=replace, evaluators=evaluators)
                except AttributeError:
                    evaluated = arg
            finally:
                evaluated_args.append(evaluated)

        evaluator = evaluators.get(self.__class__, self.__class__.create)

        return evaluator(*evaluated_args)

    @property
    def value(self):
        """The concrete value of the expression, if possible.

        This property should only be used when you expect a concrete value.
        It is computed by calling :meth:`evaluate` with the ``evaluators`` argument
        set to :const:`CONCRETE_EVALUATORS`. If the returned value is a number
        or boolean, it is returned.

        Raises:
            :exc:`NoValueError` if the expression did not evaluate to a
                number or boolean.
        """
        evaluated = self.evaluate(evaluators=CONCRETE_EVALUATORS)
        if isinstance(evaluated, numbers.Number):
            return evaluated
        msg = 'cannot get a numeric value: {} evaluates to {}'.format(self, evaluated)
        raise NoValueError(msg).with_traceback(sys.exc_info()[2])

    @property
    def variables(self):
        """This property gives all :attr:`leaves` which are instances of :class:`Variable`.

        Examples:

            >>> x, y = Variable('x'), Variable('y')
            >>> expr = (42 + x * y * 3.5) * 2
            >>> expr.variables == {x, y}
            True
        """

        return set(l for l in self.leaves if isinstance(l, Variable))

    @property
    def leaves(self):
        """The leaves of the expression tree.

        The leaves of an :class:`Operation` are all the :attr:`args` which
        do not themselves have a :attr:`leaves` property.

        Examples:

            >>> x, y = Variable('x'), Variable('y')
            >>> expr = (42 + x * y * 3.5) * 2
            >>> expr.leaves == {42, x, y, 3.5, 2}
            True
        """

        leaves = set()
        for a in self._args:
            try:
                leaves.update(a.leaves)
            except AttributeError:
                leaves.add(a)
        return leaves

    def _format_arg(self, arg):
        if isinstance(arg, (numbers.Number, Variable)):
            return str(arg)

        if isinstance(arg, Operation) and arg._priority >= self._priority:
            return str(arg)
        
        return '({})'.format(arg)

    def __str__(self):
        return self._format.format(*(self._format_arg(a) for a in self._args))

    __repr__ = short_default_repr

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)


class _MathEnabled(object):
    """Mixin to get all the math operators overloaded."""

    def __add__(self, other):
        return self if other == 0 else Add(self, other)

    def __radd__(self, other):
        return self if other == 0 else Add(other, self)

    def __sub__(self, other):
        return self if other == 0 else Sub(self, other)

    def __rsub__(self, other):
        return -self if other == 0 else Sub(other, self)

    def __mul__(self, other):
        return 0 if other == 0 else Mul(self, other)

    def __rmul__(self, other):
        return 0 if other == 0 else Mul(other, self)

    def __truediv__(self, other):
        return self * (1/other) # Takes care of division by scalars at least

    def __neg__(self):
        return -1 * self

    def __le__(self, other):
        return LessEqual(self, other)

    def __ge__(self, other):
        return LessEqual(other, self)

    def __lt__(self, other):
        return Less(self, other)

    def __gt__(self, other):
        return Less(other, self)

    __repr__ = short_default_repr


class Add(Operation, _MathEnabled):
    """Addition operator.

    See :class:`Operation` for a general description of operations.

    Args:
        *args: Should be exactly two terms to add.

    Examples:

        >>> x = VariableCollection('x')
        >>> expr = x(1) + x(2)
        >>> expr
        <friendlysam.opt.Add at 0x...>
        >>> expr == Add(x(1), x(2))
        True
        >>> x(1).value, x(2).value = 2, 3
        >>> float(expr)
        5.0

    """
    _format = '{} + {}'
    _priority = 1


class Sub(Operation, _MathEnabled):
    """Subtraction operator.

    See :class:`Operation` for a general description of operations.

    Args:
        *args: Should be exactly two items to subtract.

    Examples:

        >>> x = VariableCollection('x')
        >>> expr = x(1) - x(2)
        >>> expr
        <friendlysam.opt.Sub at 0x...>
        >>> expr == Sub(x(1), x(2))
        True
        >>> x(1).value, x(2).value = 2, 3
        >>> float(expr)
        -1.0

    """
    _format = '{} - {}'
    _priority = 1
        
    
class Mul(Operation, _MathEnabled):
    """Subtraction operator.

    See :class:`Operation` for a general description of operations.

    Args:
        *args: Should be exactly two terms to multiply.

    Examples:

        >>> x = VariableCollection('x')
        >>> expr = x(1) * x(2)
        >>> expr
        <friendlysam.opt.Mul at 0x...>
        >>> expr == Mul(x(1), x(2))
        True
        >>> x(1).value, x(2).value = 2, 3
        >>> float(expr)
        6.0

    Note:

        There is currently no division operator, but the operator ``/``
        is overloaded such that ``x = a / b`` is equivalent to ``x = a * (1/b)``.
        Hence, you can do simple things like

        >>> print(x(1) / 4)
        x(1) * 0.25

    """
    
    _format = '{} * {}'
    _priority = 2


class Sum(Operation, _MathEnabled):
    """A sum of items.

    See the base class :class:`Operation` for a basic description of attributes
    and methods.

    Attributes:
        args: A tuple of items to be summed.

    Examples:

        Note that the constructor takes an iterable of arguments, just like the
        built-in :func:`sum` function, but the classmethod :meth:`create` takes 
        a list of arguments, as follows.

            >>> x = VariableCollection('x')
            >>> terms = [x(i) for i in range(4)]
            >>> Sum(terms) == Sum.create(*terms)
            True

            >>> s = Sum(terms)
            >>> s.evaluate(evaluators={Sum: sum})
            Traceback (most recent call last):
            ...
            TypeError: sum expected at most 2 arguments, got 4

            >>> s.evaluate(evaluators={Sum: lambda *args: sum(args)})
            <friendlysam.opt.Add at 0x...>

    """
    _priority = 1

    def __new__(cls, vector):
        """Create a new Sum object

        Args:
            vector (iterable): The items to sum. Can be any iterable, also a generator,
                and may be zero length.
        """
        vector = tuple(vector)
        return cls.create(*vector)

    def __getnewargs__(self):
        # This is for pickling.
        return (self._args,)

    @classmethod
    def create(cls, *args):
        """Classmethod to create a new Sum object.

        Note that :meth:`create` has a different signature than the constructor.
        The constructor takes an iterable as only argument, but :meth:`create`
        takes a list of arguments.

        Example:

            >>> x = VariableCollection('x')
            >>> terms = [x(i) for i in range(4)]
            >>> Sum(terms) == Sum.create(*terms)
            True
        """

        if len(args) == 0:
            return 0
        if len(args) == 1:
            return args[0]
        return super().__new__(cls, *args)


    def __str__(self):
        return 'Sum({})'.format(', '.join(str(a) for a in self.args))


class Relation(Operation):
    """Base class for binary relations.

    See child classes:

        :class:`Less`
        :class:`LessEqual`
        :class:`Eq`

    """

    _priority = 0

    def __bool__(self):
        msg = ('{} is a Relation and its truthyness should not be tested. '
            'Use the .value property instead.').format(self)
        raise TypeError(msg)


class Less(Relation):
    '''The relation "less than".


    Examples:

        >>> x = Variable('x')
        >>> expr = (x < 1)
        >>> expr
        <friendlysam.opt.Less at 0x...>
        >>> expr == Less(x, 1)
        True
        >>> x.value = 1
        >>> expr.value
        False

    Note:

        There is no ``Greater`` class, but you can use
        the overloaded operator ``>``.

            >>> x > 1
            <friendlysam.opt.Less at 0x...>
            >>> print(_)
            1 < x
            >>> (x > 1) == (1 < x)
            True
    '''
    _format = '{} < {}'

class LessEqual(Relation):
    '''The relation "less than or equal to".

    Examples:
    
        >>> x = Variable('x')
        >>> expr = (x <= 1)
        >>> expr
        <friendlysam.opt.LessEqual at 0x...>
        >>> expr == LessEqual(x, 1)
        True
        >>> x.value = 1
        >>> expr.value
        True

    Note:

        There is no ``GreaterEqual`` class, but you can use
        the overloaded operator ``>=``.

            >>> x >= 1
            <friendlysam.opt.LessEqual at 0x...>
            >>> print(_)
            1 <= x
            >>> (x >= 1) == (1 <= x)
            True
    '''
    _format = '{} <= {}'


class Eq(Relation):
    '''The relation "equals".

    Warning:

        This operation does not have overloaded operators for creation,
        so instead you should use the constructor, ``Eq(a, b)``.


    Examples:

        >>> x = Variable('x')
        >>> x == 3 # Don't do this!
        False

        >>> equality = Eq(x, 3) # Do this instead.
        >>> equality
        <friendlysam.opt.Eq at 0x...>
        >>> x.value = 3
        >>> equality.value
        True
        >>> x.value = 4
        >>> equality.value
        False

    '''

    _format = '{} == {}'


class Variable(_MathEnabled):
    """A variable to build expressions with.

    Args:
        name (str, optional): A name of the variable. It has no relation
            to the identity of the variable. Just a name used in string
            representations.
        lb (number, optional): If supplied, a lower bound on the variable
            in optimization problems. If not supplied, the variable is
            unbounded downwards.
        ub (number, optional): If supplied, an upper bound on the variable
            in optimization problems. If not supplied, the variable is
            unbounded upwards.
        domain (any of the :class:`Domain` values): The domain of the
            variable, enforced in optimization problems.

    Note:
        The :attr:`name`, :attr:`lb`, :attr:`ub` and :attr:`domain` can 
        also be set as attributes after creation.

            >>> a = Variable('a')
            >>> a.lb = 10
            >>> a.Domain = Domain.integer

        is equivalent to

            >>> a = Variable('a', lb=10, domain=Domain.integer)

    Examples:

        The :func:`namespace` context manager can be used to conveniently
        name groups of variables.

            >>> with namespace('dimensions'):
            ...     w = Variable('width')
            ...     h = Variable('height')
            ...
            >>> w.name, h.name
            ('dimensions.width', 'dimensions.height')


    """

    _counter = 0

    def _next_counter(self):
        Variable._counter += 1
        return Variable._counter


    def __init__(self, name=None, lb=None, ub=None, domain=Domain.real):
        super().__init__()
        self.name = 'x{}'.format(self._next_counter()) if name is None else name
        self.name = _prefix_namespace(self.name)
        self.lb = lb
        self.ub = ub
        self.domain = domain

    @property
    def variables(self):
        return (self,)


    def evaluate(self, replace=None, evaluators=None):
        """Evaluate a variable.

        See :meth:`Operation.evaluate` for a general explanation of
        expression evaluation.

        A :class:`Variable` is evaluated with the following priority order:

            1. If it has a :attr:`value`, that is returned.

            2. Otherwise, if the variable is a key in the `replace` dictionary,
            the corresponding value is returned.

            3. Otherwise, the variable itself is returned.

        Args:

            replace (dict, optional): Replacements.
            evaluators (dict, optional): Has no effect. Just included to be
                compatible with the signature of :meth:`Operation.evaluate`.

        Examples:

            >>> x = Variable('x')
            >>> x.evaluate() == x
            True
            >>> x.evaluate({x: 5}) == 5
            True

            >>> x.value = -1
            >>> x.evaluate() == -1
            True
            >>> x.evaluate({x: 5}) == -1 # .value goes first!
            True

            >>> del x.value
            >>> x.value
            Traceback (most recent call last):
            ...
            friendlysam.opt.NoValueError

        """
        try:
            return self._value
        except AttributeError:
            if replace:
                return replace.get(self, self)
            else:
                return self


    def take_value(self, solution):
        """Try setting the value of this variable from a dictionary.

        Set ``self.value = solution[self]`` if possible.

        Raises:
            KeyError if ``solution[self]`` is not available.
        """
        try:
            self._value = solution[self]
        except KeyError as e:
            raise KeyError('variable {} is not in the solution'.format(repr(self))) from e

    __hash__ = object.__hash__

    def __eq__(self, other):
        return type(self) == type(other) and hash(self) == hash(other)


    def __str__(self):
        return self.name


    def __repr__(self):
        return short_default_repr(self, desc=str(self))


    def __float__(self):
        return float(self.value)


    def __int__(self):
        return int(self.value)

    @property
    def value(self):
        """Value property.

        Warning:

            There is nothing stopping you from setting ``value`` to a value
            which is inconsistent with the bounds and the domain of the variable.
        """
        try:
            return self._value
        except AttributeError as e:
            raise NoValueError() from e

    @value.setter
    def value(self, val):
        self._value = val

    @value.deleter
    def value(self):
        del self._value


class VariableCollection(object):
    """A lazy collection of :class:`Variable` instances.

    Use this class to create a family of variables. :class:`Variable`
    instances are created as needed, and then kept in the collection.

    Args:
        name (str, optional): Name of the variable family.
        **kwargs (optional): Passed on as keyword arguments to
            :class:`Variable` constructor.

    Examples:

        >>> x = VariableCollection('x')
        >>> x
        <friendlysam.opt.VariableCollection at 0x...: x>
        >>> x(1)
        <friendlysam.opt.Variable at 0x...: x(1)>

        >>> x = VariableCollection('y', lb=0, domain=Domain.integer)
        >>> x(1).lb
        0
        >>> x(1).domain
        <Domain.integer: 1>

    """

    def __init__(self, name=None, **kwargs):
        super().__init__()
        self.name = 'X{}'.format(self._next_counter()) if name is None else name
        self.name = _prefix_namespace(self.name)
        self._kwargs = kwargs
        self._vars = {}

    _counter = 0

    def _next_counter(self):
        VariableCollection._counter += 1
        return VariableCollection._counter

    def __call__(self, index):
        """Get a variable from the collection.

        A :class:`VariableCollection` is callable. You call the object to get
        a :class:`Variable` from the collection.

        Args:
            index (hashable object): The index of the requested variable.

        Returns:
            If the :class:`VariableCollection` has not been called earlier with this
            index, creates a new :class:`Variable` instance and returns it.

            If the index has been used before, the same :class:`Variable` instance
            will be returned.

        Examples:

            >>> x = VariableCollection('x')
            >>> x
            <friendlysam.opt.VariableCollection at 0x...: x>
            >>> x(1)
            <friendlysam.opt.Variable at 0x...: x(1)>
        """
        if not index in self._vars:
            name = '{}({})'.format(self.name, index)
            with namespace(''):
                variable = Variable(name=name, **self._kwargs)
            self._vars[index] = variable
        return self._vars[index]

    def _update_var_kwargs(self, key, value):
        self._kwargs[key] = value


    @property
    def ub(self):
        """Gets the upper bound of the contained variables.

        Warning:

            Gets the upper bound stored on the VariableCollection. The value
            on individual variables may have been changed individually.
        """
        return self._kwargs['ub']

    @ub.setter
    def ub(self, value):
        """Sets the upper bound of the contained variables.

        Warning:

            Overrides the value on all existing variables in the collection.
        """
        self._update_var_kwargs('ub', value)


    @property
    def lb(self):
        """Gets the lower bound of the contained variables.

        Warning:

            Gets the upper bound stored on the VariableCollection. The value
            on individual variables may have been changed individually.
        """
        return self._kwargs['lb']

    @lb.setter
    def lb(self, value):
        """Sets the lower bound of the contained variables.

        Warning:

            Overrides the value on all existing variables in the collection.
        """
        self._update_var_kwargs('lb', value)


    @property
    def domain(self):
        """Gets the domain of the contained variables.

        Warning:

            Gets the domain stored on the VariableCollection. The value
            on individual variables may have been changed individually.
        """
        return self._kwargs['domain']

    @domain.setter
    def domain(self, value):
        """Sets the domain of the contained variables.

        Warning:

            Overrides the value on all existing variables in the collection.
        """
        self._update_var_kwargs('domain', value)


    def __str__(self):
        return self.name


    def __repr__(self):
        return short_default_repr(self, desc=str(self))


class ConstraintError(Exception):
    """
    Raised when there is something wrong with a :class:`Constraint`.

    Attributes:
        constraint: The constraint that caused the problem.
    """
    
    def __init__(self, *args, **kwargs):
        self.constraint = kwargs.pop('constraint', None)
        super().__init__(*args, **kwargs)


class _ConstraintBase(object):
    """docstring for _ConstraintBase"""
    def __init__(self, desc=None, origin=None):
        super().__init__()
        self.desc = desc
        self.origin = origin

    @property
    def variables(self):
        raise NotImplementedError('this is a responsibility of subclasses')

    __repr__ = short_default_repr


class Constraint(_ConstraintBase):
    """An equality or inequality constraint.

    This class is used to wrap a constraint expression
    and (optionally) add some metadata.

    Args:
        expr (:class:`Relation` instance): An equality or inequality.
        desc (str, optional): A text describing the constraint.
        origin (anything, optional): Some object describing where the
            constraint comes from.

    Attributes:
        expr (``Relation`` instance)
        desc (str)
        origin
        variables: read only, shorthand for ``.expr.variables``

    Examples:

        >>> x = Variable('x')
        >>> c = Constraint(x + 1 <= 2 * x, desc='Some text')
        >>> print(c)
        <Constraint: Some text>
        >>> c.origin = 'randomly created'
        >>> print(c)
        <Constraint [randomly created]: Some text>
        >>> print(c.expr)
        x + 1 <= 2 * x

    """
    def __init__(self, expr, desc=None, origin=None):
        super().__init__(desc=desc, origin=origin)
        self.expr = expr
        self.origin = origin

    def __str__(self):
        if self.desc or self.origin:
            if self.origin:
                origin_text = ' [{}]'.format(self.origin)
            else:
                origin_text = ''
            return '<Constraint{}: {}>'.format(origin_text, self.desc)
        else:
            return repr(self)

    @property
    def long_description(self):
        return '{}\nDescription: {}\nOrigin: {}'.format(repr(self), self.desc, self.origin)


    @property
    def variables(self):
        return self.expr.variables
    


class _SOS(_ConstraintBase):
    """docstring for _SOS"""
    def __init__(self, level, variables, **kwargs):
        super().__init__(**kwargs)
        if not (isinstance(variables, tuple) or isinstance(variables, list)):
            raise ConstraintError('variables must be a tuple or list')
        self._variables = tuple(variables)
        self._level = level

    @property
    def level(self):
        return self._level
    

    def __str__(self):
        return 'SOS{}{}'.format(self._level, self._variables)

    @property
    def variables(self):
        return self._variables


class SOS1(_SOS):
    """Special ordered set, type 1

    An ordered set of variables, of which **at most one** may be nonzero.
    
    Add a :class:`SOS1` instance to an optimization problem just like a
    :class:`Constraint` to enforce this condition.

    Args:
        variables (sequence of :class:`Variable` instances): The variables
            in the ordered set. Must be an ordered sequence (today
            ``list`` and ``tuple`` are allowed).
        desc (str, optional): A text describing the constraint.
        origin (anything, optional): Some object describing where the
            constraint comes from.

    Attributes:
        variables
        desc (str)
        origin

    """
    def __init__(self, variables, **kwargs):
        super().__init__(1, variables, **kwargs)


class SOS2(_SOS):
    """Special ordered set, type 2

    An ordered set of variables, of which **at most two** may be nonzero,
    and that any nonzero variables must be adjacent in order.

    Add a :class:`SOS2` instance to an optimization problem just like a
    :class:`Constraint` to enforce this condition.

    Args:
        variables (sequence of :class:`Variable` instances): The variables
            in the ordered set. Must be an ordered sequence (today
            ``list`` and ``tuple`` are allowed).
        desc (str, optional): A text describing the constraint.
        origin (anything, optional): Some object describing where the
            constraint comes from.

    Attributes:
        variables
        desc (str)
        origin

    """
    def __init__(self, variables, **kwargs):
        super().__init__(2, variables, **kwargs)


class _Objective(object):
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    @property
    def variables(self):
        return self.expr.variables
    

class Maximize(_Objective):
    """A maximization objective.

    Args:
        expr (expression or :class:`Variable` instance):
            An expression to maximize.

    Attributes:
        expr
        variables: read only, shorthand for ``.expr.variables``

    Examples:

        >>> x = VariableCollection('x')
        >>> prob = Problem()
        >>> prob.objective = Maximize(Sum(x(i) for i in range(50)))

    """
    pass

class Minimize(_Objective):
    """A minimization objective.

    Args:
        expr (expression or :class:`Variable` instance):
            An expression to minimize.

    Attributes:
        expr
        variables: read only, shorthand for ``.expr.variables``

    Examples:

        >>> x = VariableCollection('x')
        >>> prob = Problem()
        >>> prob.objective = Minimize(Sum(x(i) for i in range(50)))

    """
    pass

def dot(a, b):
    """Make expression for the scalar product of two vectors.

    ``dot(a, b)`` is equivalent to ``Sum(ai * bi for ai, bi in zip(a, b))``.

    Returns:
        An expression.

    Examples:

        >>> n = 10
        >>> coefficients = (2 ** i for i in range(n))
        >>> x = VariableCollection('x')
        >>> vars = [x(i) for i in range(n)]
        >>> dot(coefficients, vars)
        <friendlysam.opt.Sum at 0x...>
    """
    return Sum(ai * bi for ai, bi in zip(a, b))

def piecewise_affine(points, name=None):
    """Create a piecewise affine expression and constraints.

    There are several ways to express piecewise affine functions in
    MILP problems. This function helps with one of them, using SOS2 variables.

    **Definition:**

        :math:`f(x)` is the linear interpolation of a data set 
        :math:`(x_0, y_0), (x_1, y_1), \ldots, (x_n, y_n)`.

        The :math:`x_i` are ordered: :math:`x_0 \leq x_1 \leq \ldots \leq x_n`.

        See http://en.wikipedia.org/wiki/Linear_interpolation

    Args:
        points (dict or sequence of pairs): The :math:`x_i, y_i` pairs.

            **Alternative 1:** Provide a ``dict``, e.g.
            ``{x0: y0, x1: y1, ..., x_n: y_n}``.

            **Alternative 2:** Provide a sequence of pairs, e.g.
            ``[(x0, y0), (x1, y1), ..., (xn, yn)]``

            The points are automatically sorted in increasing ``x_i``.

        name (str, optional): A name base for the variables.

    Returns:
        ``(x, y, constraints)``

        ``x`` is an expression for the argument of the function.

        ``y`` is an expression for the function value.

        ``constraints`` is a set of :class:`SOS2` and :class:`Constraint`
        instances that must be added to an optimization problem to enforce
        the relation between ``x`` and ``y``.

    Examples:
        >>> points = {1: 30, 1.5: 20, 2: 40}
        >>> x, y, constraints = fs.piecewise_affine(points, name='pwa_vars')
        >>> prob = fs.Problem()
        >>> prob.objective = fs.Minimize(y)
        >>> prob.add(constraints)
        >>> solution = get_solver().solve(prob)
        >>> for var in x.variables:
        ...     var.take_value(solution)
        ... 
        >>> float(x) == 1.5
        True
        >>> float(y) == 20
        True

    """

    points = dict(points).items()
    points = sorted(points, key=lambda p: p[0])
    x_vals, y_vals = zip(*points)

    v = VariableCollection(name=name, lb=0, ub=1, domain=Domain.real)
    variables = tuple(v(x) for x in x_vals)
    x = dot(x_vals, variables)
    y = dot(y_vals, variables)
    constraints = piecewise_affine_constraints(variables, include_lb=False)
    return x, y, constraints

def piecewise_affine_constraints(variables, include_lb=True):
    """Constrains for a piecewise affine expression.

    For some variables :math:`x_0, x_1, \ldots, x_n`, this function creates

        * A :class:`SOS2` constraint for the variables.
        * A constraint that :math:`\sum_{i=0}^n x_i = 1`.
        * For each variable :math:`x_i`, a constraint that :math:`x_i \geq 0`.

    It is used by :func:`piecewise_affine`.

    Args:
        variables (sequence of :class:`Variable` instances)
        include_lb (boolean, optional): If ``True`` (the default), lower bound
            constraints ``x[i] >= 0`` are created for the variables.
            Set to ``False`` if  your variables already have lower bounds
            ``>= 0`` and you want to avoid a few redundant constraints.

    Returns:

        set: A set of :class:`SOS2` and :class:`Constraint` instances.
    """
    variables = tuple(variables)
    return set.union(
        {
            SOS2(variables, desc='Picewise affine'),
            Constraint(Eq(Sum(variables), 1), desc='Piecewise affine sum')
        },
        {
            Constraint(v >= 0, 'Piecewise affine weight') for v in variables
        })


class Problem(object):
    """An optimization problem.

    The problem class is essentially a container for an objective
    function and a set of constraints.

    Attributes:
        objective: The objective function of the optimization problem,
            represented by a :class:`Maximize` or :class:`Minimize` instance.

        constraints: Read only. A set of constraints.

    Examples:

        >>> x = VariableCollection('x')
        >>> prob = Problem()
        >>> prob.objective = Maximize(x(1) + x(2))
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

    """
    def __init__(self):
        super().__init__()
        self._constraints = set()

    def _add_constraint(self, constraint):
        if isinstance(constraint, Relation):
            constraint = Constraint(constraint, 'Ad hoc constraint')
        if not isinstance(constraint, (Constraint, _SOS)):
            raise ConstraintError('{} is not a valid constraint'.format(constraint))
        self._constraints.add(constraint)

    def add(self, *constraints):
        """Add zero or more constraints to the problem.

        Args:
            *constraints: zero or more constraints or iterables of constraints.
                Each constraint should be an instance of :class:`Relation`,
                :class:`Constraint`, :class:`SOS1` or :class:`SOS2`.

        Note:

            The syntax ``problem += constraints`` is equivalent
            to ``problem.add(constraints).

        Examples:

            >>> prob = Problem()
            >>> x = VariableCollection('x')

            >>> prob.add(8 * x(1) + 4 * x(2) <= 11)

            >>> prob += Constraint(x(0) <= x(1), desc='Some description')

            >>> prob += ([x(i) <= i, x(i+1) <= i] for i in range(5))

        """
        for constraint in constraints:
            try:
                for constraint in constraint:
                    self._add_constraint(constraint)
            except TypeError:
                self._add_constraint(constraint)

    def __iadd__(self, addition):
        try:
            addition = iter(addition)
        except TypeError:
            addition = (addition,)
        self.add(*addition)
        return self

    def variables_without_value(self):
        """Get all :class:`Variable` instances without value.

        These are effectively the variables of the optimization problem.
        """
        sources = set(self.constraints) | {self.objective}
        variables = set(chain(*(src.variables for src in sources)))
        return set(v for v in variables if not hasattr(v, 'value'))

    @property
    def constraints(self):
        return self._constraints


CONCRETE_EVALUATORS = {
    Eq: operator.eq,
    Less: operator.lt,
    LessEqual: operator.le,
    Add: operator.add,
    Sub: operator.sub,
    Mul: operator.mul,
    Sum: lambda *x: sum(x)
}
