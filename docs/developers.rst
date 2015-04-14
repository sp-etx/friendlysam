For developers
===========================

Download the source code
-----------------------------

* **Alternative 1:** Download a zip file: https://github.com/sp-etx/friendlysam/archive/master.zip

* **Alternative 2:** If you know git, clone into the repository::

		git clone https://github.com/sp-etx/friendlysam.git


Install in developer mode
----------------------------

If you are developing the source code of Friendly Sam, you probably want to install it in "develop" mode instead. This has two benefits. First, you get some extra dependencies such as ``nose`` (testing package), ``sphinx`` (documentation package) and ``twine`` and ``wheel`` (used for releasing), etc. Second, you won't have to reinstall the package into your Python site-packages directory every time you change something.

To install Friendly Sam in develop mode, skip the previous step and instead do this::

	pip install -r develop.txt


Make Sphinx documentation
----------------------------

The documentation for residues is made with `Sphinx <http://sphinx-doc.org/latest/index.html>`_ and hosted with `Read the Docs <https://readthedocs.org/>`_. To parse nice, human-readable docstrings, we use `Napoleon <http://sphinxcontrib-napoleon.readthedocs.org/en/latest/>`_.

* If you want to make a very minor change to the documentation, you can actually just edit the source, push to the github repository and `magically <http://read-the-docs.readthedocs.org/en/latest/webhooks.html>`_, the docs will update at readthedocs.org.

* However, if you want to edit the docs a lot, you probably want to make test builds on your own machine. In that case, you need to `learn about Sphinx <http://sphinx-doc.org>`_. The documentation is at least properly set up for a Windows environment in the repository, so you can just open a command prompt and go to ``friendlysam\docs`` and run the command ``make html``. The resulting HTML can be previewed under ``friendlysam\docs\_build\index.html``.

Releasing Friendly Sam
---------------------------

If Friendly Sam is installed in develop mode, you should already have `twine <https://pypi.python.org/pypi/twine>`_ (for secure communication with PyPI and `wheel <https://pypi.python.org/pypi/wheel>`_ (for building wheel distribution files).

To make a new release on Windows, run in a command prompt::

	release.bat

What it does (at the time of this writing) is this::

	rmdir /S /Q dist
	rmdir /S /Q build
	rmdir /S /Q friendlysam.egg-info
	python setup.py bdist_wheel
	twine upload dist/*

Twine will upload to PyPI and ask you for username and password.

Updating the info on PyPI
----------------------------

To update the info shown on `PyPI <https://pypi.python.org/pypi/friendlysam>`_, change the info in ``setup.py``, ``DESCRIPTION.rst`` or whatever, and then run::

	python setup.py register
