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

def rename_namespace(s):
    global _namespace_string
    if _namespace_string == '':
        return str(s)
    return '{}.{}'.format(_namespace_string, s)

@contextmanager
def namespace(name):
    global _namespace_string
    old = _namespace_string
    _namespace_string = str(name)
    yield
    _namespace_string = old


def get_solver(options=None):
    if options is None:
        options = {}
    engine = options.pop('engine', 'pulp')

    if engine == 'pulp':            
        from friendlysam.solvers.pulpengine import PulpSolver
        return PulpSolver(options)

class SolverError(Exception): pass
        
class NoValueError(AttributeError): pass

class Domain(Enum):
    """docstring for Domain"""
    real = 0
    integer = 1
    binary = 2

DEFAULT_DOMAIN = Domain.real

class Operation(object):
    """An operation on some arguments.

    This is a base class. Concrete examples:

    Arithmetic operations: :class:`Add`, :class:`Sub`, :class:`Mul`, :class:`Sum`
    Relations: :class:`Less`, :class:`LessEqual`, :class:`Eq`, :class:`GreaterEqual`,
        :class:`Greater`

    Note:
        The :class:`Variable` class and the arithmetic operation classes have
        overloaded operators which create :class:`Operation` instances.

    Examples:

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
        """The arguments of the operation.

        See :meth:`create`.

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
        """All :attr:`leaves` which are instances of :class:`Variable`.

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

def _is_zero(something):
    return isinstance(something, numbers.Number) and something == 0


class _MathEnabled(object):
    """docstring for _MathEnabled"""

    def __add__(self, other):
        return self if _is_zero(other) else Add(self, other)

    def __radd__(self, other):
        return self if _is_zero(other) else Add(other, self)

    def __sub__(self, other):
        return self if _is_zero(other) else Sub(self, other)

    def __rsub__(self, other):
        return -self if _is_zero(other) else Sub(other, self)

    def __mul__(self, other):
        return 0 if _is_zero(other) else Mul(self, other)

    def __rmul__(self, other):
        return 0 if _is_zero(other) else Mul(other, self)

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


class Sum(Operation, _MathEnabled):
    """A sum of items

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
        if len(vector) == 0:
            return 0
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
        return super().__new__(cls, *args)


    def __str__(self):
        return 'Sum({})'.format(', '.join(str(a) for a in self.args))


class Add(Operation, _MathEnabled):
    """docstring for Add"""
    _format = '{} + {}'
    _priority = 1


class Sub(Operation, _MathEnabled):
    """docstring for Sub"""
    _format = '{} - {}'
    _priority = 1
        
    
class Mul(Operation, _MathEnabled):
    """docstring for Mul"""
    
    _format = '{} * {}'
    _priority = 2


class Variable(_MathEnabled):
    """docstring for Variable"""

    _counter = 0

    def _next_counter(self):
        Variable._counter += 1
        return Variable._counter


    def __init__(self, name=None, lb=None, ub=None, domain=DEFAULT_DOMAIN):
        super().__init__()
        self.name = 'x{}'.format(self._next_counter()) if name is None else name
        self.name = rename_namespace(self.name)
        self.lb = lb
        self.ub = ub
        self.domain = domain


    def evaluate(self, replace=None, evaluators=None):
        try:
            return self._value
        except AttributeError:
            return self


    def take_value(self, solution):
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
    """docstring for VariableCollection"""
    def __init__(self, name=None, **kwargs):
        super().__init__()
        self.name = 'X{}'.format(self._next_counter()) if name is None else name
        self.name = rename_namespace(self.name)
        self._kwargs = kwargs
        self._vars = {}

    _counter = 0

    def _next_counter(self):
        VariableCollection._counter += 1
        return VariableCollection._counter

    def __call__(self, index):
        if not index in self._vars:
            name = '{}({})'.format(self.name, index)
            with namespace(''):
                variable = Variable(name=name, **self._kwargs)
            self._vars[index] = variable
        return self._vars[index]


    def __str__(self):
        return self.name


    def __repr__(self):
        return short_default_repr(self, desc=str(self))


    def __truediv__(self, other):
        raise fs.InsanityError().with_traceback(sys.exc_info()[2])


class ConstraintError(Exception):
    """docstring"""
    
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
    """docstring for Constraint"""
    def __init__(self, expr, desc=None, **kwargs):
        super().__init__(desc=desc, **kwargs)
        self.expr = expr

    def __str__(self):
        if self.desc or self.origin:
            if self.origin:
                origin_text = ' from ' + str(self.origin)
            else:
                origin_text = ''
            return '<Constraint{}: {}>'.format(origin_text, self.desc)
        else:
            return repr(self)


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
    """docstring for SOS1"""
    def __init__(self, variables, **kwargs):
        super().__init__(1, variables, **kwargs)


class SOS2(_SOS):
    """docstring for SOS2"""
    def __init__(self, variables, **kwargs):
        super().__init__(2, variables, **kwargs)


class _Objective(object):
    """docstring for _Objective"""
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    @property
    def variables(self):
        return self.expr.variables
    

class Maximize(_Objective):
    """docstring for Maximize"""
    pass

class Minimize(_Objective):
    """docstring for Minimize"""
    pass

def dot(a, b):
    return Sum(ai * bi for ai, bi in zip(a, b))

def piecewise_affine(points, name=None):
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
    return set.union(
        {
            SOS2(variables, desc='Picewise affine'),
            Constraint(Eq(Sum(variables), 1), desc='Piecewise affine sum')
        },
        {
            Constraint(v >= 0, 'Piecewise affine weight') for v in variables
        })


class Problem(object):
    """An optimization problem"""
    def __init__(self, constraints=None, objective=None):
        super().__init__()
        self._constraints = set() if constraints is None else constraints
        self.objective = objective

    def _add_constraint(self, constraint):
        if isinstance(constraint, Relation):
            constraint = Constraint(constraint, 'Ad hoc constraint')
        if not isinstance(constraint, (Constraint, _SOS)):
            raise ConstraintError('{} is not a valid constraint'.format(constraint))
        self._constraints.add(constraint)

    def add(self, *additions):
        """docstring"""
        for constraint in additions:
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
        sources = set(self.constraints) | {self.objective}
        variables = set(chain(*(src.variables for src in sources)))
        return set(v for v in variables if not hasattr(v, 'value'))

    @property
    def constraints(self):
        return self._constraints

    def solve(self):
        """Try to solve the optimization problem"""
        raise NotImplementedError()

CONCRETE_EVALUATORS = {
    Eq: operator.eq,
    Less: operator.lt,
    LessEqual: operator.le,
    Add: operator.add,
    Sub: operator.sub,
    Mul: operator.mul,
    Sum: lambda *x: sum(x)
}
