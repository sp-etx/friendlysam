Getting started
=====================


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

Assuming you have entered/activated your Python virtual environment, or wherever you want to install it, open a command prompt/shell and run the command::

	pip install friendlysam


Make a simple model
------------------------

 ...
