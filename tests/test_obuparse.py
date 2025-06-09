import os
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "python"))

try:
    import cffi  # noqa: F401
except ImportError:
    raise RuntimeError("cffi must be installed to build the Python extension")

try:  # prefer installed package
    import obuparse
    import pyobuparse
except Exception:
    # build the CFFI extension in-place if missing
    import subprocess
    subprocess.check_call(
        [sys.executable, "ffi_builder.py"], cwd=os.path.join(ROOT_DIR, "python")
    )
    if 'obuparse' in sys.modules:
        del sys.modules['obuparse']
    import obuparse
    if 'pyobuparse' in sys.modules:
        del sys.modules['pyobuparse']
    import pyobuparse

# Test parsing an OBU header for temporal delimiter (size 0)
def test_get_next_obu_temporal_delimiter():
    data = bytes([0x12, 0x00])  # OBU type 2 with size field 0
    err_buf = obuparse.ffi.new('char[1024]')
    err = obuparse.ffi.new('OBPError *', {'error': err_buf, 'size': 1024})
    obu_type = obuparse.ffi.new('OBPOBUType *')
    offset = obuparse.ffi.new('ptrdiff_t *')
    obu_size = obuparse.ffi.new('size_t *')
    temporal_id = obuparse.ffi.new('int *')
    spatial_id = obuparse.ffi.new('int *')
    ret = obuparse.lib.obp_get_next_obu(
        data,
        len(data),
        obu_type,
        offset,
        obu_size,
        temporal_id,
        spatial_id,
        err,
    )
    assert ret == 0
    assert obu_type[0] == 2
    assert offset[0] == 2
    assert obu_size[0] == 0
    assert pyobuparse.lib is obuparse.lib
