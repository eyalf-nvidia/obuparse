obuparse
========

A simple and portable single file AV1 OBU parser written in mostly C89 with a tiny bit of C99,
with a permissive license.

Why?
----

I got tired of rewriting ad-hoc OBU parsers for various tasks suchs as ISOBMFF muxing,
MSE codec string generation, level verification, etc. So I decided to write once,
as correctly as possible, and to use it everywhere in place of probably subtly-broken
ad-hoc parsers.

I could have ripped out an OBU parser from other projects, but they're all either
very intertwined with their respective encoder/decoder, written in very unportable
manners, or in non-FFI friendly languages. At the time of writing this, I am not
aware of any permissively licensed (or otherwise) OBU parsers that actually work
portably.

How?
----

Simply copy `obuparse.c` and `obuparser.h` into your project, or use this repository
as a git submodule.

By default, the parser uses a checked bitreader, but you can define `OBP_UNCHECKED_BITREADER`
to use the unchecked version if that really matters to you.

All API documentation lives in `obuparse.h`.

There is also a Makefile provided for building a simple shared library on Linux. It
should be straightforward to build for other OSes; all public symbols are namespaced
with `obp_`. All public enums and types are namespaced with `OBP`.

Features
--------

This section will expand as more of the library becomes complete, and it moves
out of being a work in progress.

* No allocations; only works on user-provided buffers and the stack.
* OBU header parsing.
* Sequence Header OBU parsing.
* Metadata OBU parsing.
* Tile List OBU parsing.
* Tile Group OBU parsing.
* Frame Header OBU parsing.
* Frame OBU parsing.

Tools
-----

The `tools` directory contains a simple tool to parse and serialize OBUs from
an IVF file into JSON, called `dumpobu`.

Python Package
--------------

 A Python wrapper is provided using `cffi`. Build and install it in
 editable mode so the extension is compiled and the CLI is available.
 The tests expect the extension to be installed. Install in editable
 mode with the test extras so both the extension and test dependencies
 are built:


```bash
pip install -e .[test]
```

The build process now compiles both the CFFI extension and the native
`obudump` tool automatically. No manual `make` step is required when
installing via `pip`.

 This installs the `obuparse` module, a Python-based `obudump` command-line
 application, and the native `obudump` binary. The CLI can parse IVF files and
 display basic information about contained OBUs. The Makefile is still
 available should you wish to rebuild the tools manually:

```bash
make tools
```

Running tests (after installation):

```bash
pytest
```

Examples
--------

Using the Python bindings directly:

```python
>>> from obuparse import ffi, lib
>>> data = bytes([0x12, 0x00])
>>> err_buf = ffi.new('char[1024]')
>>> err = ffi.new('OBPError *', {'error': err_buf, 'size': 1024})
>>> obu_type = ffi.new('OBPOBUType *')
>>> offset = ffi.new('ptrdiff_t *')
>>> obu_size = ffi.new('size_t *')
>>> temporal_id = ffi.new('int *')
>>> spatial_id = ffi.new('int *')
>>> lib.obp_get_next_obu(data, len(data), obu_type, offset, obu_size,
...                      temporal_id, spatial_id, err)
0
```

Running the command-line tool to inspect an IVF file:

```bash
$ obudump -v sample.ivf
{'obu_type': 2, 'offset': 2, 'obu_size': 0, 'temporal_id': 0, 'spatial_id': 0}
```

