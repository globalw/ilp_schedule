Introduction
============
ilp_schedule is a python interface with the cutting edge integer linerar programming optimiser
SCIP developed at the `Konrad Zuse Institute Berlin <http://scip.zib.de/>`__. The code is enabling
developers to build user oriented software to solve large scale scheduling problems.

This project uses the  `SCIP Optimization Suite <http://scip.zib.de/>`__ and is to be handled
with the according attention to commercial usage rights. In order to install follow the installation
description in the Requirements.

Requirements
============

PySCIPOpt requires a working installation of the `SCIP Optimization Suite <http://scip.zib.de/>`__.
If SCIP is not installed in the global path you need to specify the install location using the
environment variable ``SCIPOPTDIR``:

-  | on Linux and OS X:
   | ``export SCIPOPTDIR=<path_to_install_dir>``

-  | on Windows:
   | ``set SCIPOPTDIR=<path_to_install_dir>``

``SCIPOPTDIR`` needs to have a subdirectory ``lib`` that contains the library, e.g. ``libscip.so``
(for Linux) and a subdirectory ``include`` that contains the corresponding header files:

::

    SCIPOPTDIR
      > lib
        > libscip.so ...
      > include
        > scip
        > lpi
        > nlpi
        > ...

If you are not using the installer packages, you need to `install the SCIP Optimization Suite
using CMake <http://scip.zib.de/doc/html/CMAKE.php>`__. The Makefile system is not compatible
with PySCIPOpt!

On Windows it is highly recommended to use the `Anaconda Python Platform <https://www.anaconda.com/>`__.

Installation from PyPI
======================

``pip install pyscipopt``

On Windows you may need to ensure that the ``scip`` library can be found at runtime by adjusting
your ``PATH`` environment variable:

-  on Windows:
   ``set PATH=%PATH%;%SCIPOPTDIR%\bin``

On Linux and OS X this is encoded in the generated PySCIPOpt library and therefore not necessary.

Building everything form source
===============================

PySCIPOpt requires `Cython <http://cython.org/>`__, at least version 0.21 (``pip install cython``).
Furthermore, you need to have the Python development files installed on your system (error
message "Python.h not found"):

::

    sudo apt-get install python-dev   # for Python 2, on Linux
    sudo apt-get install python3-dev  # for Python 3, on Linux

After setting up ``SCIPOPTDIR`` as specified above, please run

::

    python setup.py install

You may use the additional options ``--user`` or ``--prefix=<custom-python-path>``, to build
the interface locally.

Building with debug information
===============================

To use debug information in PySCIPOpt you need to build it like this:

::

    python setup.py install --debug

Be aware that you will need the **debug library** of the SCIP Optimization
Suite for this to work (``cmake .. -DCMAKE_BUILD_TYPE=Debug``).

Using the Scheduler
===============================
The software is build like a server-client application. You start the server in one command window with
::

   python server.py
   
When the server is running you enter in another command window
::

   python client.py
   
When the client connects to the server the computations of the optimizer will be carried out on another thread. Messages from the client are interpreted in server.py in the function
::

   check_for_commands(sharedMem,data)
   
please put your breakpoints there to interactively understand the formats and commands.
