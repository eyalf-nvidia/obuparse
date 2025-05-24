.. pyobuparse documentation master file, created by
   sphinx-quickstart on Tue Jul 12 12:00:00 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyobuparse's documentation!
======================================

`pyobuparse` is a Python library for parsing AV1 Object Bitstream Units (OBUs).
It provides a Pythonic interface to the underlying `obuparse` C library,
allowing for efficient iteration and parsing of OBU data from IVF files or
raw OBU streams.

Features:
---------
* Iterate through OBUs in a byte stream.
* Parse various OBU types, including:
    * Sequence Headers
    * Frame Headers
    * Tile Groups
    * Metadata (various types)
    * Tile Lists
* Pythonic data classes representing OBU structures.
* Command-line tool `obudump` for inspecting IVF files.

Table of Contents:
------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   installation
   usage
   api
   cli


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
