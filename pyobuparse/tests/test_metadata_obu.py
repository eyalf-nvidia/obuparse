import unittest
from pyobuparse import parser, _c_wrapper

class TestParseMetadata(unittest.TestCase):

    def test_parse_metadata_empty_data(self):
        """Test parsing empty bytes for metadata OBU raises OBUParseError."""
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse metadata OBU"):
            parser.parse_metadata(b"")

    def test_parse_metadata_truncated_type(self):
        """Test parsing truncated metadata (only partial type) raises OBUParseError."""
        # metadata_type is leb128. If it's multi-byte and truncated, it's an error.
        # 0x81 (1) would expect another byte.
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse metadata OBU"):
            parser.parse_metadata(bytes([0x81])) 

    def test_parse_metadata_hdr_cll_valid(self):
        """Test parsing a valid HDR Content Light Level metadata OBU."""
        # metadata_type = OBP_METADATA_TYPE_HDR_CLL (1) -> leb128 is 0x01
        # max_cll = 1000 (0x03E8) -> f(16)
        # max_fall = 200 (0x00C8) -> f(16)
        # Payload: 01 E803 C800 (assuming f(16) just takes 2 bytes directly in little-endian)
        # The C code reads these as direct big-endian, so 03E8 and 00C8.
        payload = bytes([
            0x01,        # metadata_type = 1
            0x03, 0xE8,  # max_cll = 1000
            0x00, 0xC8   # max_fall = 200
        ])
        md_obj = parser.parse_metadata(payload)
        self.assertEqual(md_obj.metadata_type, parser.OBP_METADATA_TYPE_HDR_CLL)
        self.assertIsNotNone(md_obj.metadata_hdr_cll)
        self.assertEqual(md_obj.metadata_hdr_cll.max_cll, 1000)
        self.assertEqual(md_obj.metadata_hdr_cll.max_fall, 200)
        self.assertIsNone(md_obj.metadata_hdr_mdcv) # Other types should be None
        self.assertIsNone(md_obj.unregistered)

    def test_parse_metadata_unregistered_valid(self):
        """Test parsing a valid unregistered metadata OBU."""
        # metadata_type = 100 (unregistered range) -> leb128 is 0x64
        custom_payload_data = b"custom_data_for_obu"
        payload = bytes([0x64]) + custom_payload_data
        
        md_obj = parser.parse_metadata(payload)
        
        self.assertEqual(md_obj.metadata_type, 100)
        self.assertIsNotNone(md_obj.unregistered)
        self.assertEqual(md_obj.unregistered.buf_size, len(custom_payload_data))
        self.assertEqual(md_obj.unregistered.buf_data, custom_payload_data)
        self.assertIsNone(md_obj.metadata_hdr_cll) # Other types should be None

    def test_parse_metadata_hdr_mdcv_minimal(self):
        """Test parsing a minimal valid HDR Mastering Display Color Volume metadata OBU."""
        # metadata_type = OBP_METADATA_TYPE_HDR_MDCV (2) -> leb128 is 0x02
        # All primaries, white point, luminance values set to simple values.
        # Values are u16 or u32, read as big-endian.
        payload = bytes([
            0x02,        # metadata_type = 2
            0x00, 0x01,  # primary_chromaticity_x[0]
            0x00, 0x02,  # primary_chromaticity_y[0]
            0x00, 0x03,  # primary_chromaticity_x[1]
            0x00, 0x04,  # primary_chromaticity_y[1]
            0x00, 0x05,  # primary_chromaticity_x[2]
            0x00, 0x06,  # primary_chromaticity_y[2]
            0x00, 0x07,  # white_point_chromaticity_x
            0x00, 0x08,  # white_point_chromaticity_y
            0x00, 0x00, 0x03, 0xE8, # luminance_max = 1000 (u32)
            0x00, 0x00, 0x00, 0xC8  # luminance_min = 200 (u32)
        ])
        md_obj = parser.parse_metadata(payload)
        self.assertEqual(md_obj.metadata_type, parser.OBP_METADATA_TYPE_HDR_MDCV)
        self.assertIsNotNone(md_obj.metadata_hdr_mdcv)
        mdcv = md_obj.metadata_hdr_mdcv
        self.assertEqual(mdcv.primary_chromaticity_x, [1, 3, 5])
        self.assertEqual(mdcv.primary_chromaticity_y, [2, 4, 6])
        self.assertEqual(mdcv.white_point_chromaticity_x, 7)
        self.assertEqual(mdcv.white_point_chromaticity_y, 8)
        self.assertEqual(mdcv.luminance_max, 1000)
        self.assertEqual(mdcv.luminance_min, 200)

    def test_parse_metadata_timecode_minimal(self):
        """Test parsing a minimal valid Timecode metadata OBU."""
        # metadata_type = OBP_METADATA_TYPE_TIMECODE (5) -> leb128 is 0x05
        # counting_type = 0, full_timestamp_flag = 0, discontinuity_flag = 0, cnt_dropped_flag = 0
        # n_frames = 10
        # (no seconds/minutes/hours flags, no time_offset)
        # Payload: 05 000A (counting_type=0, flags=0, n_frames=10)
        # counting_type (5 bits), full_ts_flag (1), disco_flag (1), cnt_dropped_flag (1) -> 1 byte
        # 0b00000000 = 0x00
        # n_frames (8 bits) = 10 (0x0A)
        # If time_offset_length > 0, more bytes. If not, ends.
        # The C code reads n_frames as u(8), not u(16).
        # If full_timestamp_flag = 1: seconds_value(u8), minutes_value(u8), hours_value(u8)
        # If time_offset_length > 0: time_offset_value(u(time_offset_length))
        # Simplest: counting_type=0, all flags=0, n_frames=10, time_offset_length=0
        payload = bytes([
            0x05, # metadata_type = 5
            0x00, # counting_type=0, full_timestamp_flag=0, discontinuity_flag=0, cnt_dropped_flag=0
            0x0A, # n_frames = 10
            # seconds_flag, minutes_flag, hours_flag are not read if full_timestamp_flag is 0
            # time_offset_length = 0 (implicit as not read further by C code if flags are 0)
        ])
        md_obj = parser.parse_metadata(payload)
        self.assertEqual(md_obj.metadata_type, parser.OBP_METADATA_TYPE_TIMECODE)
        self.assertIsNotNone(md_obj.metadata_timecode)
        tc = md_obj.metadata_timecode
        self.assertEqual(tc.counting_type, 0)
        self.assertEqual(tc.full_timestamp_flag, 0)
        self.assertEqual(tc.discontinuity_flag, 0)
        self.assertEqual(tc.cnt_dropped_flag, 0)
        self.assertEqual(tc.n_frames, 10)
        # Defaults for non-present fields
        self.assertEqual(tc.seconds_value, 0)
        self.assertEqual(tc.time_offset_length, 0)
        self.assertEqual(tc.time_offset_value, 0)


if __name__ == '__main__':
    unittest.main()
