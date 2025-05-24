Introduction
============

`pyobuparse` is a Python library designed for parsing AV1 (AOMedia Video 1)
Object Bitstream Units (OBUs). It acts as a wrapper around the efficient
`obuparse` C library, providing a user-friendly, Pythonic interface for
developers working with AV1 bitstreams.

Key functionalities include:

*   Iterating through individual OBUs within a larger data stream (e.g., from an IVF file frame).
*   Parsing specific OBU types to extract their structured data, such as:
    *   Sequence Header OBUs
    *   Frame Header OBUs
    *   Tile Group OBUs
    *   Various types of Metadata OBUs (HDR information, scalability, timecodes, etc.)
    *   Tile List OBUs
*   Representing parsed OBU data using clear Python data classes.
*   A command-line utility, `obudump`, for quick inspection and debugging of
    AV1 streams contained in IVF files.

This library is aimed at developers and researchers who need to inspect, analyze,
or manipulate AV1 bitstream data at the OBU level without delving into the
complexities of full video decoding.
