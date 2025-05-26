import unittest
from pyobuparse import parser, _c_wrapper

class TestParseFrameHeader(unittest.TestCase):
    def setUp(self):
        """Setup a valid SequenceHeader and OBPStateWrapper for tests."""
        # Payload from dav1d test `annexb_seqhdr_only`
        # OBU Payload: 000000080000000000000046 (12 bytes)
        # Corrected after re-analysis:
        # seq_level_idx[0] = 1 (Level 2.0), not 8.
        # enable_order_hint = 0, so order_hint_bits_minus_1 is not present.
        # The original dav1d payload (0x0a, 0x0c, ...) had the OBU header and size.
        # The actual sequence header payload is 12 bytes.
        # 00 (prof 0, still 0, reduced 0)
        # 00 (timing_info_present=0, decoder_model_info_present=0, initial_display_delay_present=0, op_points_cnt_minus_1=0)
        # 0000 (operating_point_idc[0]=0)
        # 08 (seq_level_idx[0]=1 (Level 2.0), seq_tier[0]=0)
        # 00 (frame_width_bits_minus_1=0, frame_height_bits_minus_1=0)
        # 00 (max_frame_width_minus_1=0 => width=1, max_frame_height_minus_1=0 => height=1)
        # 00 (all flags like frame_id_numbers_present, use_128x128_superblock etc. are 0)
        # 40 (enable_order_hint=0, enable_jnt_comp=1, enable_ref_frame_mvs=0, screen_content_tools related flags are 0)
        # 00 (enable_superres=0, enable_cdef=0, enable_restoration=0)
        # 00 (color_config all 0s, film_grain_params_present=0)
        # The byte for order_hint_bits_minus_1 is NOT present if enable_order_hint=0.
        # So the payload is 11 bytes in this case.
        # The dav1d test file `annexb_seqhdr_only` content is `0a 0c 000000080000000000000040` (1 OBU, 12 byte payload)
        # The last byte `40` means: enable_order_hint=0, enable_jnt_comp=1, enable_ref_frame_mvs=0, choose_sc=0, force_sc=0, choose_imv=0, force_imv=0
        # The byte before that (all zeros) covers: superres,cdef,restoration, color_config_flags, film_grain_present
        self.valid_sh_payload = bytes.fromhex("000000080000000000004000") # 12 bytes
        
        self.sh_obj = parser.parse_sequence_header(self.valid_sh_payload)
        self.state_obj = parser.OBPStateWrapper()
        # Manually set current_frame_id for state to reflect a parsed SH.
        # The C library might do this internally upon parsing SH, but good for explicit test state.
        self.state_obj.c_state.prev_filled = 0 # Indicate no previous frame yet
        self.state_obj.c_state.current_frame_id = 0 # A typical starting ID after SH for the first frame.

    def test_parse_fh_empty_data(self):
        """Test parsing empty bytes for a frame header raises OBUParseError."""
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse frame header"):
            parser.parse_frame_header(b"", self.sh_obj, self.state_obj, 0, 0)

    def test_parse_fh_truncated_data(self):
        """Test parsing truncated frame header data."""
        # A frame header can be quite short, but less than a few bytes is definitely an error.
        truncated_payload = bytes([0x80]) # Show_existing_frame=0, type=KEY, show_frame=0
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse frame header"):
            parser.parse_frame_header(truncated_payload, self.sh_obj, self.state_obj, 0, 0)

    def test_parse_valid_key_frame_header_minimal(self):
        """
        Test parsing a conceptually minimal valid Key Frame Header OBU payload.
        Actual byte string will be difficult to craft perfectly without bitstream tools.
        Using a placeholder that *should* be parsable for basic fields.
        This example is based on the idea of a Key Frame, show_frame=1, refresh_all_frames,
        and other features mostly off or defaulted, using SH from setUp.
        SH has: order_hint_bits = 0 (enable_order_hint=0), frame_id_numbers_present_flag=0.
        """
        # Placeholder - this is NOT a guaranteed spec-compliant minimal FH.
        # It aims to set just enough for the C parser to proceed for some fields.
        # Bits (approximate):
        # 0 (show_existing_frame)
        # 00 (frame_type = KEY_FRAME)
        # 1 (show_frame = 1)
        # 0 (error_resilient_mode = 0, as it's key frame)
        # 0 (disable_cdf_update = 0)
        # (no screen_content_tools, integer_mv flags as per SH)
        # (no current_frame_id as per SH)
        # 0 (frame_size_override_flag = 0)
        # (no order_hint as per SH)
        # 111 (primary_ref_frame = PRIMARY_REF_NONE)
        # 11111111 (refresh_frame_flags = 0xFF)
        # (No buffer_removal_time as DMI not present in SH)
        # This sequence: 0 00 1 0 0 0 111 -> 0b00010001 0b1xxxxxxx -> 0x11 ...
        # Then 0xFF for refresh_frame_flags.
        # Then many default/0 flags.
        # A real minimal keyframe header from a tool:
        # From a 1x1 keyframe, SH: 000000080000000000004000
        # FH payload: 00 ff 00 00 80 00 00 00 00 00 00 00 (12 bytes)
        # This one is from dav1d `test_obu_parser_frame_header.c` for `keyframe-1-1-1.ivf`
        # The sequence header used there is the same as self.valid_sh_payload.
        valid_fh_payload = bytes.fromhex("00ff00008000000000000000")

        fh_obj = parser.parse_frame_header(valid_fh_payload, self.sh_obj, self.state_obj, 0, 0)

        self.assertEqual(fh_obj.frame_type, parser.OBP_KEY_FRAME)
        self.assertEqual(fh_obj.show_existing_frame, 0)
        self.assertEqual(fh_obj.show_frame, 1) # Derived in C lib
        self.assertEqual(fh_obj.showable_frame, 1) # Derived in C lib for Key Frame + show_frame
        self.assertEqual(fh_obj.error_resilient_mode, 0) # Explicitly set for keyframes by C
        self.assertEqual(fh_obj.disable_cdf_update, 0)
        self.assertEqual(fh_obj.frame_size_override_flag, 0)
        
        # Since frame_size_override_flag is 0, dimensions come from SequenceHeader
        # and RenderWidth/Height in FrameHeader struct get populated by C code.
        # Our SH has max_frame_width/height_minus_1 = 0, so width/height = 1.
        self.assertEqual(fh_obj.RenderWidth, 1)
        self.assertEqual(fh_obj.RenderHeight, 1)
        
        self.assertEqual(fh_obj.refresh_frame_flags, 0xFF)
        self.assertEqual(fh_obj.order_hint, 0) # Since enable_order_hint=0 in SH

        # Check some default/derived values for key parts
        self.assertIsNotNone(fh_obj.quantization_params)
        self.assertEqual(fh_obj.quantization_params.base_q_idx, 0) # Default from C init
        
        self.assertIsNotNone(fh_obj.loop_filter_params)
        # loop_filter_level[0] for Y_V is typically non-zero if not explicitly set to 0
        # but the C code initializes them to 0.
        self.assertEqual(fh_obj.loop_filter_params.loop_filter_level[0], 0)


if __name__ == '__main__':
    unittest.main()
