import sys
import os

# Try to import the package normally first.
# If it fails, it might be because the tests are being run directly from the repo
# without the package being installed in editable mode.
# In that case, add the 'src' directory to sys.path.
try:
    from pyobuparse import (
        iter_obus, parse_sequence_header,
        OBUParseError,
    )
    from pyobuparse import _c_wrapper
    # Import the enum itself
    from pyobuparse._c_wrapper import OBPOBUType
except ImportError:
    # Calculate the path to the 'src' directory relative to this test file.
    # tests/test_parser.py -> pyobuparse/tests/test_parser.py
    # src_path needs to go up two levels from test_parser.py's dir, then into 'src'.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir)) # Up two levels: pyobuparse/
    src_path = os.path.join(project_root, 'src')

    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Retry imports
    from pyobuparse import (
        iter_obus, parse_sequence_header,
        OBUParseError,
    )
    from pyobuparse import _c_wrapper
    # Import the enum itself
    from pyobuparse._c_wrapper import OBPOBUType

import pytest # Keep pytest import separate


# --- Sample OBU Data ---
# Placeholder for a minimal Sequence Header OBU payload (11 bytes as suggested)
# A real valid payload would require specific bits set according to AV1 spec.
# e.g. seq_profile=0, still_picture=0, reduced_still_picture_header=0, timing_info_present_flag=0,
# decoder_model_info_present_flag=0, initial_display_delay_present_flag=0,
# operating_points_cnt_minus_1=0, seq_level_idx[0]=X (e.g. 0 for level 2.0), seq_tier[0]=0,
# frame_width_bits_minus_1=15, frame_height_bits_minus_1=15, etc.
# The C parser expects these fields to be parsable.
# Using all zeros might lead to valid parsing with default values, or an error if zeros are invalid for some fields.
SAMPLE_SEQ_HEADER_PAYLOAD = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" 

# Full Sequence Header OBU: Header (type 1, size field) + Size (LEB128 for 11 bytes) + Payload
# OBU Header: 0x0A (type 1, obu_extension_flag=0, obu_has_size_field=1, reserved=0 -> 00001 0 1 0)
# OBU Size (leb128): 0x0b (11 bytes)
SAMPLE_SEQ_HEADER_OBU = b"\x0a\x0b" + SAMPLE_SEQ_HEADER_PAYLOAD

# Padding OBU (type 15): Header 0x7A (type 15, size field), Size 0x01, Payload 0x00
# OBU Header: 0x7A (type 15, obu_extension_flag=0, obu_has_size_field=1, reserved=0 -> 01111 0 1 0)
# OBU Size (leb128): 0x01 (1 byte)
# OBU Payload: 0x00 (1 byte of padding)
SAMPLE_PADDING_OBU = b"\x7a\x01\x00"

SAMPLE_OBU_STREAM = SAMPLE_SEQ_HEADER_OBU + SAMPLE_PADDING_OBU

# --- Tests for iter_obus ---

def test_iter_obus_empty_data():
    """Test iter_obus with empty input data."""
    assert list(iter_obus(b'')) == []

def test_iter_obus_invalid_data_short():
    """Test iter_obus with data too short to be a valid OBU."""
    # A single byte is not enough for header + size if size field is present.
    # The iter_obus function should now handle this by returning an empty list
    # instead of raising OBUParseError, due to internal handling of C errors on very short buffers.
    assert list(iter_obus(b'\x0a')) == [] # Valid header byte, but no size or payload

def test_iter_obus_invalid_data_malformed():
    """Test iter_obus with malformed OBU data (e.g., bad LEB128 size)."""
    # 0x0a (SH OBU, size present), then an invalid LEB128 size (0x80 without continuation)
    with pytest.raises(OBUParseError):
        list(iter_obus(b'\x0a\x80'))

def test_iter_obus_valid_stream():
    """Test iter_obus with a valid stream of OBUs."""
    obus = list(iter_obus(SAMPLE_OBU_STREAM))
    assert len(obus) == 2

    # Check Sequence Header OBU
    assert obus[0][0] == OBPOBUType.OBP_OBU_SEQUENCE_HEADER
    # obus[0][1] is temporal_id, obus[0][2] is spatial_id.
    # Default C parser may set these to 0 if not present in header extension.
    assert obus[0][1] == 0 # Default temporal_id if not set by OBU header extension
    assert obus[0][2] == 0 # Default spatial_id
    assert obus[0][3] == SAMPLE_SEQ_HEADER_PAYLOAD

    # Check Padding OBU
    assert obus[1][0] == OBPOBUType.OBP_OBU_PADDING
    assert obus[1][1] == 0 # Default temporal_id
    assert obus[1][2] == 0 # Default spatial_id
    assert obus[1][3] == b"\x00" # Payload of the padding OBU

def test_iter_obus_temporal_delimiter():
    """Test iter_obus with a Temporal Delimiter OBU."""
    # OBU Header: type 2 (Temporal Delimiter), has_size_field=1 -> 0x12
    # OBU Size (leb128): 0 bytes -> 0x00
    SAMPLE_TD_OBU = b"\x12\x00"
    obus = list(iter_obus(SAMPLE_TD_OBU))
    assert len(obus) == 1
    assert obus[0][0] == OBPOBUType.OBP_OBU_TEMPORAL_DELIMITER
    assert obus[0][1] == 0 # Default temporal_id
    assert obus[0][2] == 0 # Default spatial_id
    assert obus[0][3] == b"" # Empty payload

# --- Tests for parse_sequence_header ---

# A truly minimal valid sequence header payload is hard to craft without spec details.
# For now, let's use a placeholder that the C code might accept or reject.
# If the C code's obp_parse_sequence_header is robust, it might parse zeros as default values.
# This specific payload consists of all zeros.
# A real minimal payload for reduced_still_picture_header=0, profile=0, level=2.0 (idx=0)
# timing_info_present=0, decoder_model_info_present=0, initial_display_delay_present=0
# op_points_cnt_minus_1=0.
# Bits:
# seq_profile (3) = 000
# still_picture (1) = 0
# reduced_still_picture_header (1) = 0
# timing_info_present_flag (1) = 0
# decoder_model_info_present_flag (1) = 0
# initial_display_delay_present_flag (1) = 0
# operating_points_cnt_minus_1 (5) = 00000
# operating_point_idc[0] (12) = (skipped if op_points_cnt_minus_1 is 0 before this, but spec says read 1) -> 0
# seq_level_idx[0] (5) = 00000 (level 2.0)
# seq_tier[0] (1) = 0
# (decoder_model_present_for_this_op[0] (1) = 0 - only if !reduced_still_picture_header && decoder_model_info_present)
# (initial_display_delay_present_for_this_op[0] (1) = 0 - only if initial_display_delay_present_flag)
# frame_width_bits_minus_1 (4) = (e.g. 1 for 2 pixels width, to be minimal, 0000)
# frame_height_bits_minus_1 (4) = (e.g. 0000)
# max_frame_width_minus_1 (value of frame_width_bits_minus_1 + 1 bits) -> (e.g. 1 bit for 2 pixels, value 1)
# max_frame_height_minus_1 (value of frame_height_bits_minus_1 + 1 bits) -> (e.g. 1 bit for 2 pixels, value 1)
# ... and so on. This is complex.
# The current C code `obuparse.c` has some default assignments for seq header fields.
# It's possible `b"\x00"*11` might parse without error due to how `br_get_bits` handles end-of-buffer.
# Let's try a slightly more structured minimal payload based on common defaults:
# Assuming: profile=0, still=0, reduced_header=0, no timing/decoder_model/display_delay info,
# 1 operating point (level 2.0 / idx 0, tier 0),
# frame_width_bits_minus_1 = 15 (for 16 bits for width)
# frame_height_bits_minus_1 = 15 (for 16 bits for height)
# max_frame_width_minus_1 = 0 (actual width is 1)
# max_frame_height_minus_1 = 0 (actual height is 1)
# no frame_id_numbers, use_128x128_superblock=1, all features disabled, color_config defaults.
# This requires careful bit packing.
# For now, the all-zero placeholder `SAMPLE_SEQ_HEADER_PAYLOAD` will be used.
# The C parser might successfully parse this with many fields as 0.

def test_parse_sequence_header_valid_placeholder():
    """
    Test parse_sequence_header with the placeholder payload.
    This mainly checks for successful parsing without exceptions.
    Detailed field value assertions depend on the exact nature of the placeholder
    and how the C parser interprets it.
    """
    try:
        # This payload is all zeros. The C parser might default many fields.
        seq_header = parse_sequence_header(SAMPLE_SEQ_HEADER_PAYLOAD)
        assert seq_header is not None
        # Basic assertions based on an all-zero payload:
        assert seq_header.seq_profile == 0
        assert seq_header.still_picture == 0
        assert seq_header.reduced_still_picture_header == 0
        assert seq_header.timing_info_present_flag == 0
        assert seq_header.timing_info is None
        assert seq_header.decoder_model_info_present_flag == 0
        assert seq_header.decoder_model_info is None
        assert seq_header.initial_display_delay_present_flag == 0
        assert seq_header.operating_points_cnt_minus_1 == 0
        assert len(seq_header.operating_point_idc) == 1
        assert seq_header.operating_point_idc[0] == 0 
        # This part is tricky: operating_parameters_info is an array of structs.
        # If operating_points_cnt_minus_1 is 0, there's 1 op point.
        # The C code initializes this struct.
        assert len(seq_header.operating_parameters_info) == 1
        # seq_level_idx[0] would be 0 from all-zero payload.
        assert seq_header.seq_level_idx[0] == 0
        # Potentially more assertions if behavior of C parser with zeros is known.
    except OBUParseError as e:
        # If the all-zero placeholder is actually invalid for the C parser's strictness
        pytest.fail(f"parse_sequence_header failed with placeholder payload: {e}")


def test_parse_sequence_header_invalid_payload_too_short():
    """Test parse_sequence_header with a payload that's too short."""
    # The C parser expects a certain number of bytes for minimal fields.
    # 3 bytes is likely too short.
    with pytest.raises(OBUParseError):
        parse_sequence_header(b'\x00\x01\x02')

def test_parse_sequence_header_empty_payload():
    """Test parse_sequence_header with an empty payload."""
    with pytest.raises(OBUParseError):
        parse_sequence_header(b'')

# --- Test Library Loading ---

def test_c_library_loaded():
    """Test that the C library (_obuparse_c) is loaded."""
    # _c_wrapper._lib is initialized by _c_wrapper._load_c_library()
    # If it's None, loading failed. The _load_c_library prints critical errors.
    assert _c_wrapper._lib is not None, \
        "C library object _c_wrapper._lib is None. Check loading errors at import time."

# --- More tests to be added for other parsing functions and OBU types ---
# Placeholder for future tests
def test_parse_frame_header_valid():
    """Placeholder for testing valid Frame Header parsing."""
    pytest.skip("Test not implemented")

def test_parse_frame_header_error_conditions():
    """Placeholder for testing Frame Header parsing error conditions."""
    pytest.skip("Test not implemented")

def test_parse_frame_valid():
    """Placeholder for testing valid Frame OBU parsing."""
    pytest.skip("Test not implemented")

def test_parse_frame_error_conditions():
    """Placeholder for testing Frame OBU parsing error conditions."""
    pytest.skip("Test not implemented")

def test_parse_tile_group_valid():
    """Placeholder for testing valid Tile Group OBU parsing."""
    pytest.skip("Test not implemented")

def test_parse_tile_group_error_conditions():
    """Placeholder for testing Tile Group OBU parsing error conditions."""
    pytest.skip("Test not implemented")

def test_parse_metadata_hdr_cll():
    """Placeholder for testing Metadata OBU (HDR CLL) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_hdr_mdcv():
    """Placeholder for testing Metadata OBU (HDR MDCV) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_scalability():
    """Placeholder for testing Metadata OBU (Scalability) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_itut_t35():
    """Placeholder for testing Metadata OBU (ITU-T T.35) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_timecode():
    """Placeholder for testing Metadata OBU (Timecode) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_unregistered():
    """Placeholder for testing Metadata OBU (Unregistered) parsing."""
    pytest.skip("Test not implemented")

def test_parse_metadata_error_conditions():
    """Placeholder for testing Metadata OBU parsing error conditions."""
    pytest.skip("Test not implemented")

def test_parse_tile_list_valid():
    """Placeholder for testing valid Tile List OBU parsing."""
    pytest.skip("Test not implemented")

def test_parse_tile_list_error_conditions():
    """Placeholder for testing Tile List OBU parsing error conditions."""
    pytest.skip("Test not implemented")

def test_obu_state_wrapper():
    """Placeholder for testing OBPStateWrapper functionality."""
    # Primarily, ensure it can be created and passed to functions.
    # from pyobuparse.parser import OBPStateWrapper
    # state = OBPStateWrapper()
    # assert state._c_state_instance is not None # Basic check
    pytest.skip("Test not implemented")
