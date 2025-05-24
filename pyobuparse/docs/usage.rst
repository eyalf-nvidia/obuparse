Installation and Usage
========================

Installation
------------

To install PyObuParse, you can clone the repository and install it using pip:

.. code-block:: bash

   git clone <repository_url>  # Replace <repository_url> with the actual URL
   cd pyobuparse/pyobuparse    # Navigate into the pyobuparse sub-directory
   pip install .

This will install the package along with its dependencies, including compiling the C extension.

Basic Usage
-----------

### Using the Library

The `pyobuparse.parser` module provides functions to parse AV1 OBUs. The primary entry point is `iter_obus`, which iterates over OBUs in a byte stream.

.. code-block:: python

   from pyobuparse import iter_obus, parse_sequence_header
   from pyobuparse._c_wrapper import OBPOBUType

   # Example: Read from an IVF file (after skipping IVF headers)
   # with open("your_video.ivf", "rb") as f:
   #     # Skip IVF global header (32 bytes)
   #     f.seek(32)
   #     # Read IVF frame header (12 bytes)
   #     ivf_frame_header = f.read(12)
   #     if not ivf_frame_header:
   #         # Handle EOF
   #     packet_size = int.from_bytes(ivf_frame_header[:4], byteorder='little')
   #     packet_data = f.read(packet_size)

   # Assuming 'packet_data' contains one Annex B frame
   # For raw OBU streams, you can pass the data directly.
   
   # packet_data = b"your_obu_data_here" # Replace with actual OBU data
   # for obu_type, temporal_id, spatial_id, obu_payload in iter_obus(packet_data):
   #     print(f"Found OBU: Type={obu_type}, TemporalID={temporal_id}, SpatialID={spatial_id}, Size={len(obu_payload)}")
   #     if obu_type == OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
   #         try:
   #             seq_header = parse_sequence_header(obu_payload)
   #             print(f"  Profile: {seq_header.seq_profile}")
   #             # Access other sequence header fields...
   #         except OBUParseError as e:
   #             print(f"  Error parsing sequence header: {e}")

### Using the CLI Tool (`obudump`)

PyObuParse also provides a command-line tool `obudump` (similar to the C version)
for inspecting IVF files and printing OBU information in JSON format.

.. code-block:: bash

   obudump your_video.ivf > obu_info.json
   obudump --verbose your_video.ivf

See `obudump --help` for more options.

Contributing
------------

To contribute to PyObuParse:

1.  **Set up a development environment:**
    It's recommended to use a virtual environment.
    .. code-block:: bash

       python -m venv .venv
       source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
       pip install -e .[dev]      # Install in editable mode with dev dependencies (if defined)

2.  **Run tests:**
    Tests are located in the `pyobuparse/tests` directory and can be run using pytest.
    .. code-block:: bash

       pytest pyobuparse/tests

3.  **Build documentation:**
    Navigate to the `pyobuparse/docs` directory and build the documentation using Sphinx.
    .. code-block:: bash

       cd pyobuparse/docs
       make html

    The generated HTML will be in `pyobuparse/docs/_build/html`.

Please refer to the project's contribution guidelines for more details on submitting patches.
