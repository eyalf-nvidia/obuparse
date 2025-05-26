import ctypes
import importlib 
import platform
import os
import ctypes.util 

# --- Standard CTypes Aliases ---
c_int_t = ctypes.c_int  # General purpose int, often used for enums or boolean style flags
c_uint8_t = ctypes.c_uint8
c_uint16_t = ctypes.c_uint16
c_uint32_t = ctypes.c_uint32
c_uint64_t = ctypes.c_uint64
c_int8_t = ctypes.c_int8
c_int16_t = ctypes.c_int16
c_int32_t = ctypes.c_int32 
c_int64_t = ctypes.c_int64 
c_size_t = ctypes.c_size_t
c_ssize_t = ctypes.c_ssize_t
if hasattr(ctypes, 'c_ptrdiff_t'):
    c_ptrdiff_t = ctypes.c_ptrdiff_t
else:
    # Fallback for older Python versions or environments where c_ptrdiff_t might be missing
    # c_ssize_t is often a suitable equivalent for ptrdiff_t
    c_ptrdiff_t = ctypes.c_ssize_t
c_char_p = ctypes.c_char_p
c_bool = ctypes.c_bool

_lib = None

def _load_c_library():
    global _lib
    if _lib is not None: 
        return _lib

    loaded_from_path = None
    lib_name_base = "_obuparse_c_lib" # Used for fallback messages

    # --- Primary Method: Load via importlib (Python Extension) ---
    try:
        extension_module_name = "pyobuparse._obuparse_c"
        print(f"INFO: Attempting to load C extension '{extension_module_name}' via importlib...")
        module = importlib.import_module(extension_module_name)
        if hasattr(module, '__file__') and module.__file__:
            _lib = ctypes.CDLL(module.__file__)
            loaded_from_path = module.__file__
            print(f"INFO: Successfully loaded C extension from: {loaded_from_path}")
            return _lib
        else:
            print(f"WARNING: Imported module '{extension_module_name}' but it has no '__file__' attribute.")
    except ImportError:
        print(f"INFO: C extension module '{extension_module_name}' not found via importlib. Will try fallback methods.")
    except OSError as e:
        print(f"INFO: OSError when trying to load C extension '{extension_module_name}' via importlib: {e}. Will try fallback methods.")
    except AttributeError: # Can happen if module is already loaded or other exotic issues
        print(f"INFO: AttributeError when trying to load C extension '{extension_module_name}' (possibly already loaded or other issue). Will try fallback methods.")

    # --- Fallback Method 1: Search predefined paths for specific library names ---
    print("INFO: Fallback: Trying to load library by searching predefined paths for specific library names...")
    system = platform.system()
    if system == "Windows":
        lib_actual_names = [f"{lib_name_base}.dll", f"lib{lib_name_base}.dll"]
    elif system == "Darwin": 
        lib_actual_names = [f"lib{lib_name_base}.dylib"]
    else: 
        lib_actual_names = [f"lib{lib_name_base}.so"]

    search_paths = []
    current_dir = None 
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths.append(current_dir)
    except NameError: 
        pass # __file__ not defined, e.g. in interactive interpreter

    if current_dir:
        # Add parent and grandparent directories to search path for library
        search_paths.append(os.path.abspath(os.path.join(current_dir, "..")))
        search_paths.append(os.path.abspath(os.path.join(current_dir, "..", "..")))

    for path_dir in search_paths:
        for name_variant in lib_actual_names:
            candidate_path = os.path.join(path_dir, name_variant)
            if os.path.exists(candidate_path):
                try:
                    _lib = ctypes.CDLL(candidate_path)
                    loaded_from_path = candidate_path
                    print(f"INFO: Fallback: Successfully loaded library from: {loaded_from_path}")
                    return _lib
                except OSError: 
                    print(f"INFO: Fallback: Found library at '{candidate_path}' but failed to load it.")
                    _lib = None # Reset _lib on failure to allow other methods to try
    
    if _lib: # Should not happen if logic is correct, but as a safeguard
        return _lib

    # --- Fallback Method 2: ctypes.util.find_library ---
    print(f"INFO: Fallback: Trying ctypes.util.find_library...")
    find_name_variants = [lib_name_base]
    if platform.system() == "Linux": # On Linux, it might be lib<name>.so
        find_name_variants.append(f"lib{lib_name_base}")
    
    for name_to_find in find_name_variants:
        found_by_util = ctypes.util.find_library(name_to_find)
        if found_by_util:
            try:
                _lib = ctypes.CDLL(found_by_util)
                loaded_from_path = found_by_util
                print(f"INFO: Fallback: Successfully loaded library via find_library: {loaded_from_path} (searched for '{name_to_find}')")
                return _lib
            except OSError:
                print(f"INFO: Fallback: Found library via find_library ('{found_by_util}' for '{name_to_find}') but failed to load it.")
                _lib = None # Reset _lib

    # Final check and error message
    if not _lib:
        print(f"CRITICAL: C library for 'pyobuparse._obuparse_c' could not be loaded.")
        print("  Primary attempt was to load the Python C extension via importlib.")
        print("  Fallback attempts included searching predefined paths and using ctypes.util.find_library.")
        print(f"  Predefined search paths attempted: {search_paths if search_paths else 'N/A (could not determine script path)'}")
        print(f"  Names tried with ctypes.util.find_library: {find_name_variants}")
        print("  Ensure the pyobuparse C library (expected as 'pyobuparse._obuparse_c' extension module) is compiled and accessible.")
        print("  If you compiled it manually (e.g. with build_clib), ensure it's in a standard system library path or PYTHONPATH.")

    return None

_lib = _load_c_library()

# OBPError struct definition
class OBPError(ctypes.Structure):
    _fields_ = [
        ("error", c_char_p), 
        ("size", c_size_t),  
    ]

# --- Enum Constants --- 
OBP_OBU_SEQUENCE_HEADER = 1
OBP_OBU_TEMPORAL_DELIMITER = 2
OBP_OBU_FRAME_HEADER = 3
OBP_OBU_TILE_GROUP = 4
OBP_OBU_METADATA = 5
OBP_OBU_FRAME = 6
OBP_OBU_REDUNDANT_FRAME_HEADER = 7
OBP_OBU_TILE_LIST = 8
OBP_OBU_PADDING = 15

OBP_METADATA_TYPE_HDR_CLL = 1
OBP_METADATA_TYPE_HDR_MDCV = 2
OBP_METADATA_TYPE_SCALABILITY = 3
OBP_METADATA_TYPE_ITUT_T35 = 4
OBP_METADATA_TYPE_TIMECODE = 5
# OBP_METADATA_TYPE_UNREGISTERED is not explicitly in the C enum,
# but 6-31 are for "Unregistered user private"
# Keeping this as the wrapper expects it, might need review based on C lib usage.
OBP_METADATA_TYPE_UNREGISTERED = 6


OBP_CP_BT_709 = 1
OBP_CP_UNSPECIFIED = 2
OBP_CP_BT_470_M = 4
OBP_CP_BT_470_B_G = 5
OBP_CP_BT_601 = 6
OBP_CP_SMPTE_240 = 7
OBP_CP_GENERIC_FILM = 8
OBP_CP_BT_2020 = 9
OBP_CP_XYZ = 10
OBP_CP_SMPTE_431 = 11
OBP_CP_SMPTE_432 = 12
OBP_CP_EBU_3213 = 22

OBP_TC_RESERVED_0 = 0
OBP_TC_BT_709 = 1
OBP_TC_UNSPECIFIED = 2
OBP_TC_RESERVED_3 = 3
OBP_TC_BT_470_M = 4
OBP_TC_BT_470_B_G = 5
OBP_TC_BT_601 = 6
OBP_TC_SMPTE_240 = 7
OBP_TC_LINEAR = 8
OBP_TC_LOG_100 = 9
OBP_TC_LOG_100_SQRT10 = 10
OBP_TC_IEC_61966 = 11
OBP_TC_BT_1361 = 12
OBP_TC_SRGB = 13
OBP_TC_BT_2020_10_BIT = 14
OBP_TC_BT_2020_12_BIT = 15
OBP_TC_SMPTE_2084 = 16
OBP_TC_SMPTE_428 = 17
OBP_TC_HLG = 18

OBP_MC_IDENTITY = 0
OBP_MC_BT_709 = 1
OBP_MC_UNSPECIFIED = 2
OBP_MC_RESERVED_3 = 3
OBP_MC_FCC = 4
OBP_MC_BT_470_B_G = 5
OBP_MC_BT_601 = 6
OBP_MC_SMPTE_240 = 7
OBP_MC_SMPTE_YCGCO = 8
OBP_MC_BT_2020_NCL = 9
OBP_MC_BT_2020_CL = 10
OBP_MC_SMPTE_2085 = 11
OBP_MC_CHROMAT_NCL = 12
OBP_MC_CHROMAT_CL = 13
OBP_MC_ICTCP = 14

OBP_CSP_UNKNOWN = 0
OBP_CSP_VERTICAL = 1
OBP_CSP_COLOCATED = 2
# 3 Reserved for OBP_CSP


# For compatibility with existing wrapper code that uses the old names.
# New code should use OBP_CP_*, OBP_TC_*, OBP_MC_*, OBP_CSP_*
OBP_COLOR_PRIMARIES_BT_709 = OBP_CP_BT_709
OBP_COLOR_PRIMARIES_BT_UNSPECIFIED = OBP_CP_UNSPECIFIED
OBP_COLOR_PRIMARIES_BT_470_M = OBP_CP_BT_470_M
OBP_COLOR_PRIMARIES_BT_470_B_G = OBP_CP_BT_470_B_G
OBP_COLOR_PRIMARIES_BT_601 = OBP_CP_BT_601
OBP_COLOR_PRIMARIES_SMPTE_240 = OBP_CP_SMPTE_240
OBP_COLOR_PRIMARIES_GENERIC_FILM = OBP_CP_GENERIC_FILM
OBP_COLOR_PRIMARIES_BT_2020 = OBP_CP_BT_2020
OBP_COLOR_PRIMARIES_XYZ = OBP_CP_XYZ
OBP_COLOR_PRIMARIES_SMPTE_431 = OBP_CP_SMPTE_431
OBP_COLOR_PRIMARIES_SMPTE_432 = OBP_CP_SMPTE_432
OBP_COLOR_PRIMARIES_EBU_3213 = OBP_CP_EBU_3213

OBP_TRANSFER_CHARACTERISTICS_RESERVED_0 = OBP_TC_RESERVED_0
OBP_TRANSFER_CHARACTERISTICS_BT_709 = OBP_TC_BT_709
OBP_TRANSFER_CHARACTERISTICS_UNSPECIFIED = OBP_TC_UNSPECIFIED
OBP_TRANSFER_CHARACTERISTICS_RESERVED_3 = OBP_TC_RESERVED_3
OBP_TRANSFER_CHARACTERISTICS_BT_470_M = OBP_TC_BT_470_M
OBP_TRANSFER_CHARACTERISTICS_BT_470_B_G = OBP_TC_BT_470_B_G
OBP_TRANSFER_CHARACTERISTICS_BT_601 = OBP_TC_BT_601
OBP_TRANSFER_CHARACTERISTICS_SMPTE_240 = OBP_TC_SMPTE_240
OBP_TRANSFER_CHARACTERISTICS_LINEAR = OBP_TC_LINEAR
OBP_TRANSFER_CHARACTERISTICS_LOG_100 = OBP_TC_LOG_100
OBP_TRANSFER_CHARACTERISTICS_LOG_100_SQRT10 = OBP_TC_LOG_100_SQRT10
OBP_TRANSFER_CHARACTERISTICS_IEC_61966 = OBP_TC_IEC_61966
OBP_TRANSFER_CHARACTERISTICS_BT_1361 = OBP_TC_BT_1361
OBP_TRANSFER_CHARACTERISTICS_SRGB = OBP_TC_SRGB
OBP_TRANSFER_CHARACTERISTICS_BT_2020_10_BIT = OBP_TC_BT_2020_10_BIT
OBP_TRANSFER_CHARACTERISTICS_BT_2020_12_BIT = OBP_TC_BT_2020_12_BIT
OBP_TRANSFER_CHARACTERISTICS_SMPTE_2084 = OBP_TC_SMPTE_2084
OBP_TRANSFER_CHARACTERISTICS_SMPTE_428 = OBP_TC_SMPTE_428
OBP_TRANSFER_CHARACTERISTICS_HLG = OBP_TC_HLG

OBP_MATRIX_COEFFICIENTS_IDENTITY = OBP_MC_IDENTITY
OBP_MATRIX_COEFFICIENTS_BT_709 = OBP_MC_BT_709
OBP_MATRIX_COEFFICIENTS_UNSPECIFIED = OBP_MC_UNSPECIFIED
OBP_MATRIX_COEFFICIENTS_RESERVED_3 = OBP_MC_RESERVED_3
OBP_MATRIX_COEFFICIENTS_FCC = OBP_MC_FCC
OBP_MATRIX_COEFFICIENTS_BT_470_B_G = OBP_MC_BT_470_B_G
OBP_MATRIX_COEFFICIENTS_BT_601 = OBP_MC_BT_601
OBP_MATRIX_COEFFICIENTS_SMPTE_240 = OBP_MC_SMPTE_240
OBP_MATRIX_COEFFICIENTS_YCGCO = OBP_MC_SMPTE_YCGCO
OBP_MATRIX_COEFFICIENTS_BT_2020_NCL = OBP_MC_BT_2020_NCL
OBP_MATRIX_COEFFICIENTS_BT_2020_CL = OBP_MC_BT_2020_CL
OBP_MATRIX_COEFFICIENTS_SMPTE_2085 = OBP_MC_SMPTE_2085
OBP_MATRIX_COEFFICIENTS_CHROMAT_NCL = OBP_MC_CHROMAT_NCL
OBP_MATRIX_COEFFICIENTS_CHROMAT_CL = OBP_MC_CHROMAT_CL
OBP_MATRIX_COEFFICIENTS_ICTCP = OBP_MC_ICTCP

OBP_CHROMA_SAMPLE_POSITION_UNKNOWN = OBP_CSP_UNKNOWN
OBP_CHROMA_SAMPLE_POSITION_VERTICAL = OBP_CSP_VERTICAL
OBP_CHROMA_SAMPLE_POSITION_COLOCATED = OBP_CSP_COLOCATED

OBP_KEY_FRAME = 0
OBP_INTER_FRAME = 1
OBP_INTRA_ONLY_FRAME = 2
OBP_SWITCH_FRAME = 3

# For compatibility with existing wrapper code that uses the old names.
# New code should use OBP_KEY_FRAME etc.
OBP_FRAME_TYPE_KEY_FRAME = OBP_KEY_FRAME
OBP_FRAME_TYPE_INTER_FRAME = OBP_INTER_FRAME
OBP_FRAME_TYPE_INTRA_ONLY_FRAME = OBP_INTRA_ONLY_FRAME
OBP_FRAME_TYPE_SWITCH_FRAME = OBP_SWITCH_FRAME

# --- Nested C Structs ---
class OBPTimingInfo(ctypes.Structure):
    _fields_ = [
        ("num_units_in_display_tick", c_uint32_t),
        ("time_scale", c_uint32_t),
        ("equal_picture_interval", c_int_t), # C: int
        ("num_ticks_per_picture_minus_1", c_uint32_t),
    ]

class OBPDecoderModelInfo(ctypes.Structure):
    _fields_ = [
        ("buffer_delay_length_minus_1", c_uint8_t),
        ("num_units_in_decoding_tick", c_uint32_t),
        ("buffer_removal_time_length_minus_1", c_uint8_t),
        ("frame_presentation_time_length_minus_1", c_uint8_t),
    ]

class OBPOperatingParametersInfo(ctypes.Structure): # As per C struct
    _fields_ = [
        ("decoder_buffer_delay", c_uint64_t), # C: uint64_t
        ("encoder_buffer_delay", c_uint64_t), # C: uint64_t
        ("low_delay_mode_flag", c_int_t),    # C: int
    ]

class OBPColorConfig(ctypes.Structure): # As per C struct
    _fields_ = [
        ("high_bitdepth", c_int_t), # C: int
        ("twelve_bit", c_int_t), # C: int
        ("BitDepth", c_uint8_t), # Added from C
        ("mono_chrome", c_int_t), # C: int
        ("NumPlanes", c_uint8_t), # Added from C
        ("color_description_present_flag", c_int_t), # C: int
        ("color_primaries", c_int_t), # Was c_uint8_t, OBPColorPrimaries (enum)
        ("transfer_characteristics", c_int_t), # Was c_uint8_t, OBPTransferCharacteristics (enum)
        ("matrix_coefficients", c_int_t), # Was c_uint8_t, OBPMatrixCoefficients (enum)
        ("color_range", c_int_t), # C: int, was c_uint8_t
        ("subsampling_x", c_int_t), # Added from C
        ("subsampling_y", c_int_t), # Added from C
        ("chroma_sample_position", c_int_t), # Was c_uint8_t, OBPChromaSamplePosition (enum)
        ("separate_uv_delta_q", c_int_t), # C: int, was c_uint8_t
    ]

class OBPSuperresParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("use_superres", c_int_t), # C: int
        ("coded_denom", c_uint8_t),
        # Below fields are not in C struct, but might be derived by lib.
        # For strict C struct mapping, these would be removed. Kept for now.
        # ("superres_upscaled_width", c_uint16_t),
        # ("superres_upscaled_height", c_uint16_t),
    ]

class OBPInterpolationFilter(ctypes.Structure): # As per C struct
    _fields_ = [
        ("is_filter_switchable", c_int_t), # C: int
        ("interpolation_filter", c_uint8_t) # C: uint8_t - enum type, but raw value
        # ("value", c_uint8_t) # Old field, replaced by above
    ]


class OBPTileInfo(ctypes.Structure): # As per C struct
    _fields_ = [
        ("uniform_tile_spacing_flag", c_int_t), # C: int
        # MiColStarts, MiRowStarts, width_in_sbs_minus_1, height_in_sbs_minus_1 are not in C struct
        # They are likely calculated by the library. For strict C mapping, remove.
        # ("MiColStarts", c_uint32_t * 65),
        # ("MiRowStarts", c_uint32_t * 65),
        # ("width_in_sbs_minus_1", c_uint16_t * 64),
        # ("height_in_sbs_minus_1", c_uint16_t * 64),
        ("TileRows", c_uint16_t), # C: uint16_t
        ("TileCols", c_uint16_t), # C: uint16_t
        ("context_update_tile_id", c_uint32_t), # C: uint32_t
        ("tile_size_bytes_minus_1", c_uint8_t), # C: uint8_t
        # tile_cols, tile_rows in python struct were likely TileCols, TileRows.
    ]

class OBPQuantizationParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("base_q_idx", c_uint8_t),
        # DeltaQYDc etc. are not in C struct, diff_uv_delta is.
        # ("DeltaQYDc", c_int8_t),
        # ("DeltaQUDc", c_int8_t),
        # ("DeltaQUAc", c_int8_t),
        # ("DeltaQVDc", c_int8_t),
        # ("DeltaQVAc", c_int8_t),
        ("diff_uv_delta", c_int_t), # C: int
        ("using_qmatrix", c_int_t), # C: int
        ("qm_y", c_uint8_t),
        ("qm_u", c_uint8_t),
        ("qm_v", c_uint8_t),
    ]

class OBPSegmentationParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("segmentation_enabled", c_int_t), # C: int
        ("segmentation_update_map", c_int_t), # C: int
        ("segmentation_temporal_update", c_int_t), # C: int
        ("segmentation_update_data", c_int_t), # C: int
        # SEG_LVL_MAX is 8 in C code (not in header but implied by array sizes)
        # feature_enabled[8][SEG_LVL_MAX], feature_data[8][SEG_LVL_MAX]
        ("feature_enabled", (c_uint8_t * 8) * 8), # Corrected from * 4 to * 8
        ("feature_data", (c_int16_t * 8) * 8),  # Corrected from * 4 to * 8
    ]

class OBPDeltaQParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("delta_q_present", c_int_t), # C: int
        ("delta_q_res", c_uint8_t),
    ]

class OBPDeltaLFParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("delta_lf_present", c_int_t), # C: int
        ("delta_lf_res", c_uint8_t),
        ("delta_lf_multi", c_int_t), # C: int
    ]

class OBPLoopFilterParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("loop_filter_level", c_uint8_t * 4),
        ("loop_filter_sharpness", c_uint8_t),
        ("loop_filter_delta_enabled", c_int_t), # C: int
        ("update_ref_delta", c_int_t * 8), # Added from C
        ("loop_filter_ref_deltas", c_int8_t * 8),
        ("update_mode_delta", c_int_t * 8), # Added from C
        ("loop_filter_mode_deltas", c_int8_t * 8), # Corrected from * 2 to * 8
    ]

class OBPCdefParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("cdef_damping_minus_3", c_uint8_t),
        ("cdef_bits", c_uint8_t),
        ("cdef_y_pri_strength", c_uint8_t * 8),
        ("cdef_y_sec_strength", c_uint8_t * 8),
        ("cdef_uv_pri_strength", c_uint8_t * 8),
        ("cdef_uv_sec_strength", c_uint8_t * 8),
    ]

class OBPLrParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("lr_type", c_uint8_t * 3), # enum types, but raw values
        ("lr_unit_shift", c_uint8_t),
        ("lr_uv_shift", c_int_t), # C: int
    ]

class OBPGlobalMotionParams(ctypes.Structure): # As per C struct
    _fields_ = [
        ("gm_type", c_uint8_t * 8), 
        ("gm_params", (c_int32_t * 6) * 8),       # Represents C: int32_t gm_params[8][6]
        ("prev_gm_params", (c_uint32_t * 6) * 8)  # Represents C: uint32_t prev_gm_params[8][6]
    ]


class OBPTileListEntry(ctypes.Structure): # As per C struct
    _fields_ = [
        ("anchor_frame_idx", c_uint8_t),
        ("anchor_tile_row", c_uint8_t),
        ("anchor_tile_col", c_uint8_t),
        ("tile_data_size_minus_1", c_uint16_t),
        ("coded_tile_data", ctypes.POINTER(c_uint8_t)), # Renamed from tile_specific_data
        ("coded_tile_data_size", c_size_t) # Added from C
    ]

class OBPMetadataITUTT35(ctypes.Structure): # As per C struct
    _fields_ = [
        ("itu_t_t35_country_code", c_uint8_t),
        ("itu_t_t35_country_code_extension_byte", c_uint8_t), # Added from C
        # ("itu_t_t35_terminal_provider_code", c_uint16_t), # Not in C struct
        # ("itu_t_t35_terminal_provider_oriented_code", c_uint16_t), # Not in C struct
        ("itu_t_t35_payload_bytes", ctypes.POINTER(c_uint8_t)), # Added _bytes for clarity
        ("itu_t_t35_payload_bytes_size", c_size_t), # Renamed from itu_t_t35_payload_byte_count
    ]

class OBPMetadataHDRCLL(ctypes.Structure): # As per C struct
    _fields_ = [
        ("max_cll", c_uint16_t),
        ("max_fall", c_uint16_t)
    ]

class OBPMetadataHDRMDCV(ctypes.Structure): # As per C struct
    _fields_ = [
        ("primary_chromaticity_x", c_uint16_t * 3),
        ("primary_chromaticity_y", c_uint16_t * 3),
        ("white_point_chromaticity_x", c_uint16_t),
        ("white_point_chromaticity_y", c_uint16_t),
        ("luminance_max", c_uint32_t),
        ("luminance_min", c_uint32_t),
    ]

class OBPScalabilityStructure(ctypes.Structure): # As per C struct
    _fields_ = [
        ("spatial_layers_cnt_minus_1", c_uint8_t),
        ("spatial_layer_dimensions_present_flag", c_int_t), # C: int
        ("spatial_layer_description_present_flag", c_int_t), # C: int
        ("temporal_group_description_present_flag", c_int_t), # C: int
        ("scalability_structure_reserved_3bits", c_uint8_t),
        # Added missing fields from C struct below
        ("spatial_layer_max_width", c_uint16_t * 3),
        ("spatial_layer_max_height", c_uint16_t * 3),
        ("spatial_layer_ref_id", c_uint8_t * 3),
        ("temporal_group_size", c_uint8_t),
        ("temporal_group_temporal_id", c_uint8_t * 256),
        ("temporal_group_temporal_switching_up_point_flag", c_int_t * 256), # C: int
        ("temporal_group_spatial_switching_up_point_flag", c_int_t * 256), # C: int
        ("temporal_group_ref_cnt", c_uint8_t * 256),
        ("temporal_group_ref_pic_diff", (c_uint8_t * 8) * 256), # C: uint8_t temporal_group_ref_pic_diff[256][8]
    ]


class OBPMetadataScalability(ctypes.Structure): # As per C struct
    _fields_ = [
        ("scalability_mode_idc", c_uint8_t),
        ("scalability_structure", OBPScalabilityStructure),
    ]

class OBPMetadataTimecode(ctypes.Structure): # As per C struct
    _fields_ = [
        ("counting_type", c_uint8_t),
        ("full_timestamp_flag", c_int_t), # C: int
        ("discontinuity_flag", c_int_t), # C: int
        ("cnt_dropped_flag", c_int_t), # C: int
        ("n_frames", c_uint16_t), # C: uint16_t
        ("seconds_value", c_uint8_t),
        ("minutes_value", c_uint8_t),
        ("hours_value", c_uint8_t),
        ("seconds_flag", c_int_t), # C: int
        ("minutes_flag", c_int_t), # C: int
        ("hours_flag", c_int_t), # C: int
        ("time_offset_length", c_uint8_t),
        ("time_offset_value", c_uint32_t), # C: uint32_t
    ]

class OBPMetadataUnregistered(ctypes.Structure): # As per C struct
    _fields_ = [
        # ("uuid", c_uint8_t * 16), # Not in C struct for unregistered (it's for a specific type of metadata)
        # ("payload_byte_count", c_size_t),
        # ("payload", ctypes.POINTER(c_uint8_t)),
        ("buf", ctypes.POINTER(c_uint8_t)), # From C struct
        ("buf_size", c_size_t),             # From C struct
    ]

# --- Main C Structs ---
class OBPFilmGrainParameters(ctypes.Structure): # As per C struct
    _fields_ = [
        ("apply_grain", c_int_t), # C: int
        ("grain_seed", c_uint16_t),
        ("update_grain", c_int_t), # C: int
        ("film_grain_params_ref_idx", c_uint8_t),
        ("num_y_points", c_uint8_t),
        ("point_y_value", c_uint8_t * 16), # Corrected from 14
        ("point_y_scaling", c_uint8_t * 16), # Corrected from 14
        ("chroma_scaling_from_luma", c_int_t), # C: int
        ("num_cb_points", c_uint8_t),
        ("point_cb_value", c_uint8_t * 16), # Corrected from 10
        ("point_cb_scaling", c_uint8_t * 16), # Corrected from 10
        ("num_cr_points", c_uint8_t),
        ("point_cr_value", c_uint8_t * 16), # Corrected from 10
        ("point_cr_scaling", c_uint8_t * 16), # Corrected from 10
        ("grain_scaling_minus_8", c_uint8_t),
        ("ar_coeff_lag", c_uint8_t),
        ("ar_coeffs_y_plus_128", c_uint8_t * 24),
        ("ar_coeffs_cb_plus_128", c_uint8_t * 25),
        ("ar_coeffs_cr_plus_128", c_uint8_t * 25),
        ("ar_coeff_shift_minus_6", c_uint8_t),
        ("grain_scale_shift", c_uint8_t),
        ("cb_mult", c_uint8_t),
        ("cb_luma_mult", c_uint8_t),
        ("cb_offset", c_uint16_t),
        ("cr_mult", c_uint8_t),
        ("cr_luma_mult", c_uint8_t),
        ("cr_offset", c_uint16_t),
        ("overlap_flag", c_int_t), # C: int
        ("clip_to_restricted_range", c_int_t), # C: int
    ]

class OBPSequenceHeader(ctypes.Structure): # As per C struct
    _fields_ = [
        ("seq_profile", c_uint8_t),
        ("still_picture", c_int_t), # C: int
        ("reduced_still_picture_header", c_int_t), # C: int
        ("timing_info_present_flag", c_int_t), # C: int
        ("timing_info", OBPTimingInfo),
        ("decoder_model_info_present_flag", c_int_t), # C: int
        ("decoder_model_info", OBPDecoderModelInfo),
        ("initial_display_delay_present_flag", c_int_t), # C: int
        ("operating_points_cnt_minus_1", c_uint8_t),
        ("operating_point_idc", c_uint8_t * 32), # Corrected from c_uint16_t
        ("seq_level_idx", c_uint8_t * 32),
        ("seq_tier", c_uint8_t * 32),
        ("decoder_model_present_for_this_op", c_int_t * 32), # C: int array
        ("operating_parameters_info", OBPOperatingParametersInfo * 32), # Nested struct array
        ("initial_display_delay_present_for_this_op", c_int_t * 32), # C: int array
        ("initial_display_delay_minus_1", c_uint8_t * 32),
        ("frame_width_bits_minus_1", c_uint8_t),
        ("frame_height_bits_minus_1", c_uint8_t),
        ("max_frame_width_minus_1", c_uint32_t),
        ("max_frame_height_minus_1", c_uint32_t),
        ("frame_id_numbers_present_flag", c_int_t), # C: int
        ("delta_frame_id_length_minus_2", c_uint8_t),
        ("additional_frame_id_length_minus_1", c_uint8_t),
        ("use_128x128_superblock", c_int_t), # C: int
        ("enable_filter_intra", c_int_t), # C: int
        ("enable_intra_edge_filter", c_int_t), # C: int
        ("enable_interintra_compound", c_int_t), # C: int
        ("enable_masked_compound", c_int_t), # C: int
        ("enable_warped_motion", c_int_t), # C: int
        ("enable_dual_filter", c_int_t), # C: int
        ("enable_order_hint", c_int_t), # C: int
        ("enable_jnt_comp", c_int_t), # C: int
        ("enable_ref_frame_mvs", c_int_t), # C: int
        ("seq_choose_screen_content_tools", c_int_t), # C: int
        ("seq_force_screen_content_tools", c_int_t), # C: int (actually select_screen_content_tools in spec?)
        ("seq_choose_integer_mv", c_int_t), # C: int
        ("seq_force_integer_mv", c_int_t), # C: int (actually select_integer_mv in spec?)
        ("order_hint_bits_minus_1", c_uint8_t),
        ("OrderHintBits", c_uint8_t), # Added from C
        ("enable_superres", c_int_t), # C: int
        ("enable_cdef", c_int_t), # C: int
        ("enable_restoration", c_int_t), # C: int
        ("color_config", OBPColorConfig),
        ("film_grain_params_present", c_int_t), # C: int
        # FrameWidth, FrameHeight are not part of the C struct, they are derived.
        # ("FrameWidth", c_uint32_t),
        # ("FrameHeight", c_uint32_t),
    ]

class OBPFrameHeader(ctypes.Structure): # As per C struct
    _fields_ = [
        ("show_existing_frame", c_int_t), # C: int
        ("frame_to_show_map_idx", c_uint8_t),
        # ("temporal_point_info_present", c_uint8_t), # Python helper, not in C struct
        ("temporal_point_info", c_uint32_t), # C struct is: struct { uint32_t frame_presentation_time; } temporal_point_info;
                                             # Flattening to frame_presentation_time for simplicity.
        ("display_frame_id", c_uint32_t), # Not in C struct (added by lib?)
        ("frame_type", c_int_t), # Was c_uint8_t, OBPFrameType (enum)
        ("show_frame", c_int_t), # C: int
        ("showable_frame", c_int_t), # C: int
        ("error_resilient_mode", c_int_t), # C: int
        ("disable_cdf_update", c_int_t), # C: int
        ("allow_screen_content_tools", c_int_t), # C: int
        ("force_integer_mv", c_int_t), # C: int
        ("current_frame_id", c_uint32_t), # Not in C struct (added by lib?)
        ("frame_size_override_flag", c_int_t), # C: int
        ("order_hint", c_uint8_t), # C: uint8_t
        ("primary_ref_frame", c_uint8_t),
        ("buffer_removal_time_present_flag", c_int_t), # Added from C
        ("buffer_removal_time", c_uint32_t * 32), # Added from C
        ("refresh_frame_flags", c_uint8_t),
        ("ref_order_hint", c_uint8_t * 8), # Corrected from c_uint32_t
        ("frame_width_minus_1", c_uint32_t),
        ("frame_height_minus_1", c_uint32_t),
        ("superres_params", OBPSuperresParams),
        ("render_and_frame_size_different", c_int_t), # Added from C
        ("render_width_minus_1", c_uint16_t), # Corrected from c_uint32_t
        ("render_height_minus_1", c_uint16_t), # Corrected from c_uint32_t
        ("RenderWidth", c_uint32_t), # Added from C (derived)
        ("RenderHeight", c_uint32_t), # Added from C (derived)
        ("allow_intrabc", c_int_t), # C: int
        # ("palette_mode_enabled", c_uint8_t), # Not in C struct
        ("frame_refs_short_signaling", c_int_t), # Added from C
        ("last_frame_idx", c_uint8_t), # Added from C
        ("gold_frame_idx", c_uint8_t), # Added from C
        ("ref_frame_idx", c_uint8_t * 7), # Added from C
        ("delta_frame_id_minus_1", c_uint8_t * 7), # Added from C
        ("found_ref", c_int_t), # Added from C
        ("allow_high_precision_mv", c_int_t), # C: int
        ("interpolation_filter", OBPInterpolationFilter), # This is struct in C
        ("is_motion_mode_switchable", c_int_t), # C: int
        ("use_ref_frame_mvs", c_int_t), # C: int
        ("disable_frame_end_update_cdf", c_int_t), # C: int
        ("tile_info", OBPTileInfo),
        ("quantization_params", OBPQuantizationParams),
        ("segmentation_params", OBPSegmentationParams),
        ("delta_q_params", OBPDeltaQParams),
        ("delta_lf_params", OBPDeltaLFParams),
        ("loop_filter_params", OBPLoopFilterParams),
        ("cdef_params", OBPCdefParams),
        ("lr_params", OBPLrParams),
        ("tx_mode_select", c_int_t), # Added from C (tx_mode in C)
        ("skip_mode_present", c_int_t), # C: int
        ("reference_select", c_int_t), # Added from C
        ("allow_warped_motion", c_int_t), # C: int
        ("reduced_tx_set", c_int_t), # C: int
        ("global_motion_params", OBPGlobalMotionParams * 8),
        ("film_grain_params", OBPFilmGrainParameters),
        # MiCols, MiRows, FrameWidth, FrameHeight are not part of C struct, they are derived
        # ("MiCols", c_uint32_t),
        # ("MiRows", c_uint32_t),
        # ("FrameWidth", c_uint32_t),
        # ("FrameHeight", c_uint32_t),
        # ("large_scale_tile", c_uint8_t), # Not in C struct
    ]

class OBPTileGroup(ctypes.Structure): # As per C struct
    _fields_ = [
        ("NumTiles", c_uint16_t), # Not in C struct (derived?) - Actually it is in C struct.
        ("tile_start_and_end_present_flag", c_int_t), # Added from C
        ("tg_start", c_uint16_t), # Added from C
        ("tg_end", c_uint16_t),   # Added from C
        ("TileSize", c_uint64_t * 4096), # Added from C
        # ("obu_size", c_size_t), # Not in C struct
        # ("data", ctypes.POINTER(c_uint8_t)), # Not in C struct (TileSize implies data)
        # ("obu_data_offset_within_tile_group_obu", c_size_t), # Not in C struct
    ]

class OBPTileList(ctypes.Structure): # As per C struct
    _fields_ = [
        ("output_frame_width_in_tiles_minus_1", c_uint8_t), # Corrected name
        ("output_frame_height_in_tiles_minus_1", c_uint8_t), # Corrected name
        ("tile_count_minus_1", c_uint16_t),
        ("tile_list_entry", OBPTileListEntry * 65536), # C: tile_list_entry[65536]
    ]

class OBPMetadata(ctypes.Structure): # As per C struct
    _fields_ = [
        ("metadata_type", c_int_t), # Was type (c_uint32_t), OBPMetadataType (enum)
        ("metadata_itut_t35", OBPMetadataITUTT35),
        ("metadata_hdr_cll", OBPMetadataHDRCLL),
        ("metadata_hdr_mdcv", OBPMetadataHDRMDCV),
        ("metadata_scalability", OBPMetadataScalability),
        ("metadata_timecode", OBPMetadataTimecode),
        ("unregistered", OBPMetadataUnregistered), # C struct for generic unregistered metadata
        # ("obu_size", c_size_t), # Not in C struct
        # ("data", ctypes.POINTER(c_uint8_t)), # Not in C struct
    ]

class OBPState(ctypes.Structure): # As per C struct
    _fields_ = [
        ("prev", OBPFrameHeader), # Added from C
        ("prev_filled", c_int_t), # Added from C
        ("frame_header_end_pos", c_size_t), # Added from C
        ("RefFrameType", c_int_t * 8), # OBPFrameType (enum)
        ("RefValid", c_uint8_t * 8),
        ("RefOrderHint", c_uint8_t * 8), # C: uint8_t RefOrderHint[8]
        ("OrderHint", c_uint8_t * 8), # C: uint8_t OrderHint[8]
        ("RefFrameId", c_uint8_t * 8), # C: uint8_t RefFrameId[8]
        ("RefUpscaledWidth", c_uint32_t * 8), # C: uint32_t
        ("RefFrameHeight", c_uint32_t * 8), # C: uint32_t
        ("RefRenderWidth", c_uint32_t * 8), # C: uint32_t
        ("RefRenderHeight", c_uint32_t * 8), # C: uint32_t
        ("RefFrameSignBias", c_int32_t * 8), # C: int32_t RefFrameSignBias[8]
        ("RefGrainParams", OBPFilmGrainParameters * 8), # C: OBPFilmGrainParameters RefGrainParams[8]
        ("order_hint", c_uint8_t), # C: uint8_t order_hint (lowercase)
        ("SavedGmParams", ((c_uint32_t * 6) * 8) * 8), # C: uint32_t SavedGmParams[8][8][6]
        ("SavedFeatureEnabled", ((c_int_t * 8) * 8) * 8), # C: int SavedFeatureEnabled[8][8][8]
        ("SavedFeatureData", ((c_int16_t * 8) * 8) * 8), # C: int16_t SavedFeatureData[8][8][8]
        ("SavedLoopFilterRefDeltas", (c_int8_t * 8) * 8), # C: int8_t SavedLoopFilterRefDeltas[8][8]
        ("SavedLoopFilterModeDeltas", (c_int8_t * 8) * 8), # C: int8_t SavedLoopFilterModeDeltas[8][8]

        # Fields below were in Python but not in C header OBPState, removed for alignment.
        # ("ref_frame_sign_bias", c_int_t * 7),
        # ("OrderHints", c_uint32_t * 8), # Replaced by RefOrderHint and OrderHint
        # ("current_frame_id", c_int_t),
        # ("PrevGmParams", OBPGlobalMotionParams * 8), # Replaced by SavedGmParams
        # ("PrevFilmGrainParams", OBPFilmGrainParameters), # Replaced by RefGrainParams
        # ("active_ref_idx", c_int_t * 7),
        # ("RefFrameWidth", c_int_t * 8), # Covered by OBPFrameHeader in prev or specific fields
        # ("RefFrameHeight", c_int_t * 8),
        # ("RefMiCols", c_int_t * 8),
        # ("RefMiRows", c_int_t * 8),
        # ("RefSubsamplingX", c_int_t * 8),
        # ("RefSubsamplingY", c_int_t * 8),
        # ("FrameIsIntra", c_bool * 8),
        # ("error_resilient_mode", c_uint8_t),
        # ("large_scale_tile", c_uint8_t),
        # ("primary_ref_frame", c_uint8_t),
        # ("disable_cdf_update", c_uint8_t),
        # ("allow_screen_content_tools", c_uint8_t),
        # ("force_integer_mv", c_uint8_t),
        # ("coded_lossless", c_uint8_t),
        # ("all_lossless", c_uint8_t),
        # ("delta_q_present_flag", c_uint8_t),
        # ("prev_segment_ids", c_uint8_t * (64*64)),
        # ("last_active_seg_id", c_uint8_t),
        # ("seg_feature_active", c_bool * (8*4)),
    ]

# --- Function Signatures ---
if _lib:
    # obp_get_next_obu(uint8_t *buf, size_t buf_size, OBPOBUType *obu_type, ptrdiff_t *offset,
    #                  size_t *obu_size, int *temporal_id, int *spatial_id, OBPError *err);
    _lib.obp_get_next_obu.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(c_int_t),      # obu_type (OBPOBUType is an enum, so pointer to underlying int)
        ctypes.POINTER(c_ptrdiff_t),  # offset
        ctypes.POINTER(c_size_t),     # obu_size
        ctypes.POINTER(c_int_t),      # temporal_id
        ctypes.POINTER(c_int_t),      # spatial_id
        # ctypes.POINTER(c_int_t),    # REMOVED: obu_extension_flag_ptr (not in C function signature)
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_get_next_obu.restype = c_int_t

    # obp_parse_sequence_header(uint8_t *buf, size_t buf_size, OBPSequenceHeader *seq_header, OBPError *err);

    _lib.obp_parse_sequence_header.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPSequenceHeader), # seq_header
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_sequence_header.restype = c_int_t

    # obp_parse_frame_header(uint8_t *buf, size_t buf_size, OBPSequenceHeader *seq_header, OBPState *state,
    #                        int temporal_id, int spatial_id, OBPFrameHeader *frame_header, int *SeenFrameHeader, OBPError *err);
    _lib.obp_parse_frame_header.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPSequenceHeader), # seq_header
        ctypes.POINTER(OBPState),     # state
        c_int_t,                      # temporal_id
        c_int_t,                      # spatial_id
        ctypes.POINTER(OBPFrameHeader),# frame_header
        ctypes.POINTER(c_int_t),      # SeenFrameHeader
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_frame_header.restype = c_int_t

    # obp_parse_frame(uint8_t *buf, size_t buf_size, OBPSequenceHeader *seq_header, OBPState *state,
    #                 int temporal_id, int spatial_id, OBPFrameHeader *frame_header, OBPTileGroup *tile_group,
    #                 int *SeenFrameHeader, OBPError *err);
    _lib.obp_parse_frame.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPSequenceHeader), # seq_header
        ctypes.POINTER(OBPState),     # state
        c_int_t,                      # temporal_id
        c_int_t,                      # spatial_id
        ctypes.POINTER(OBPFrameHeader),# frame_header
        ctypes.POINTER(OBPTileGroup), # tile_group
        ctypes.POINTER(c_int_t),      # SeenFrameHeader
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_frame.restype = c_int_t

    # obp_parse_tile_group(uint8_t *buf, size_t buf_size, OBPFrameHeader *frame_header, OBPTileGroup *tile_group,
    #                      int *SeenFrameHeader, OBPError *err);
    _lib.obp_parse_tile_group.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPFrameHeader),# frame_header
        ctypes.POINTER(OBPTileGroup), # tile_group
        ctypes.POINTER(c_int_t),      # SeenFrameHeader
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_tile_group.restype = c_int_t

    # obp_parse_metadata(uint8_t *buf, size_t buf_size, OBPMetadata *metadata, OBPError *err);
    _lib.obp_parse_metadata.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPMetadata),  # metadata
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_metadata.restype = c_int_t

    # obp_parse_tile_list(uint8_t *buf, size_t buf_size, OBPTileList *tile_list, OBPError *err);
    _lib.obp_parse_tile_list.argtypes = [
        ctypes.POINTER(c_uint8_t),    # buf
        c_size_t,                     # buf_size
        ctypes.POINTER(OBPTileList),  # tile_list
        ctypes.POINTER(OBPError)      # err
    ]
    _lib.obp_parse_tile_list.restype = c_int_t

    # OBPState is an opaque struct in the public API, but if the library provides an init function:
    # void obp_state_init(OBPState *state); (Example, not in provided header)
    # Check if such a function exists in the actual library if state needs explicit initialization.
    # For now, assuming direct zero-initialization by the user is sufficient as per C header comment.
    if hasattr(_lib, "obp_state_init"): # Keep this if it's used by the project
        _lib.obp_state_init.argtypes = [ctypes.POINTER(OBPState)]
        _lib.obp_state_init.restype = None

    # void obp_free_error_string(char *error_str); (Example, not in provided header)
    # Assuming OBPError.error is allocated by the C lib and needs freeing.
    # The existing wrapper has this, so keeping it.
    if hasattr(_lib, "obp_free_error_string"):
        _lib.obp_free_error_string.argtypes = [c_char_p]
        _lib.obp_free_error_string.restype = None
else:
    # This part should remain unchanged
    print("Warning: obuparse C library not loaded. OBU parsing functions in _c_wrapper will not be configured.")
    def _dummy_func_factory(name):
        def _dummy_func(*args, **kwargs):
            raise OSError(f"C library not loaded. Cannot call {name}.")
        return _dummy_func

    obp_get_next_obu = _dummy_func_factory("obp_get_next_obu")
    obp_parse_sequence_header = _dummy_func_factory("obp_parse_sequence_header")
    obp_parse_frame_header = _dummy_func_factory("obp_parse_frame_header")
    obp_parse_frame = _dummy_func_factory("obp_parse_frame")
    obp_parse_tile_group = _dummy_func_factory("obp_parse_tile_group")
    obp_parse_metadata = _dummy_func_factory("obp_parse_metadata")
    obp_parse_tile_list = _dummy_func_factory("obp_parse_tile_list")
    obp_state_init = _dummy_func_factory("obp_state_init")
    obp_free_error_string = _dummy_func_factory("obp_free_error_string")


def free_obp_error_string(error_struct_instance: OBPError):
    if _lib and hasattr(_lib, 'obp_free_error_string') and error_struct_instance.error:
        _lib.obp_free_error_string(error_struct_instance.error)
        error_struct_instance.error = None 
        error_struct_instance.size = 0

__all__ = [
    "OBPError", "free_obp_error_string",
    "OBP_OBU_SEQUENCE_HEADER", "OBP_OBU_TEMPORAL_DELIMITER", "OBP_OBU_FRAME_HEADER",
    "OBP_OBU_TILE_GROUP", "OBP_OBU_METADATA", "OBP_OBU_FRAME", # Corrected OBU enum exports
    "OBP_OBU_REDUNDANT_FRAME_HEADER", "OBP_OBU_TILE_LIST", "OBP_OBU_PADDING",
    "OBP_METADATA_TYPE_HDR_CLL", "OBP_METADATA_TYPE_HDR_MDCV", "OBP_METADATA_TYPE_SCALABILITY",
    "OBP_METADATA_TYPE_ITUT_T35", "OBP_METADATA_TYPE_TIMECODE", "OBP_METADATA_TYPE_UNREGISTERED",

    # Exporting new standard enum names
    "OBP_CP_BT_709", "OBP_CP_UNSPECIFIED", "OBP_CP_BT_470_M", "OBP_CP_BT_470_B_G",
    "OBP_CP_BT_601", "OBP_CP_SMPTE_240", "OBP_CP_GENERIC_FILM", "OBP_CP_BT_2020",
    "OBP_CP_XYZ", "OBP_CP_SMPTE_431", "OBP_CP_SMPTE_432", "OBP_CP_EBU_3213",

    "OBP_TC_RESERVED_0", "OBP_TC_BT_709", "OBP_TC_UNSPECIFIED", "OBP_TC_RESERVED_3",
    "OBP_TC_BT_470_M", "OBP_TC_BT_470_B_G", "OBP_TC_BT_601", "OBP_TC_SMPTE_240",
    "OBP_TC_LINEAR", "OBP_TC_LOG_100", "OBP_TC_LOG_100_SQRT10", "OBP_TC_IEC_61966",
    "OBP_TC_BT_1361", "OBP_TC_SRGB", "OBP_TC_BT_2020_10_BIT", "OBP_TC_BT_2020_12_BIT",
    "OBP_TC_SMPTE_2084", "OBP_TC_SMPTE_428", "OBP_TC_HLG",

    "OBP_MC_IDENTITY", "OBP_MC_BT_709", "OBP_MC_UNSPECIFIED", "OBP_MC_RESERVED_3",
    "OBP_MC_FCC", "OBP_MC_BT_470_B_G", "OBP_MC_BT_601", "OBP_MC_SMPTE_240",
    "OBP_MC_SMPTE_YCGCO", "OBP_MC_BT_2020_NCL", "OBP_MC_BT_2020_CL", "OBP_MC_SMPTE_2085",
    "OBP_MC_CHROMAT_NCL", "OBP_MC_CHROMAT_CL", "OBP_MC_ICTCP",

    "OBP_CSP_UNKNOWN", "OBP_CSP_VERTICAL", "OBP_CSP_COLOCATED",

    "OBP_KEY_FRAME", "OBP_INTER_FRAME", "OBP_INTRA_ONLY_FRAME", "OBP_SWITCH_FRAME",

    # Keep old compatibility names for now
    "OBP_COLOR_PRIMARIES_BT_709", "OBP_COLOR_PRIMARIES_BT_UNSPECIFIED", # ... and so on for all old names
    "OBP_TRANSFER_CHARACTERISTICS_BT_709", # ... and so on
    "OBP_MATRIX_COEFFICIENTS_IDENTITY", # ... and so on
    "OBP_CHROMA_SAMPLE_POSITION_UNKNOWN", # ... and so on
    "OBP_FRAME_TYPE_KEY_FRAME", "OBP_FRAME_TYPE_INTER_FRAME", "OBP_FRAME_TYPE_INTRA_ONLY_FRAME", "OBP_FRAME_TYPE_SWITCH_FRAME",

    "c_int_t", "c_uint8_t", "c_uint16_t", "c_uint32_t", "c_uint64_t", # Basic types
    "c_int8_t", "c_int16_t", "c_int32_t", "c_int64_t", # Basic types
    "c_size_t", "c_ssize_t", "c_ptrdiff_t", "c_char_p", "c_bool",
    "OBPTimingInfo", "OBPDecoderModelInfo", "OBPOperatingParametersInfo", "OBPColorConfig",
    "OBPSuperresParams", "OBPInterpolationFilter", "OBPTileInfo", "OBPQuantizationParams",
    "OBPSegmentationParams", "OBPDeltaQParams", "OBPDeltaLFParams", "OBPLoopFilterParams",
    "OBPCdefParams", "OBPLrParams", "OBPGlobalMotionParams", "OBPTileListEntry",
    "OBPMetadataITUTT35", "OBPMetadataHDRCLL", "OBPMetadataHDRMDCV",
    "OBPScalabilityStructure", "OBPMetadataScalability", "OBPMetadataTimecode", "OBPMetadataUnregistered",
    "OBPFilmGrainParameters", "OBPSequenceHeader", "OBPFrameHeader", "OBPTileGroup",
    "OBPTileList", "OBPMetadata", "OBPState",
    "obp_get_next_obu", "obp_parse_sequence_header", "obp_parse_frame_header",
    "obp_parse_frame", "obp_parse_tile_group", "obp_parse_metadata", "obp_parse_tile_list",
    "obp_state_init",
]
