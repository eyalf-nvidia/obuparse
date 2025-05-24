# pyobuparse

`pyobuparse` is a Python library for parsing AV1 (AOMedia Video 1) Object Bitstream Units (OBUs). It wraps the `obuparse` C library to provide an efficient and Pythonic way to inspect AV1 bitstreams. This is particularly useful for developers and researchers working with AV1 files at a low level, without needing a full decoder.

The library allows iteration through OBUs within a frame and parsing of various OBU types, including Sequence Headers, Frame Headers, Metadata, Tile Groups, and more. It also includes a command-line tool, `obudump`, for quick inspection of IVF files containing AV1 data.

## Features

*   Iterate through OBUs in a byte stream using `iter_obus()`.
*   Parse common OBU types with dedicated functions (e.g., `parse_sequence_header()`, `parse_frame_header()`):
    *   Sequence Header
    *   Frame Header (and Frame OBUs which combine Frame Header and Tile Group)
    *   Temporal Delimiter (identified by `iter_obus`, typically empty payload)
    *   Tile Group
    *   Metadata (HDR CLL, HDR MDCV, Scalability, ITU-T T.35, Timecode, and unregistered)
    *   Padding (identified by `iter_obus`)
    *   Tile List
*   Pythonic data classes representing OBU structures (e.g., `SequenceHeader`, `FrameHeader`, `ColorConfig`, `Metadata`).
*   Command-line tool `obudump` for inspecting AV1 IVF files.
*   Relies on the efficient `obuparse` C library for core parsing logic (not duplicated within this package).

## Installation

### From Source (Recommended for Development)

1.  **Prerequisites**:
    *   A C compiler (like GCC or Clang).
    *   Python development headers.
    *   `pip` and `setuptools`.
    *   On Debian/Ubuntu: `sudo apt-get install build-essential python3-dev python3-pip`
    *   On Fedora: `sudo dnf install gcc python3-devel python3-pip`
    *   (Similar commands for other systems)

2.  **Clone the Repository**:
    If you haven't already, clone the main repository that contains `obuparse.c`, `obuparse.h`, the `Makefile`, and the `pyobuparse` subdirectory.

3.  **Install**:
    Navigate to the root directory of the cloned repository (the one containing this `pyobuparse` subdirectory). Then, install the `pyobuparse` package using pip:
    ```bash
    pip install ./pyobuparse
    ```
    This command will:
    *   Invoke the build process defined in `pyobuparse/pyproject.toml` and `pyobuparse/setup.py`.
    *   Compile the C extension, linking against `obuparse.c` from the root directory.
    *   Install the `pyobuparse` Python package into your Python environment.
    *   Make the `obudump` command-line tool available.

### From PyPI (Once Published)

Once the package is published to the Python Package Index (PyPI), installation will be simpler:

```bash
pip install pyobuparse
```
(This is a future step and not yet available.)


## Usage

### As a Python Library

Here's a basic example of how to use `pyobuparse` to iterate through OBUs in a frame's data:

```python
from pyobuparse import iter_obus, OBUParseError
from pyobuparse.parser import (
    parse_sequence_header,
    parse_frame_header,
    # ... import other parsers as needed ...
    SequenceHeader, # For type hinting and context
    OBPStateWrapper # For stateful parsing (e.g. Frame Headers)
)
from pyobuparse._c_wrapper import OBPOBUType, OBPMetadataType # For OBU type enums

# Assume 'frame_data' is a bytes object containing the raw data of an IVF frame
# (i.e., excluding the 12-byte IVF frame header).

# Example: A minimal IVF frame might contain a Sequence Header OBU
# followed by a Temporal Delimiter OBU.
# OBU Header (Seq): 0x0A (type 1, size field) + Size (0x0b for 11 bytes) + Payload (11 zeros)
# OBU Header (TD): 0x12 (type 2, size field) + Size (0x00 for 0 bytes)
sample_obu_stream = b"\\x0a\\x0b" + (b"\\x00" * 11) + b"\\x12\\x00"
frame_data = sample_obu_stream

# Store sequence header and state for context-dependent parsing
current_seq_header: SequenceHeader | None = None
# OBPStateWrapper is needed for functions that maintain state across calls,
# like parse_frame_header or parse_frame.
state_wrapper = OBPStateWrapper() 

try:
    for obu_type, temporal_id, spatial_id, obu_payload in iter_obus(frame_data):
        type_name = obu_type.name if isinstance(obu_type, OBPOBUType) else f"UNKNOWN_TYPE_{obu_type}"
        print(f"Found OBU: Type={type_name}, Size={len(obu_payload)}, TID={temporal_id}, SID={spatial_id}")

        if obu_type == OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
            try:
                seq_header = parse_sequence_header(obu_payload)
                current_seq_header = seq_header # Store for later frames/OBUs
                print(f"  Parsed Sequence Header: Profile={seq_header.seq_profile}, "
                      f"Max Frame Width={seq_header.max_frame_width_minus_1+1}")
                # Explore other seq_header attributes as needed
            except OBUParseError as e:
                print(f"  Error parsing Sequence Header: {e}")
        
        elif obu_type == OBPOBUType.OBP_OBU_FRAME_HEADER:
            if current_seq_header:
                try:
                    frame_hdr = parse_frame_header(
                        obu_payload, 
                        current_seq_header, 
                        state_wrapper, 
                        temporal_id, 
                        spatial_id
                    )
                    # Use .name for enums, fallback to value for robustness
                    frame_type_name = frame_hdr.frame_type.name if isinstance(frame_hdr.frame_type, OBPOBUType) else frame_hdr.frame_type # Corrected: OBPFrameType
                    print(f"  Parsed Frame Header: Type={frame_type_name}, "
                          f"OrderHint={frame_hdr.order_hint}")
                    # Explore other frame_hdr attributes
                except OBUParseError as e:
                    print(f"  Error parsing Frame Header: {e}")
            else:
                print("  Skipping Frame Header parsing - Sequence Header not seen yet.")

        # Add more parsing logic for other OBU types (Frame, Tile Group, Metadata, etc.)
        # Example for Metadata OBU:
        # elif obu_type == OBPOBUType.OBP_OBU_METADATA:
        #     try:
        #         metadata_obj = parse_metadata(obu_payload)
        #         metadata_type_name = metadata_obj.type.name if isinstance(metadata_obj.type, OBPMetadataType) else metadata_obj.type
        #         print(f"  Parsed Metadata OBU: Type={metadata_type_name}")
        #         if metadata_obj.metadata_hdr_cll:
        #             print(f"    MaxCLL={metadata_obj.metadata_hdr_cll.max_cll}")
        #     except OBUParseError as e:
        #         print(f"  Error parsing Metadata OBU: {e}")

except OBUParseError as e:
    print(f"Error iterating OBUs: {e}")
```

For detailed API information, please refer to the generated Sphinx documentation (once built).

### Command-Line Tool: `obudump`

The `obudump` tool is installed with the package and can be used to inspect AV1 IVF files from your terminal.

**Basic Usage:**
Prints basic information (type, size, temporal/spatial ID) for each OBU.
```bash
obudump /path/to/your/video.ivf
```

**Verbose Output:**
Attempts to fully parse each OBU's payload and print a summary of its contents.
```bash
obudump --verbose /path/to/your/video.ivf
# or
obudump -v /path/to/your/video.ivf
```

**Limit OBUs per Frame:**
Restricts the number of OBUs displayed per IVF frame, useful for brevity.
```bash
obudump --max-obus 5 /path/to/your/video.ivf
```

**Help:**
Shows all available options and usage instructions.
```bash
obudump --help
```

## Documentation

Full API documentation can be built using Sphinx from the `docs` directory within the `pyobuparse` package source.
1. Install Sphinx and dependencies: `pip install sphinx sphinx_rtd_theme toml`
2. Navigate to `pyobuparse/docs`.
3. Build the HTML documentation: `python -m sphinx -b html . _build` (or `make html` if a Makefile exists).
The entry point will be `docs/_build/html/index.html`.

## Contributing

Contributions to `pyobuparse` are welcome! Whether it's bug reports, feature requests, documentation improvements, or code contributions, please feel free to open an issue or pull request on the GitHub repository.

**Development Workflow:**
1.  Clone the main repository.
2.  Ensure you have the necessary build tools (C compiler, Python dev headers).
3.  It's recommended to work in a Python virtual environment.
4.  Install the package in editable mode from the root of the main repository:
    ```bash
    pip install -e ./pyobuparse
    ```
5.  Make your changes.
6.  Add or update unit tests in the `pyobuparse/tests` directory.
7.  Ensure all tests pass: `pytest pyobuparse/tests`
8.  Update documentation if applicable.
9.  Submit a pull request.

## License

This project is licensed under the ISC License. See the `LICENSE` file in the root of the main repository for details.
(The `LICENSE` file is typically located one level above the `pyobuparse` package directory).
