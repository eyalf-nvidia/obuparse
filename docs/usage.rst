Usage
=====

This section provides examples of how to use the `pyobuparse` library
and the `obudump` command-line tool.

Library Usage
-------------

The primary way to use `pyobuparse` is to iterate through OBUs within a
frame's data and then, if needed, parse specific OBUs.

**1. Iterating through OBUs**

The `pyobuparse.iter_obus()` function is used to find OBU boundaries and get
basic OBU header information.

.. code-block:: python

   from pyobuparse import iter_obus, OBUParseError
   from pyobuparse._c_wrapper import OBPOBUType # For OBU type enums

   # Assume 'frame_data' is a bytes object from an IVF frame payload.
   # Example: A Sequence Header OBU followed by a Temporal Delimiter OBU.
   # OBU Header (Seq): type 1 (0x0A with size field) + Size (0x0b for 11 bytes) + Payload (11 zeros)
   # OBU Header (TD): type 2 (0x12 with size field) + Size (0x00 for 0 bytes)
   sample_obu_stream = b"\\x0a\\x0b" + (b"\\x00" * 11) + b"\\x12\\x00"
   frame_data = sample_obu_stream

   try:
       for obu_type, temporal_id, spatial_id, obu_payload in iter_obus(frame_data):
           type_name = obu_type.name if isinstance(obu_type, OBPOBUType) else f"UNKNOWN_TYPE_{obu_type}"
           print(f"Found OBU: Type={type_name}, Size={len(obu_payload)}, "
                 f"TID={temporal_id}, SID={spatial_id}")
           
           # 'obu_payload' contains the data for this specific OBU,
           # excluding its common OBU header.
           # You can now pass 'obu_payload' to specific parsing functions.

   except OBUParseError as e:
       print(f"Error iterating OBUs: {e}")

**2. Parsing Specific OBUs**

Once you have an `obu_payload` from `iter_obus`, you can parse it using
functions from `pyobuparse.parser`.

.. code-block:: python

   from pyobuparse import iter_obus, OBUParseError
   from pyobuparse.parser import (
       parse_sequence_header,
       parse_frame_header,
       parse_metadata,
       SequenceHeader, # For type hinting and context
       OBPStateWrapper # For stateful parsing
   )
   from pyobuparse._c_wrapper import OBPOBUType, OBPMetadataType

   # frame_data from previous example
   frame_data = b"\\x0a\\x0b" + (b"\\x00" * 11) + b"\\x12\\x00" 

   current_seq_header: SequenceHeader | None = None
   state_wrapper = OBPStateWrapper() # Maintains state for frame header parsing

   for obu_type, tid, sid, payload in iter_obus(frame_data):
       if obu_type == OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
           try:
               seq_header = parse_sequence_header(payload)
               current_seq_header = seq_header
               print(f"  Parsed Sequence Header: Profile={seq_header.seq_profile}, "
                     f"Max Frame Width={seq_header.max_frame_width_minus_1+1}")
               if seq_header.color_config:
                   print(f"    Color Primaries: {seq_header.color_config.color_primaries.name}")
           except OBUParseError as e:
               print(f"  Error parsing Sequence Header: {e}")
       
       elif obu_type == OBPOBUType.OBP_OBU_FRAME_HEADER:
           if not current_seq_header:
               print("  Cannot parse Frame Header: Sequence Header not seen yet.")
               continue
           try:
               fh = parse_frame_header(payload, current_seq_header, state_wrapper, tid, sid)
               print(f"  Parsed Frame Header: Type={fh.frame_type.name}, OrderHint={fh.order_hint}")
           except OBUParseError as e:
               print(f"  Error parsing Frame Header: {e}")

       # Example for Metadata (assuming metadata_obu_payload is available)
       # elif obu_type == OBPOBUType.OBP_OBU_METADATA:
       #     try:
       #         meta = parse_metadata(payload)
       #         meta_type_name = meta.type.name if isinstance(meta.type, OBPMetadataType) else meta.type # Corrected: meta.type
       #         print(f"  Parsed Metadata OBU: Type={meta_type_name}")
       #         if meta.metadata_hdr_cll:
       #             print(f"    MaxCLL: {meta.metadata_hdr_cll.max_cll}")
       #     except OBUParseError as e:
       #         print(f"  Error parsing Metadata OBU: {e}")

**3. Error Handling**

Parsing functions will raise `OBUParseError` if they encounter issues, such as
malformed data or insufficient bytes. Always wrap parsing calls in `try...except`
blocks.

.. code-block:: python

   try:
       # ... parsing calls ...
       pass
   except OBUParseError as e:
       print(f"A parsing error occurred: {e}")
   except Exception as e:
       print(f"An unexpected error: {e}")


Refer to the :ref:`api-reference` for detailed information on all available
parsing functions and the data classes they return.

Command-Line Tool (`obudump`)
-----------------------------

See the :doc:`cli` page for details on `obudump`.
