Command-Line Interface: `obudump`
===================================

The `pyobuparse` package provides a command-line tool called `obudump` for
inspecting AV1 OBU streams from IVF files. This tool is a Python-based
equivalent of the C `obudump` utility provided in the `libavif` reference
implementation and other AV1 parsing toolsets.

Usage
-----

.. code-block:: bash

   obudump [options] <input_file.ivf>

Arguments
---------

*   ``<input_file.ivf>``: Path to the input IVF file. This argument is required.

Options
-------

*   ``-h, --help``: Show the help message and exit.
*   ``--verbose``: Output OBU type as a string (e.g., "OBP_OBU_SEQUENCE_HEADER")
    instead of its integer value. This also enables indented JSON output for
    better readability.

Output
------

The tool outputs a JSON array to standard output. Each element in the array
is a JSON object representing a single OBU found in the input IVF file.

The JSON object for each OBU includes:

*   ``obu_type``: The type of the OBU (integer or string, depending on ``--verbose``).
*   ``offset_in_ivf_packet``: An *approximate* starting offset of the OBU's payload
    within the current IVF frame packet.
    *(Note: This offset calculation is an approximation in the Python version).*
*   ``obu_size``: The size of the OBU payload in bytes.
*   ``temporal_id``: The temporal ID of the OBU, if present in the OBU header extension.
*   ``spatial_id``: The spatial ID of the OBU, if present in the OBU header extension.

If the OBU type is one that the parser can provide detailed information for
(e.g., Sequence Header, Frame Header, Metadata), additional fields will be
present in the JSON object, nested under a key corresponding to the OBU type
(e.g., ``"sequence_header": {...}``, ``"frame_obu": {"frame_header": ..., "tile_group": ...}``).

Example
-------

.. code-block:: bash

   obudump --verbose my_video.ivf

This command would parse `my_video.ivf` and output detailed, human-readable
JSON information about each OBU to the console.

Automated Documentation
-----------------------

The `obudump` command-line tool is implemented in the
`pyobuparse.cli.obudump_py` module.

.. automodule:: pyobuparse.cli.obudump_py
   :members: main, obu_type_to_str
   :undoc-members:
   :show-inheritance:
   :noindex:
