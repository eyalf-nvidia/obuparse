import unittest
from pyobuparse import parser, _c_wrapper

class TestIterOBUs(unittest.TestCase):
    # Valid 12-byte Sequence Header OBU payload from dav1d tests
    # Decoded: profile 0, still 0, reduced 0, 1 op_point (idc 0),
    # level 2.0 (idx 1), tier 0,
    # frame_width/height_bits_minus_1 = 0 (actual value uses 1 bit),
    # max_frame_width_minus_1 = 0 (actual width 1),
    # max_frame_height_minus_1 = 0 (actual height 1),
    # frame_id_numbers_present = 0,
    # various flags (use_128x128_sb, filter_intra etc.) all 0
    # enable_order_hint = 0 (so OrderHintBits = 0)
    # enable_jnt_comp = 1
    # seq_force_screen_content_tools = 0
    # seq_force_integer_mv = 0
    # color_config all 0, film_grain_params_present=0
    VALID_SH_PAYLOAD = bytes.fromhex("000000080000000000004000")

    # Valid 12-byte Frame Header OBU payload from dav1d tests
    # For Key Frame, show_frame=1, refresh_flags=0xFF, order_hint=0 (as per above SH)
    VALID_FH_PAYLOAD = bytes.fromhex("00ff00008000000000000000")


    def test_iter_obus_empty_stream(self):
        """Test iter_obus with empty data yields nothing."""
        obus = list(parser.iter_obus(b""))
        self.assertEqual(len(obus), 0)

    def test_iter_obus_single_sh_no_size(self):
        """Test a stream with a single Sequence Header OBU (no size field)."""
        obu_header = bytes.fromhex("0A00") # type=SH, ext=0, size=0, layers=0
        stream_bytes = obu_header + self.VALID_SH_PAYLOAD
        
        obus = list(parser.iter_obus(stream_bytes))
        
        self.assertEqual(len(obus), 1)
        obu_type, temporal_id, spatial_id, payload = obus[0]
        self.assertEqual(obu_type, _c_wrapper.OBP_OBU_SEQUENCE_HEADER)
        self.assertEqual(temporal_id, 0)
        self.assertEqual(spatial_id, 0)
        self.assertEqual(payload, self.VALID_SH_PAYLOAD)

    def test_iter_obus_single_sh_with_size(self):
        """Test a stream with a single Sequence Header OBU (with size field)."""
        obu_header_flags = 0x0C # type=SH, ext=0, size=1, reserved=0
        layers_byte = 0x00
        payload_size_leb128 = bytes([len(self.VALID_SH_PAYLOAD)]) # LEB128 for 12 is 0x0C
        
        stream_bytes = bytes([obu_header_flags, layers_byte]) + payload_size_leb128 + self.VALID_SH_PAYLOAD
        
        obus = list(parser.iter_obus(stream_bytes))
        
        self.assertEqual(len(obus), 1)
        obu_type, temporal_id, spatial_id, payload = obus[0]
        self.assertEqual(obu_type, _c_wrapper.OBP_OBU_SEQUENCE_HEADER)
        self.assertEqual(temporal_id, 0)
        self.assertEqual(spatial_id, 0)
        self.assertEqual(payload, self.VALID_SH_PAYLOAD)

    def test_iter_obus_sh_td_stream(self):
        """Test a stream with Sequence Header and Temporal Delimiter."""
        sh_obu_header = bytes.fromhex("0A00") # type=SH, no size, layers=0
        td_obu_header = bytes.fromhex("1200") # type=TD, no size, layers=0
        td_payload = b"" # Temporal Delimiter has no payload

        stream_bytes = sh_obu_header + self.VALID_SH_PAYLOAD + \
                       td_obu_header + td_payload
        
        obus = list(parser.iter_obus(stream_bytes))
        
        self.assertEqual(len(obus), 2)
        
        obu_type, temporal_id, spatial_id, payload = obus[0]
        self.assertEqual(obu_type, _c_wrapper.OBP_OBU_SEQUENCE_HEADER)
        self.assertEqual(temporal_id, 0)
        self.assertEqual(spatial_id, 0)
        self.assertEqual(payload, self.VALID_SH_PAYLOAD)
        
        obu_type_2, temporal_id_2, spatial_id_2, payload_2 = obus[1]
        self.assertEqual(obu_type_2, _c_wrapper.OBP_OBU_TEMPORAL_DELIMITER)
        self.assertEqual(temporal_id_2, 0)
        self.assertEqual(spatial_id_2, 0)
        self.assertEqual(payload_2, td_payload)

    def test_iter_obus_sh_with_size_fh_no_size(self):
        """Test SH (size) followed by Frame Header (no size)."""
        sh_header_flags = 0x0C # type=SH, size=1
        sh_layers_byte = 0x00
        sh_payload_size_leb128 = bytes([len(self.VALID_SH_PAYLOAD)])
        sh_obu = bytes([sh_header_flags, sh_layers_byte]) + sh_payload_size_leb128 + self.VALID_SH_PAYLOAD

        fh_obu_header = bytes.fromhex("1A00") # type=FH, no size, layers=0
        fh_payload = self.VALID_FH_PAYLOAD 
        fh_obu = fh_obu_header + fh_payload
        
        stream_bytes = sh_obu + fh_obu
        obus = list(parser.iter_obus(stream_bytes))

        self.assertEqual(len(obus), 2)
        self.assertEqual(obus[0][0], _c_wrapper.OBP_OBU_SEQUENCE_HEADER)
        self.assertEqual(obus[0][3], self.VALID_SH_PAYLOAD)
        self.assertEqual(obus[1][0], _c_wrapper.OBP_OBU_FRAME_HEADER)
        self.assertEqual(obus[1][3], fh_payload)

    def test_iter_obus_truncated_payload_with_size(self):
        """Test OBU with size field claiming more data than available."""
        header_flags = 0x0C # type=SH, size=1
        layers_byte = 0x00
        # Claim payload size of 16 (0x10 in LEB128)
        payload_size_leb128 = bytes([0x10]) 
        
        # Provide only 5 bytes of actual payload
        truncated_sh_payload = self.VALID_SH_PAYLOAD[:5] 
        stream_bytes = bytes([header_flags, layers_byte]) + payload_size_leb128 + truncated_sh_payload
        
        with self.assertRaisesRegex(parser.OBUParseError, "OBU payload extends beyond data buffer"):
            list(parser.iter_obus(stream_bytes))

    def test_iter_obus_malformed_header_reserved_type(self):
        """Test iter_obus with a reserved OBU type."""
        # OBU Type 14 is reserved. Header: 1110xxxx (type) 0 (ext) 0 (size) 0 (rsv) 0 (rsv) = 11100000 = 0xE0
        # Followed by layers byte 0x00
        malformed_stream = bytes.fromhex("E000") 
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to get next OBU"):
             list(parser.iter_obus(malformed_stream))

    def test_iter_obus_padding_obu_no_size_at_end(self):
        """Test a stream ending with a Padding OBU (no size field)."""
        sh_obu = bytes.fromhex("0A00") + self.VALID_SH_PAYLOAD
        # Padding OBU: type=15 (0b01111), ext=0, size=0, rsv=0, rsv=0 -> 0b01111000 = 0x78
        # But obuparse.c expects 0x7A for padding (type 15, ext=0, has_size=0, two reserved bits 00)
        # obu_header = (OBU_PADDING << 3) | (0 << 2) | (0 << 1) | 0; -> (15 << 3) = 120 = 0x78
        # The C code actually has: `(type << 3) | (extension_flag << 2) | (has_size_field << 1) | obu_reserved_bit`
        # So for padding (15), no ext, no size, reserved=0: (15<<3) = 0b01111000 = 0x78
        padding_obu_header = bytes.fromhex("7800") # type=Padding, layers=0
        
        # Case 1: Padding is effectively zero length because it's last and no size
        stream1 = sh_obu + padding_obu_header
        obus1 = list(parser.iter_obus(stream1))
        self.assertEqual(len(obus1), 2)
        self.assertEqual(obus1[1][0], _c_wrapper.OBP_OBU_PADDING)
        self.assertEqual(len(obus1[1][3]), 0) # Payload is empty

        # Case 2: Padding with some trailing bytes that are considered part of padding
        stream2 = sh_obu + padding_obu_header + b"\x00\x00\x00" # 3 bytes of padding data
        obus2 = list(parser.iter_obus(stream2))
        self.assertEqual(len(obus2), 2)
        self.assertEqual(obus2[1][0], _c_wrapper.OBP_OBU_PADDING)
        self.assertEqual(obus2[1][3], b"\x00\x00\x00")


    def test_iter_obus_padding_obu_with_size(self):
        """Test a Padding OBU with an explicit size field."""
        sh_obu = bytes.fromhex("0A00") + self.VALID_SH_PAYLOAD
        # Padding OBU: type=15 (0b01111), ext=0, size=1, rsv=0 -> 0b01111010 = 0x7A
        padding_header_flags = 0x7A 
        padding_layers_byte = 0x00
        padding_payload_size_leb128 = bytes([0x03]) # Size 3
        padding_payload = b"\x01\x02\x03"
        
        stream = sh_obu + bytes([padding_header_flags, padding_layers_byte]) + \
                 padding_payload_size_leb128 + padding_payload
        
        obus = list(parser.iter_obus(stream))
        self.assertEqual(len(obus), 2)
        self.assertEqual(obus[1][0], _c_wrapper.OBP_OBU_PADDING)
        self.assertEqual(obus[1][3], padding_payload)

if __name__ == '__main__':
    unittest.main()
