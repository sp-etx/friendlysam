rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q friendlysam.egg-info
python setup.py bdist_wheel
twine upload dist/*