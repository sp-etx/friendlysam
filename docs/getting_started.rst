Getting started
=====================

No stable release is available yet. Instead, download the master development branch from the source code repository.

* **Alternative 1:** Download a zip file: https://github.com/sp-etx/friendlysam/archive/master.zip

* **Alternative 2:** If you know git, clone into the repository::

		git clone https://github.com/sp-etx/friendlysam.git


Get Python 3
----------------

Friendly Sam is developed in Python 3 (at the time of this writing, Python 3.4). Download and install it now, if you haven't already.


Use a virtual environment
------------------------------

It is highly recommended that you use a virtual environment. It's not strictly necessary, but if you choose not to, there is a risk that you will have conflicts between different versions of the packages that Friendly Sam and other Python packages depend on. Google for ``python virtualenv`` if you want to learn more. If not, you can also do it the way I do, using `vex <https://pypi.python.org/pypi/vex>`_.

* **If you are on Windows**
	1. Open a command prompt.
	2. Make sure you have the latest ``setuptools`` by running ``pip install setuptools --upgrade``
	3. Install vex by running ``pip install --user vex``
	4. Create a virtual environment named ``my_project_name`` and enter it by running ``vex -m --python C:\Python34\python.exe my_project_name cmd``

	Now, whenever you want to use your virtual environment, open a command prompt and run ``vex my_project_name cmd``.

* **If you are on Linux**

	Basically, you follow the instructions for Windows above, but exchange ``cmd`` for ``bash`` and ``C:\Python34\python.exe`` for something more suitable. Also see the docs for `vex <https://pypi.python.org/pypi/vex>`_ if you have problems.


Install Friendly Sam
-----------------------------

Assuming you have entered/activated your Python virtual environment, or wherever you want to install it, open a command prompt/shell and go to the place you downloaded (and unpacked) the source code. Stand in the directory containing ``setup.py`` and run the command::

	python setup.py install

This will install Friendly Sam. You are now ready to boot up Python and do ``import friendlysam``.


For developers
===========================

Install in developer mode
----------------------------

If you are developing the source code of Friendly Sam, you probably want to install it in "develop" mode instead. This has two benefits. First, you get some extra dependencies such as ``nose`` (testing package), ``sphinx`` (documentation package) and ``dill`` (used for pickling stuff). Second, you won't have to reinstall the package into your Python site-packages directory every time you change something.

To install Friendly Sam in develop mode, skip the previous step and instead do this::

	pip install -r develop.txt



Make Sphinx documentation
----------------------------

	The documentation for residues is made with `Sphinx <http://sphinx-doc.org/latest/index.html>`_ and hosted with `Read the Docs <https://readthedocs.org/>`_. To parse nice, human-readable docstrings, we use `Napoleon <http://sphinxcontrib-napoleon.readthedocs.org/en/latest/>`_.

	* If you want to make a very minor change to the documentation, you can actually just edit the source, push to the github repository and `magically <http://read-the-docs.readthedocs.org/en/latest/webhooks.html>`_, the docs will update at readthedocs.org.

	* However, if you want to edit the docs a lot, you probably want to make test builds on your own machine. In that case, you need to `learn about Sphinx <http://sphinx-doc.org>`_. The documentation is at least properly set up for a Windows environment in the repository, so you can just open a command prompt and go to ``friendlysam\docs`` and run the command ``make html``. The resulting HTML can be previewed under ``friendlysam\docs\_build\index.html
