API Reference
=============

This section provides detailed API documentation for the `pyobuparse` library
and its command-line interface.

Library API (`pyobuparse.parser`)
---------------------------------

.. automodule:: pyobuparse.parser
   :members:
   :undoc-members:
   :show-inheritance:

Command-Line Interface (`pyobuparse.cli`)
-----------------------------------------

.. automodule:: pyobuparse.cli
   :members: main, parse_ivf_header, parse_ivf_frame_header
   :undoc-members:
   :show-inheritance:

Internal C Wrapper (`pyobuparse._c_wrapper`)
--------------------------------------------
While not intended for direct public use, the C wrapper's enums might be useful for reference.

.. automodule:: pyobuparse._c_wrapper
   :members: OBPOBUType, OBPMetadataType, OBPColorPrimaries, OBPTransferCharacteristics, OBPMatrixCoefficients, OBPChromaSamplePosition, OBPFrameType
   :undoc-members:
   :show-inheritance:
