How to install Friendly Sam
=============================


Get Python 3
----------------

Friendly Sam is developed in `Python 3 <https://www.python.org/downloads/>`_ (at the time of this writing, Python 3.4). Download and install it now, if you haven't already.

.. _virtual-environment:

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

	Basically, you follow the instructions for Windows above but exchange ``C:\Python34\python.exe`` for something more suitable, and then do ``vex my_project_name bash`` instead. Also see the docs for `vex <https://pypi.python.org/pypi/vex>`_ if you have problems. Make sure your ``pip`` and ``python`` commands points to ``pip3`` and ``python3`` respectively, in case you have multiple versions of python installed.

If you get the error: ``distutils.errors.DistutilsOptionError: can't combine user with prefix`` when trying to install vex, execute pip with the --prefix flag: 
``pip install --user --install-option="--prefix=" vex``

Install Friendly Sam
-----------------------------

Assuming you have entered/activated your Python virtual environment, or wherever you want to install it, open a command prompt/shell and run the command::

	pip install friendlysam

Optional dependencies
^^^^^^^^^^^^^^^^^^^^^^^

If you want to add support for ``pandas`` related stuff, or for saving and loading models using ``dill``, do one of::

    pip install friendlysam[pandas]
    pip install friendlysam[pickling]
    pip install friendlysam[pandas,pickling]


