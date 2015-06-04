# Friendly Sam change log

## [unreleased] - unreleased

## [0.2.0] - 2015-06-04

### Added
- Added the `MyopicDispatchModel`.
- Added `get_solver()` function.
- Added `resources` property to `Part`.
- Improved expressions and variables: `Sum` class and support for division.
- New helper functions for creating piecewise affine functions.
- New time functionality on `Part`.

### Changed
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
