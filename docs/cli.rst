Command-Line Tool (`obudump`)
=============================

The `pyobuparse` package includes a command-line tool called `obudump`
for inspecting AV1 bitstreams within IVF (Indeo Video Format) files.

Installation
------------

When you install the `pyobuparse` package, the `obudump` tool is automatically
made available in your environment if the scripts directory is in your PATH.

See the :doc:`installation` page for details.

Usage
-----

To use `obudump`, you provide the path to an IVF file:

.. code-block:: bash

   obudump /path/to/your/video.ivf

This will print basic information about each OBU found in every frame of the
IVF file, including its type, size, temporal ID, and spatial ID.

Options
-------

``--verbose``, ``-v``
  Enables verbose output. In this mode, `obudump` will attempt to parse
  the payload of each OBU using the library's parsing functions and print
  a summary of the parsed data.

  .. code-block:: bash

     obudump --verbose video.ivf

``--max-obus N``
  Limits the number of OBUs printed per IVF frame to `N`. This is useful for
  brevity when inspecting files with many OBUs per frame.

  .. code-block:: bash

     obudump --max-obus 5 video.ivf

``--help``
  Shows the help message and exits.

Example Output (Basic)
----------------------

.. code-block:: text

   IVF Header: Version=0, Length=32, Codec=b'AV01', WxH=1920x1080, FPS=30/1, Frames=150
   Processed 0 frames from IVF file. (This is a sample stderr line before frames)

   IVF Frame 1: Size=12345, PTS=0
     OBU: Type=OBP_OBU_SEQUENCE_HEADER (1), Size=50, TID=0, SID=0
     OBU: Type=OBP_OBU_FRAME_HEADER (3), Size=20, TID=0, SID=0
     OBU: Type=OBP_OBU_TILE_GROUP (4), Size=12275, TID=0, SID=0
   
   IVF Frame 2: Size=6789, PTS=1
     OBU: Type=OBP_OBU_FRAME_HEADER (3), Size=18, TID=0, SID=0
     OBU: Type=OBP_OBU_TILE_GROUP (4), Size=6771, TID=0, SID=0
   ...

Example Output (Verbose)
------------------------

.. code-block:: text

   IVF Header: Version=0, Length=32, Codec=b'AV01', WxH=1920x1080, FPS=30/1, Frames=150
   Processed 0 frames from IVF file.

   IVF Frame 1: Size=12345, PTS=0
     OBU: Type=OBP_OBU_SEQUENCE_HEADER (1), Size=50, TID=0, SID=0
       Parsed SequenceHeader: profile=0, max_width=1920, max_height=1080
     OBU: Type=OBP_OBU_FRAME_HEADER (3), Size=20, TID=0, SID=0
       Parsed FrameHeader: type=KEY_FRAME, width=1920, height=1080, order_hint=0
     OBU: Type=OBP_OBU_TILE_GROUP (4), Size=12275, TID=0, SID=0
       Found TileGroup OBU (verbose parsing not yet implemented for standalone TG here)
   ...

(Note: The exact verbose output format may vary.)

Error Handling
--------------

`obudump` will print error messages to standard error if:
* The specified IVF file is not found.
* The IVF file header is invalid.
* An error occurs while iterating through OBUs in a frame.
* An error occurs during the verbose parsing of an OBU payload.
