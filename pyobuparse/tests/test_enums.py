import unittest
from pyobuparse import parser # Assuming enums are exposed via parser module

class TestEnums(unittest.TestCase):

    def test_obu_type_enums(self):
        self.assertEqual(parser.OBP_OBU_SEQUENCE_HEADER, 1)
        self.assertEqual(parser.OBP_OBU_TEMPORAL_DELIMITER, 2)
        self.assertEqual(parser.OBP_OBU_FRAME_HEADER, 3)
        self.assertEqual(parser.OBP_OBU_TILE_GROUP, 4)
        self.assertEqual(parser.OBP_OBU_METADATA, 5)
        self.assertEqual(parser.OBP_OBU_FRAME, 6)
        self.assertEqual(parser.OBP_OBU_REDUNDANT_FRAME_HEADER, 7)
        self.assertEqual(parser.OBP_OBU_TILE_LIST, 8)
        self.assertEqual(parser.OBP_OBU_PADDING, 15)

    def test_metadata_type_enums(self):
        self.assertEqual(parser.OBP_METADATA_TYPE_HDR_CLL, 1)
        self.assertEqual(parser.OBP_METADATA_TYPE_HDR_MDCV, 2)
        self.assertEqual(parser.OBP_METADATA_TYPE_SCALABILITY, 3)
        self.assertEqual(parser.OBP_METADATA_TYPE_ITUT_T35, 4)
        self.assertEqual(parser.OBP_METADATA_TYPE_TIMECODE, 5)
        # OBP_METADATA_TYPE_UNREGISTERED = 6 (as defined in _c_wrapper.py for ranges)
        self.assertEqual(parser.OBP_METADATA_TYPE_UNREGISTERED, 6)


    def test_color_primaries_enums(self):
        self.assertEqual(parser.OBP_CP_BT_709, 1)
        self.assertEqual(parser.OBP_CP_UNSPECIFIED, 2)
        self.assertEqual(parser.OBP_CP_BT_470_M, 4)
        self.assertEqual(parser.OBP_CP_BT_470_B_G, 5)
        self.assertEqual(parser.OBP_CP_BT_601, 6)
        self.assertEqual(parser.OBP_CP_SMPTE_240, 7)
        self.assertEqual(parser.OBP_CP_GENERIC_FILM, 8)
        self.assertEqual(parser.OBP_CP_BT_2020, 9)
        self.assertEqual(parser.OBP_CP_XYZ, 10)
        self.assertEqual(parser.OBP_CP_SMPTE_431, 11)
        self.assertEqual(parser.OBP_CP_SMPTE_432, 12)
        self.assertEqual(parser.OBP_CP_EBU_3213, 22)
        # Check compatibility aliases
        self.assertEqual(parser.OBP_COLOR_PRIMARIES_BT_709, 1)


    def test_transfer_characteristics_enums(self):
        self.assertEqual(parser.OBP_TC_RESERVED_0, 0)
        self.assertEqual(parser.OBP_TC_BT_709, 1)
        self.assertEqual(parser.OBP_TC_UNSPECIFIED, 2)
        self.assertEqual(parser.OBP_TC_RESERVED_3, 3)
        self.assertEqual(parser.OBP_TC_BT_470_M, 4)
        self.assertEqual(parser.OBP_TC_BT_470_B_G, 5)
        self.assertEqual(parser.OBP_TC_BT_601, 6)
        self.assertEqual(parser.OBP_TC_SMPTE_240, 7)
        self.assertEqual(parser.OBP_TC_LINEAR, 8)
        self.assertEqual(parser.OBP_TC_LOG_100, 9)
        self.assertEqual(parser.OBP_TC_LOG_100_SQRT10, 10)
        self.assertEqual(parser.OBP_TC_IEC_61966, 11)
        self.assertEqual(parser.OBP_TC_BT_1361, 12)
        self.assertEqual(parser.OBP_TC_SRGB, 13)
        self.assertEqual(parser.OBP_TC_BT_2020_10_BIT, 14)
        self.assertEqual(parser.OBP_TC_BT_2020_12_BIT, 15)
        self.assertEqual(parser.OBP_TC_SMPTE_2084, 16)
        self.assertEqual(parser.OBP_TC_SMPTE_428, 17)
        self.assertEqual(parser.OBP_TC_HLG, 18)
        # Check compatibility aliases
        self.assertEqual(parser.OBP_TRANSFER_CHARACTERISTICS_BT_709, 1)

    def test_matrix_coefficients_enums(self):
        self.assertEqual(parser.OBP_MC_IDENTITY, 0)
        self.assertEqual(parser.OBP_MC_BT_709, 1)
        self.assertEqual(parser.OBP_MC_UNSPECIFIED, 2)
        self.assertEqual(parser.OBP_MC_RESERVED_3, 3)
        self.assertEqual(parser.OBP_MC_FCC, 4)
        self.assertEqual(parser.OBP_MC_BT_470_B_G, 5)
        self.assertEqual(parser.OBP_MC_BT_601, 6)
        self.assertEqual(parser.OBP_MC_SMPTE_240, 7)
        self.assertEqual(parser.OBP_MC_SMPTE_YCGCO, 8)
        self.assertEqual(parser.OBP_MC_BT_2020_NCL, 9)
        self.assertEqual(parser.OBP_MC_BT_2020_CL, 10)
        self.assertEqual(parser.OBP_MC_SMPTE_2085, 11)
        self.assertEqual(parser.OBP_MC_CHROMAT_NCL, 12)
        self.assertEqual(parser.OBP_MC_CHROMAT_CL, 13)
        self.assertEqual(parser.OBP_MC_ICTCP, 14)
        # Check compatibility aliases
        self.assertEqual(parser.OBP_MATRIX_COEFFICIENTS_BT_709, 1)

    def test_chroma_sample_position_enums(self):
        self.assertEqual(parser.OBP_CSP_UNKNOWN, 0)
        self.assertEqual(parser.OBP_CSP_VERTICAL, 1)
        self.assertEqual(parser.OBP_CSP_COLOCATED, 2)
        # Check compatibility aliases
        self.assertEqual(parser.OBP_CHROMA_SAMPLE_POSITION_UNKNOWN, 0)

    def test_frame_type_enums(self):
        self.assertEqual(parser.OBP_KEY_FRAME, 0)
        self.assertEqual(parser.OBP_INTER_FRAME, 1)
        self.assertEqual(parser.OBP_INTRA_ONLY_FRAME, 2)
        self.assertEqual(parser.OBP_SWITCH_FRAME, 3)
        # Check compatibility aliases
        self.assertEqual(parser.OBP_FRAME_TYPE_KEY_FRAME, 0)

if __name__ == '__main__':
    unittest.main()
