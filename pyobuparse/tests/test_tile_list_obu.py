import unittest
from pyobuparse import parser, _c_wrapper

class TestParseTileList(unittest.TestCase):

    def test_parse_tile_list_empty_data(self):
        """Test parsing empty bytes for Tile List OBU raises OBUParseError."""
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse tile list OBU"):
            parser.parse_tile_list(b"")

    def test_parse_tile_list_truncated_header(self):
        """Test parsing truncated Tile List OBU (incomplete header)."""
        # Header needs at least 4 bytes:
        # output_frame_width_in_tiles_minus_1 (1)
        # output_frame_height_in_tiles_minus_1 (1)
        # tile_count_minus_1 (2)
        truncated_payload = bytes([0x00, 0x00, 0x00]) # Missing one byte from tile_count_minus_1
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse tile list OBU"):
            parser.parse_tile_list(truncated_payload)

    def test_parse_tile_list_truncated_entry(self):
        """Test parsing Tile List OBU with truncated entry data."""
        # Header: 1 tile wide, 1 tile high, 1 tile entry
        # Entry: anchor_idx=0, anchor_row=0, anchor_col=0, tile_data_size_minus_1=1 (2 bytes)
        # But only 1 byte of tile data provided
        payload = bytes.fromhex("000000000000000001CA") # Missing second byte of tile data
        with self.assertRaisesRegex(parser.OBUParseError, "Failed to parse tile list OBU"):
            # The error might come from C's attempt to read past buffer, or Python's string_at
            parser.parse_tile_list(payload)
            
    def test_parse_valid_minimal_tile_list(self):
        """Test parsing a minimal valid Tile List OBU."""
        # output_frame_width_in_tiles_minus_1 = 0 (1 tile wide)
        # output_frame_height_in_tiles_minus_1 = 0 (1 tile high)
        # tile_count_minus_1 = 0 (1 tile entry)
        # Entry 0:
        #   anchor_frame_idx = 0
        #   anchor_tile_row = 0
        #   anchor_tile_col = 0
        #   tile_data_size_minus_1 = 1 (meaning 2 bytes of tile data)
        #   coded_tile_data = b"\xCA\xFE"
        payload = bytes.fromhex(
            "00" +      # output_frame_width_in_tiles_minus_1 = 0
            "00" +      # output_frame_height_in_tiles_minus_1 = 0
            "0000" +    # tile_count_minus_1 = 0
            "00" +      # entry[0].anchor_frame_idx = 0
            "00" +      # entry[0].anchor_tile_row = 0
            "00" +      # entry[0].anchor_tile_col = 0
            "0001" +    # entry[0].tile_data_size_minus_1 = 1
            "CAFE"      # entry[0].coded_tile_data (2 bytes)
        )
        
        tl_obj = parser.parse_tile_list(payload)

        self.assertEqual(tl_obj.output_frame_width_in_tiles_minus_1, 0)
        self.assertEqual(tl_obj.output_frame_height_in_tiles_minus_1, 0)
        self.assertEqual(tl_obj.tile_count_minus_1, 0)
        
        self.assertEqual(len(tl_obj.tile_list_entries), 1)
        entry0 = tl_obj.tile_list_entries[0]
        self.assertEqual(entry0.anchor_frame_idx, 0)
        self.assertEqual(entry0.anchor_tile_row, 0)
        self.assertEqual(entry0.anchor_tile_col, 0)
        self.assertEqual(entry0.tile_data_size_minus_1, 1)
        self.assertEqual(len(entry0.coded_tile_data), 2)
        self.assertEqual(entry0.coded_tile_data, b"\xCA\xFE")

    def test_parse_valid_tile_list_multiple_entries(self):
        """Test parsing a Tile List OBU with multiple entries."""
        # 2 tiles wide, 1 tile high, 2 tile entries
        # Entry 0: anchor_idx=0, row=0, col=0, size_m1=0 (1 byte data: AA)
        # Entry 1: anchor_idx=0, row=0, col=1, size_m1=1 (2 bytes data: BBCC)
        payload = bytes.fromhex(
            "01" +      # output_frame_width_in_tiles_minus_1 = 1 (2 tiles wide)
            "00" +      # output_frame_height_in_tiles_minus_1 = 0 (1 tile high)
            "0001" +    # tile_count_minus_1 = 1 (2 entries)
            # Entry 0
            "00" +      # anchor_frame_idx
            "00" +      # anchor_tile_row
            "00" +      # anchor_tile_col
            "0000" +    # tile_data_size_minus_1 = 0 (1 byte)
            # Entry 1
            "00" +      # anchor_frame_idx
            "00" +      # anchor_tile_row
            "01" +      # anchor_tile_col
            "0001" +    # tile_data_size_minus_1 = 1 (2 bytes)
            # Tile Data (concatenated)
            "AA" +      # Data for Entry 0
            "BBCC"      # Data for Entry 1
        )
        
        tl_obj = parser.parse_tile_list(payload)

        self.assertEqual(tl_obj.output_frame_width_in_tiles_minus_1, 1)
        self.assertEqual(tl_obj.output_frame_height_in_tiles_minus_1, 0)
        self.assertEqual(tl_obj.tile_count_minus_1, 1)
        
        self.assertEqual(len(tl_obj.tile_list_entries), 2)
        
        entry0 = tl_obj.tile_list_entries[0]
        self.assertEqual(entry0.anchor_frame_idx, 0)
        self.assertEqual(entry0.anchor_tile_row, 0)
        self.assertEqual(entry0.anchor_tile_col, 0)
        self.assertEqual(entry0.tile_data_size_minus_1, 0)
        self.assertEqual(entry0.coded_tile_data, b"\xAA")

        entry1 = tl_obj.tile_list_entries[1]
        self.assertEqual(entry1.anchor_frame_idx, 0)
        self.assertEqual(entry1.anchor_tile_row, 0)
        self.assertEqual(entry1.anchor_tile_col, 1)
        self.assertEqual(entry1.tile_data_size_minus_1, 1)
        self.assertEqual(entry1.coded_tile_data, b"\xBB\xCC")

if __name__ == '__main__':
    unittest.main()
