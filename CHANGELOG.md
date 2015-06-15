# Friendly Sam change log

## [X.Y.Z] - unreleased

## [0.3.0] - 2015-06-15

=======

### Added
 - A lot of documentation.
 - Added `ub`, `lb`, and `domain` to `VariableCollection`.
 - Added `long_description` to `Constraint`.
 - Added `capacity` keyword arg to `FlowNetwork.connect()`.
 - Added `FlowNetwork.get_flow()` method.

### Changed
 - Moved some `__init__` code to `__new__` to simplify inheritance of e.g. `Node`.
 - Node.resources now contains keys from inflows and outflows.
 - Renamed `ConstraintCollection.__call__()` to `.make()`.
 - Renamed `common` module to `util`.

### Removed
 - Removed Part.add_parts()

### Fixed
- Fixed a serious bug in `FlowNetwork`/`Node` implementation causing problems if one `Node` was connected in several `FlowNetwork`s.
- Doctests work under Linux


## [0.2.0] - 2015-06-08

### Added
- Added the `MyopicDispatchModel`.
- Added `get_solver()` function.
- Added `resources` property to `Part`.
- Improved expressions and variables: `Sum` class and support for division.
- Added an `evaluators` keyword to `evaluate()`, allowing drop-in of other functions (e.g. `pulp.lpSum` for the `Sum` operation).
- New helper functions for creating piecewise affine functions.
- New time functionality on `Part`. See examples in `tests/test_time.py`.
- A couple of convenience functions added for getting `list` or `pandas.Series` of values from functions like `Node.production[...]()`.
- New optional dependency, pandas.
- Wrote some documentation.

### Changed
- Changed indexing convention in `VariableCollection`, `ConstraintCollection`, etc, from multi-dimensional to one-dimensional: It is now `func(index)`, not `func(*indices)`.
- Renamed `ResourceNetwork` -> `FlowNetwork`.
- Simplified package structure significantly, resulting in modules and functions being renamed.
- Removed friendlysam.log module.
- Increased friendliness significantly (more consistent and helpful error messages, better `str()` and `repr()` functions, etc).

### Removed
- `Variable` can no longer have constraints. `PiecewiseAffine` class removed as a result.

### Fixed
- Fixed many minor bugs discovered during testing.


## [0.1.0] - 2015-04-15

First working release. Everything is a terrible mess.
