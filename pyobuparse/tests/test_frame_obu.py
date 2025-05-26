import unittest
from pyobuparse import parser, _c_wrapper

class TestParseFrameOBU(unittest.TestCase):
    def setUp(self):
        """Setup a valid SequenceHeader and OBPStateWrapper for tests."""
        # SH Payload from dav1d test `annexb_seqhdr_only`, re-verified
        # 00 (prof 0, still 0, reduced 0)
        # 00 (timing_info_present=0, decoder_model_info_present=0, initial_display_delay_present=0, op_points_cnt_minus_1=0)
        # 0000 (operating_point_idc[0]=0)
        # 08 (seq_level_idx[0]=1 (Level 2.0), seq_tier[0]=0)
        # 00 (frame_width_bits_minus_1=0, frame_height_bits_minus_1=0) -> 1 bit for width/height values
        # 00 (max_frame_width_minus_1=0 => width=1, max_frame_height_minus_1=0 => height=1)
        # 00 (all flags like frame_id_numbers_present, use_128x128_superblock etc. are 0)
        # 40 (enable_order_hint=0, enable_jnt_comp=1, enable_ref_frame_mvs=0, force_screen_content_tools=0, force_integer_mv=0)
        # 00 (order_hint_bits_minus_1 not present. enable_superres=0, enable_cdef=0, enable_restoration=0)
        # 00 (color_config all 0s, film_grain_params_present=0)
        self.valid_sh_payload = bytes.fromhex("000000080000000000004000")
        
        self.sh_obj = parser.parse_sequence_header(self.valid_sh_payload)
        self.state_obj = parser.OBPStateWrapper()
        # For Frame OBU, state might be more relevant if it were an Inter frame.
        # For a Key Frame, a fresh state is typical.
        # The C library initializes state->current_frame_id to -1.
        # obp_parse_frame_header (called by obp_parse_frame) will update it.

    def test_parse_frame_obu_empty_data(self):
        """Test parsing empty bytes for a Frame OBU raises OBUParseError."""
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse frame OBU"):
            parser.parse_frame(b"", self.sh_obj, self.state_obj, 0, 0)

    def test_parse_frame_obu_truncated_fh(self):
        """Test parsing Frame OBU with truncated frame header part."""
        truncated_payload = bytes([0x80, 0xFF]) # Minimal FH part, but no tile data
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse frame OBU"):
            parser.parse_frame(truncated_payload, self.sh_obj, self.state_obj, 0, 0)

    def test_parse_valid_minimal_key_frame_obu(self):
        """
        Test parsing a minimal valid Frame OBU (Key Frame header + minimal tile data).
        Uses the SH from setUp and the known valid FH payload.
        """
        # FH payload from dav1d test `keyframe-1-1-1.ivf`
        valid_fh_payload = bytes.fromhex("00ff00008000000000000000")
        dummy_tile_data = b"\xAB\xCD" # 2 bytes of dummy tile data
        
        valid_frame_obu_payload = valid_fh_payload + dummy_tile_data

        fh_obj, tg_obj = parser.parse_frame(valid_frame_obu_payload, self.sh_obj, self.state_obj, 0, 0)

        # --- Assertions for FrameHeader part (similar to test_frame_header.py) ---
        self.assertIsNotNone(fh_obj)
        self.assertEqual(fh_obj.frame_type, parser.OBP_KEY_FRAME)
        self.assertEqual(fh_obj.show_existing_frame, 0)
        self.assertEqual(fh_obj.show_frame, 1)
        self.assertEqual(fh_obj.showable_frame, 1)
        self.assertEqual(fh_obj.error_resilient_mode, 0) 
        self.assertEqual(fh_obj.disable_cdf_update, 0)
        self.assertEqual(fh_obj.allow_screen_content_tools, self.sh_obj.seq_force_screen_content_tools)
        self.assertEqual(fh_obj.force_integer_mv, self.sh_obj.seq_force_integer_mv)
        self.assertEqual(fh_obj.frame_size_override_flag, 0)
        self.assertEqual(fh_obj.order_hint, 0) 
        self.assertEqual(fh_obj.primary_ref_frame, 0) 
        self.assertEqual(fh_obj.refresh_frame_flags, 0xFF)
        self.assertEqual(fh_obj.RenderWidth, 1) 
        self.assertEqual(fh_obj.RenderHeight, 1)
        self.assertEqual(fh_obj.allow_intrabc, 0)
        self.assertEqual(fh_obj.quantization_params.base_q_idx, 0)
        self.assertIsNone(fh_obj.film_grain_params)

        # --- Assertions for TileGroup part ---
        self.assertIsNotNone(tg_obj)
        # Based on SH (1x1 frame) and FH (uniform_tile_spacing=1), NumTiles should be 1.
        # The C code sets:
        # tile_group->NumTiles = FrameHeader->tile_info.TileCols * FrameHeader->tile_info.TileRows;
        # For the given FH payload (00ff000080...), the 4th byte is 0x80.
        # tile_info.uniform_tile_spacing_flag = (0x80 >> 7) & 1 = 1.
        # TileCols and TileRows are derived from frame dimensions and mi_cols/rows by the C lib.
        # For a 1x1 frame, MiCols=1, MiRows=1.
        # If uniform_tile_spacing_flag=1, TileColsLog2=0, TileRowsLog2=0 -> TileCols=1, TileRows=1.
        self.assertEqual(tg_obj.NumTiles, 1) 
        
        # tg_start and tg_end are relative to the full frame, so 0 for a single tile.
        self.assertEqual(tg_obj.tg_start, 0)
        self.assertEqual(tg_obj.tg_end, 0)
        
        # TileSize[0] should be the size of the tile data that followed the frame header.
        # The C code: tile_group->TileSize[0] = obu_size - state->frame_header_end_pos;
        # state->frame_header_end_pos is the size of the uncompressed_header() part.
        # For this specific FH payload ("00ff00008000000000000000"), the uncompressed header is 12 bytes.
        # So TileSize[0] should be len(valid_frame_obu_payload) - 12 = len(dummy_tile_data)
        self.assertEqual(len(tg_obj.TileSize), 1) # Only one tile, so only one size
        self.assertEqual(tg_obj.TileSize[0], len(dummy_tile_data))

if __name__ == '__main__':
    unittest.main()
