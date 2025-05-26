import ctypes
from typing import Sequence, Tuple, Any # Added Sequence, Tuple, Any
from . import _c_wrapper

# --- Custom Exception ---
class OBUParseError(Exception):
    """Custom exception for errors during OBU parsing."""
    pass

# --- Helper function to copy C array to Python list ---
def _c_array_to_list(c_array, length: int | None = None):
    if not c_array:
        return []
    if length is None: # If length is not provided, assume it's a_c_wrapper.null-terminated array (not safe for all types)
        # This part is tricky and depends on array type. For now, require length for non-char pointers.
        # For ctypes arrays with _length_ attribute (fixed size arrays in structs)
        if hasattr(c_array, '_length_'):
             return [c_array[i] for i in range(getattr(c_array, '_length_'))]
        raise ValueError("Length must be provided for C arrays not part of a structure field with _length_")
    return [c_array[i] for i in range(length)]

# --- Helper Python classes for SequenceHeader nested structures ---

class TimingInfo: # Corresponds to _c_wrapper.OBPTimingInfo
    def __init__(self, c_timing_info: _c_wrapper.OBPTimingInfo):
        self.num_units_in_display_tick: int = c_timing_info.num_units_in_display_tick
        self.time_scale: int = c_timing_info.time_scale
        self.equal_picture_interval: int = c_timing_info.equal_picture_interval # C type is int
        self.num_ticks_per_picture_minus_1: int = c_timing_info.num_ticks_per_picture_minus_1

    def __repr__(self) -> str:
        return (
            f"TimingInfo(num_units_in_display_tick={self.num_units_in_display_tick}, "
            f"time_scale={self.time_scale}, equal_picture_interval={self.equal_picture_interval}, "
            f"num_ticks_per_picture_minus_1={self.num_ticks_per_picture_minus_1})"
        )

class DecoderModelInfo: # Corresponds to _c_wrapper.OBPDecoderModelInfo
    def __init__(self, c_decoder_model_info: _c_wrapper.OBPDecoderModelInfo):
        self.buffer_delay_length_minus_1: int = c_decoder_model_info.buffer_delay_length_minus_1
        self.num_units_in_decoding_tick: int = c_decoder_model_info.num_units_in_decoding_tick
        self.buffer_removal_time_length_minus_1: int = c_decoder_model_info.buffer_removal_time_length_minus_1
        self.frame_presentation_time_length_minus_1: int = c_decoder_model_info.frame_presentation_time_length_minus_1

    def __repr__(self) -> str:
        return (
            f"DecoderModelInfo(buffer_delay_length_minus_1={self.buffer_delay_length_minus_1}, "
            f"num_units_in_decoding_tick={self.num_units_in_decoding_tick}, "
            f"buffer_removal_time_length_minus_1={self.buffer_removal_time_length_minus_1}, "
            f"frame_presentation_time_length_minus_1={self.frame_presentation_time_length_minus_1})"
        )

class OperatingParametersInfo: # Corresponds to _c_wrapper.OBPOperatingParametersInfo
    def __init__(self, c_op_info: _c_wrapper.OBPOperatingParametersInfo):
        self.decoder_buffer_delay: int = c_op_info.decoder_buffer_delay # C type is uint64_t
        self.encoder_buffer_delay: int = c_op_info.encoder_buffer_delay # C type is uint64_t
        self.low_delay_mode_flag: int = c_op_info.low_delay_mode_flag   # C type is int

    def __repr__(self) -> str:
        return (
            f"OperatingParametersInfo(decoder_buffer_delay={self.decoder_buffer_delay}, "
            f"encoder_buffer_delay={self.encoder_buffer_delay}, low_delay_mode_flag={self.low_delay_mode_flag})"
        )

class ColorConfig: # Corresponds to _c_wrapper.OBPColorConfig
    def __init__(self, c_color_config: _c_wrapper.OBPColorConfig):
        self.high_bitdepth: int = c_color_config.high_bitdepth # C type is int
        self.twelve_bit: int = c_color_config.twelve_bit     # C type is int
        self.BitDepth: int = c_color_config.BitDepth # Added, C type is uint8_t
        self.mono_chrome: int = c_color_config.mono_chrome   # C type is int
        self.NumPlanes: int = c_color_config.NumPlanes # Added, C type is uint8_t
        self.color_description_present_flag: int = c_color_config.color_description_present_flag # C type is int
        self.color_primaries: int = c_color_config.color_primaries # Enum OBPColorPrimaries
        self.transfer_characteristics: int = c_color_config.transfer_characteristics # Enum OBPTransferCharacteristics
        self.matrix_coefficients: int = c_color_config.matrix_coefficients # Enum OBPMatrixCoefficients
        self.color_range: int = c_color_config.color_range # C type is int
        self.subsampling_x: int = c_color_config.subsampling_x # Added, C type is int
        self.subsampling_y: int = c_color_config.subsampling_y # Added, C type is int
        self.chroma_sample_position: int = c_color_config.chroma_sample_position # Enum OBPChromaSamplePosition
        self.separate_uv_delta_q: int = c_color_config.separate_uv_delta_q # C type is int


    def __repr__(self) -> str:
        return (
            f"ColorConfig(BitDepth={self.BitDepth}, NumPlanes={self.NumPlanes}, "
            f"color_primaries={self.color_primaries}, transfer_characteristics={self.transfer_characteristics}, "
            f"matrix_coefficients={self.matrix_coefficients}, color_range={self.color_range}, "
            f"chroma_sample_position={self.chroma_sample_position}, ...)"
        )

# --- Helper Python classes for FrameHeader nested structures ---

class SuperresParams: # Corresponds to _c_wrapper.OBPSuperresParams
    def __init__(self, c_params: _c_wrapper.OBPSuperresParams):
        self.use_superres: int = c_params.use_superres # C type is int
        self.coded_denom: int = c_params.coded_denom # C type is uint8_t
        # The C struct in obuparse.h does not have superres_upscaled_width/height directly.
        # These were in the original Python wrapper but might be calculated elsewhere or were from an older version.
        # For now, matching obuparse.h, these are removed from direct mapping.
        # self.superres_upscaled_width: int = c_params.superres_upscaled_width
        # self.superres_upscaled_height: int = c_params.superres_upscaled_height
    def __repr__(self) -> str:
        # return f"SuperresParams(use_superres={self.use_superres}, coded_denom={self.coded_denom}, upscaled_width={self.superres_upscaled_width}, upscaled_height={self.superres_upscaled_height})"
        return f"SuperresParams(use_superres={self.use_superres}, coded_denom={self.coded_denom})"


class InterpolationFilter: # Corresponds to _c_wrapper.OBPInterpolationFilter
    def __init__(self, c_filter: _c_wrapper.OBPInterpolationFilter):
        # _c_wrapper.OBPInterpolationFilter has is_filter_switchable (int) and interpolation_filter (uint8_t)
        self.is_filter_switchable: int = c_filter.is_filter_switchable
        self.interpolation_filter: int = c_filter.interpolation_filter
    def __repr__(self) -> str:
        return f"InterpolationFilter(is_switchable={self.is_filter_switchable}, filter={self.interpolation_filter})"

class TileInfo: # Corresponds to _c_wrapper.OBPTileInfo
    def __init__(self, c_info: _c_wrapper.OBPTileInfo):
        self.uniform_tile_spacing_flag: int = c_info.uniform_tile_spacing_flag # C type is int
        # MiColStarts, MiRowStarts, width_in_sbs_minus_1, height_in_sbs_minus_1 are not in C struct definition
        # They are calculated by the library if needed, but not part of the core struct.
        # self.MiColStarts: list[int] = _c_array_to_list(c_info.MiColStarts)
        # self.MiRowStarts: list[int] = _c_array_to_list(c_info.MiRowStarts)
        # self.width_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.width_in_sbs_minus_1)
        # self.height_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.height_in_sbs_minus_1)
        self.TileRows: int = c_info.TileRows # C type is uint16_t
        self.TileCols: int = c_info.TileCols # C type is uint16_t
        self.context_update_tile_id: int = c_info.context_update_tile_id # C type is uint32_t
        self.tile_size_bytes_minus_1: int = c_info.tile_size_bytes_minus_1 # C type is uint8_t
    def __repr__(self) -> str:
        return f"TileInfo(TileCols={self.TileCols}, TileRows={self.TileRows}, uniform_spacing={self.uniform_tile_spacing_flag}, context_update_tile_id={self.context_update_tile_id}, tile_size_bytes_minus_1={self.tile_size_bytes_minus_1})"

class QuantizationParams: # Corresponds to _c_wrapper.OBPQuantizationParams
    def __init__(self, c_params: _c_wrapper.OBPQuantizationParams):
        self.base_q_idx: int = c_params.base_q_idx
        self.diff_uv_delta: int = c_params.diff_uv_delta # Added, C type is int
        # DeltaQYDc, DeltaQUDc, etc. are not in the C struct.
        # self.DeltaQYDc: int = c_params.DeltaQYDc
        # self.DeltaQUDc: int = c_params.DeltaQUDc
        # self.DeltaQUAc: int = c_params.DeltaQUAc
        # self.DeltaQVDc: int = c_params.DeltaQVDc
        # self.DeltaQVAc: int = c_params.DeltaQVAc
        self.using_qmatrix: int = c_params.using_qmatrix # C type is int
        self.qm_y: int = c_params.qm_y
        self.qm_u: int = c_params.qm_u
        self.qm_v: int = c_params.qm_v
    def __repr__(self) -> str:
        return f"QuantizationParams(base_q_idx={self.base_q_idx}, diff_uv_delta={self.diff_uv_delta}, using_qmatrix={self.using_qmatrix}, qm_y={self.qm_y}, qm_u={self.qm_u}, qm_v={self.qm_v})"

class SegmentationParams: # Corresponds to _c_wrapper.OBPSegmentationParams
    def __init__(self, c_params: _c_wrapper.OBPSegmentationParams):
        self.segmentation_enabled: int = c_params.segmentation_enabled # C type is int
        self.segmentation_update_map: int = c_params.segmentation_update_map # C type is int
        self.segmentation_temporal_update: int = c_params.segmentation_temporal_update # C type is int
        self.segmentation_update_data: int = c_params.segmentation_update_data # C type is int
        # C: feature_enabled[8][8], feature_data[8][8]
        self.feature_enabled: list[list[int]] = [_c_array_to_list(c_params.feature_enabled[i]) for i in range(8)] 
        self.feature_data: list[list[int]] = [_c_array_to_list(c_params.feature_data[i]) for i in range(8)]
    def __repr__(self) -> str:
        return f"SegmentationParams(enabled={self.segmentation_enabled}, update_map={self.segmentation_update_map}, temporal_update={self.segmentation_temporal_update}, update_data={self.segmentation_update_data}, ...)"

class DeltaQParams: # Corresponds to _c_wrapper.OBPDeltaQParams
    def __init__(self, c_params: _c_wrapper.OBPDeltaQParams):
        self.delta_q_present: int = c_params.delta_q_present # C type is int
        self.delta_q_res: int = c_params.delta_q_res
    def __repr__(self) -> str:
        return f"DeltaQParams(present={self.delta_q_present}, res={self.delta_q_res})"

class DeltaLFParams: # Corresponds to _c_wrapper.OBPDeltaLFParams
    def __init__(self, c_params: _c_wrapper.OBPDeltaLFParams):
        self.delta_lf_present: int = c_params.delta_lf_present # C type is int
        self.delta_lf_res: int = c_params.delta_lf_res
        self.delta_lf_multi: int = c_params.delta_lf_multi     # C type is int
    def __repr__(self) -> str:
        return f"DeltaLFParams(present={self.delta_lf_present}, res={self.delta_lf_res}, multi={self.delta_lf_multi})"

class LoopFilterParams: # Corresponds to _c_wrapper.OBPLoopFilterParams
    def __init__(self, c_params: _c_wrapper.OBPLoopFilterParams):
        self.loop_filter_level: list[int] = _c_array_to_list(c_params.loop_filter_level)
        self.loop_filter_sharpness: int = c_params.loop_filter_sharpness
        self.loop_filter_delta_enabled: int = c_params.loop_filter_delta_enabled # C type is int
        self.update_ref_delta: list[int] = _c_array_to_list(c_params.update_ref_delta) # Added, C type is int[8]
        self.loop_filter_ref_deltas: list[int] = _c_array_to_list(c_params.loop_filter_ref_deltas)
        self.update_mode_delta: list[int] = _c_array_to_list(c_params.update_mode_delta) # Added, C type is int[8]
        self.loop_filter_mode_deltas: list[int] = _c_array_to_list(c_params.loop_filter_mode_deltas) # C type is int8_t[8]
    def __repr__(self) -> str:
        return (f"LoopFilterParams(levels={self.loop_filter_level}, sharpness={self.loop_filter_sharpness}, "
                f"delta_enabled={self.loop_filter_delta_enabled}, ref_deltas={self.loop_filter_ref_deltas}, "
                f"mode_deltas={self.loop_filter_mode_deltas}, ...)")

class CdefParams: # Corresponds to _c_wrapper.OBPCdefParams
    def __init__(self, c_params: _c_wrapper.OBPCdefParams):
        self.cdef_damping_minus_3: int = c_params.cdef_damping_minus_3
        self.cdef_bits: int = c_params.cdef_bits
        self.cdef_y_pri_strength: list[int] = _c_array_to_list(c_params.cdef_y_pri_strength)
        self.cdef_y_sec_strength: list[int] = _c_array_to_list(c_params.cdef_y_sec_strength)
        self.cdef_uv_pri_strength: list[int] = _c_array_to_list(c_params.cdef_uv_pri_strength)
        self.cdef_uv_sec_strength: list[int] = _c_array_to_list(c_params.cdef_uv_sec_strength)
    def __repr__(self) -> str:
        return f"CdefParams(damping={self.cdef_damping_minus_3+3}, bits={self.cdef_bits}, y_pri_str={self.cdef_y_pri_strength}, ...)"

class LrParams: # Corresponds to _c_wrapper.OBPLrParams
    def __init__(self, c_params: _c_wrapper.OBPLrParams):
        self.lr_type: list[int] = _c_array_to_list(c_params.lr_type)
        self.lr_unit_shift: int = c_params.lr_unit_shift
        self.lr_uv_shift: int = c_params.lr_uv_shift # C type is int
    def __repr__(self) -> str:
        return f"LrParams(type_y={self.lr_type[0]}, type_u={self.lr_type[1]}, type_v={self.lr_type[2]}, unit_shift={self.lr_unit_shift}, uv_shift={self.lr_uv_shift})"

class GlobalMotionParams: # Wrapper for one element of the global_motion_params array in OBPFrameHeader
    def __init__(self, c_gmp_struct: _c_wrapper.OBPGlobalMotionParams): # Takes the C struct
        self.gm_type: list[int] = list(c_gmp_struct.gm_type) # C: uint8_t gm_type[8]
        # C: int32_t gm_params[8][6] -> list of 8 lists, each 6 ints
        self.gm_params: list[list[int]] = [_c_array_to_list(row) for row in c_gmp_struct.gm_params]
        # C: uint32_t prev_gm_params[8][6] -> list of 8 lists, each 6 ints
        self.prev_gm_params: list[list[int]] = [_c_array_to_list(row) for row in c_gmp_struct.prev_gm_params]

    def __repr__(self) -> str:
        # Assuming gm_type[0] is the relevant type for a single reference frame's motion.
        # The C struct `global_motion_params` in OBPFrameHeader is an array of these, one per ref frame.
        # The `gm_type` array within `OBPGlobalMotionParams` might be a bit confusing if it implies multiple types
        # for a single reference's global motion. The C struct for OBPFrameHeader has `global_motion_params[REF_FRAMES]`,
        # and *inside that* is `gm_type[MAX_REF_FRAMES]` which seems redundant if the outer array is already for refs.
        # However, `obuparse.c` for `read_global_motion_params` uses `gm_type[ref]` and `gm_params[ref]`.
        # This means the OBPGlobalMotionParams struct from _c_wrapper is for *all* ref frames, not one.
        # The python FrameHeader class then takes one element of this array.
        # This leads to a slight mismatch in how GlobalMotionParams python class should be structured.
        # Let's assume the current loop in FrameHeader is correct:
        # `self.global_motion_params.append(GlobalMotionParams(gm_type_val, gm_params_for_ref_vals))`
        # This means the Python GlobalMotionParams class is for ONE ref frame's global motion.
        # The C struct `_c_wrapper.OBPGlobalMotionParams` holds ALL gm_type and gm_params for ALL refs.
        # This needs careful handling in FrameHeader.__init__
        # For now, let's assume this Python class represents ONE set of gm_type and gm_params
        # as it was in the original code. The init will be updated in FrameHeader.
        # This class will be for a *single reference frame's* motion parameters.
        # The `gm_type` field in the C struct `global_motion_params` of `OBPFrameHeader` is `uint8_t gm_type[8]`
        # The `gm_params` field is `int32_t gm_params[8][6]`
        # So, if this class represents *one* of these, it should be:
        # self.gm_type: int (a single type for this one ref frame)
        # self.gm_params: list[int] (a list of 6 params for this one ref frame)
        # This means FrameHeader's loop needs to extract the correct index.

        # Re-evaluating: The C struct `OBPGlobalMotionParams` in `_c_wrapper.py` is for ONE ref frame's group of params.
        # `OBPFrameHeader` has `("global_motion_params", OBPGlobalMotionParams * 8)`.
        # So, the `GlobalMotionParams` Python class should take one `_c_wrapper.OBPGlobalMotionParams` instance.
        self.gm_type_val: int = self.gm_type[0] # Assuming the relevant type is the first one for this ref
        return f"GlobalMotionParams(type={self.gm_type_val}, params_matrix_shape=({len(self.gm_params)}x{len(self.gm_params[0]) if self.gm_params else 0}))"


class FilmGrainParameters: # Corresponds to _c_wrapper.OBPFilmGrainParameters
    def __init__(self, c_params: _c_wrapper.OBPFilmGrainParameters):
        self.apply_grain: int = c_params.apply_grain # C type is int
        self.grain_seed: int = c_params.grain_seed
        self.update_grain: int = c_params.update_grain # C type is int
        self.film_grain_params_ref_idx: int = c_params.film_grain_params_ref_idx
        self.num_y_points: int = c_params.num_y_points
        self.point_y_value: list[int] = _c_array_to_list(c_params.point_y_value, self.num_y_points if self.num_y_points <= len(c_params.point_y_value) else len(c_params.point_y_value))
        self.point_y_scaling: list[int] = _c_array_to_list(c_params.point_y_scaling, self.num_y_points if self.num_y_points <= len(c_params.point_y_scaling) else len(c_params.point_y_scaling))
        self.chroma_scaling_from_luma: int = c_params.chroma_scaling_from_luma # C type is int
        self.num_cb_points: int = c_params.num_cb_points
        self.point_cb_value: list[int] = _c_array_to_list(c_params.point_cb_value, self.num_cb_points if self.num_cb_points <= len(c_params.point_cb_value) else len(c_params.point_cb_value))
        self.point_cb_scaling: list[int] = _c_array_to_list(c_params.point_cb_scaling, self.num_cb_points if self.num_cb_points <= len(c_params.point_cb_scaling) else len(c_params.point_cb_scaling))
        self.num_cr_points: int = c_params.num_cr_points
        self.point_cr_value: list[int] = _c_array_to_list(c_params.point_cr_value, self.num_cr_points if self.num_cr_points <= len(c_params.point_cr_value) else len(c_params.point_cr_value))
        self.point_cr_scaling: list[int] = _c_array_to_list(c_params.point_cr_scaling, self.num_cr_points if self.num_cr_points <= len(c_params.point_cr_scaling) else len(c_params.point_cr_scaling))
        self.grain_scaling_minus_8: int = c_params.grain_scaling_minus_8
        self.ar_coeff_lag: int = c_params.ar_coeff_lag
        # These are fixed size arrays in C struct definition (e.g. uint8_t ar_coeffs_y_plus_128[24])
        self.ar_coeffs_y_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_y_plus_128) 
        self.ar_coeffs_cb_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_cb_plus_128)
        self.ar_coeffs_cr_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_cr_plus_128)
        self.ar_coeff_shift_minus_6: int = c_params.ar_coeff_shift_minus_6
        self.grain_scale_shift: int = c_params.grain_scale_shift
        self.cb_mult: int = c_params.cb_mult
        self.cb_luma_mult: int = c_params.cb_luma_mult
        self.cb_offset: int = c_params.cb_offset
        self.cr_mult: int = c_params.cr_mult
        self.cr_luma_mult: int = c_params.cr_luma_mult
        self.cr_offset: int = c_params.cr_offset
        self.overlap_flag: int = c_params.overlap_flag # C type is int
        self.clip_to_restricted_range: int = c_params.clip_to_restricted_range # C type is int
    def __repr__(self) -> str:
        return f"FilmGrainParameters(apply_grain={self.apply_grain}, seed={self.grain_seed}, num_y_points={self.num_y_points}, chroma_scaling_from_luma={self.chroma_scaling_from_luma}, ...)"

# --- Helper Python classes for Metadata OBU nested structures ---
class MetadataITUTT35: # Corresponds to _c_wrapper.OBPMetadataITUTT35
    def __init__(self, c_meta: _c_wrapper.OBPMetadataITUTT35):
        self.itu_t_t35_country_code: int = c_meta.itu_t_t35_country_code
        self.itu_t_t35_country_code_extension_byte: int = c_meta.itu_t_t35_country_code_extension_byte # Added
        # The C struct in obuparse.h doesn't have terminal_provider_code or terminal_provider_oriented_code.
        # self.itu_t_t35_terminal_provider_code: int = c_meta.itu_t_t35_terminal_provider_code
        # self.itu_t_t35_terminal_provider_oriented_code: int = c_meta.itu_t_t35_terminal_provider_oriented_code
        payload_size = c_meta.itu_t_t35_payload_bytes_size # Corrected field name
        self.itu_t_t35_payload_bytes: bytes = ctypes.string_at(c_meta.itu_t_t35_payload_bytes, payload_size) if c_meta.itu_t_t35_payload_bytes and payload_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataITUTT35(country_code={self.itu_t_t35_country_code}, country_code_ext={self.itu_t_t35_country_code_extension_byte}, payload_len={len(self.itu_t_t35_payload_bytes)})"

class MetadataHDRCLL: # Corresponds to _c_wrapper.OBPMetadataHDRCLL
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRCLL):
        self.max_cll: int = c_meta.max_cll
        self.max_fall: int = c_meta.max_fall
    def __repr__(self) -> str:
        return f"MetadataHDRCLL(max_cll={self.max_cll}, max_fall={self.max_fall})"

class MetadataHDRMDCV: # Corresponds to _c_wrapper.OBPMetadataHDRMDCV
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRMDCV):
        self.primary_chromaticity_x: list[int] = _c_array_to_list(c_meta.primary_chromaticity_x)
        self.primary_chromaticity_y: list[int] = _c_array_to_list(c_meta.primary_chromaticity_y)
        self.white_point_chromaticity_x: int = c_meta.white_point_chromaticity_x
        self.white_point_chromaticity_y: int = c_meta.white_point_chromaticity_y
        self.luminance_max: int = c_meta.luminance_max 
        self.luminance_min: int = c_meta.luminance_min 
    def __repr__(self) -> str:
        return (f"MetadataHDRMDCV(primary_x={self.primary_chromaticity_x}, primary_y={self.primary_chromaticity_y}, "
                f"wp_x={self.white_point_chromaticity_x}, wp_y={self.white_point_chromaticity_y}, "
                f"lum_max={self.luminance_max}, lum_min={self.luminance_min})")

class ScalabilityStructure: # Corresponds to _c_wrapper.OBPScalabilityStructure
    def __init__(self, c_struct: _c_wrapper.OBPScalabilityStructure):
        self.spatial_layers_cnt_minus_1: int = c_struct.spatial_layers_cnt_minus_1
        self.spatial_layer_dimensions_present_flag: int = c_struct.spatial_layer_dimensions_present_flag # C type is int
        self.spatial_layer_description_present_flag: int = c_struct.spatial_layer_description_present_flag # C type is int
        self.temporal_group_description_present_flag: int = c_struct.temporal_group_description_present_flag # C type is int
        self.scalability_structure_reserved_3bits: int = c_struct.scalability_structure_reserved_3bits
        # Added fields from C struct
        num_spatial_layers = self.spatial_layers_cnt_minus_1 + 1
        self.spatial_layer_max_width: list[int] = _c_array_to_list(c_struct.spatial_layer_max_width, num_spatial_layers)
        self.spatial_layer_max_height: list[int] = _c_array_to_list(c_struct.spatial_layer_max_height, num_spatial_layers)
        self.spatial_layer_ref_id: list[int] = _c_array_to_list(c_struct.spatial_layer_ref_id, num_spatial_layers)
        
        if self.temporal_group_description_present_flag:
            self.temporal_group_size: int = c_struct.temporal_group_size
            tg_size = self.temporal_group_size
            self.temporal_group_temporal_id: list[int] = _c_array_to_list(c_struct.temporal_group_temporal_id, tg_size)
            self.temporal_group_temporal_switching_up_point_flag: list[int] = _c_array_to_list(c_struct.temporal_group_temporal_switching_up_point_flag, tg_size)
            self.temporal_group_spatial_switching_up_point_flag: list[int] = _c_array_to_list(c_struct.temporal_group_spatial_switching_up_point_flag, tg_size)
            self.temporal_group_ref_cnt: list[int] = _c_array_to_list(c_struct.temporal_group_ref_cnt, tg_size)
            self.temporal_group_ref_pic_diff: list[list[int]] = []
            for i in range(tg_size):
                # Each element is an array of up to 8 (MAX_NUM_REF_PICS)
                # The actual number of diffs depends on temporal_group_ref_cnt[i]
                num_refs = self.temporal_group_ref_cnt[i]
                self.temporal_group_ref_pic_diff.append(
                    _c_array_to_list(c_struct.temporal_group_ref_pic_diff[i], num_refs if num_refs <= 8 else 8)
                )
        else:
            self.temporal_group_size = 0
            self.temporal_group_temporal_id = []
            self.temporal_group_temporal_switching_up_point_flag = []
            self.temporal_group_spatial_switching_up_point_flag = []
            self.temporal_group_ref_cnt = []
            self.temporal_group_ref_pic_diff = []


    def __repr__(self) -> str:
        return f"ScalabilityStructure(spatial_layers={self.spatial_layers_cnt_minus_1+1}, temporal_group_size={self.temporal_group_size}, ...)"

class MetadataScalability: # Corresponds to _c_wrapper.OBPMetadataScalability
    def __init__(self, c_meta: _c_wrapper.OBPMetadataScalability):
        self.scalability_mode_idc: int = c_meta.scalability_mode_idc
        self.scalability_structure: ScalabilityStructure = ScalabilityStructure(c_meta.scalability_structure)
    def __repr__(self) -> str:
        return f"MetadataScalability(mode_idc={self.scalability_mode_idc}, structure={self.scalability_structure})"

class MetadataTimecode: # Corresponds to _c_wrapper.OBPMetadataTimecode
    def __init__(self, c_meta: _c_wrapper.OBPMetadataTimecode):
        self.counting_type: int = c_meta.counting_type
        self.full_timestamp_flag: int = c_meta.full_timestamp_flag # C type is int
        self.discontinuity_flag: int = c_meta.discontinuity_flag # C type is int
        self.cnt_dropped_flag: int = c_meta.cnt_dropped_flag     # C type is int
        self.n_frames: int = c_meta.n_frames # C type is uint16_t
        self.seconds_value: int = c_meta.seconds_value
        self.minutes_value: int = c_meta.minutes_value
        self.hours_value: int = c_meta.hours_value
        self.seconds_flag: int = c_meta.seconds_flag # C type is int
        self.minutes_flag: int = c_meta.minutes_flag # C type is int
        self.hours_flag: int = c_meta.hours_flag     # C type is int
        self.time_offset_length: int = c_meta.time_offset_length
        self.time_offset_value: int = c_meta.time_offset_value # C type is uint32_t
    def __repr__(self) -> str:
        return f"MetadataTimecode(h={self.hours_value}, m={self.minutes_value}, s={self.seconds_value}, f={self.n_frames}, offset_len={self.time_offset_length}, offset_val={self.time_offset_value}, ...)"

class MetadataUnregistered: # Corresponds to _c_wrapper.OBPMetadataUnregistered
    def __init__(self, c_meta: _c_wrapper.OBPMetadataUnregistered):
        # C struct has `buf` (pointer) and `buf_size`.
        # The previous Python wrapper had UUID and payload, which is specific.
        # This should represent the generic unregistered metadata.
        self.buf_size: int = c_meta.buf_size
        self.buf_data: bytes = ctypes.string_at(c_meta.buf, self.buf_size) if c_meta.buf and self.buf_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataUnregistered(buf_size={self.buf_size}, data_preview='{self.buf_data[:20].hex() if self.buf_data else ''}...')>"


# --- Helper Python classes for TileList OBU nested structures ---
class TileListEntry: # Corresponds to _c_wrapper.OBPTileListEntry
    def __init__(self, c_entry: _c_wrapper.OBPTileListEntry): # Removed obu_data_payload, data extraction handled by string_at
        self.anchor_frame_idx: int = c_entry.anchor_frame_idx
        self.anchor_tile_row: int = c_entry.anchor_tile_row
        self.anchor_tile_col: int = c_entry.anchor_tile_col
        self.tile_data_size_minus_1: int = c_entry.tile_data_size_minus_1
        
        # _c_wrapper.OBPTileListEntry has `coded_tile_data` (POINTER(c_uint8_t)) and `coded_tile_data_size` (size_t)
        # These are populated by the C parser.
        tile_data_size = c_entry.coded_tile_data_size # Use the size from C struct
        if c_entry.coded_tile_data and tile_data_size > 0:
            self.coded_tile_data: bytes = ctypes.string_at(c_entry.coded_tile_data, tile_data_size)
        else:
            self.coded_tile_data: bytes = b""

    def __repr__(self) -> str:
        return f"TileListEntry(anchor_idx={self.anchor_frame_idx}, row={self.anchor_tile_row}, col={self.anchor_tile_col}, data_size={len(self.coded_tile_data)})"


# --- Main Python OBU Classes ---
class SequenceHeader:
    def __init__(self, c_seq_header: _c_wrapper.OBPSequenceHeader):
        self._c_seq_header = c_seq_header # Keep a reference to the C struct for other parsing functions
        self.seq_profile: int = c_seq_header.seq_profile
        self.still_picture: int = c_seq_header.still_picture
        self.reduced_still_picture_header: int = c_seq_header.reduced_still_picture_header
        
        self.timing_info_present_flag: int = c_seq_header.timing_info_present_flag
        self.timing_info: TimingInfo | None = (
            TimingInfo(c_seq_header.timing_info) if self.timing_info_present_flag else None
        )
        
        self.decoder_model_info_present_flag: int = c_seq_header.decoder_model_info_present_flag
        self.decoder_model_info: DecoderModelInfo | None = (
            DecoderModelInfo(c_seq_header.decoder_model_info) if self.decoder_model_info_present_flag else None
        )
        
        self.initial_display_delay_present_flag: int = c_seq_header.initial_display_delay_present_flag
        self.operating_points_cnt_minus_1: int = c_seq_header.operating_points_cnt_minus_1
        op_count = self.operating_points_cnt_minus_1 + 1
        
        self.operating_point_idc: list[int] = _c_array_to_list(c_seq_header.operating_point_idc, op_count)
        self.seq_level_idx: list[int] = _c_array_to_list(c_seq_header.seq_level_idx, op_count)
        self.seq_tier: list[int] = _c_array_to_list(c_seq_header.seq_tier, op_count)
        self.decoder_model_present_for_this_op: list[int] = _c_array_to_list(c_seq_header.decoder_model_present_for_this_op, op_count)
        self.initial_display_delay_present_for_this_op: list[int] = _c_array_to_list(c_seq_header.initial_display_delay_present_for_this_op, op_count)
        
        self.operating_parameters_info: list[OperatingParametersInfo] = [
            OperatingParametersInfo(c_seq_header.operating_parameters_info[i]) for i in range(op_count)
        ]
        
        self.initial_display_delay_minus_1: list[int] = _c_array_to_list(c_seq_header.initial_display_delay_minus_1, op_count)
        
        self.frame_width_bits_minus_1: int = c_seq_header.frame_width_bits_minus_1
        self.frame_height_bits_minus_1: int = c_seq_header.frame_height_bits_minus_1
        self.max_frame_width_minus_1: int = c_seq_header.max_frame_width_minus_1
        self.max_frame_height_minus_1: int = c_seq_header.max_frame_height_minus_1
        
        self.frame_id_numbers_present_flag: int = c_seq_header.frame_id_numbers_present_flag
        self.delta_frame_id_length_minus_2: int = c_seq_header.delta_frame_id_length_minus_2
        self.additional_frame_id_length_minus_1: int = c_seq_header.additional_frame_id_length_minus_1
        
        self.use_128x128_superblock: int = c_seq_header.use_128x128_superblock
        self.enable_filter_intra: int = c_seq_header.enable_filter_intra
        self.enable_intra_edge_filter: int = c_seq_header.enable_intra_edge_filter
        self.enable_interintra_compound: int = c_seq_header.enable_interintra_compound
        self.enable_masked_compound: int = c_seq_header.enable_masked_compound
        self.enable_warped_motion: int = c_seq_header.enable_warped_motion
        self.enable_dual_filter: int = c_seq_header.enable_dual_filter
        self.enable_order_hint: int = c_seq_header.enable_order_hint
        self.enable_jnt_comp: int = c_seq_header.enable_jnt_comp
        self.enable_ref_frame_mvs: int = c_seq_header.enable_ref_frame_mvs
        
        self.seq_choose_screen_content_tools: int = c_seq_header.seq_choose_screen_content_tools
        self.seq_force_screen_content_tools: int = ( 
            c_seq_header.seq_force_screen_content_tools
            if self.seq_choose_screen_content_tools == 0 else 2 
        )
        self.seq_choose_integer_mv: int = c_seq_header.seq_choose_integer_mv
        self.seq_force_integer_mv: int = (
            c_seq_header.seq_force_integer_mv
            if self.seq_choose_integer_mv == 0 else 2
        )

        self.order_hint_bits_minus_1: int = c_seq_header.order_hint_bits_minus_1
        self.enable_superres: int = c_seq_header.enable_superres
        self.enable_cdef: int = c_seq_header.enable_cdef
        self.enable_restoration: int = c_seq_header.enable_restoration
        
        self.color_config: ColorConfig = ColorConfig(c_seq_header.color_config)
        self.film_grain_params_present: int = c_seq_header.film_grain_params_present

        # C struct OBPSequenceHeader has OrderHintBits, FrameWidth, FrameHeight.
        # These are not directly parsed but calculated by the C library.
        # They were added to _c_wrapper.OBPSequenceHeader.
        # Ensure they are mapped here.
        self.OrderHintBits: int = c_seq_header.OrderHintBits
        # FrameWidth and FrameHeight are not in obuparse.h's OBPSequenceHeader struct.
        # They are usually derived. If _c_wrapper.OBPSequenceHeader has them from an older version,
        # it's fine to map them if they are indeed populated by the C lib.
        # Let's assume they are not in the C struct based on obuparse.h for now.
        # self.FrameWidth: int = c_seq_header.FrameWidth
        # self.FrameHeight: int = c_seq_header.FrameHeight


    def __repr__(self) -> str:
        return (
            f"SequenceHeader(seq_profile={self.seq_profile}, still_picture={self.still_picture}, "
            f"max_frame_width={self.max_frame_width_minus_1+1}, max_frame_height={self.max_frame_height_minus_1+1}, "
            f"op_points={self.operating_points_cnt_minus_1+1}, OrderHintBits={self.OrderHintBits})"
        )

class FrameHeader: # Corresponds to _c_wrapper.OBPFrameHeader
    def __init__(self, c_fh: _c_wrapper.OBPFrameHeader, sequence_header: SequenceHeader): # sequence_header is Python type
        self._c_frame_header = c_fh 
        self._py_sequence_header = sequence_header 

        self.show_existing_frame: int = c_fh.show_existing_frame # C type is int
        self.frame_to_show_map_idx: int = c_fh.frame_to_show_map_idx
        
        # OBPFrameHeader in C has `temporal_point_info.frame_presentation_time`
        # _c_wrapper.OBPFrameHeader flattens this to `temporal_point_info` (uint32_t)
        # The Python wrapper had `temporal_point_info_present` and `frame_presentation_time`
        # Let's stick to what _c_wrapper.OBPFrameHeader provides.
        self.frame_presentation_time: int = c_fh.temporal_point_info # This field name in _c_wrapper is `temporal_point_info`
        
        self.display_frame_id: int = c_fh.display_frame_id # Not in obuparse.h struct, but in wrapper
        self.frame_type: int = c_fh.frame_type # Enum OBPFrameType
        self.show_frame: int = c_fh.show_frame # C type is int
        self.showable_frame: int = c_fh.showable_frame # C type is int
        self.error_resilient_mode: int = c_fh.error_resilient_mode # C type is int
        self.disable_cdf_update: int = c_fh.disable_cdf_update # C type is int
        self.allow_screen_content_tools: int = c_fh.allow_screen_content_tools # C type is int
        self.force_integer_mv: int = c_fh.force_integer_mv # C type is int
        self.current_frame_id: int = c_fh.current_frame_id # Not in obuparse.h struct, but in wrapper
        self.frame_size_override_flag: int = c_fh.frame_size_override_flag # C type is int
        self.order_hint: int = c_fh.order_hint # C type is uint8_t
        self.primary_ref_frame: int = c_fh.primary_ref_frame
        self.buffer_removal_time_present_flag: int = c_fh.buffer_removal_time_present_flag # Added, C type is int
        self.buffer_removal_time: list[int] = _c_array_to_list(c_fh.buffer_removal_time) # Added, C type is uint32_t[32]
        self.refresh_frame_flags: int = c_fh.refresh_frame_flags
        self.ref_order_hint: list[int] = _c_array_to_list(c_fh.ref_order_hint) # C type is uint8_t[8]

        self.frame_width_minus_1: int = c_fh.frame_width_minus_1
        self.frame_height_minus_1: int = c_fh.frame_height_minus_1
        self.superres_params: SuperresParams = SuperresParams(c_fh.superres_params)
        self.render_and_frame_size_different: int = c_fh.render_and_frame_size_different # Added, C type is int
        self.render_width_minus_1: int = c_fh.render_width_minus_1 # C type is uint16_t
        self.render_height_minus_1: int = c_fh.render_height_minus_1 # C type is uint16_t
        self.RenderWidth: int = c_fh.RenderWidth   # Added, C type is uint32_t (derived in C lib)
        self.RenderHeight: int = c_fh.RenderHeight # Added, C type is uint32_t (derived in C lib)

        self.allow_intrabc: int = c_fh.allow_intrabc # C type is int
        # palette_mode_enabled is not in C struct OBPFrameHeader
        # self.palette_mode_enabled: int = c_fh.palette_mode_enabled 
        self.frame_refs_short_signaling: int = c_fh.frame_refs_short_signaling # Added, C type is int
        self.last_frame_idx: int = c_fh.last_frame_idx # Added
        self.gold_frame_idx: int = c_fh.gold_frame_idx # Added
        self.ref_frame_idx: list[int] = _c_array_to_list(c_fh.ref_frame_idx) # Added, C type is uint8_t[7]
        self.delta_frame_id_minus_1: list[int] = _c_array_to_list(c_fh.delta_frame_id_minus_1) # Added, C type is uint8_t[7]
        self.found_ref: int = c_fh.found_ref # Added, C type is int

        self.allow_high_precision_mv: int = c_fh.allow_high_precision_mv # C type is int
        self.interpolation_filter: InterpolationFilter = InterpolationFilter(c_fh.interpolation_filter)
        self.is_motion_mode_switchable: int = c_fh.is_motion_mode_switchable # C type is int
        self.use_ref_frame_mvs: int = c_fh.use_ref_frame_mvs # C type is int
        self.disable_frame_end_update_cdf: int = c_fh.disable_frame_end_update_cdf # C type is int
        
        self.tile_info: TileInfo = TileInfo(c_fh.tile_info)
        self.quantization_params: QuantizationParams = QuantizationParams(c_fh.quantization_params)
        self.segmentation_params: SegmentationParams = SegmentationParams(c_fh.segmentation_params)
        self.delta_q_params: DeltaQParams = DeltaQParams(c_fh.delta_q_params)
        self.delta_lf_params: DeltaLFParams = DeltaLFParams(c_fh.delta_lf_params)
        self.loop_filter_params: LoopFilterParams = LoopFilterParams(c_fh.loop_filter_params)
        self.cdef_params: CdefParams = CdefParams(c_fh.cdef_params)
        self.lr_params: LrParams = LrParams(c_fh.lr_params)

        self.tx_mode_select: int = c_fh.tx_mode_select # Added, C type is int (tx_mode in C struct)
        self.skip_mode_present: int = c_fh.skip_mode_present # C type is int
        self.reference_select: int = c_fh.reference_select # Added, C type is int
        self.allow_warped_motion: int = c_fh.allow_warped_motion # C type is int
        self.reduced_tx_set: int = c_fh.reduced_tx_set # C type is int
        
        # OBPFrameHeader._c_frame_header.global_motion_params is an array of 8 OBPGlobalMotionParams (from _c_wrapper)
        self.global_motion_params: list[GlobalMotionParams] = [
            GlobalMotionParams(c_fh.global_motion_params[i]) for i in range(8) # REF_FRAMES = 8
        ]
        
        # Film grain params are present if flag in sequence header is set
        if sequence_header.film_grain_params_present: # Use the Python SequenceHeader object
            self.film_grain_params: FilmGrainParameters | None = FilmGrainParameters(c_fh.film_grain_params)
        else:
            self.film_grain_params = None
        
        # large_scale_tile is not in obuparse.h struct OBPFrameHeader
        # self.large_scale_tile: int = c_fh.large_scale_tile

        # Fields from C that were not in the original Python wrapper but are in _c_wrapper
        self.RenderWidth: int = c_fh.RenderWidth
        self.RenderHeight: int = c_fh.RenderHeight
        # MiCols and MiRows are not in C struct OBPFrameHeader, but calculated by lib.
        # If needed, they should be obtained from the C library's calculations, not direct mapping.
        # self.MiCols: int = c_fh.MiCols
        # self.MiRows: int = c_fh.MiRows


    def __repr__(self) -> str:
        return (f"FrameHeader(type={self.frame_type}, width={self.RenderWidth}, height={self.RenderHeight}, " # Used RenderWidth/Height
                f"show_frame={self.show_frame}, order_hint={self.order_hint})")

class TileGroup: # Corresponds to _c_wrapper.OBPTileGroup
    def __init__(self, c_tg: _c_wrapper.OBPTileGroup):
        self._c_tile_group = c_tg # This is the C struct from _c_wrapper
        
        # Map fields from _c_wrapper.OBPTileGroup which should mirror obuparse.h's OBPTileGroup
        self.NumTiles: int = c_tg.NumTiles
        self.tile_start_and_end_present_flag: int = c_tg.tile_start_and_end_present_flag # Added
        self.tg_start: int = c_tg.tg_start # Added
        self.tg_end: int = c_tg.tg_end     # Added
        
        # The TileSize array itself is large. We might not want to copy all 4096 ulonglongs.
        # The NumTiles field indicates how many are relevant.
        # For now, let's provide access to the relevant part.
        self.TileSize: list[int] = _c_array_to_list(c_tg.TileSize, self.NumTiles if self.NumTiles <= len(c_tg.TileSize) else len(c_tg.TileSize))

        # The old Python `TileGroup` had `obu_size` and `data` which were related to how
        # the C library might have been passing data for a *single* tile group OBU's payload.
        # The current C struct `OBPTileGroup` from `obuparse.h` describes the properties of the tile group,
        # especially when it's part of a Frame OBU.
        # The actual combined data of tiles within this group isn't directly part of this specific struct.
        # If `parse_tile_group` or `parse_frame` C functions populate `c_tg.data` and `c_tg.obu_size`
        # (as the old Python code suggested for `_c_wrapper.OBPTileGroup`), then that data is separate.
        # The current _c_wrapper.OBPTileGroup matches obuparse.h, so it does not have `data` or `obu_size` fields.
        # This class will represent the header information of the tile group.
        # The actual tile data bytes are not directly part of this structure.
        # self.data: bytes = b"" # This would need to be populated by the calling parser function

    def __repr__(self) -> str:
        return f"TileGroup(NumTiles={self.NumTiles}, tg_start={self.tg_start}, tg_end={self.tg_end}, TileSize_preview={self.TileSize[:min(self.NumTiles, 5)]}...)"


class Metadata: # Corresponds to _c_wrapper.OBPMetadata
    def __init__(self, c_meta: _c_wrapper.OBPMetadata, obu_payload: bytes): # obu_payload is the full OBU content
        self._c_metadata = c_meta
        self.metadata_type: int = c_meta.metadata_type # Renamed from 'type' to 'metadata_type'

        # The C struct OBPMetadata has direct members for each metadata type struct.
        # It also has `unregistered.buf` and `unregistered.buf_size`.
        # The `obu_size` and `data` fields were in the old Python wrapper for OBPMetadata,
        # but not in the C header struct. `obu_payload` passed to constructor is the actual OBU content.
        self.obu_payload: bytes = obu_payload # Store the raw OBU payload for reference

        self.metadata_itut_t35: MetadataITUTT35 | None = None
        self.metadata_hdr_cll: MetadataHDRCLL | None = None
        self.metadata_hdr_mdcv: MetadataHDRMDCV | None = None
        self.metadata_scalability: MetadataScalability | None = None
        self.metadata_timecode: MetadataTimecode | None = None
        self.unregistered: MetadataUnregistered | None = None # For the generic unregistered type

        if self.metadata_type == _c_wrapper.OBP_METADATA_TYPE_ITUT_T35:
            self.metadata_itut_t35 = MetadataITUTT35(c_meta.metadata_itut_t35)
        elif self.metadata_type == _c_wrapper.OBP_METADATA_TYPE_HDR_CLL:
            self.metadata_hdr_cll = MetadataHDRCLL(c_meta.metadata_hdr_cll)
        elif self.metadata_type == _c_wrapper.OBP_METADATA_TYPE_HDR_MDCV:
            self.metadata_hdr_mdcv = MetadataHDRMDCV(c_meta.metadata_hdr_mdcv)
        elif self.metadata_type == _c_wrapper.OBP_METADATA_TYPE_SCALABILITY:
            self.metadata_scalability = MetadataScalability(c_meta.metadata_scalability)
        elif self.metadata_type == _c_wrapper.OBP_METADATA_TYPE_TIMECODE:
            self.metadata_timecode = MetadataTimecode(c_meta.metadata_timecode)
        # For other types, including generic unregistered (if type > 5 and not specific known one)
        # or if it's a registered type not yet having a specific class,
        # the `unregistered` part of the C union might be used by the C lib, or it's user-defined.
        # The C struct `OBPMetadata` has a specific `unregistered` member.
        # We should map this if the type indicates it's truly an "unregistered" type by spec,
        # or if it's any other type not handled explicitly above.
        # The C library populates `unregistered.buf` and `unregistered.buf_size` for metadata types
        # that are not one of the explicitly parsed ones (HDR_CLL, HDR_MDCV, SCALABILITY, ITUT_T35, TIMECODE).
        # This means if `metadata_type` is e.g. 0 or some other reserved/custom value, the payload
        # would be in `unregistered`.
        else: # Fallback for any other metadata type not explicitly handled
            self.unregistered = MetadataUnregistered(c_meta.unregistered)


    def __repr__(self) -> str:
        return f"Metadata(type={self.metadata_type}, specific_metadata_present={self._get_specific_metadata_repr()})"

    def _get_specific_metadata_repr(self) -> str:
        if self.metadata_itut_t35: return repr(self.metadata_itut_t35)
        if self.metadata_hdr_cll: return repr(self.metadata_hdr_cll)
        if self.metadata_hdr_mdcv: return repr(self.metadata_hdr_mdcv)
        if self.metadata_scalability: return repr(self.metadata_scalability)
        if self.metadata_timecode: return repr(self.metadata_timecode)
        if self.unregistered: return repr(self.unregistered) # This will now catch other types
        return "None"

class TileList: # Corresponds to _c_wrapper.OBPTileList
    def __init__(self, c_tl: _c_wrapper.OBPTileList, obu_payload: bytes): # obu_payload not strictly needed if c_entry.coded_tile_data is absolute
        self._c_tile_list = c_tl
        self.output_frame_width_in_tiles_minus_1: int = c_tl.output_frame_width_in_tiles_minus_1 # Corrected name
        self.output_frame_height_in_tiles_minus_1: int = c_tl.output_frame_height_in_tiles_minus_1 # Corrected name
        self.tile_count_minus_1: int = c_tl.tile_count_minus_1
        
        self.tile_list_entries: list[TileListEntry] = []
        # _c_wrapper.OBPTileList.tile_list_entry is an array of OBPTileListEntry structs, not a pointer.
        # So we iterate up to tile_count_minus_1 + 1
        num_entries = self.tile_count_minus_1 + 1
        for i in range(num_entries):
            c_entry = c_tl.tile_list_entry[i] # Access element from the array
            # TileListEntry constructor now handles data extraction using c_entry.coded_tile_data and coded_tile_data_size
            self.tile_list_entries.append(TileListEntry(c_entry))

    def __repr__(self) -> str:
        return (f"TileList(width_tiles={self.output_frame_width_in_tiles_minus_1+1}, "
                f"height_tiles={self.output_frame_height_in_tiles_minus_1+1}, count={self.tile_count_minus_1+1})")


# --- OBPState Wrapper ---
class OBPStateWrapper:
    def __init__(self):
        self._c_state_instance = _c_wrapper.OBPState()
        if _c_wrapper._lib and hasattr(_c_wrapper._lib, 'obp_state_init'):
            _c_wrapper._lib.obp_state_init(ctypes.byref(self._c_state_instance))
        else:
            # Manual basic initialization if obp_state_init is not available or lib not loaded
            # This might not be fully correct as obp_state_init does more.
            ctypes.memset(ctypes.byref(self._c_state_instance), 0, ctypes.sizeof(_c_wrapper.OBPState))
            # A key field to initialize for first frame_header parsing:
            self._c_state_instance.current_frame_id = -1 


    @property
    def c_state(self) -> _c_wrapper.OBPState:
        return self._c_state_instance

    def __repr__(self) -> str:
        # Provide a minimal representation
        return f"OBPStateWrapper(current_frame_id={self._c_state_instance.current_frame_id})"


# --- Parsing Functions ---

def _handle_parse_error(ret_code: int, err_struct: _c_wrapper.OBPError, context_message: str) -> None:
    if ret_code != 0:
        error_message = "Unknown C parsing error"
        if err_struct.error:
            error_message = err_struct.error.decode('utf-8', errors='replace')
            if _c_wrapper._lib and hasattr(_c_wrapper._lib, 'obp_free_error_string'):
                _c_wrapper.free_obp_error_string(err_struct) # Use the one from _c_wrapper
            else: # Fallback if free_obp_error_string is somehow not available
                err_struct.error = None # Avoid dangling pointer issues if Python were to try to free it
        raise OBUParseError(f"{context_message} (code {ret_code}): {error_message}")


def parse_sequence_header(data: bytes) -> SequenceHeader:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_seq_header_instance = _c_wrapper.OBPSequenceHeader()
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))

    ret_code = c_lib.obp_parse_sequence_header(data_ptr, len(data), ctypes.byref(c_seq_header_instance), ctypes.byref(err_struct))
    _handle_parse_error(ret_code, err_struct, "Failed to parse sequence header")
    return SequenceHeader(c_seq_header_instance)


def parse_frame_header(data: bytes, sequence_header_obj: SequenceHeader, 
                       state_wrapper: OBPStateWrapper, temporal_id: int, spatial_id: int) -> FrameHeader:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_frame_header_instance = _c_wrapper.OBPFrameHeader()
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))
    
    # SeenFrameHeader is an output parameter, int*
    seen_frame_header_cval = _c_wrapper.c_int_t()

    ret_code = c_lib.obp_parse_frame_header(
        data_ptr, len(data),
        ctypes.byref(sequence_header_obj._c_seq_header), # Pass the C struct by reference
        ctypes.byref(state_wrapper.c_state),           # Pass the C struct by reference
        temporal_id, spatial_id,
        ctypes.byref(c_frame_header_instance),
        ctypes.byref(seen_frame_header_cval),
        ctypes.byref(err_struct)
    )
    _handle_parse_error(ret_code, err_struct, "Failed to parse frame header")
    # The value of seen_frame_header_cval can be checked if needed.
    return FrameHeader(c_frame_header_instance, sequence_header_obj)

def parse_frame(data: bytes, sequence_header_obj: SequenceHeader, state_wrapper: OBPStateWrapper,
                temporal_id: int, spatial_id: int) -> Tuple[FrameHeader, TileGroup]:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_frame_header_instance = _c_wrapper.OBPFrameHeader() # Output if redundant frame header
    c_tile_group_instance = _c_wrapper.OBPTileGroup()   # Output for tile group data
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))
    seen_frame_header_cval = _c_wrapper.c_int_t() # Input/Output

    # If a frame header has already been parsed for this frame, its state might be needed.
    # For now, obp_parse_frame can take an empty OBPFrameHeader if it's the first part of a frame OBU.
    # The C function obp_parse_frame internally calls obp_parse_frame_header if SeenFrameHeader is 0.

    ret_code = c_lib.obp_parse_frame(
        data_ptr, len(data),
        ctypes.byref(sequence_header_obj._c_seq_header),
        ctypes.byref(state_wrapper.c_state),
        temporal_id, spatial_id,
        ctypes.byref(c_frame_header_instance), # Can be populated by parse_frame_header inside
        ctypes.byref(c_tile_group_instance),
        ctypes.byref(seen_frame_header_cval),  # Mark if frame header was seen/parsed
        ctypes.byref(err_struct)
    )
    _handle_parse_error(ret_code, err_struct, "Failed to parse frame OBU (frame header + tile group)")
    
    py_frame_header = FrameHeader(c_frame_header_instance, sequence_header_obj)
    py_tile_group = TileGroup(c_tile_group_instance)
    return py_frame_header, py_tile_group


def parse_tile_group(data: bytes, frame_header_obj: FrameHeader) -> TileGroup:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_tile_group_instance = _c_wrapper.OBPTileGroup()
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))
    
    # SeenFrameHeader for context, assume frame header is already known and parsed.
    # The C function obp_parse_tile_group expects SeenFrameHeader to be non-zero.
    # It's an int*, so pass a c_int by reference, set to 1 (true).
    seen_frame_header_cval = _c_wrapper.c_int_t(1) 

    ret_code = c_lib.obp_parse_tile_group(
        data_ptr, len(data),
        ctypes.byref(frame_header_obj._c_frame_header), # Pass underlying C struct
        ctypes.byref(c_tile_group_instance),
        ctypes.byref(seen_frame_header_cval), # Indicate FH is known
        ctypes.byref(err_struct)
    )
    _handle_parse_error(ret_code, err_struct, "Failed to parse tile group")
    return TileGroup(c_tile_group_instance)

def parse_metadata(data: bytes) -> Metadata:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_metadata_instance = _c_wrapper.OBPMetadata()
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))

    ret_code = c_lib.obp_parse_metadata(data_ptr, len(data), ctypes.byref(c_metadata_instance), ctypes.byref(err_struct))
    _handle_parse_error(ret_code, err_struct, "Failed to parse metadata OBU")
    # Pass `data` (OBU payload) to Metadata constructor for context if needed for pointer arithmetic
    return Metadata(c_metadata_instance, data)


def parse_tile_list(data: bytes) -> TileList:
    if not _c_wrapper._lib: raise OBUParseError("C library not loaded.")
    c_lib = _c_wrapper._lib
    err_struct = _c_wrapper.OBPError()
    c_tile_list_instance = _c_wrapper.OBPTileList()
    data_ptr = ctypes.cast(data, ctypes.POINTER(_c_wrapper.c_uint8_t))

    ret_code = c_lib.obp_parse_tile_list(data_ptr, len(data), ctypes.byref(c_tile_list_instance), ctypes.byref(err_struct))
    _handle_parse_error(ret_code, err_struct, "Failed to parse tile list OBU")
    # Pass `data` (OBU payload) to TileList constructor for context
    return TileList(c_tile_list_instance, data)


# --- iter_obus (updated for spatial_id) ---
_PY_OBP_OBU_TYPE_MAP = {
    _c_wrapper.OBP_OBU_SEQUENCE_HEADER: _c_wrapper.OBP_OBU_SEQUENCE_HEADER,
    _c_wrapper.OBP_OBU_TEMPORAL_DELIMITER: _c_wrapper.OBP_OBU_TEMPORAL_DELIMITER,
    _c_wrapper.OBP_OBU_FRAME_HEADER: _c_wrapper.OBP_OBU_FRAME_HEADER,
    _c_wrapper.OBP_OBU_TILE_GROUP: _c_wrapper.OBP_OBU_TILE_GROUP,
    _c_wrapper.OBP_OBU_METADATA: _c_wrapper.OBP_OBU_METADATA, # Added
    _c_wrapper.OBP_OBU_FRAME: _c_wrapper.OBP_OBU_FRAME,
    _c_wrapper.OBP_OBU_REDUNDANT_FRAME_HEADER: _c_wrapper.OBP_OBU_REDUNDANT_FRAME_HEADER,
    _c_wrapper.OBP_OBU_TILE_LIST: _c_wrapper.OBP_OBU_TILE_LIST,
    _c_wrapper.OBP_OBU_PADDING: _c_wrapper.OBP_OBU_PADDING,
}

def iter_obus(data: bytes):
    """
    Generates OBU information from a byte stream.
    Yields tuples of (obu_type_constant, temporal_id, spatial_id, obu_payload_bytes).
    obu_type_constant will be one of the OBP_OBU_* constants from _c_wrapper.
    """
    if not _c_wrapper._lib:
        raise OBUParseError("C library not loaded.")
    
    c_lib = _c_wrapper._lib
    c_lib = _c_wrapper._lib
    
    # _c_wrapper.py should now consistently define obp_get_next_obu with 8 arguments,
    # including pointers for temporal_id and spatial_id.
    # The C function signature:
    # int obp_get_next_obu(uint8_t *buf, size_t buf_size, 
    #                      OBPOBUType *obu_type, ptrdiff_t *offset, size_t *obu_size, 
    #                      int *temporal_id, int *spatial_id, OBPError *err);
    # *offset will be the OBU header size.
    # *obu_size will be the OBU payload size.

    data_len = len(data)
    current_pos = 0
    
    while current_pos < data_len:
        obu_type_cval = _c_wrapper.c_int_t()
        obu_header_size_cval = _c_wrapper.c_ptrdiff_t() # ptrdiff_t *offset (output for header size)
        obu_payload_size_cval = _c_wrapper.c_size_t()   # size_t *obu_size (output for payload size)
        temporal_id_cval = _c_wrapper.c_int_t()
        spatial_id_cval = _c_wrapper.c_int_t(0) # Initialize to 0, will be filled by C func
        
        err_struct = _c_wrapper.OBPError()

        current_data_slice_bytes = data[current_pos:]
        remaining_data_size = len(current_data_slice_bytes)

        if remaining_data_size == 0:
            break

        input_buffer_ptr = ctypes.cast(current_data_slice_bytes, ctypes.POINTER(_c_wrapper.c_uint8_t))

        ret_code = c_lib.obp_get_next_obu(
            input_buffer_ptr, remaining_data_size,
            ctypes.byref(obu_type_cval),
            ctypes.byref(obu_header_size_cval),
            ctypes.byref(obu_payload_size_cval),
            ctypes.byref(temporal_id_cval),
            ctypes.byref(spatial_id_cval),
            ctypes.byref(err_struct)
        )

        if ret_code != 0:
            error_message = f"Failed to get next OBU (code {ret_code})"
            if err_struct.error:
                error_message += f": {err_struct.error.decode('utf-8', errors='replace')}"
                # Ensure free_obp_error_string is used from _c_wrapper
                _c_wrapper.free_obp_error_string(err_struct)
            
            # If remaining data is very small (e.g. less than a minimal OBU header) and an error occurs,
            # it might be due to trailing incomplete data rather than a fatal error.
            # However, the C library should ideally handle this gracefully.
            # For now, if any error, we raise.
            # if remaining_data_size < 2 and ret_code !=0 : # Example minimal check
            #     break 
            raise OBUParseError(error_message)

        obu_header_size = obu_header_size_cval.value
        obu_payload_size = obu_payload_size_cval.value
        total_obu_length = obu_header_size + obu_payload_size
        
        # If total_obu_length is 0, it might indicate end of valid OBUs or an issue.
        # The C function should ideally handle this. If it returns 0 (success)
        # with total_obu_length 0, it's likely a padding OBU or similar that means stop.
        if total_obu_length == 0: # If C lib reports 0 total length, assume end of useful data
            break

        payload_start_abs = current_pos + obu_header_size
        payload_end_abs = payload_start_abs + obu_payload_size
        
        if payload_end_abs > data_len:
            raise OBUParseError(
                f"OBU payload extends beyond data buffer. Calculated end: {payload_end_abs}, Data Len: {data_len}. "
                f"OBU Type: {obu_type_cval.value}, Reported Header Size: {obu_header_size}, Reported Payload Size: {obu_payload_size}"
            )
            
        obu_payload_bytes = data[payload_start_abs:payload_end_abs]
        py_obu_type = _PY_OBP_OBU_TYPE_MAP.get(obu_type_cval.value, obu_type_cval.value)

        yield (
            py_obu_type,
            temporal_id_cval.value,
            spatial_id_cval.value,
            obu_payload_bytes
        )

        current_pos += total_obu_length
        if current_pos > data_len:
            raise OBUParseError("Current position exceeded data length unexpectedly.")


__all__ = [
    "OBUParseError",
    # Sequence Header related
    "TimingInfo", "DecoderModelInfo", "OperatingParametersInfo", "ColorConfig", "SequenceHeader",
    "parse_sequence_header",
    # Frame Header related
    "SuperresParams", "InterpolationFilter", "TileInfo", "QuantizationParams",
    "SegmentationParams", "DeltaQParams", "DeltaLFParams", "LoopFilterParams",
    "CdefParams", "LrParams", "GlobalMotionParams", "FilmGrainParameters", "FrameHeader",
    "parse_frame_header",
    # Tile Group related
    "TileGroup", "parse_tile_group",
    # Frame (FH + TG) related
    "parse_frame",
    # Metadata related
    "MetadataITUTT35", "MetadataHDRCLL", "MetadataHDRMDCV", "ScalabilityStructure",
    "MetadataScalability", "MetadataTimecode", "MetadataUnregistered", "Metadata",
    "parse_metadata",
    # Tile List related
    "TileListEntry", "TileList", "parse_tile_list",
    # State
    "OBPStateWrapper",
    # Iterator
    "iter_obus",
]
