API reference
===================

.. currentmodule:: friendlysam.opt

Variables
--------------------------

.. autosummary::
  :toctree: generated/

  Variable
  VariableCollection
  Domain
  namespace

Expressions
-------------------------
.. autosummary::
  :toctree: generated/
  
  Operation
  Add
  Sub
  Mul
  Sum
  dot
  Relation
  Less
  LessEqual
  Eq

Constraints and optimization
-----------------------------
.. autosummary::
  :toctree: generated/

  get_solver
  Problem
  Maximize
  Minimize
  Constraint
  SOS1
  SOS2
  piecewise_affine
  piecewise_affine_constraints




Models
---------------------------

.. currentmodule:: friendlysam.parts

.. autosummary::
  :toctree: generated/

  Part
  Node
  FlowNetwork
  Cluster
  Storage
  ConstraintCollection


.. currentmodule:: friendlysam.models

.. autosummary::
  :toctree: generated/

  MyopicDispatchModel


Utilities
-------------------------

.. currentmodule:: friendlysam.util

.. autosummary::
  :toctree: generated/

  get_list
  get_series


Exceptions
----------------------

.. currentmodule:: friendlysam.opt
.. autosummary::
  :toctree: generated/

  ConstraintError
  NoValueError
  SolverError

.. currentmodule:: friendlysam
.. autosummary::
  :toctree: generated/

  InsanityError