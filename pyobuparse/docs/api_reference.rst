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

Error Handling
--------------
The primary exception raised by this library is:

.. autoclass:: pyobuparse.parser.OBUParseError
   :members:

Constants and Low-Level Wrappers (Advanced)
-------------------------------------------
These are typically for internal use or advanced scenarios.

.. automodule:: pyobuparse._c_wrapper
   :members: OBP_OBU_SEQUENCE_HEADER, OBP_OBU_TEMPORAL_DELIMITER, OBP_OBU_FRAME_HEADER, OBP_OBU_TILE_GROUP, OBP_OBU_METADATA, OBP_OBU_FRAME, OBP_OBU_REDUNDANT_FRAME_HEADER, OBP_OBU_TILE_LIST, OBP_OBU_PADDING, OBPMetadataType, OBPColorPrimaries, OBPTransferCharacteristics, OBPMatrixCoefficients, OBPChromaSamplePosition, OBPFrameType
   :undoc-members:
