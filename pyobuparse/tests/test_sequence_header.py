import unittest
from pyobuparse import parser, _c_wrapper

class TestParseSequenceHeader(unittest.TestCase):

    def test_parse_empty_data(self):
        """Test parsing empty bytes raises OBUParseError."""
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse sequence header"):
            parser.parse_sequence_header(b"")

    def test_parse_truncated_data(self):
        """Test parsing truncated sequence header data raises OBUParseError."""
        # A minimal valid payload is around 11-12 bytes.
        # This is just the first byte of a potentially valid payload.
        truncated_payload = bytes([0x00]) 
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse sequence header"):
            parser.parse_sequence_header(truncated_payload)

        # Slightly longer but still incomplete
        truncated_payload_2 = bytes([
            0x00, # profile 0, still 0, reduced 0
            0x00, # flags, op_count_m1=0
            0x00, 0x00, # op_idc[0]
            # Missing seq_level_idx and more
        ])
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse sequence header"):
            parser.parse_sequence_header(truncated_payload_2)

    def test_parse_valid_minimal_sequence_header(self):
        """
        Test parsing a minimal valid Sequence Header OBU payload.
        This payload is from dav1d test `annexb_seqhdr_only`:
        OBU Payload: 000000200000000000000046 (12 bytes)
        Decoded fields:
        - seq_profile = 0
        - still_picture = 0
        - reduced_still_picture_header = 0
        - timing_info_present_flag = 0 (so timing_info is None)
        - decoder_model_info_present_flag = 0 (so decoder_model_info is None)
        - initial_display_delay_present_flag = 0
        - operating_points_cnt_minus_1 = 0 (1 operating point)
        - operating_point_idc[0] = 0
        - seq_level_idx[0] = 8 (AV1 Level 4.0 Major, 0 Minor -> idx 8)
        - seq_tier[0] = 0
        - frame_width_bits_minus_1 = 0 (value needs 1 bit)
        - frame_height_bits_minus_1 = 0 (value needs 1 bit)
        - max_frame_width_minus_1 = 0 (actual width 1)
        - max_frame_height_minus_1 = 0 (actual height 1)
        - frame_id_numbers_present_flag = 0
        - use_128x128_superblock = 0
        - enable_filter_intra = 0
        - enable_intra_edge_filter = 0
        - enable_interintra_compound = 0
        - enable_masked_compound = 0
        - enable_warped_motion = 0
        - enable_dual_filter = 0
        - enable_order_hint = 1
        - enable_jnt_comp = 0
        - enable_ref_frame_mvs = 0
        - seq_choose_screen_content_tools = 0 (implies seq_force_screen_content_tools = 0)
        - seq_choose_integer_mv = 0 (implies seq_force_integer_mv = 0)
        - order_hint_bits_minus_1 = 2 (OrderHintBits = 3)
        - enable_superres = 0
        - enable_cdef = 0
        - enable_restoration = 0
        - color_config.high_bitdepth = 0
        - color_config.twelve_bit = 0
        - color_config.mono_chrome = 0
        - color_config.color_description_present_flag = 0
        - film_grain_params_present = 0
        """
        valid_sh_payload = bytes([
            0x00, # seq_profile=0, still_picture=0, reduced_still_picture_header=0
            0x00, # timing_info_present=0, decoder_model_info_present=0, initial_display_delay_present=0, operating_points_cnt_minus_1=0
            0x00, 0x00, # operating_point_idc[0]=0
            0x08, # seq_level_idx[0]=8 (Level 4.0), seq_tier[0]=0. (Note: 0x20 was a typo, 0x08 is correct for level_idx 8)
            0x00, # frame_width_bits_minus_1=0, frame_height_bits_minus_1=0
            0x00, # max_frame_width_minus_1=0 (1 bit '0'), max_frame_height_minus_1=0 (1 bit '0')
                  # This byte actually contains: max_frame_width_minus_1 (1 bit), then max_frame_height_minus_1 (1 bit)
                  # The C parser reads these as f(1)=0, f(1)=0.
            0x00, # frame_id_numbers_present_flag=0, use_128x128_superblock=0, enable_filter_intra=0, enable_intra_edge_filter=0, enable_interintra_compound=0, enable_masked_compound=0, enable_warped_motion=0, enable_dual_filter=0
            0x80, # enable_order_hint=1, enable_jnt_comp=0, enable_ref_frame_mvs=0, seq_force_screen_content_tools=0 (as choose=0), seq_force_integer_mv=0 (as choose=0)
            0x02, # order_hint_bits_minus_1 = 2
            0x00, # enable_superres=0, enable_cdef=0, enable_restoration=0
            0x00, # color_config: high_bitdepth=0, twelve_bit=0, mono_chrome=0, color_description_present_flag=0. film_grain_params_present=0 (last bit)
        ])
        
        self.assertEqual(len(valid_sh_payload), 12) # Ensure payload length

        seq_header = parser.parse_sequence_header(valid_sh_payload)

        self.assertEqual(seq_header.seq_profile, 0)
        self.assertEqual(seq_header.still_picture, 0)
        self.assertEqual(seq_header.reduced_still_picture_header, 0)

        self.assertEqual(seq_header.timing_info_present_flag, 0)
        self.assertIsNone(seq_header.timing_info)
        self.assertEqual(seq_header.decoder_model_info_present_flag, 0)
        self.assertIsNone(seq_header.decoder_model_info)
        self.assertEqual(seq_header.initial_display_delay_present_flag, 0)
        
        self.assertEqual(seq_header.operating_points_cnt_minus_1, 0)
        self.assertEqual(len(seq_header.operating_point_idc), 1)
        self.assertEqual(seq_header.operating_point_idc[0], 0)
        self.assertEqual(len(seq_header.seq_level_idx), 1)
        self.assertEqual(seq_header.seq_level_idx[0], 8) # Level 4.0
        self.assertEqual(len(seq_header.seq_tier), 1)
        self.assertEqual(seq_header.seq_tier[0], 0)

        self.assertEqual(seq_header.frame_width_bits_minus_1, 0)
        self.assertEqual(seq_header.frame_height_bits_minus_1, 0)
        self.assertEqual(seq_header.max_frame_width_minus_1, 0) # Width will be 1
        self.assertEqual(seq_header.max_frame_height_minus_1, 0) # Height will be 1
        
        self.assertEqual(seq_header.frame_id_numbers_present_flag, 0)
        self.assertEqual(seq_header.use_128x128_superblock, 0)
        self.assertEqual(seq_header.enable_filter_intra, 0)
        self.assertEqual(seq_header.enable_intra_edge_filter, 0)
        self.assertEqual(seq_header.enable_interintra_compound, 0)
        self.assertEqual(seq_header.enable_masked_compound, 0)
        self.assertEqual(seq_header.enable_warped_motion, 0)
        self.assertEqual(seq_header.enable_dual_filter, 0)
        
        self.assertEqual(seq_header.enable_order_hint, 1)
        self.assertEqual(seq_header.enable_jnt_comp, 0)
        self.assertEqual(seq_header.enable_ref_frame_mvs, 0)
        self.assertEqual(seq_header.seq_choose_screen_content_tools, 0)
        self.assertEqual(seq_header.seq_force_screen_content_tools, 0) # Auto to 0 if choose is 0
        self.assertEqual(seq_header.seq_choose_integer_mv, 0)
        self.assertEqual(seq_header.seq_force_integer_mv, 0) # Auto to 0 if choose is 0
        self.assertEqual(seq_header.order_hint_bits_minus_1, 2)
        self.assertEqual(seq_header.OrderHintBits, 3) # Calculated by lib

        self.assertEqual(seq_header.enable_superres, 0)
        self.assertEqual(seq_header.enable_cdef, 0)
        self.assertEqual(seq_header.enable_restoration, 0)

        self.assertIsNotNone(seq_header.color_config)
        cc = seq_header.color_config
        self.assertEqual(cc.high_bitdepth, 0)
        self.assertEqual(cc.twelve_bit, 0) # Not present in minimal, defaults to 0
        self.assertEqual(cc.mono_chrome, 0)
        self.assertEqual(cc.color_description_present_flag, 0)
        # If color_description_present_flag is 0, these are not read but set to defaults
        self.assertEqual(cc.color_primaries, _c_wrapper.OBP_CP_UNSPECIFIED) # Default is 2
        self.assertEqual(cc.transfer_characteristics, _c_wrapper.OBP_TC_UNSPECIFIED) # Default is 2
        self.assertEqual(cc.matrix_coefficients, _c_wrapper.OBP_MC_UNSPECIFIED) # Default is 2
        
        self.assertEqual(seq_header.film_grain_params_present, 0)

if __name__ == '__main__':
    unittest.main()
