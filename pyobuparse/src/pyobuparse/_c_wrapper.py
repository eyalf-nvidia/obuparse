"""
Low-level ctypes wrapper for the obuparse C library.

This module defines the C-level structures, enums, and function signatures
necessary to interface with the compiled `obuparse` shared library.
It handles loading the library and provides direct access to its functions.

The definitions herein are intended to closely mirror those in `obuparse.h`.
Pythonic wrappers and higher-level abstractions are provided in the
`parser.py` module.

Attributes:
    _lib (ctypes.CDLL | None): A handle to the loaded C library. `None` if loading failed.
"""
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

# --- Enum Definitions ---
import enum

class OBPOBUType(enum.IntEnum):
    OBP_OBU_SEQUENCE_HEADER = 1
    OBP_OBU_TEMPORAL_DELIMITER = 2
    OBP_OBU_FRAME_HEADER = 3
    OBP_OBU_TILE_GROUP = 4
    OBP_OBU_METADATA = 5
    OBP_OBU_FRAME = 6
    OBP_OBU_REDUNDANT_FRAME_HEADER = 7
    OBP_OBU_TILE_LIST = 8
    OBP_OBU_PADDING = 15

class OBPMetadataType(enum.IntEnum):
    OBP_METADATA_TYPE_HDR_CLL = 1
    OBP_METADATA_TYPE_HDR_MDCV = 2
    OBP_METADATA_TYPE_SCALABILITY = 3
    OBP_METADATA_TYPE_ITUT_T35 = 4
    OBP_METADATA_TYPE_TIMECODE = 5
    # Values 6-31 are for unregistered user private metadata as per AV1 spec.
    # Value 32 and greater are reserved for AOM use.
    # No specific OBP_METADATA_TYPE_UNREGISTERED in C enum, so omitting for direct mapping.

class OBPColorPrimaries(enum.IntEnum):
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

class OBPTransferCharacteristics(enum.IntEnum):
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

class OBPMatrixCoefficients(enum.IntEnum):
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

class OBPChromaSamplePosition(enum.IntEnum):
    OBP_CSP_UNKNOWN = 0
    OBP_CSP_VERTICAL = 1
    OBP_CSP_COLOCATED = 2
    # OBP_CSP_RESERVED = 3 (from C comments, not adding to enum unless used)

class OBPFrameType(enum.IntEnum):
    OBP_KEY_FRAME = 0
    OBP_INTER_FRAME = 1
    OBP_INTRA_ONLY_FRAME = 2
    OBP_SWITCH_FRAME = 3

# --- Nested C Structs ---
class OBPTimingInfo(ctypes.Structure):
    _fields_ = [
        ("num_units_in_display_tick", c_uint32_t),
        ("time_scale", c_uint32_t),
        ("equal_picture_interval", c_int_t), # Changed from c_uint8_t to c_int_t
        ("num_ticks_per_picture_minus_1", c_uint32_t),
    ]

class OBPDecoderModelInfo(ctypes.Structure):
    _fields_ = [
        ("buffer_delay_length_minus_1", c_uint8_t),
        ("num_units_in_decoding_tick", c_uint32_t),
        ("buffer_removal_time_length_minus_1", c_uint8_t),
        ("frame_presentation_time_length_minus_1", c_uint8_t),
    ]

class OBPOperatingParametersInfo(ctypes.Structure):
    _fields_ = [
        ("decoder_buffer_delay", c_uint64_t), # Changed from c_uint32_t
        ("encoder_buffer_delay", c_uint64_t), # Changed from c_uint32_t
        ("low_delay_mode_flag", c_int_t),    # Changed from c_uint8_t
    ]

class OBPColorConfig(ctypes.Structure):
    _fields_ = [
        ("high_bitdepth", c_int_t),
        ("twelve_bit", c_int_t),
        ("BitDepth", c_uint8_t),
        ("mono_chrome", c_int_t),
        ("NumPlanes", c_uint8_t),
        ("color_description_present_flag", c_int_t),
        ("color_primaries", c_int_t), # Was OBPColorPrimaries enum
        ("transfer_characteristics", c_int_t), # Was OBPTransferCharacteristics enum
        ("matrix_coefficients", c_int_t),    # Was OBPMatrixCoefficients enum
        ("color_range", c_int_t),
        ("subsampling_x", c_int_t),
        ("subsampling_y", c_int_t),
        ("chroma_sample_position", c_int_t), # Was OBPChromaSamplePosition enum
        ("separate_uv_delta_q", c_int_t),
    ]

class OBPSuperresParams(ctypes.Structure):
    _fields_ = [
        ("use_superres", c_uint8_t), 
        ("coded_denom", c_uint8_t), 
        ("superres_upscaled_width", c_uint16_t),
        ("superres_upscaled_height", c_uint16_t),
    ]

class OBPInterpolationFilter(ctypes.Structure): 
    _fields_ = [("value", c_uint8_t)]

class OBPTileInfo(ctypes.Structure):
    _fields_ = [
        ("uniform_tile_spacing_flag", c_uint8_t), 
        ("MiColStarts", c_uint32_t * 65), 
        ("MiRowStarts", c_uint32_t * 65), 
        ("width_in_sbs_minus_1", c_uint16_t * 64), 
        ("height_in_sbs_minus_1", c_uint16_t * 64), 
        ("context_update_tile_id", c_uint16_t), 
        ("tile_cols", c_uint8_t), 
        ("tile_rows", c_uint8_t), 
    ]

class OBPQuantizationParams(ctypes.Structure):
    _fields_ = [
        ("base_q_idx", c_uint8_t),
        ("DeltaQYDc", c_int8_t),
        ("DeltaQUDc", c_int8_t),
        ("DeltaQUAc", c_int8_t),
        ("DeltaQVDc", c_int8_t),
        ("DeltaQVAc", c_int8_t),
        ("diff_uv_delta", c_int_t), # Added field
        ("using_qmatrix", c_uint8_t), 
        ("qm_y", c_uint8_t), 
        ("qm_u", c_uint8_t), 
        ("qm_v", c_uint8_t), 
    ]

class OBPSegmentationParams(ctypes.Structure):
    _fields_ = [
        ("segmentation_enabled", c_uint8_t), 
        ("segmentation_update_map", c_uint8_t), 
        ("segmentation_temporal_update", c_uint8_t), 
        ("segmentation_update_data", c_uint8_t), 
        ("feature_enabled", (c_uint8_t * 8) * 4), 
        ("feature_data", (c_int16_t * 8) * 4), 
    ]

class OBPDeltaQParams(ctypes.Structure):
    _fields_ = [
        ("delta_q_present", c_uint8_t), 
        ("delta_q_res", c_uint8_t), 
    ]

class OBPDeltaLFParams(ctypes.Structure):
    _fields_ = [
        ("delta_lf_present", c_uint8_t), 
        ("delta_lf_res", c_uint8_t), 
        ("delta_lf_multi", c_uint8_t), 
    ]

class OBPLoopFilterParams(ctypes.Structure):
    _fields_ = [
        ("loop_filter_level", c_uint8_t * 4), 
        ("loop_filter_sharpness", c_uint8_t), 
        ("loop_filter_delta_enabled", c_int_t), # Was c_uint8_t
        ("update_ref_delta", c_int_t * 8),      # Added field
        ("loop_filter_ref_deltas", c_int8_t * 8), 
        ("update_mode_delta", c_int_t * 2),     # Added field
        ("loop_filter_mode_deltas", c_int8_t * 2),
    ]

class OBPCdefParams(ctypes.Structure):
    _fields_ = [
        ("cdef_damping_minus_3", c_uint8_t), 
        ("cdef_bits", c_uint8_t), 
        ("cdef_y_pri_strength", c_uint8_t * 8), 
        ("cdef_y_sec_strength", c_uint8_t * 8), 
        ("cdef_uv_pri_strength", c_uint8_t * 8), 
        ("cdef_uv_sec_strength", c_uint8_t * 8), 
    ]

class OBPLrParams(ctypes.Structure):
    _fields_ = [
        ("lr_type", c_uint8_t * 3), 
        ("lr_unit_shift", c_uint8_t), 
        ("lr_uv_shift", c_uint8_t), 
    ]

class OBPGlobalMotionParams(ctypes.Structure): # Represents one set of GM params
    _fields_ = [
        ("gm_type", c_uint8_t), # Was c_uint8_t * 8
        ("gm_params", c_int32_t * 6), # Was (c_int32_t * 8) * 6
    ]

class OBPTileListEntry(ctypes.Structure):
    _fields_ = [
        ("anchor_frame_idx", c_uint8_t),
        ("anchor_tile_row", c_uint8_t),
        ("anchor_tile_col", c_uint8_t),
        ("tile_data_size_minus_1", c_uint16_t),
        ("tile_specific_data", ctypes.POINTER(c_uint8_t)),
    ]

class OBPMetadataITUTT35(ctypes.Structure):
    _fields_ = [
        ("itu_t_t35_country_code", c_uint8_t),
        ("itu_t_t35_country_code_extension_byte", c_uint8_t), # Added
        # ("itu_t_t35_terminal_provider_code", c_uint16_t), # Removed
        # ("itu_t_t35_terminal_provider_oriented_code", c_uint16_t), # Removed
        ("itu_t_t35_payload_bytes_size", c_size_t), # Renamed from itu_t_t35_payload_byte_count
        ("itu_t_t35_payload_bytes", ctypes.POINTER(c_uint8_t)),
    ]

class OBPMetadataHDRCLL(ctypes.Structure):
    _fields_ = [("max_cll", c_uint16_t), ("max_fall", c_uint16_t)]

class OBPMetadataHDRMDCV(ctypes.Structure):
    _fields_ = [
        ("primary_chromaticity_x", c_uint16_t * 3),
        ("primary_chromaticity_y", c_uint16_t * 3),
        ("white_point_chromaticity_x", c_uint16_t),
        ("white_point_chromaticity_y", c_uint16_t),
        ("luminance_max", c_uint32_t),
        ("luminance_min", c_uint32_t),
    ]

class OBPScalabilityStructure(ctypes.Structure):
    _fields_ = [
        ("spatial_layers_cnt_minus_1", c_uint8_t),
        ("spatial_layer_dimensions_present_flag", c_uint8_t),
        ("spatial_layer_description_present_flag", c_uint8_t),
        ("temporal_group_description_present_flag", c_uint8_t),
        ("scalability_structure_reserved_3bits", c_uint8_t),
    ]

class OBPMetadataScalability(ctypes.Structure):
    _fields_ = [
        ("scalability_mode_idc", c_uint8_t),
        ("scalability_structure", OBPScalabilityStructure),
    ]

class OBPMetadataTimecode(ctypes.Structure):
    _fields_ = [
        ("counting_type", c_uint8_t), 
        ("full_timestamp_flag", c_uint8_t),
        ("discontinuity_flag", c_uint8_t), 
        ("cnt_dropped_flag", c_uint8_t),
        ("n_frames", c_uint16_t), # Was c_uint8_t
        ("seconds_value", c_uint8_t),
        ("minutes_value", c_uint8_t), 
        ("hours_value", c_uint8_t),
        ("seconds_flag", c_uint8_t), 
        ("minutes_flag", c_uint8_t),
        ("hours_flag", c_uint8_t), 
        ("time_offset_length", c_uint8_t),
        ("time_offset_value", c_uint32_t), # Was c_int32_t
    ]

class OBPMetadataUnregistered(ctypes.Structure):
    _fields_ = [
        ("buf", ctypes.POINTER(c_uint8_t)), # Was uuid, payload_byte_count, payload
        ("buf_size", c_size_t),             # Was uuid, payload_byte_count, payload
    ]

# --- Main C Structs ---
class OBPFilmGrainParameters(ctypes.Structure):
    _fields_ = [
        ("apply_grain", c_uint8_t), ("grain_seed", c_uint16_t),
        ("update_grain", c_uint8_t), ("film_grain_params_ref_idx", c_uint8_t),
        ("num_y_points", c_uint8_t), ("point_y_value", c_uint8_t * 14),
        ("point_y_scaling", c_uint8_t * 14), ("chroma_scaling_from_luma", c_uint8_t),
        ("num_cb_points", c_uint8_t), ("point_cb_value", c_uint8_t * 10),
        ("point_cb_scaling", c_uint8_t * 10), ("num_cr_points", c_uint8_t),
        ("point_cr_value", c_uint8_t * 10), ("point_cr_scaling", c_uint8_t * 10),
        ("grain_scaling_minus_8", c_uint8_t), ("ar_coeff_lag", c_uint8_t),
        ("ar_coeffs_y_plus_128", c_uint8_t * 24), ("ar_coeffs_cb_plus_128", c_uint8_t * 25),
        ("ar_coeffs_cr_plus_128", c_uint8_t * 25), ("ar_coeff_shift_minus_6", c_uint8_t),
        ("grain_scale_shift", c_uint8_t), ("cb_mult", c_uint8_t),
        ("cb_luma_mult", c_uint8_t), ("cb_offset", c_uint16_t),
        ("cr_mult", c_uint8_t), ("cr_luma_mult", c_uint8_t),
        ("cr_offset", c_uint16_t), ("overlap_flag", c_uint8_t),
        ("clip_to_restricted_range", c_uint8_t),
    ]

class OBPSequenceHeader(ctypes.Structure):
    _fields_ = [
        ("seq_profile", c_uint8_t), 
        ("still_picture", c_int_t), # Was c_uint8_t
        ("reduced_still_picture_header", c_int_t), # Was c_uint8_t
        ("timing_info_present_flag", c_int_t), # Was c_uint8_t
        ("timing_info", OBPTimingInfo), 
        ("decoder_model_info_present_flag", c_int_t), # Was c_uint8_t
        ("decoder_model_info", OBPDecoderModelInfo), 
        ("initial_display_delay_present_flag", c_int_t), # Was c_uint8_t
        ("operating_points_cnt_minus_1", c_uint8_t), 
        ("operating_point_idc", c_uint8_t * 32), # Was c_uint16_t * 32
        ("seq_level_idx", c_uint8_t * 32), 
        ("seq_tier", c_uint8_t * 32),
        ("decoder_model_present_for_this_op", c_int_t * 32), # Was c_uint8_t * 32
        ("initial_display_delay_present_for_this_op", c_int_t * 32), # Was c_uint8_t * 32
        ("operating_parameters_info", OBPOperatingParametersInfo * 32),
        ("initial_display_delay_minus_1", c_uint8_t * 32), 
        ("frame_width_bits_minus_1", c_uint8_t),
        ("frame_height_bits_minus_1", c_uint8_t), 
        ("max_frame_width_minus_1", c_uint32_t),
        ("max_frame_height_minus_1", c_uint32_t), 
        ("frame_id_numbers_present_flag", c_int_t), # Was c_uint8_t
        ("delta_frame_id_length_minus_2", c_uint8_t), 
        ("additional_frame_id_length_minus_1", c_uint8_t),
        ("use_128x128_superblock", c_int_t), # Was c_uint8_t
        ("enable_filter_intra", c_int_t), # Was c_uint8_t
        ("enable_intra_edge_filter", c_int_t), # Was c_uint8_t
        ("enable_interintra_compound", c_int_t), # Was c_uint8_t
        ("enable_masked_compound", c_int_t), # Was c_uint8_t
        ("enable_warped_motion", c_int_t), # Was c_uint8_t
        ("enable_dual_filter", c_int_t), # Was c_uint8_t
        ("enable_order_hint", c_int_t), # Was c_uint8_t
        ("enable_jnt_comp", c_int_t), # Was c_uint8_t
        ("enable_ref_frame_mvs", c_int_t), # Was c_uint8_t
        ("seq_choose_screen_content_tools", c_int_t), # Was c_uint8_t - C: int, but spec says syntax_element_is_bool
        ("seq_force_screen_content_tools", c_int_t), # Was c_uint8_t - C: int, but spec says syntax_element_is_bool
        ("seq_choose_integer_mv", c_int_t), # Was c_uint8_t - C: int, but spec says syntax_element_is_bool
        ("seq_force_integer_mv", c_int_t), # Was c_uint8_t - C: int, but spec says syntax_element_is_bool
        ("order_hint_bits_minus_1", c_uint8_t), 
        ("enable_superres", c_int_t), # Was c_uint8_t
        ("enable_cdef", c_int_t), # Was c_uint8_t
        ("enable_restoration", c_int_t), # Was c_uint8_t
        ("color_config", OBPColorConfig), 
        ("film_grain_params_present", c_int_t), # Was c_uint8_t
        ("FrameWidth", c_uint32_t), 
        ("FrameHeight", c_uint32_t), 
        ("OrderHintBits", c_uint8_t),
    ]

class OBPFrameHeader(ctypes.Structure):
    _fields_ = [
        ("show_existing_frame", c_int_t), # Was c_uint8_t
        ("frame_to_show_map_idx", c_uint8_t), # Matches C uint8_t
        ("temporal_point_info_present", c_uint8_t), # Matches derived/internal flag logic
        ("frame_presentation_time", c_uint32_t), 
        ("display_frame_id", c_uint32_t),
        ("frame_type", c_int_t), # Was OBPFrameType enum
        ("show_frame", c_int_t), 
        ("showable_frame", c_int_t), 
        ("error_resilient_mode", c_int_t), 
        ("disable_cdf_update", c_int_t), # Was c_uint8_t
        ("allow_screen_content_tools", c_int_t), # Was c_uint8_t
        ("force_integer_mv", c_int_t), # Was c_uint8_t
        ("current_frame_id", c_uint32_t), 
        ("frame_size_override_flag", c_int_t), # Was c_uint8_t
        ("order_hint", c_uint8_t), # Was c_uint32_t
        ("primary_ref_frame", c_uint8_t),
        ("buffer_removal_time_present_flag", c_int_t), # Added field (from C int)
        ("buffer_removal_time", c_uint32_t * 32),    # Added field
        ("refresh_frame_flags", c_uint8_t), 
        ("ref_order_hint", c_uint8_t * 8), # Was c_uint32_t * 8
        # Frame size and superres params
        ("frame_width_minus_1", c_uint32_t),
        ("frame_height_minus_1", c_uint32_t), 
        ("superres_params", OBPSuperresParams),
        ("render_and_frame_size_different", c_int_t), # Added field
        ("render_width_minus_1", c_uint16_t), # C: uint16_t
        ("render_height_minus_1", c_uint16_t),# C: uint16_t
        ("RenderWidth", c_uint32_t), # Derived in C
        ("RenderHeight", c_uint32_t),# Derived in C
        # Reference frame signaling
        ("allow_intrabc", c_int_t), # Was c_uint8_t (moved for logical grouping)
        ("frame_refs_short_signaling", c_int_t), # Added field
        ("last_frame_idx", c_uint8_t),          # Added field
        ("gold_frame_idx", c_uint8_t),          # Added field
        ("ref_frame_idx", c_uint8_t * 7),       # Added field
        ("delta_frame_id_minus_1", c_uint8_t * 7), # Added field
        ("found_ref", c_int_t),                 # Added field
        # Motion vector and interpolation
        ("allow_high_precision_mv", c_int_t), # Was c_uint8_t
        ("interpolation_filter", OBPInterpolationFilter),
        ("is_motion_mode_switchable", c_int_t), # Was c_uint8_t
        ("use_ref_frame_mvs", c_int_t), # Was c_uint8_t
        ("disable_frame_end_update_cdf", c_int_t), # Was c_uint8_t
        # Tile info (OBPTileInfo in wrapper is different from C's OBPFrameHeader.tile_info)
        # The C parser populates fh->TileCols, fh->TileRows, etc. These are captured in OBPTileInfo wrapper struct.
        ("tile_info", OBPTileInfo), 
        # Quantization, Segmentation, Loop Filter, CDEF, LR params
        ("quantization_params", OBPQuantizationParams),
        ("segmentation_params", OBPSegmentationParams), 
        ("delta_q_params", OBPDeltaQParams), # Contains delta_q_present (int), delta_q_res (uint8_t)
        ("delta_lf_params", OBPDeltaLFParams),# Contains delta_lf_present (int), delta_lf_res (uint8_t), delta_lf_multi (int)
        ("loop_filter_params", OBPLoopFilterParams),
        ("cdef_params", OBPCdefParams),
        ("lr_params", OBPLrParams),
        # Misc flags
        ("tx_mode_select", c_int_t), # Added field (from C int) - wrapper had palette_mode_enabled here, which is not in C OBPFrameHeader
        ("skip_mode_present", c_int_t), # Was c_uint8_t
        ("reference_select", c_int_t),  # Was c_uint8_t
        ("allow_warped_motion", c_int_t), # Was c_uint8_t
        ("reduced_tx_set", c_int_t), # Was c_uint8_t
        # Global motion, film grain
        ("global_motion_params", OBPGlobalMotionParams * 8), 
        ("film_grain_params", OBPFilmGrainParameters), 
        # Derived/internal state populated by parser
        ("MiCols", c_uint32_t), # Matches C derived
        ("MiRows", c_uint32_t), # Matches C derived
        ("large_scale_tile", c_uint8_t), # This was from an older version of wrapper, C has no large_scale_tile in OBPFrameHeader
                                         # but it's used in parser.py. Let's assume it's a helper/derived field for now.
                                         # C header has no such field. obuparse.c also doesn't seem to set it in OBPFrameHeader.
                                         # Removing for now to match C header strictly. If parser.py needs it, it should be handled there.
        # ("large_scale_tile", c_uint8_t),
    ]

class OBPTileGroup(ctypes.Structure):
    _fields_ = [
        ("NumTiles", c_uint16_t), ("obu_size", c_size_t),
        ("data", ctypes.POINTER(c_uint8_t)), ("tg_start", c_uint16_t),
        ("tg_end", c_uint16_t), ("obu_data_offset_within_tile_group_obu", c_size_t),
    ]

class OBPTileList(ctypes.Structure):
    _fields_ = [
        ("output_frame_width_in_tiles_minus_1", c_uint8_t), # Renamed
        ("output_frame_height_in_tiles_minus_1", c_uint8_t),# Renamed
        ("tile_count_minus_1", c_uint16_t),
        ("tile_list_entries", ctypes.POINTER(OBPTileListEntry)),
    ]

class OBPMetadata(ctypes.Structure):
    _fields_ = [
        ("metadata_type", c_int_t), # Was OBPMetadataType enum
        ("metadata_itut_t35", OBPMetadataITUTT35),
        ("metadata_hdr_cll", OBPMetadataHDRCLL), 
        ("metadata_hdr_mdcv", OBPMetadataHDRMDCV),
        ("metadata_scalability", OBPMetadataScalability), 
        ("metadata_timecode", OBPMetadataTimecode),
        ("unregistered", OBPMetadataUnregistered), 
        # Removed obu_size and data, not part of C struct OBPMetadata
    ]

class OBPState(ctypes.Structure):
    pass # Forward declaration for OBPFrameHeader if it were to reference OBPState

# Define OBPState fields after all other necessary structs are defined
OBPState._fields_ = [
    ("prev", OBPFrameHeader), 
    ("prev_filled", c_int_t),
    ("frame_header_end_pos", c_size_t),
    ("RefFrameType", c_int_t * 8), # Was OBPFrameType * 8
    ("RefValid", c_uint8_t * 8),
    ("RefOrderHint", c_uint8_t * 8),
    ("OrderHint", c_uint8_t * 8), 
    ("RefFrameId", c_uint8_t * 8),
    ("RefUpscaledWidth", c_uint32_t * 8),
    ("RefFrameHeight", c_uint32_t * 8),
    ("RefRenderWidth", c_uint32_t * 8),
    ("RefRenderHeight", c_uint32_t * 8),
    ("RefFrameSignBias", c_int32_t * 8),
    ("RefGrainParams", OBPFilmGrainParameters * 8),
    ("order_hint", c_uint8_t), # Current frame's order_hint
    # Corrected 3D array definitions for Saved* fields
    ("SavedGmParams", ((c_uint32_t * 6) * 8) * 8), # [8][8][6]
    ("SavedFeatureEnabled", ((c_int_t * 8) * 8) * 8),    # [8][8][8]
    ("SavedFeatureData", ((c_int16_t * 8) * 8) * 8),   # [8][8][8]
    ("SavedLoopFilterRefDeltas", ((c_int8_t * 8) * 8)), # [8][8]
    ("SavedLoopFilterModeDeltas", ((c_int8_t * 8) * 8)),# [8][8]
]

# --- Function Signatures ---
if _lib:
    _lib.obp_get_next_obu.argtypes = [
        ctypes.POINTER(c_uint8_t),    
        c_size_t,                     
        ctypes.POINTER(c_int_t),      
        ctypes.POINTER(c_ssize_t),    
        ctypes.POINTER(c_size_t),     
        ctypes.POINTER(c_int_t),      
        ctypes.POINTER(c_int_t),      
        ctypes.POINTER(c_int_t),      
        ctypes.POINTER(OBPError)      
    ]
    _lib.obp_get_next_obu.restype = c_int_t

    _lib.obp_parse_sequence_header.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPSequenceHeader), ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_sequence_header.restype = c_int_t

    _lib.obp_parse_frame_header.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPSequenceHeader), ctypes.POINTER(OBPState),
        c_int_t, c_int_t, ctypes.POINTER(OBPFrameHeader),
        ctypes.POINTER(c_int_t), ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_frame_header.restype = c_int_t

    _lib.obp_parse_frame.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPSequenceHeader), ctypes.POINTER(OBPState),
        c_int_t, c_int_t, ctypes.POINTER(OBPFrameHeader),
        ctypes.POINTER(OBPTileGroup), ctypes.POINTER(c_int_t),
        ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_frame.restype = c_int_t
    
    _lib.obp_parse_tile_group.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPFrameHeader), ctypes.POINTER(OBPTileGroup),
        ctypes.POINTER(c_int_t), ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_tile_group.restype = c_int_t

    _lib.obp_parse_metadata.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPMetadata), ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_metadata.restype = c_int_t

    _lib.obp_parse_tile_list.argtypes = [
        ctypes.POINTER(c_uint8_t), c_size_t,
        ctypes.POINTER(OBPTileList), ctypes.POINTER(OBPError)
    ]
    _lib.obp_parse_tile_list.restype = c_int_t
    
    if hasattr(_lib, "obp_state_init"):
        _lib.obp_state_init.argtypes = [ctypes.POINTER(OBPState)]
        _lib.obp_state_init.restype = None

    if hasattr(_lib, "obp_free_error_string"):
        _lib.obp_free_error_string.argtypes = [c_char_p]
        _lib.obp_free_error_string.restype = None
else:
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
    "OBPOBUType", "OBPMetadataType", "OBPColorPrimaries", "OBPTransferCharacteristics",
    "OBPMatrixCoefficients", "OBPChromaSamplePosition", "OBPFrameType",
    "c_int_t", "c_uint8_t", "c_uint16_t", "c_uint32_t", "c_uint64_t", # Keep basic C type aliases
    "c_int8_t", "c_int16_t", "c_int32_t", "c_int64_t", # Keep basic C type aliases
    "c_size_t", "c_ssize_t", "c_ptrdiff_t", "c_char_p", "c_bool", # Keep basic C type aliases
    "OBPTimingInfo", "OBPDecoderModelInfo", "OBPOperatingParametersInfo", "OBPColorConfig", # Structs
    "OBPSuperresParams", "OBPInterpolationFilter", "OBPTileInfo", "OBPQuantizationParams", # Structs
    "OBPSegmentationParams", "OBPDeltaQParams", "OBPDeltaLFParams", "OBPLoopFilterParams", # Structs
    "OBPCdefParams", "OBPLrParams", "OBPGlobalMotionParams", "OBPTileListEntry", # Structs
    "OBPMetadataITUTT35", "OBPMetadataHDRCLL", "OBPMetadataHDRMDCV", # Structs
    "OBPScalabilityStructure", "OBPMetadataScalability", "OBPMetadataTimecode", "OBPMetadataUnregistered", # Structs
    "OBPFilmGrainParameters", "OBPSequenceHeader", "OBPFrameHeader", "OBPTileGroup", # Structs
    "OBPTileList", "OBPMetadata", "OBPState", # Structs
    "obp_get_next_obu", "obp_parse_sequence_header", "obp_parse_frame_header", # Functions
    "obp_parse_frame", "obp_parse_tile_group", "obp_parse_metadata", "obp_parse_tile_list", # Functions
    "obp_state_init", # Functions
]
