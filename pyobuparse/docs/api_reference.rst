API Reference
=============

This page provides an auto-generated summary of PyObuParse's API.

Main Parser Module
------------------

.. automodule:: pyobuparse.parser
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. note::
      Due to previous tooling issues, docstrings for some classes within
      this module (specifically `SequenceHeader` and `FrameHeader`) may be
      incomplete or not up-to-date in the generated documentation.

Error Handling
--------------
The primary exception raised by this library is `pyobuparse.parser.OBUParseError`.
It is documented as part of the `pyobuparse.parser` module above.
If specific details are needed here, they can be added, but `automodule` for
`pyobuparse.parser` should cover it.
The `OBUParseError` class is part of `pyobuparse.parser` and will be documented
when `pyobuparse.parser` is processed by `automodule`.

Low-Level C Wrapper (Advanced)
------------------------------
This module provides the low-level ctypes interface to the C library.
These are typically for internal use or advanced scenarios.

.. automodule:: pyobuparse._c_wrapper
   :members: OBPOBUType, OBPMetadataType, OBPColorPrimaries, OBPTransferCharacteristics, OBPMatrixCoefficients, OBPChromaSamplePosition, OBPFrameType, OBPError, OBPState, free_obp_error_string
   :undoc-members:
