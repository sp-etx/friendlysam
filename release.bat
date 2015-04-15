rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q friendlysam.egg-info
python setup.py sdist bdist_wheel bdist_wininst
twine upload dist/*