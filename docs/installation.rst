Installation
============

Python Version
--------------

`pyobuparse` requires Python >= 3.7.

From Source (Development / Current Method)
------------------------------------------

To install `pyobuparse` from a source checkout (e.g., after cloning the repository):

1.  **Prerequisites**:
    *   A C compiler compatible with your Python distribution (e.g., GCC, Clang, MSVC).
    *   Python development headers. These are often in a package like `python3-dev`
        or `python3-devel`.
    *   `pip` for installing the package.
    *   `setuptools` and `wheel` (usually installed with pip).

    Example for Debian/Ubuntu:
      .. code-block:: bash

         sudo apt-get update
         sudo apt-get install build-essential python3-dev python3-pip

    Example for Fedora:
      .. code-block:: bash

         sudo dnf install gcc python3-devel python3-pip

2.  **Clone the Repository** (if you haven't already):
    Obtain the source code, which includes the main `obuparse.c` library and the
    `pyobuparse` Python wrapper subdirectory.

3.  **Navigate and Install**:
    Change to the **root directory** of the cloned repository (this is the directory
    that contains the `pyobuparse` subdirectory, `obuparse.c`, etc.).
    Then, run:

    .. code-block:: bash

       pip install ./pyobuparse

    This command performs the following actions:
    *   Reads `pyobuparse/pyproject.toml` and `pyobuparse/setup.py`.
    *   Builds the C extension module, compiling `obuparse.c` (from the root)
        and the wrapper code.
    *   Installs the `pyobuparse` package into your Python environment.
    *   Installs the `obudump` command-line script.

4.  **Editable Install (for developers)**:
    If you are developing `pyobuparse`, you might prefer an editable install.
    From the same root directory:

    .. code-block:: bash

        pip install -e ./pyobuparse

    This allows you to make changes to the Python code and have them immediately
    effective without reinstalling. Changes to the C code will still require
    rebuilding (which `pip` might handle automatically on next run, or you might
    need to manually trigger a build or reinstall).

Verifying Installation
----------------------

After installation, you can verify it by:

1.  Trying to import the package in Python:

    .. code-block:: python

       import pyobuparse
       print(pyobuparse.__version__) # If __version__ is available

2.  Running the command-line tool:

    .. code-block:: bash

       obudump --help


Future Installation (PyPI)
--------------------------

Once the package is published to the Python Package Index (PyPI), installation
will be as simple as:

.. code-block:: bash

   pip install pyobuparse
