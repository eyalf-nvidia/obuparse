# PyObuParse: Python AV1 OBU Parser

PyObuParse is a Python wrapper around the efficient `obuparse` C library, providing tools to parse individual AV1 Open Bitstream Units (OBUs). It's designed for scenarios where you need to inspect or manipulate AV1 OBU data at a low level from Python.

This wrapper uses `ctypes` to interface with the compiled C library, offering access to detailed OBU structures like Sequence Headers, Frame Headers, Metadata, etc.

## Features

*   Parses various AV1 OBU types:
    *   Sequence Header
    *   Frame Header (and full Frame OBUs)
    *   Tile Group
    *   Metadata
    *   Tile List
    *   Padding
    *   Temporal Delimiter
*   Provides an iterator (`iter_obus`) to easily extract OBUs from a byte stream.
*   Exposes detailed OBU structures and their fields.
*   Error handling for malformed OBUs.

## Requirements

*   Python 3.7+
*   A C compiler (GCC, Clang, MSVC) to build the bundled `obuparse` C library during installation. Standard build tools (`make`, etc.) are not strictly required for installation via pip, as setuptools handles the C extension build.

## Setting up a Virtual Environment (Recommended)

Before installing `pyobuparse` and its dependencies, it's highly recommended to create and activate a Python virtual environment. This isolates the project's dependencies from your global Python installation.

1.  **Create a virtual environment:**
    Open your terminal in the `pyobuparse` project directory and run:
    ```bash
    python -m venv .venv
    ```
    (You can replace `.venv` with your preferred environment name).

2.  **Activate the virtual environment:**
    *   On Windows (Command Prompt/PowerShell):
        ```bash
        .venv\Scripts\activate
        ```
    *   On macOS and Linux (bash/zsh):
        ```bash
        source .venv/bin/activate
        ```
    Your terminal prompt should change to indicate that the virtual environment is active.

## Installation

### From PyPI (Once Published)

```bash
pip install pyobuparse
```

### From Source (Local Build/Development)

1.  Clone the repository:
    ```bash
    git clone https_://github.com/google/pyobuparse.git # Replace with actual URL
    cd pyobuparse
    ```
2.  Install in editable mode (recommended for development):
    ```bash
    pip install -e .
    ```
    This will compile the C extension and install the package. To run tests, you might need to install pytest:
    ```bash
    pip install pytest
    ```

## Basic Usage

### Iterating through OBUs in a stream

```python
from pyobuparse import iter_obus, OBUParseError
from pyobuparse._c_wrapper import OBP_OBU_SEQUENCE_HEADER # For OBU type constants

# Example: data = b"your_av1_obu_stream_data_here"
# For this example, let's use the sample data from tests:
SAMPLE_SEQ_HEADER_PAYLOAD = b"\x00"*11 
SAMPLE_SEQ_HEADER_OBU = b"\x0a\x0b" + SAMPLE_SEQ_HEADER_PAYLOAD
SAMPLE_PADDING_OBU = b"\x7a\x01\x00"
data = SAMPLE_SEQ_HEADER_OBU + SAMPLE_PADDING_OBU

try:
    for obu_type, temporal_id, spatial_id, obu_payload in iter_obus(data):
        print(f"Found OBU: Type={obu_type}, TemporalID={temporal_id}, SpatialID={spatial_id}, Payload Length={len(obu_payload)}")
        if obu_type == OBP_OBU_SEQUENCE_HEADER:
            # You can then parse the specific OBU payload
            from pyobuparse import parse_sequence_header
            seq_header = parse_sequence_header(obu_payload)
            print(f"  Sequence Header Profile: {seq_header.seq_profile}")
            # Access other sequence header fields...
except OBUParseError as e:
    print(f"Error iterating OBUs: {e}")

```

### Parsing a specific OBU payload

```python
from pyobuparse import parse_sequence_header, OBUParseError

# Assuming 'seq_header_payload' is a bytes object containing only the Sequence Header OBU's payload
# (i.e., without the common OBU header or size fields)
seq_header_payload = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" # Placeholder from tests

try:
    seq_header = parse_sequence_header(seq_header_payload)
    print(f"Sequence Profile: {seq_header.seq_profile}")
    print(f"Still Picture: {seq_header.still_picture}")
    print(f"Reduced Still Picture Header: {seq_header.reduced_still_picture_header}")
    # Access other fields like seq_header.color_config.BitDepth, etc.
    if seq_header.timing_info: # Check if TimingInfo was present and parsed
      print(f"Time Scale: {seq_header.timing_info.time_scale}")

except OBUParseError as e:
    print(f"Error parsing Sequence Header: {e}")
```

## Building from Source (Detailed)

The package uses `setuptools` to build the C extension. When you run `pip install .` or `pip install -e .`, it should automatically compile `src/pyobuparse/obuparse.c`. Ensure you have a C compiler and Python development headers installed on your system.

*   On Debian/Ubuntu: `sudo apt-get install build-essential python3-dev`
*   On Fedora: `sudo yum groupinstall "Development Tools" && sudo yum install python3-devel`
*   On macOS: Xcode Command Line Tools (includes Clang)
*   On Windows: MSVC (Visual Studio Build Tools) are required. Ensure they are installed and correctly configured for command-line builds. The `pip install .` command should then be able to compile the C library.

### A Note on C Compiler Warnings

When building on Windows using MSVC, you may observe several `C4244` warnings related to data type conversions (e.g., `'=': conversion from 'uint64_t' to 'int', possible loss of data`). These warnings originate from the bundled `obuparse.c` library. While the Python wrapper aims to function correctly, these warnings indicate potential areas in the C code where data precision *could* be lost if extremely large numerical values are encountered that exceed the capacity of the smaller target types. For typical OBU parsing scenarios, these may not impact functionality, but users performing in-depth analysis or working with unusual AV1 streams should be aware of them. Addressing these warnings would require modifications to the underlying `obuparse.c` code.

## Running Tests

Tests are written using `pytest`.

1.  Install `pytest`:
    ```bash
    pip install pytest
    ```
2.  Run tests from the `pyobuparse` root directory:
    ```bash
    pytest
    ```

## API Documentation

Detailed API documentation, generated using Sphinx, will be available [here](link_to_gh_pages_or_readthedocs_once_available). (Placeholder)
For now, refer to the docstrings in the `pyobuparse/parser.py` module.

## License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.
The underlying `obuparse` C library is also licensed under ISC.

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.
(Further details can be added for contribution guidelines).
```
