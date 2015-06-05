For developers
===========================

Install in developer mode
----------------------------

If you are developing the source code of Friendly Sam, you probably want to install it in "develop" mode instead. This has two benefits. First, you get some extra dependencies such as ``nose`` (testing package), ``sphinx`` (documentation package) and ``twine`` and ``wheel`` (used for releasing), etc. Second, you won't have to reinstall the package into your Python site-packages directory every time you change something.

1. Get `Python 3 <https://www.python.org/downloads/>`_. (Note: If you are on Windows it might be convenient to use a ready-made distribution like `WinPython <https://winpython.github.io/>`_ and skip step 5 below, but we can't guarantee it will work.)

2. Download the source code

    * **Alternative 1:** Download a zip file: https://github.com/sp-etx/friendlysam/archive/master.zip

    * **Alternative 2:** If you know git, clone into the repository::

            git clone https://github.com/sp-etx/friendlysam.git

3. You probably want to install Friendly Sam in a :ref:`virtual environment <virtual-environment>`. Create one and activate it before you take the next step.

4. Now, to install Friendly Sam in develop mode, do this::

        pip install -r develop.txt


.. note::

    If you are on Windows, ``pip``-installation of some packages will fail if you don't have a compiler correctly configured. One such example is NumPy. A simple way around it is to install binaries from `Christoph Gohlke's website <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ for the packages that throw errors when you do ``pip install -r develop.txt``.

    Let's say you are on Windows and download an installer called something like ``numpy-MKL-1.9.0.win-amd64-py3.4.exe``. Don't just run the file, because then it will be installed in your "main" Python installation (usually at ``C:\Python34``). Instead,  do this:

    1. Open a command prompt.
    
    2. Go into your virtual environment (e.g. ``vex my_project_name cmd``).
    
    3. (option a) Do this::

        easy_install numpy-MKL-1.9.0.win-amd64-py3.4.exe

    3. (option b) Or, if you have a wheels file ``something.whl``, do this::

        pip install something.whl


Make Sphinx documentation
----------------------------

The documentation for residues is made with `Sphinx <http://sphinx-doc.org/latest/index.html>`_ and hosted with `Read the Docs <https://readthedocs.org/>`_. To parse nice, human-readable docstrings, we use `Napoleon <http://sphinxcontrib-napoleon.readthedocs.org/en/latest/>`_.

* If you want to make a very minor change to the documentation, you can actually just edit the source, push to the github repository and `magically <http://read-the-docs.readthedocs.org/en/latest/webhooks.html>`_, the docs will update at readthedocs.org.

* However, if you want to edit the docs a lot, you probably want to make test builds on your own machine. In that case, you need to `learn about Sphinx <http://sphinx-doc.org>`_. To build the docs, open a command prompt, go to ``friendlysam\docs`` and run the command::

    make html

The resulting HTML can be previewed under ``friendlysam\docs\_build\index.html``.

Releasing Friendly Sam
---------------------------

If Friendly Sam is installed in develop mode, you should already have `twine <https://pypi.python.org/pypi/twine>`_ (for secure communication with PyPI) and `wheel <https://pypi.python.org/pypi/wheel>`_ (for building wheel distribution files).

    1. To put things on PyPI, you have to register on PyPI, and you should register on the test PyPI too:

        https://pypi.python.org/pypi

        https://testpypi.python.org/pypi

    2. Make sure that your account is activated. You should get an email from PyPI.

    3. Make sure you are added as a maintainer of the friendlysam repository at PyPI/testPyPI.

    4. Create yourself a file called ``.pypirc`` and put it in your home directory. If you are on Windows, the file path should be``C:\Users\yourusername\.pypirc``. Put the following content in it::

        [distutils]
        index-servers =
            pypi
            test

        [pypi]
        repository:https://pypi.python.org/pypi
        username:your_pypi_username

        [test]
        repository:https://testpypi.python.org/pypi
        username:your_testpypi_username

    5. (Windows users) For Windows, there is a nice ``pypi.bat`` you can use.

        To register info about the package on PyPI, first push to the PyPI test site::

            pypi.bat register test

        You will be asked for your PyPI test password. Make sure it turned out as you wanted. Then do the real thing::

            pypi.bat register pypi

        To build and upload the distribution, do this::

            pypi.bat upload test

        Twine will upload to PyPI and ask you for username and password. Check on the test site that everything is OK. You can also run ``pip install ...`` from the test repo to be sure. Then upload the package to the real repo by running::

            pypi.bat upload pypi

    5. (Linux/Mac users) You can easily translate ``pypi.bat`` into a bash script. Please do so and contribute it to the repository!
