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

class TimingInfo:
    def __init__(self, c_timing_info: _c_wrapper.OBPTimingInfo):
        self.num_units_in_display_tick: int = c_timing_info.num_units_in_display_tick
        self.time_scale: int = c_timing_info.time_scale
        self.equal_picture_interval: int = c_timing_info.equal_picture_interval
        self.num_ticks_per_picture_minus_1: int = c_timing_info.num_ticks_per_picture_minus_1

    def __repr__(self) -> str:
        return (
            f"TimingInfo(num_units_in_display_tick={self.num_units_in_display_tick}, "
            f"time_scale={self.time_scale}, equal_picture_interval={self.equal_picture_interval}, "
            f"num_ticks_per_picture_minus_1={self.num_ticks_per_picture_minus_1})"
        )

class DecoderModelInfo:
    def __init__(self, c_decoder_model_info: _c_wrapper.OBPDecoderModelInfo):
        self.buffer_delay_length_minus_1: int = c_decoder_model_info.buffer_delay_length_minus_1
        self.num_units_in_decoding_tick: int = c_decoder_model_info.num_units_in_decoding_tick
        self.buffer_removal_time_length_minus_1: int = c_decoder_model_info.buffer_removal_time_length_minus_1
        self.frame_presentation_time_length_minus_1: int = c_decoder_model_info.frame_presentation_time_length_minus_1

    def __repr__(self) -> str:
        return (
            f"DecoderModelInfo(buffer_delay_length_minus_1={self.buffer_delay_length_minus_1}, "
            # (repr was too long, shortened for brevity)
            f"..., frame_presentation_time_length_minus_1={self.frame_presentation_time_length_minus_1})"
        )

class OperatingParametersInfo:
    def __init__(self, c_op_info: _c_wrapper.OBPOperatingParametersInfo):
        self.decoder_buffer_delay: int = c_op_info.decoder_buffer_delay
        self.encoder_buffer_delay: int = c_op_info.encoder_buffer_delay
        self.low_delay_mode_flag: int = c_op_info.low_delay_mode_flag

    def __repr__(self) -> str:
        return (
            f"OperatingParametersInfo(decoder_buffer_delay={self.decoder_buffer_delay}, "
            f"encoder_buffer_delay={self.encoder_buffer_delay}, low_delay_mode_flag={self.low_delay_mode_flag})"
        )

class ColorConfig:
    def __init__(self, c_color_config: _c_wrapper.OBPColorConfig):
        self.high_bitdepth: int = c_color_config.high_bitdepth
        self.twelve_bit: int = c_color_config.twelve_bit
        self.mono_chrome: int = c_color_config.mono_chrome
        self.color_range: int = c_color_config.color_range
        self.separate_uv_delta_q: int = c_color_config.separate_uv_delta_q
        self.color_description_present_flag: int = c_color_config.color_description_present_flag
        self.color_primaries: int = c_color_config.color_primaries
        self.transfer_characteristics: int = c_color_config.transfer_characteristics
        self.matrix_coefficients: int = c_color_config.matrix_coefficients
        self.chroma_sample_position: int = c_color_config.chroma_sample_position

    def __repr__(self) -> str:
        return (
            f"ColorConfig(high_bitdepth={self.high_bitdepth}, twelve_bit={self.twelve_bit}, "
            # (repr was too long, shortened for brevity)
            f"..., chroma_sample_position={self.chroma_sample_position})"
        )

# --- Helper Python classes for FrameHeader nested structures ---

class SuperresParams:
    def __init__(self, c_params: _c_wrapper.OBPSuperresParams):
        self.use_superres: int = c_params.use_superres
        self.coded_denom: int = c_params.coded_denom
        self.superres_upscaled_width: int = c_params.superres_upscaled_width
        self.superres_upscaled_height: int = c_params.superres_upscaled_height
    def __repr__(self) -> str:
        return f"SuperresParams(use_superres={self.use_superres}, coded_denom={self.coded_denom}, upscaled_width={self.superres_upscaled_width}, upscaled_height={self.superres_upscaled_height})"

class InterpolationFilter: # Simple wrapper
    def __init__(self, c_filter: _c_wrapper.OBPInterpolationFilter):
        self.value: int = c_filter.value
    def __repr__(self) -> str:
        return f"InterpolationFilter(value={self.value})"

class TileInfo:
    def __init__(self, c_info: _c_wrapper.OBPTileInfo):
        self.uniform_tile_spacing_flag: int = c_info.uniform_tile_spacing_flag
        self.MiColStarts: list[int] = _c_array_to_list(c_info.MiColStarts)
        self.MiRowStarts: list[int] = _c_array_to_list(c_info.MiRowStarts)
        self.width_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.width_in_sbs_minus_1)
        self.height_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.height_in_sbs_minus_1)
        self.context_update_tile_id: int = c_info.context_update_tile_id
        self.tile_cols: int = c_info.tile_cols
        self.tile_rows: int = c_info.tile_rows
    def __repr__(self) -> str:
        return f"TileInfo(tile_cols={self.tile_cols}, tile_rows={self.tile_rows}, uniform_spacing={self.uniform_tile_spacing_flag}, ...)"

class QuantizationParams:
    def __init__(self, c_params: _c_wrapper.OBPQuantizationParams):
        self.base_q_idx: int = c_params.base_q_idx
        self.DeltaQYDc: int = c_params.DeltaQYDc
        self.DeltaQUDc: int = c_params.DeltaQUDc
        self.DeltaQUAc: int = c_params.DeltaQUAc
        self.DeltaQVDc: int = c_params.DeltaQVDc
        self.DeltaQVAc: int = c_params.DeltaQVAc
        self.using_qmatrix: int = c_params.using_qmatrix
        self.qm_y: int = c_params.qm_y
        self.qm_u: int = c_params.qm_u
        self.qm_v: int = c_params.qm_v
    def __repr__(self) -> str:
        return f"QuantizationParams(base_q_idx={self.base_q_idx}, using_qmatrix={self.using_qmatrix}, ...)"

class SegmentationParams:
    def __init__(self, c_params: _c_wrapper.OBPSegmentationParams):
        self.segmentation_enabled: int = c_params.segmentation_enabled
        self.segmentation_update_map: int = c_params.segmentation_update_map
        self.segmentation_temporal_update: int = c_params.segmentation_temporal_update
        self.segmentation_update_data: int = c_params.segmentation_update_data
        self.feature_enabled: list[list[int]] = [_c_array_to_list(c_params.feature_enabled[i]) for i in range(4)] # SEG_LVL_MAX = 4
        self.feature_data: list[list[int]] = [_c_array_to_list(c_params.feature_data[i]) for i in range(4)]
    def __repr__(self) -> str:
        return f"SegmentationParams(enabled={self.segmentation_enabled}, update_map={self.segmentation_update_map}, ...)"

class DeltaQParams:
    def __init__(self, c_params: _c_wrapper.OBPDeltaQParams):
        self.delta_q_present: int = c_params.delta_q_present
        self.delta_q_res: int = c_params.delta_q_res
    def __repr__(self) -> str:
        return f"DeltaQParams(present={self.delta_q_present}, res={self.delta_q_res})"

class DeltaLFParams:
    def __init__(self, c_params: _c_wrapper.OBPDeltaLFParams):
        self.delta_lf_present: int = c_params.delta_lf_present
        self.delta_lf_res: int = c_params.delta_lf_res
        self.delta_lf_multi: int = c_params.delta_lf_multi
    def __repr__(self) -> str:
        return f"DeltaLFParams(present={self.delta_lf_present}, res={self.delta_lf_res}, multi={self.delta_lf_multi})"

class LoopFilterParams:
    def __init__(self, c_params: _c_wrapper.OBPLoopFilterParams):
        self.loop_filter_level: list[int] = _c_array_to_list(c_params.loop_filter_level)
        self.loop_filter_sharpness: int = c_params.loop_filter_sharpness
        self.loop_filter_delta_enabled: int = c_params.loop_filter_delta_enabled
        self.loop_filter_ref_deltas: list[int] = _c_array_to_list(c_params.loop_filter_ref_deltas)
        self.loop_filter_mode_deltas: list[int] = _c_array_to_list(c_params.loop_filter_mode_deltas)
    def __repr__(self) -> str:
        return f"LoopFilterParams(level_y_v={self.loop_filter_level[1]}, sharpness={self.loop_filter_sharpness}, ...)"

class CdefParams:
    def __init__(self, c_params: _c_wrapper.OBPCdefParams):
        self.cdef_damping_minus_3: int = c_params.cdef_damping_minus_3
        self.cdef_bits: int = c_params.cdef_bits
        self.cdef_y_pri_strength: list[int] = _c_array_to_list(c_params.cdef_y_pri_strength)
        self.cdef_y_sec_strength: list[int] = _c_array_to_list(c_params.cdef_y_sec_strength)
        self.cdef_uv_pri_strength: list[int] = _c_array_to_list(c_params.cdef_uv_pri_strength)
        self.cdef_uv_sec_strength: list[int] = _c_array_to_list(c_params.cdef_uv_sec_strength)
    def __repr__(self) -> str:
        return f"CdefParams(damping={self.cdef_damping_minus_3+3}, bits={self.cdef_bits}, ...)"

class LrParams:
    def __init__(self, c_params: _c_wrapper.OBPLrParams):
        self.lr_type: list[int] = _c_array_to_list(c_params.lr_type)
        self.lr_unit_shift: int = c_params.lr_unit_shift
        self.lr_uv_shift: int = c_params.lr_uv_shift
    def __repr__(self) -> str:
        return f"LrParams(type_y={self.lr_type[0]}, unit_shift={self.lr_unit_shift}, uv_shift={self.lr_uv_shift})"

class GlobalMotionParams: # Wrapper for a single GlobalMotionParam array element
    def __init__(self, gm_type: int, gm_params: Sequence[int]):
        self.gm_type: int = gm_type
        self.gm_params: list[int] = list(gm_params) # Should be 6 elements
    def __repr__(self) -> str:
        return f"GlobalMotionParams(type={self.gm_type}, params={self.gm_params[:2]}...)"

class FilmGrainParameters: # For OBPFilmGrainParameters
    def __init__(self, c_params: _c_wrapper.OBPFilmGrainParameters):
        self.apply_grain: int = c_params.apply_grain
        self.grain_seed: int = c_params.grain_seed
        self.update_grain: int = c_params.update_grain
        self.film_grain_params_ref_idx: int = c_params.film_grain_params_ref_idx
        self.num_y_points: int = c_params.num_y_points
        self.point_y_value: list[int] = _c_array_to_list(c_params.point_y_value, self.num_y_points)
        self.point_y_scaling: list[int] = _c_array_to_list(c_params.point_y_scaling, self.num_y_points)
        self.chroma_scaling_from_luma: int = c_params.chroma_scaling_from_luma
        self.num_cb_points: int = c_params.num_cb_points
        self.point_cb_value: list[int] = _c_array_to_list(c_params.point_cb_value, self.num_cb_points)
        self.point_cb_scaling: list[int] = _c_array_to_list(c_params.point_cb_scaling, self.num_cb_points)
        self.num_cr_points: int = c_params.num_cr_points
        self.point_cr_value: list[int] = _c_array_to_list(c_params.point_cr_value, self.num_cr_points)
        self.point_cr_scaling: list[int] = _c_array_to_list(c_params.point_cr_scaling, self.num_cr_points)
        self.grain_scaling_minus_8: int = c_params.grain_scaling_minus_8
        self.ar_coeff_lag: int = c_params.ar_coeff_lag
        self.ar_coeffs_y_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_y_plus_128) # Max 24
        self.ar_coeffs_cb_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_cb_plus_128) # Max 25
        self.ar_coeffs_cr_plus_128: list[int] = _c_array_to_list(c_params.ar_coeffs_cr_plus_128) # Max 25
        self.ar_coeff_shift_minus_6: int = c_params.ar_coeff_shift_minus_6
        self.grain_scale_shift: int = c_params.grain_scale_shift
        self.cb_mult: int = c_params.cb_mult
        self.cb_luma_mult: int = c_params.cb_luma_mult
        self.cb_offset: int = c_params.cb_offset
        self.cr_mult: int = c_params.cr_mult
        self.cr_luma_mult: int = c_params.cr_luma_mult
        self.cr_offset: int = c_params.cr_offset
        self.overlap_flag: int = c_params.overlap_flag
        self.clip_to_restricted_range: int = c_params.clip_to_restricted_range
    def __repr__(self) -> str:
        return f"FilmGrainParameters(apply_grain={self.apply_grain}, seed={self.grain_seed}, num_y_points={self.num_y_points}, ...)"

# --- Helper Python classes for Metadata OBU nested structures ---
class MetadataITUTT35:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataITUTT35):
        self.itu_t_t35_country_code: int = c_meta.itu_t_t35_country_code
        self.itu_t_t35_terminal_provider_code: int = c_meta.itu_t_t35_terminal_provider_code
        self.itu_t_t35_terminal_provider_oriented_code: int = c_meta.itu_t_t35_terminal_provider_oriented_code
        payload_size = c_meta.itu_t_t35_payload_byte_count
        self.itu_t_t35_payload_bytes: bytes = ctypes.string_at(c_meta.itu_t_t35_payload_bytes, payload_size) if c_meta.itu_t_t35_payload_bytes and payload_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataITUTT35(country_code={self.itu_t_t35_country_code}, provider_code={self.itu_t_t35_terminal_provider_code}, payload_len={len(self.itu_t_t35_payload_bytes)})"

class MetadataHDRCLL:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRCLL):
        self.max_cll: int = c_meta.max_cll
        self.max_fall: int = c_meta.max_fall
    def __repr__(self) -> str:
        return f"MetadataHDRCLL(max_cll={self.max_cll}, max_fall={self.max_fall})"

class MetadataHDRMDCV:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRMDCV):
        self.primary_chromaticity_x: list[int] = _c_array_to_list(c_meta.primary_chromaticity_x)
        self.primary_chromaticity_y: list[int] = _c_array_to_list(c_meta.primary_chromaticity_y)
        self.white_point_chromaticity_x: int = c_meta.white_point_chromaticity_x
        self.white_point_chromaticity_y: int = c_meta.white_point_chromaticity_y
        self.luminance_max: int = c_meta.luminance_max # Stored as u32 in c_wrapper for flexibility
        self.luminance_min: int = c_meta.luminance_min # Stored as u32 in c_wrapper for flexibility
    def __repr__(self) -> str:
        return f"MetadataHDRMDCV(wp_x={self.white_point_chromaticity_x}, lum_max={self.luminance_max}, ...)"

class ScalabilityStructure:
    def __init__(self, c_struct: _c_wrapper.OBPScalabilityStructure):
        self.spatial_layers_cnt_minus_1: int = c_struct.spatial_layers_cnt_minus_1
        self.spatial_layer_dimensions_present_flag: int = c_struct.spatial_layer_dimensions_present_flag
        self.spatial_layer_description_present_flag: int = c_struct.spatial_layer_description_present_flag
        self.temporal_group_description_present_flag: int = c_struct.temporal_group_description_present_flag
        self.scalability_structure_reserved_3bits: int = c_struct.scalability_structure_reserved_3bits
    def __repr__(self) -> str:
        return f"ScalabilityStructure(spatial_layers={self.spatial_layers_cnt_minus_1+1}, ...)"

class MetadataScalability:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataScalability):
        self.scalability_mode_idc: int = c_meta.scalability_mode_idc
        self.scalability_structure: ScalabilityStructure = ScalabilityStructure(c_meta.scalability_structure)
    def __repr__(self) -> str:
        return f"MetadataScalability(mode_idc={self.scalability_mode_idc}, structure={self.scalability_structure})"

class MetadataTimecode:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataTimecode):
        self.counting_type: int = c_meta.counting_type
        self.full_timestamp_flag: int = c_meta.full_timestamp_flag
        self.discontinuity_flag: int = c_meta.discontinuity_flag
        self.cnt_dropped_flag: int = c_meta.cnt_dropped_flag
        self.n_frames: int = c_meta.n_frames
        self.seconds_value: int = c_meta.seconds_value
        self.minutes_value: int = c_meta.minutes_value
        self.hours_value: int = c_meta.hours_value
        self.seconds_flag: int = c_meta.seconds_flag
        self.minutes_flag: int = c_meta.minutes_flag
        self.hours_flag: int = c_meta.hours_flag
        self.time_offset_length: int = c_meta.time_offset_length
        self.time_offset_value: int = c_meta.time_offset_value
    def __repr__(self) -> str:
        return f"MetadataTimecode(h={self.hours_value}, m={self.minutes_value}, s={self.seconds_value}, f={self.n_frames}, ...)"

class MetadataUnregistered:
    def __init__(self, c_meta: _c_wrapper.OBPMetadataUnregistered):
        self.uuid: bytes = bytes(c_meta.uuid) # c_uint8_t * 16
        payload_size = c_meta.payload_byte_count
        self.payload: bytes = ctypes.string_at(c_meta.payload, payload_size) if c_meta.payload and payload_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataUnregistered(uuid={self.uuid.hex()}, payload_len={len(self.payload)})"


# --- Helper Python classes for TileList OBU nested structures ---
class TileListEntry:
    def __init__(self, c_entry: _c_wrapper.OBPTileListEntry, obu_data_payload: bytes):
        self.anchor_frame_idx: int = c_entry.anchor_frame_idx
        self.anchor_tile_row: int = c_entry.anchor_tile_row
        self.anchor_tile_col: int = c_entry.anchor_tile_col
        self.tile_data_size_minus_1: int = c_entry.tile_data_size_minus_1
        tile_data_size = self.tile_data_size_minus_1 + 1
        
        # The tile_specific_data in OBPTileListEntry points into the OBU buffer.
        # We need to copy this data. The parser function for TileList should provide the base OBU buffer.
        # For now, let's assume the C parser populates tile_specific_data as a pointer within the provided buffer.
        # The `parse_tile_list` function will need to handle the actual extraction carefully.
        # Let's store the raw pointer and size for now, and `parse_tile_list` will populate `coded_tile_data`.
        # Or, if the C struct itself gives an offset, that would be better.
        # Based on obuparse.c, `tile_specific_data` points directly to the data.
        # The `parse_tile_list` function will need to pass the main OBU buffer to this constructor.
        if c_entry.tile_specific_data and tile_data_size > 0:
             # This assumes obu_data_payload is the start of the current OBU's payload
             # and tile_specific_data is an absolute pointer or an offset that needs context.
             # The C code makes tile_specific_data point into the input buffer.
             # We need to calculate the offset from the start of the OBU data buffer passed to parse_tile_list.
             # This is tricky. Let's defer the actual data copying to the parse_tile_list function.
             # This class will be instantiated there.
            self.coded_tile_data: bytes = obu_data_payload # Placeholder, will be sliced correctly by parse_tile_list
        else:
            self.coded_tile_data: bytes = b""

    def __repr__(self) -> str:
        return f"TileListEntry(anchor_idx={self.anchor_frame_idx}, row={self.anchor_tile_row}, col={self.anchor_tile_col}, size={len(self.coded_tile_data)})"


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

        self.FrameWidth: int = c_seq_header.FrameWidth
        self.FrameHeight: int = c_seq_header.FrameHeight
        self.OrderHintBits: int = c_seq_header.OrderHintBits

    def __repr__(self) -> str:
        return (
            f"SequenceHeader(seq_profile={self.seq_profile}, still_picture={self.still_picture}, "
            f"max_frame_width={self.max_frame_width_minus_1+1}, max_frame_height={self.max_frame_height_minus_1+1}, "
            f"op_points={self.operating_points_cnt_minus_1+1})"
        )

class FrameHeader:
    def __init__(self, c_fh: _c_wrapper.OBPFrameHeader, sequence_header: SequenceHeader):
        self._c_frame_header = c_fh # Keep ref for other functions
        self._py_sequence_header = sequence_header # Keep ref for context

        self.show_existing_frame: int = c_fh.show_existing_frame
        self.frame_to_show_map_idx: int = c_fh.frame_to_show_map_idx
        self.temporal_point_info_present: int = c_fh.temporal_point_info_present
        self.frame_presentation_time: int = c_fh.frame_presentation_time
        self.display_frame_id: int = c_fh.display_frame_id
        self.frame_type: int = c_fh.frame_type # OBPOBPFrameType enum
        self.show_frame: int = c_fh.show_frame
        self.showable_frame: int = c_fh.showable_frame
        self.error_resilient_mode: int = c_fh.error_resilient_mode
        self.disable_cdf_update: int = c_fh.disable_cdf_update
        self.allow_screen_content_tools: int = c_fh.allow_screen_content_tools
        self.force_integer_mv: int = c_fh.force_integer_mv
        self.current_frame_id: int = c_fh.current_frame_id
        self.frame_size_override_flag: int = c_fh.frame_size_override_flag
        self.order_hint: int = c_fh.order_hint
        self.primary_ref_frame: int = c_fh.primary_ref_frame
        self.refresh_frame_flags: int = c_fh.refresh_frame_flags
        self.ref_order_hint: list[int] = _c_array_to_list(c_fh.ref_order_hint) # REFS_PER_FRAME (8)

        self.allow_high_precision_mv: int = c_fh.allow_high_precision_mv
        self.interpolation_filter: InterpolationFilter = InterpolationFilter(c_fh.interpolation_filter)
        self.is_motion_mode_switchable: int = c_fh.is_motion_mode_switchable
        self.use_ref_frame_mvs: int = c_fh.use_ref_frame_mvs
        self.disable_frame_end_update_cdf: int = c_fh.disable_frame_end_update_cdf
        self.allow_intrabc: int = c_fh.allow_intrabc
        self.palette_mode_enabled: int = c_fh.palette_mode_enabled

        self.frame_width_minus_1: int = c_fh.frame_width_minus_1
        self.frame_height_minus_1: int = c_fh.frame_height_minus_1
        self.superres_params: SuperresParams = SuperresParams(c_fh.superres_params)
        self.render_width_minus_1: int = c_fh.render_width_minus_1
        self.render_height_minus_1: int = c_fh.render_height_minus_1

        self.FrameWidth: int = c_fh.FrameWidth
        self.FrameHeight: int = c_fh.FrameHeight
        self.MiCols: int = c_fh.MiCols
        self.MiRows: int = c_fh.MiRows

        self.tile_info: TileInfo = TileInfo(c_fh.tile_info)
        self.quantization_params: QuantizationParams = QuantizationParams(c_fh.quantization_params)
        self.segmentation_params: SegmentationParams = SegmentationParams(c_fh.segmentation_params)
        self.delta_q_params: DeltaQParams = DeltaQParams(c_fh.delta_q_params)
        self.delta_lf_params: DeltaLFParams = DeltaLFParams(c_fh.delta_lf_params)
        self.loop_filter_params: LoopFilterParams = LoopFilterParams(c_fh.loop_filter_params)
        self.cdef_params: CdefParams = CdefParams(c_fh.cdef_params)
        self.lr_params: LrParams = LrParams(c_fh.lr_params)

        self.skip_mode_present: int = c_fh.skip_mode_present
        self.reference_select: int = c_fh.reference_select
        self.allow_warped_motion: int = c_fh.allow_warped_motion
        self.reduced_tx_set: int = c_fh.reduced_tx_set
        
        self.global_motion_params: list[GlobalMotionParams] = []
        for i in range(8): # TOTAL_REFS_PER_FRAME
            gm_type = c_fh.global_motion_params[i].gm_type[0] # gm_type is an array of 1 in C struct for some reason
            gm_params_for_ref = _c_array_to_list(c_fh.global_motion_params[i].gm_params[0]) # gm_params is [1][6] in C struct
            self.global_motion_params.append(GlobalMotionParams(gm_type, gm_params_for_ref))

        if sequence_header.film_grain_params_present:
            self.film_grain_params: FilmGrainParameters | None = FilmGrainParameters(c_fh.film_grain_params)
        else:
            self.film_grain_params = None
        
        self.large_scale_tile: int = c_fh.large_scale_tile

    def __repr__(self) -> str:
        return (f"FrameHeader(type={self.frame_type}, width={self.FrameWidth}, height={self.FrameHeight}, "
                f"show_frame={self.show_frame}, order_hint={self.order_hint})")

class TileGroup:
    def __init__(self, c_tg: _c_wrapper.OBPTileGroup):
        self._c_tile_group = c_tg
        self.NumTiles: int = c_tg.NumTiles
        self.obu_size: int = c_tg.obu_size # Size of this specific Tile Group OBU
        
        # data points to start of tile group data within the OBU payload.
        # The C parser sets this pointer relative to the OBU buffer it received.
        # The actual tile data starts at `obu_data_offset_within_tile_group_obu`
        # within the *original* OBU payload passed to `parse_tile_group` or `parse_frame`.
        # `c_tg.data` should point to this location. `c_tg.obu_size` is the size of the OBU itself.
        # The actual raw tile data that this tile group represents is a sub-segment of the OBU.
        # The `obuparse.c` sets `tile_group->data` to `buf + header_size` and
        # `tile_group->obu_size` to `obu_size` (which is header + payload of the tile group OBU).
        # `tile_group->obu_data_offset_within_tile_group_obu` is the size of the tile group header.
        # So, the actual tile data bytes are from `c_tg.data + c_tg.obu_data_offset_within_tile_group_obu`
        # for a length of `c_tg.obu_size - c_tg.obu_data_offset_within_tile_group_obu`.

        tile_data_start_offset = c_tg.obu_data_offset_within_tile_group_obu
        tile_data_len = c_tg.obu_size - tile_data_start_offset
        if c_tg.data and tile_data_len > 0:
            self.data: bytes = ctypes.string_at(ctypes.cast(c_tg.data, ctypes.POINTER(ctypes.c_char)) + tile_data_start_offset, tile_data_len)
        else:
            self.data: bytes = b""
            
        self.tg_start: int = c_tg.tg_start
        self.tg_end: int = c_tg.tg_end
        
    def __repr__(self) -> str:
        return f"TileGroup(num_tiles={self.NumTiles}, tg_start={self.tg_start}, tg_end={self.tg_end}, data_len={len(self.data)})"


class Metadata:
    def __init__(self, c_meta: _c_wrapper.OBPMetadata, obu_payload: bytes):
        self._c_metadata = c_meta
        self.type: int = c_meta.type # OBPMetadataType enum
        self.obu_size: int = c_meta.obu_size # Size of the metadata OBU itself

        # `c_meta.data` points to the start of the OBU payload.
        # The specific metadata structs within `c_meta` (e.g., `metadata_itut_t35`)
        # will have pointers (`itu_t_t35_payload_bytes`) that also point *within* this same `obu_payload`.
        # The Python helper classes (MetadataITUTT35 etc.) will use these pointers relative to `obu_payload`
        # or use the absolute pointers if `ctypes.string_at` can handle them directly.
        # The `obuparse.c` sets `metadata_obj->xxx.payload_bytes = buf + offset_to_payload_bytes_in_obu`.
        # So, `ctypes.string_at` on these pointers should work directly.

        self.metadata_itut_t35: MetadataITUTT35 | None = None
        self.metadata_hdr_cll: MetadataHDRCLL | None = None
        self.metadata_hdr_mdcv: MetadataHDRMDCV | None = None
        self.metadata_scalability: MetadataScalability | None = None
        self.metadata_timecode: MetadataTimecode | None = None
        self.unregistered: MetadataUnregistered | None = None

        if self.type == _c_wrapper.OBP_METADATA_TYPE_ITUT_T35:
            self.metadata_itut_t35 = MetadataITUTT35(c_meta.metadata_itut_t35)
        elif self.type == _c_wrapper.OBP_METADATA_TYPE_HDR_CLL:
            self.metadata_hdr_cll = MetadataHDRCLL(c_meta.metadata_hdr_cll)
        elif self.type == _c_wrapper.OBP_METADATA_TYPE_HDR_MDCV:
            self.metadata_hdr_mdcv = MetadataHDRMDCV(c_meta.metadata_hdr_mdcv)
        elif self.type == _c_wrapper.OBP_METADATA_TYPE_SCALABILITY:
            self.metadata_scalability = MetadataScalability(c_meta.metadata_scalability)
        elif self.type == _c_wrapper.OBP_METADATA_TYPE_TIMECODE:
            self.metadata_timecode = MetadataTimecode(c_meta.metadata_timecode)
        # Check for OBP_METADATA_TYPE_UNREGISTERED from _c_wrapper
        elif self.type == getattr(_c_wrapper, 'OBP_METADATA_TYPE_UNREGISTERED', -1): # Use getattr for safety
            self.unregistered = MetadataUnregistered(c_meta.unregistered)
        
        # Raw data of the metadata OBU's payload (after OBU header)
        # c_meta.data points to the start of the OBU's content (after OBU header)
        # c_meta.obu_size is the size of the OBU's content (matching len(obu_payload))
        if c_meta.data and self.obu_size > 0:
            self.data: bytes = ctypes.string_at(c_meta.data, self.obu_size)
        else:
            self.data: bytes = b""


    def __repr__(self) -> str:
        return f"Metadata(type={self.type}, obu_size={self.obu_size}, specific_metadata_present={self._get_specific_metadata_repr()})"

    def _get_specific_metadata_repr(self) -> str:
        if self.metadata_itut_t35: return repr(self.metadata_itut_t35)
        if self.metadata_hdr_cll: return repr(self.metadata_hdr_cll)
        if self.metadata_hdr_mdcv: return repr(self.metadata_hdr_mdcv)
        if self.metadata_scalability: return repr(self.metadata_scalability)
        if self.metadata_timecode: return repr(self.metadata_timecode)
        if self.unregistered: return repr(self.unregistered)
        return "None"

class TileList:
    def __init__(self, c_tl: _c_wrapper.OBPTileList, obu_payload: bytes):
        self._c_tile_list = c_tl
        self.output_frame_width_in_tiles: int = c_tl.output_frame_width_in_tiles
        self.output_frame_height_in_tiles: int = c_tl.output_frame_height_in_tiles
        self.tile_count_minus_1: int = c_tl.tile_count_minus_1
        
        self.tile_list_entries: list[TileListEntry] = []
        if c_tl.tile_list_entries:
            num_entries = self.tile_count_minus_1 + 1
            for i in range(num_entries):
                c_entry = c_tl.tile_list_entries[i]
                entry_data_size = c_entry.tile_data_size_minus_1 + 1
                
                # tile_specific_data in C is a pointer into the OBU payload.
                # We need to find its offset from the start of obu_payload.
                # This requires knowing the address of obu_payload's buffer and c_entry.tile_specific_data.
                # This is complex. A simpler way if obuparse.c guarantees these pointers are valid *within* the
                # OBU payload it was given:
                # The C parser (obp_parse_tile_list) sets `entry->tile_specific_data = buf + offset;`
                # where `buf` is the start of the OBU payload.
                # So, `c_entry.tile_specific_data` is an absolute pointer.
                # `ctypes.addressof(ctypes.c_char.from_buffer(obu_payload,0))` gives start of our buffer.
                # `ctypes.addressof(c_entry.tile_specific_data.contents)` if it's POINTER(c_uint8)
                # This is getting too complex. The C code should ideally give offsets or the Python wrapper
                # should be careful.
                # Let's assume `c_entry.tile_specific_data` is already a usable pointer that `string_at` can handle.
                # This implies the C library correctly manages these pointers to be valid for the lifetime
                # of the `obu_payload` bytes object, or they are offsets.
                # The `obuparse.c` sets `entry->tile_specific_data = local_buf_ptr;` where `local_buf_ptr` iterates
                # through the input buffer. So `ctypes.string_at` should work directly on `c_entry.tile_specific_data`.
                
                py_entry = TileListEntry(c_entry, b"") # Temp empty bytes
                if c_entry.tile_specific_data and entry_data_size > 0:
                    py_entry.coded_tile_data = ctypes.string_at(c_entry.tile_specific_data, entry_data_size)
                else:
                    py_entry.coded_tile_data = b""
                self.tile_list_entries.append(py_entry)

    def __repr__(self) -> str:
        return f"TileList(width_tiles={self.output_frame_width_in_tiles}, height_tiles={self.output_frame_height_in_tiles}, count={self.tile_count_minus_1+1})"


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
    # Check if obp_get_next_obu has 9 arguments (including spatial_id)
    # This is a runtime check, assuming _c_wrapper might not be updated yet.
    # A more robust solution is to ensure _c_wrapper.py is correct first.
    takes_spatial_id_arg = len(c_lib.obp_get_next_obu.argtypes) == 9


    data_len = len(data)
    current_pos = 0
    
    while current_pos < data_len:
        obu_type_cval = _c_wrapper.c_int_t()
        obu_offset_cval = _c_wrapper.c_ptrdiff_t() 
        obu_size_cval = _c_wrapper.c_size_t()    
        obu_has_size_field_cval = _c_wrapper.c_int_t()
        temporal_id_cval = _c_wrapper.c_int_t()
        spatial_id_cval = _c_wrapper.c_int_t(0) # Initialize to 0
        
        err_struct = _c_wrapper.OBPError()

        buffer_slice_ptr = ctypes.cast(ctypes.byref(ctypes.c_char.from_buffer(data, current_pos)), 
                                      ctypes.POINTER(_c_wrapper.c_uint8_t))
        remaining_data_size = data_len - current_pos

        if takes_spatial_id_arg:
             ret_code = c_lib.obp_get_next_obu(
                buffer_slice_ptr, remaining_data_size,
                ctypes.byref(obu_type_cval), ctypes.byref(obu_offset_cval),
                ctypes.byref(obu_size_cval), ctypes.byref(obu_has_size_field_cval),
                ctypes.byref(temporal_id_cval), ctypes.byref(spatial_id_cval), # Pass spatial_id
                ctypes.byref(err_struct)
            )
        else: # Fallback if _c_wrapper.py's obp_get_next_obu is old (8 args)
            # This path should ideally not be needed if _c_wrapper is correctly updated.
            # Forcing an error or logging a warning might be better.
            # For now, call the 8-arg version and spatial_id remains 0.
            # This part should be removed once _c_wrapper.py is confirmed to have spatial_id.
            temp_argtypes = c_lib.obp_get_next_obu.argtypes
            c_lib.obp_get_next_obu.argtypes = temp_argtypes[:7] + temp_argtypes[8:] # Remove spatial_id arg
            ret_code = c_lib.obp_get_next_obu(
                buffer_slice_ptr, remaining_data_size,
                ctypes.byref(obu_type_cval), ctypes.byref(obu_offset_cval),
                ctypes.byref(obu_size_cval), ctypes.byref(obu_has_size_field_cval),
                ctypes.byref(temporal_id_cval), # No spatial_id here
                ctypes.byref(err_struct)
            )
            c_lib.obp_get_next_obu.argtypes = temp_argtypes # Restore


        if ret_code != 0:
            error_message = f"Failed to get next OBU (code {ret_code})"
            if err_struct.error:
                error_message += f": {err_struct.error.decode('utf-8', errors='replace')}"
                if hasattr(c_lib, 'obp_free_error_string'):
                    _c_wrapper.free_obp_error_string(err_struct)
            
            if remaining_data_size < 2 and ret_code !=0 :
                break 
            raise OBUParseError(error_message)

        obu_header_size = obu_offset_cval.value
        obu_payload_size = obu_size_cval.value
        total_obu_length = obu_header_size + obu_payload_size
        
        if total_obu_length == 0 and ret_code == 0:
            break

        payload_start_abs = current_pos + obu_header_size
        payload_end_abs = payload_start_abs + obu_payload_size
        
        if payload_end_abs > data_len:
            raise OBUParseError(
                f"OBU payload extends beyond data buffer. Start: {payload_start_abs}, End: {payload_end_abs}, Data Len: {data_len}. "
                f"OBU Type: {obu_type_cval.value}, Header Size: {obu_header_size}, Payload Size: {obu_payload_size}"
            )
            
        obu_payload_bytes = data[payload_start_abs:payload_end_abs]
        py_obu_type = _PY_OBP_OBU_TYPE_MAP.get(obu_type_cval.value, obu_type_cval.value)

        yield (
            py_obu_type,
            temporal_id_cval.value,
            spatial_id_cval.value, # Yield the value from C
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
