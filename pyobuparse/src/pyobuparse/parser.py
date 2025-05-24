"""
Python parser for AV1 Object Bitstream Units (OBUs).

This module provides classes and functions to parse AV1 OBU data,
leveraging a C library (`obuparse`) for the low-level parsing tasks.
It defines Pythonic representations of OBU structures and offers
functions to parse different OBU types.
"""
import ctypes
from typing import Sequence, Tuple, Any # Added Sequence, Tuple, Any
from . import _c_wrapper

# --- Custom Exception ---
class OBUParseError(Exception):
    """
    Custom exception raised for errors encountered during OBU parsing.

    Attributes:
        message (str): A human-readable message describing the error.
    """
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
    """
    Represents the timing information from an AV1 Sequence Header OBU.

    Corresponds to the `timing_info` struct in the AV1 specification.

    Args:
        c_timing_info (_c_wrapper.OBPTimingInfo): The ctypes structure
            containing the C-level timing information.

    Attributes:
        num_units_in_display_tick (int): Number of time units of a clock operating at
            `time_scale` frequency that correspond to one increment of a display clock tick.
        time_scale (int): The number of time units that pass in one second.
        equal_picture_interval (int): Flag indicating if picture intervals are equal.
            A value of 1 indicates that `num_ticks_per_picture_minus_1` is not present
            and implies a value of 0 for `num_ticks_per_picture_minus_1`.
        num_ticks_per_picture_minus_1 (int): Specifies the number of display clock ticks
            that shall occur between the output time of two consecutive pictures in
            the coded video sequence.
    """
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
    """
    Represents the decoder model information from an AV1 Sequence Header OBU.

    Corresponds to the `decoder_model_info` struct in the AV1 specification.

    Args:
        c_decoder_model_info (_c_wrapper.OBPDecoderModelInfo): The ctypes structure
            containing the C-level decoder model information.

    Attributes:
        buffer_delay_length_minus_1 (int): Specifies the length of the
            `decoder_buffer_delay` and `encoder_buffer_delay` syntax elements, in bits.
        num_units_in_decoding_tick (int): Number of time units of a clock operating at
            `time_scale` frequency that correspond to one increment of a decoding clock tick.
        buffer_removal_time_length_minus_1 (int): Specifies the length of the
            `buffer_removal_time` syntax element in `frame_header_obu`, in bits.
        frame_presentation_time_length_minus_1 (int): Specifies the length of the
            `frame_presentation_time` syntax element in `frame_header_obu`, in bits.
    """
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
    """
    Represents operating point specific decoder model parameters.

    Corresponds to the `operating_parameters_info` struct in the AV1 specification.

    Args:
        c_op_info (_c_wrapper.OBPOperatingParametersInfo): The ctypes structure
            containing the C-level operating parameters information.

    Attributes:
        decoder_buffer_delay (int): Specifies, for the current operating point, the
             बिट-stream buffer size of the HRD.
        encoder_buffer_delay (int): Specifies, for the current operating point, the
            maximum size of the encoder's bitstream buffer.
        low_delay_mode_flag (int): If equal to 1, indicates that the current
            operating point is a low-delay operating point. Otherwise, it is not.
    """
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
        """
        Initializes the ColorConfig object from a C-level OBPColorConfig struct.

        Args:
            c_color_config (_c_wrapper.OBPColorConfig): The ctypes structure
                from the C parser.
        """
        self.high_bitdepth: int = c_color_config.high_bitdepth
        self.twelve_bit: int = c_color_config.twelve_bit
        self.BitDepth: int = c_color_config.BitDepth 
        self.mono_chrome: int = c_color_config.mono_chrome
        self.NumPlanes: int = c_color_config.NumPlanes 
        self.color_description_present_flag: int = c_color_config.color_description_present_flag
        
        self.color_primaries: _c_wrapper.OBPColorPrimaries = _c_wrapper.OBPColorPrimaries(c_color_config.color_primaries)
        self.transfer_characteristics: _c_wrapper.OBPTransferCharacteristics = _c_wrapper.OBPTransferCharacteristics(c_color_config.transfer_characteristics)
        self.matrix_coefficients: _c_wrapper.OBPMatrixCoefficients = _c_wrapper.OBPMatrixCoefficients(c_color_config.matrix_coefficients)
        
        self.color_range: int = c_color_config.color_range
        self.subsampling_x: int = c_color_config.subsampling_x 
        self.subsampling_y: int = c_color_config.subsampling_y 
        
        self.chroma_sample_position: _c_wrapper.OBPChromaSamplePosition = _c_wrapper.OBPChromaSamplePosition(c_color_config.chroma_sample_position)
        self.separate_uv_delta_q: int = c_color_config.separate_uv_delta_q

    def __repr__(self) -> str:
        return (
            f"ColorConfig(BitDepth={self.BitDepth}, NumPlanes={self.NumPlanes}, "
            f"color_primaries={self.color_primaries.name if isinstance(self.color_primaries, _c_wrapper.enum.IntEnum) else self.color_primaries}, "
            f"subsampling_x={self.subsampling_x}, subsampling_y={self.subsampling_y}, "
            # (repr was too long, shortened for brevity)
            f"..., chroma_sample_position={self.chroma_sample_position.name if isinstance(self.chroma_sample_position, _c_wrapper.enum.IntEnum) else self.chroma_sample_position})"
        )

# --- Helper Python classes for FrameHeader nested structures ---

class SuperresParams:
    """
    Represents super-resolution parameters from an AV1 Frame Header.

    Corresponds to the `superres_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPSuperresParams): The ctypes structure from C.

    Attributes:
        use_superres (int): Indicates if super-resolution is used for this frame.
        coded_denom (int): The denominator for upscaling factor calculation.
        superres_upscaled_width (int): The width of the frame after upscaling.
            (Derived by C parser, not directly in C OBPFrameHeader.superres_params)
        superres_upscaled_height (int): The height of the frame after upscaling.
            (Derived by C parser, not directly in C OBPFrameHeader.superres_params)
    """
    def __init__(self, c_params: _c_wrapper.OBPSuperresParams):
        self.use_superres: int = c_params.use_superres
        self.coded_denom: int = c_params.coded_denom
        # These upscaled_width/height are not in C OBPFrameHeader.superres_params
        # but are in the _c_wrapper.OBPSuperresParams. They are derived by C code.
        self.superres_upscaled_width: int = c_params.superres_upscaled_width 
        self.superres_upscaled_height: int = c_params.superres_upscaled_height
    def __repr__(self) -> str:
        return f"SuperresParams(use_superres={self.use_superres}, coded_denom={self.coded_denom}, upscaled_width={self.superres_upscaled_width}, upscaled_height={self.superres_upscaled_height})"

class InterpolationFilter:
    """
    Represents interpolation filter parameters from an AV1 Frame Header.

    Corresponds to the `interpolation_filter` struct in the AV1 specification.

    Args:
        c_filter (_c_wrapper.OBPInterpolationFilter): The ctypes structure from C.

    Attributes:
        is_filter_switchable (int): Indicates if the interpolation filter can be switched.
        interpolation_filter (int): Specifies the type of interpolation filter.
    """
    def __init__(self, c_filter: _c_wrapper.OBPInterpolationFilter):
        self.is_filter_switchable: int = c_filter.is_filter_switchable # Added
        self.interpolation_filter: int = c_filter.interpolation_filter # Renamed from value
    def __repr__(self) -> str:
        return f"InterpolationFilter(switchable={self.is_filter_switchable}, filter={self.interpolation_filter})"

class TileInfo:
    """
    Represents tile information from an AV1 Frame Header.

    Note: The fields in this Python class are based on the `_c_wrapper.OBPTileInfo`
    structure, which itself is based on fields populated by the C parser, some of
    which are derived or structured differently than the `tile_info` sub-struct
    within `OBPFrameHeader` in `obuparse.h`.

    Args:
        c_info (_c_wrapper.OBPTileInfo): The ctypes structure from C.

    Attributes:
        uniform_tile_spacing_flag (int): Indicates if tile spacing is uniform.
        MiColStarts (list[int]): Starting column positions of tiles in MI units.
        MiRowStarts (list[int]): Starting row positions of tiles in MI units.
        width_in_sbs_minus_1 (list[int]): Width of each tile column in superblocks minus 1.
        height_in_sbs_minus_1 (list[int]): Height of each tile row in superblocks minus 1.
        context_update_tile_id (int): Specifies the tile that is used for
            updating the CDFs.
        tile_cols (int): Number of tile columns.
        tile_rows (int): Number of tile rows.
    """
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
    """
    Represents quantization parameters from an AV1 Frame Header.

    Corresponds to the `quantization_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPQuantizationParams): The ctypes structure from C.

    Attributes:
        base_q_idx (int): The base quantization index.
        DeltaQYDc (int): The DC quantization parameter for the Y plane.
        DeltaQUDc (int): The DC quantization parameter for the U plane.
        DeltaQUAc (int): The AC quantization parameter for the U plane.
        DeltaQVDc (int): The DC quantization parameter for the V plane.
        DeltaQVAc (int): The AC quantization parameter for the V plane.
        diff_uv_delta (int): Indicates if separate delta quantization is used for UV planes.
        using_qmatrix (int): Indicates if a quantizer matrix is used.
        qm_y (int): Quantizer matrix level for Y plane.
        qm_u (int): Quantizer matrix level for U plane.
        qm_v (int): Quantizer matrix level for V plane.
    """
    def __init__(self, c_params: _c_wrapper.OBPQuantizationParams):
        self.base_q_idx: int = c_params.base_q_idx
        self.DeltaQYDc: int = c_params.DeltaQYDc
        self.DeltaQUDc: int = c_params.DeltaQUDc
        self.DeltaQUAc: int = c_params.DeltaQUAc
        self.DeltaQVDc: int = c_params.DeltaQVDc
        self.DeltaQVAc: int = c_params.DeltaQVAc
        self.diff_uv_delta: int = c_params.diff_uv_delta # Added
        self.using_qmatrix: int = c_params.using_qmatrix
        self.qm_y: int = c_params.qm_y
        self.qm_u: int = c_params.qm_u
        self.qm_v: int = c_params.qm_v
    def __repr__(self) -> str:
        return f"QuantizationParams(base_q_idx={self.base_q_idx}, diff_uv_delta={self.diff_uv_delta}, using_qmatrix={self.using_qmatrix}, ...)"

class SegmentationParams:
    """
    Represents segmentation parameters from an AV1 Frame Header.

    Corresponds to the `segmentation_params` struct in the AV1 specification.
    The Python wrapper may include additional fields like `feature_enabled` and
    `feature_data` if populated by the C parser based on the main flags.

    Args:
        c_params (_c_wrapper.OBPSegmentationParams): The ctypes structure from C.

    Attributes:
        segmentation_enabled (int): Indicates if segmentation is enabled.
        segmentation_update_map (int): Indicates if the segmentation map is updated.
        segmentation_temporal_update (int): Indicates if temporal updates to the
            segmentation map are used.
        segmentation_update_data (int): Indicates if new segmentation data is provided.
        feature_enabled (list[list[int]]): For each segment and feature, indicates if
            the feature is enabled. (Often derived/populated by parser logic).
        feature_data (list[list[int]]): Data for each segment feature.
            (Often derived/populated by parser logic).
    """
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
    """
    Represents delta quantization parameters from an AV1 Frame Header.

    Corresponds to the `delta_q_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPDeltaQParams): The ctypes structure from C.

    Attributes:
        delta_q_present (int): Indicates if delta quantization is present.
        delta_q_res (int): The resolution of the delta quantization values.
    """
    def __init__(self, c_params: _c_wrapper.OBPDeltaQParams):
        self.delta_q_present: int = c_params.delta_q_present
        self.delta_q_res: int = c_params.delta_q_res
    def __repr__(self) -> str:
        return f"DeltaQParams(present={self.delta_q_present}, res={self.delta_q_res})"

class DeltaLFParams:
    """
    Represents delta loop filter parameters from an AV1 Frame Header.

    Corresponds to the `delta_lf_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPDeltaLFParams): The ctypes structure from C.

    Attributes:
        delta_lf_present (int): Indicates if delta loop filter values are present.
        delta_lf_res (int): The resolution of the delta loop filter values.
        delta_lf_multi (int): Indicates if separate delta loop filter values are
            present for horizontal luma, vertical luma, U, and V edges.
    """
    def __init__(self, c_params: _c_wrapper.OBPDeltaLFParams):
        self.delta_lf_present: int = c_params.delta_lf_present
        self.delta_lf_res: int = c_params.delta_lf_res
        self.delta_lf_multi: int = c_params.delta_lf_multi
    def __repr__(self) -> str:
        return f"DeltaLFParams(present={self.delta_lf_present}, res={self.delta_lf_res}, multi={self.delta_lf_multi})"

class LoopFilterParams:
    """
    Represents loop filter parameters from an AV1 Frame Header.

    Corresponds to the `loop_filter_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPLoopFilterParams): The ctypes structure from C.

    Attributes:
        loop_filter_level (list[int]): Loop filter strength values for different planes/directions.
        loop_filter_sharpness (int): Loop filter sharpness level.
        loop_filter_delta_enabled (int): Indicates if loop filter delta adjustments are enabled.
        update_ref_delta (list[int]): Indicates which `loop_filter_ref_deltas` are updated.
        loop_filter_ref_deltas (list[int]): Loop filter strength adjustments for reference frames.
        update_mode_delta (list[int]): Indicates which `loop_filter_mode_deltas` are updated.
        loop_filter_mode_deltas (list[int]): Loop filter strength adjustments for modes.
    """
    def __init__(self, c_params: _c_wrapper.OBPLoopFilterParams):
        self.loop_filter_level: list[int] = _c_array_to_list(c_params.loop_filter_level)
        self.loop_filter_sharpness: int = c_params.loop_filter_sharpness
        self.loop_filter_delta_enabled: int = c_params.loop_filter_delta_enabled
        self.update_ref_delta: list[int] = _c_array_to_list(c_params.update_ref_delta) # Added
        self.loop_filter_ref_deltas: list[int] = _c_array_to_list(c_params.loop_filter_ref_deltas)
        self.update_mode_delta: list[int] = _c_array_to_list(c_params.update_mode_delta) # Added
        self.loop_filter_mode_deltas: list[int] = _c_array_to_list(c_params.loop_filter_mode_deltas)
    def __repr__(self) -> str:
        return f"LoopFilterParams(level_y_v={self.loop_filter_level[1]}, sharpness={self.loop_filter_sharpness}, delta_enabled={self.loop_filter_delta_enabled}, ...)"

class CdefParams:
    """
    Represents Constrained Directional Enhancement Filter (CDEF) parameters.

    Corresponds to the `cdef_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPCdefParams): The ctypes structure from C.

    Attributes:
        cdef_damping_minus_3 (int): CDEF damping value minus 3.
        cdef_bits (int): Number of bits used to specify CDEF strength.
        cdef_y_pri_strength (list[int]): Primary CDEF strength for Y plane.
        cdef_y_sec_strength (list[int]): Secondary CDEF strength for Y plane.
        cdef_uv_pri_strength (list[int]): Primary CDEF strength for UV planes.
        cdef_uv_sec_strength (list[int]): Secondary CDEF strength for UV planes.
    """
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
    """
    Represents Loop Restoration Filter parameters.

    Corresponds to the `lr_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPLrParams): The ctypes structure from C.

    Attributes:
        lr_type (list[int]): Type of loop restoration filter for each plane.
        lr_unit_shift (int): Subsampling shift for the loop restoration filter.
        lr_uv_shift (int): Subsampling shift for UV planes if `lr_type` indicates Wiener filter.
    """
    def __init__(self, c_params: _c_wrapper.OBPLrParams):
        self.lr_type: list[int] = _c_array_to_list(c_params.lr_type)
        self.lr_unit_shift: int = c_params.lr_unit_shift
        self.lr_uv_shift: int = c_params.lr_uv_shift
    def __repr__(self) -> str:
        return f"LrParams(type_y={self.lr_type[0]}, unit_shift={self.lr_unit_shift}, uv_shift={self.lr_uv_shift})"

class GlobalMotionParams:
    """
    Represents global motion parameters for a single reference frame.

    Args:
        c_gm_entry (_c_wrapper.OBPGlobalMotionParams): The ctypes structure for a single
            global motion parameter set from C.

    Attributes:
        gm_type (int): The type of global motion model.
        gm_params (list[int]): The parameters for the global motion model (typically 6).
    """
    def __init__(self, c_gm_entry: _c_wrapper.OBPGlobalMotionParams): # Changed input to be a C struct entry
        self.gm_type: int = c_gm_entry.gm_type
        self.gm_params: list[int] = _c_array_to_list(c_gm_entry.gm_params) # Should be 6 elements
    def __repr__(self) -> str:
        return f"GlobalMotionParams(type={self.gm_type}, params={self.gm_params[:2]}...)"

class FilmGrainParameters: # For OBPFilmGrainParameters
    """
    Represents film grain parameters from an AV1 Frame Header.

    Corresponds to the `film_grain_params` struct in the AV1 specification.

    Args:
        c_params (_c_wrapper.OBPFilmGrainParameters): The ctypes structure from C.

    Attributes:
        apply_grain (int): Indicates if film grain should be applied.
        grain_seed (int): Starting seed for the film grain synthesis process.
        update_grain (int): Indicates if the film grain parameters are updated in this frame.
        film_grain_params_ref_idx (int): Reference index for film grain parameters.
        num_y_points (int): Number of points for the Y plane scaling function.
        point_y_value (list[int]): Y component values for scaling function points.
        point_y_scaling (list[int]): Scaling values for Y component points.
        chroma_scaling_from_luma (int): Indicates if chroma scaling is derived from luma.
        num_cb_points (int): Number of points for the Cb plane scaling function.
        point_cb_value (list[int]): Cb component values for scaling function points.
        point_cb_scaling (list[int]): Scaling values for Cb component points.
        num_cr_points (int): Number of points for the Cr plane scaling function.
        point_cr_value (list[int]): Cr component values for scaling function points.
        point_cr_scaling (list[int]): Scaling values for Cr component points.
        grain_scaling_minus_8 (int): Grain scaling factor minus 8.
        ar_coeff_lag (int): Auto-regressive coefficient lag.
        ar_coeffs_y_plus_128 (list[int]): AR coefficients for Y plane, offset by 128.
        ar_coeffs_cb_plus_128 (list[int]): AR coefficients for Cb plane, offset by 128.
        ar_coeffs_cr_plus_128 (list[int]): AR coefficients for Cr plane, offset by 128.
        ar_coeff_shift_minus_6 (int): Bit shift for AR coefficients minus 6.
        grain_scale_shift (int): Shift value for grain scaling.
        cb_mult (int): Cb multiplier for chroma scaling.
        cb_luma_mult (int): Cb luma multiplier for chroma scaling.
        cb_offset (int): Cb offset for chroma scaling.
        cr_mult (int): Cr multiplier for chroma scaling.
        cr_luma_mult (int): Cr luma multiplier for chroma scaling.
        cr_offset (int): Cr offset for chroma scaling.
        overlap_flag (int): Indicates if overlap is applied between film grain blocks.
        clip_to_restricted_range (int): Indicates if output should be clipped to restricted range.
    """
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
    """
    Represents ITU-T T.35 metadata from an AV1 Metadata OBU.

    Args:
        c_meta (_c_wrapper.OBPMetadataITUTT35): The ctypes structure from C.

    Attributes:
        itu_t_t35_country_code (int): ITU-T T.35 country code.
        itu_t_t35_country_code_extension_byte (int): Extension byte for country code.
        itu_t_t35_payload_bytes (bytes): The payload of the T.35 metadata.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataITUTT35):
        self.itu_t_t35_country_code: int = c_meta.itu_t_t35_country_code
        self.itu_t_t35_country_code_extension_byte: int = c_meta.itu_t_t35_country_code_extension_byte
        payload_size = c_meta.itu_t_t35_payload_bytes_size
        self.itu_t_t35_payload_bytes: bytes = ctypes.string_at(c_meta.itu_t_t35_payload_bytes, payload_size) if c_meta.itu_t_t35_payload_bytes and payload_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataITUTT35(country_code={self.itu_t_t35_country_code}, ext_byte={self.itu_t_t35_country_code_extension_byte}, payload_len={len(self.itu_t_t35_payload_bytes)})"

class MetadataHDRCLL:
    """
    Represents HDR Content Light Level information from an AV1 Metadata OBU.

    Args:
        c_meta (_c_wrapper.OBPMetadataHDRCLL): The ctypes structure from C.

    Attributes:
        max_cll (int): Maximum Content Light Level.
        max_fall (int): Maximum Frame-Average Light Level.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRCLL):
        self.max_cll: int = c_meta.max_cll
        self.max_fall: int = c_meta.max_fall
    def __repr__(self) -> str:
        return f"MetadataHDRCLL(max_cll={self.max_cll}, max_fall={self.max_fall})"

class MetadataHDRMDCV:
    """
    Represents HDR Mastering Display Color Volume information from an AV1 Metadata OBU.

    Args:
        c_meta (_c_wrapper.OBPMetadataHDRMDCV): The ctypes structure from C.

    Attributes:
        primary_chromaticity_x (list[int]): X coordinates of primary chromaticities.
        primary_chromaticity_y (list[int]): Y coordinates of primary chromaticities.
        white_point_chromaticity_x (int): X coordinate of white point chromaticity.
        white_point_chromaticity_y (int): Y coordinate of white point chromaticity.
        luminance_max (int): Maximum luminance.
        luminance_min (int): Minimum luminance.
    """
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
    """
    Represents the scalability structure within AV1 Scalability Metadata.

    Note: This wrapper includes fields parsed by the C library, which might be a
    subset of the full structure in the AV1 specification.

    Args:
        c_struct (_c_wrapper.OBPScalabilityStructure): The ctypes structure from C.

    Attributes:
        spatial_layers_cnt_minus_1 (int): Number of spatial layers minus 1.
        spatial_layer_dimensions_present_flag (int): Flag indicating if spatial layer
            dimensions are present.
        spatial_layer_description_present_flag (int): Flag indicating if spatial layer
            descriptions are present.
        temporal_group_description_present_flag (int): Flag indicating if temporal group
            descriptions are present.
        scalability_structure_reserved_3bits (int): Reserved bits.
    """
    def __init__(self, c_struct: _c_wrapper.OBPScalabilityStructure):
        self.spatial_layers_cnt_minus_1: int = c_struct.spatial_layers_cnt_minus_1
        self.spatial_layer_dimensions_present_flag: int = c_struct.spatial_layer_dimensions_present_flag
        self.spatial_layer_description_present_flag: int = c_struct.spatial_layer_description_present_flag
        self.temporal_group_description_present_flag: int = c_struct.temporal_group_description_present_flag
        self.scalability_structure_reserved_3bits: int = c_struct.scalability_structure_reserved_3bits
    def __repr__(self) -> str:
        return f"ScalabilityStructure(spatial_layers={self.spatial_layers_cnt_minus_1+1}, ...)"

class MetadataScalability:
    """
    Represents Scalability Metadata from an AV1 Metadata OBU.

    Args:
        c_meta (_c_wrapper.OBPMetadataScalability): The ctypes structure from C.

    Attributes:
        scalability_mode_idc (int): Scalability mode identifier.
        scalability_structure (ScalabilityStructure): Nested scalability structure information.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataScalability):
        self.scalability_mode_idc: int = c_meta.scalability_mode_idc
        self.scalability_structure: ScalabilityStructure = ScalabilityStructure(c_meta.scalability_structure)
    def __repr__(self) -> str:
        return f"MetadataScalability(mode_idc={self.scalability_mode_idc}, structure={self.scalability_structure})"

class MetadataTimecode:
    """
    Represents Timecode Metadata from an AV1 Metadata OBU.

    Args:
        c_meta (_c_wrapper.OBPMetadataTimecode): The ctypes structure from C.

    Attributes:
        counting_type (int): Type of time counting.
        full_timestamp_flag (int): Indicates if a full timestamp is present.
        discontinuity_flag (int): Indicates a discontinuity in timecode.
        cnt_dropped_flag (int): Indicates if frame counting was dropped.
        n_frames (int): Number of frames in the timecode.
        seconds_value (int): Seconds value.
        minutes_value (int): Minutes value.
        hours_value (int): Hours value.
        seconds_flag (int): Indicates if seconds value is present.
        minutes_flag (int): Indicates if minutes value is present.
        hours_flag (int): Indicates if hours value is present.
        time_offset_length (int): Length of the time offset value.
        time_offset_value (int): Time offset value.
    """
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
    """
    Represents Unregistered User Private Metadata from an AV1 Metadata OBU.

    This is used when the metadata type is not one of the known specific types
    and the C parser provides data in the 'unregistered' field.

    Args:
        c_meta (_c_wrapper.OBPMetadataUnregistered): The ctypes structure from C,
            corresponding to the `unregistered` field of `OBPMetadata`.

    Attributes:
        buf (bytes): The raw payload of the unregistered metadata.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataUnregistered):
        # self.uuid: bytes = bytes(c_meta.uuid) # uuid was removed from _c_wrapper.OBPMetadataUnregistered
        payload_size = c_meta.buf_size
        self.buf: bytes = ctypes.string_at(c_meta.buf, payload_size) if c_meta.buf and payload_size > 0 else b""
    def __repr__(self) -> str:
        return f"MetadataUnregistered(payload_len={len(self.buf)})"


# --- Helper Python classes for TileList OBU nested structures ---
class TileListEntry:
    """
    Represents a single entry in a Tile List OBU.

    Args:
        c_entry (_c_wrapper.OBPTileListEntry): The ctypes structure from C.
        obu_data_payload (bytes): The full payload of the OBU this tile entry
            belongs to. This is used by the constructor if `coded_tile_data`
            needs to be copied based on an offset within this payload.
            However, current implementation relies on `c_entry.tile_specific_data`
            being a direct pointer that `ctypes.string_at` can use.

    Attributes:
        anchor_frame_idx (int): Anchor frame index for this tile.
        anchor_tile_row (int): Anchor tile row for this tile.
        anchor_tile_col (int): Anchor tile column for this tile.
        tile_data_size_minus_1 (int): Size of the coded tile data minus 1.
        coded_tile_data (bytes): The actual coded tile data.
    """
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
    """
    Represents a parsed AV1 Sequence Header OBU.

    This class provides a Pythonic interface to the data contained in a
    Sequence Header OBU, as defined by the AV1 specification. It is initialized
    from a C-level `OBPSequenceHeader` struct populated by the C parser.

    Args:
        c_seq_header (_c_wrapper.OBPSequenceHeader): The ctypes structure
            from the C parser containing the sequence header data.

    Attributes:
        seq_profile (int): Indicates the AV1 profile (0, 1, or 2).
        still_picture (int): If 1, indicates that the video is a still picture.
        reduced_still_picture_header (int): If 1, indicates that a reduced still
            picture header is used.
        timing_info_present_flag (int): If 1, `timing_info` is present.
        timing_info (TimingInfo | None): Timing information for the sequence. `None` if not present.
        decoder_model_info_present_flag (int): If 1, `decoder_model_info` is present.
        decoder_model_info (DecoderModelInfo | None): Decoder model information. `None` if not present.
        initial_display_delay_present_flag (int): If 1, initial display delay information is present.
        operating_points_cnt_minus_1 (int): Number of operating points minus 1. There are
            `operating_points_cnt_minus_1 + 1` operating points in total.
        operating_point_idc (list[int]): List of IDC (Identification Code) for each operating point.
            Length is `operating_points_cnt_minus_1 + 1`.
        seq_level_idx (list[int]): List of sequence level indices (e.g., 2.0, 3.1) for each
            operating point. Length is `operating_points_cnt_minus_1 + 1`.
        seq_tier (list[int]): List of sequence tiers (0 for Main tier, 1 for High tier) for each
            operating point. Length is `operating_points_cnt_minus_1 + 1`.
        decoder_model_present_for_this_op (list[int]): Flags (0 or 1) indicating if decoder model
            parameters are present for each operating point. Length is `operating_points_cnt_minus_1 + 1`.
        operating_parameters_info (list[OperatingParametersInfo]): List of
            `OperatingParametersInfo` objects for each operating point.
            Length is `operating_points_cnt_minus_1 + 1`.
        initial_display_delay_present_for_this_op (list[int]): Flags (0 or 1) indicating if
            initial display delay is present for each operating point.
            Length is `operating_points_cnt_minus_1 + 1`.
        initial_display_delay_minus_1 (list[int]): List of initial display delays minus 1
            for each operating point where `initial_display_delay_present_for_this_op` is 1.
            Length is `operating_points_cnt_minus_1 + 1`.
        frame_width_bits_minus_1 (int): Number of bits used to specify frame width, minus 1.
        frame_height_bits_minus_1 (int): Number of bits used to specify frame height, minus 1.
        max_frame_width_minus_1 (int): Maximum frame width in pixels, minus 1.
        max_frame_height_minus_1 (int): Maximum frame height in pixels, minus 1.
        frame_id_numbers_present_flag (int): If 1, frame ID numbers are present in frame headers.
        delta_frame_id_length_minus_2 (int): Length in bits of `delta_frame_id` minus 2.
        additional_frame_id_length_minus_1 (int): Length in bits of `additional_frame_id` minus 1.
        use_128x128_superblock (int): If 1, superblocks are 128x128; otherwise 64x64.
        enable_filter_intra (int): If 1, filter intra predictor is enabled.
        enable_intra_edge_filter (int): If 1, intra edge filter process is enabled.
        enable_interintra_compound (int): If 1, inter-intra compound prediction is enabled.
        enable_masked_compound (int): If 1, masked compound prediction is enabled.
        enable_warped_motion (int): If 1, warped motion is enabled.
        enable_dual_filter (int): If 1, dual interpolation filter is enabled.
        enable_order_hint (int): If 1, order hint syntax is enabled.
        enable_jnt_comp (int): If 1, joint compound prediction (distance-weighted compound) is enabled.
        enable_ref_frame_mvs (int): If 1, using reference frame MVs for motion field estimation is enabled.
        seq_choose_screen_content_tools (int): If 1, the encoder may choose to use screen content tools.
        seq_force_screen_content_tools (int): If `seq_choose_screen_content_tools` is 0, this specifies
            if screen content tools are forced (0=not forced, 1=forced, 2=auto/not applicable).
            If `seq_choose_screen_content_tools` is 1, this value is 2 (auto/not applicable).
        seq_choose_integer_mv (int): If 1, the encoder may choose to use integer MVs.
        seq_force_integer_mv (int): If `seq_choose_integer_mv` is 0, this specifies if integer MVs
            are forced (0=not forced, 1=forced, 2=auto/not applicable).
            If `seq_choose_integer_mv` is 1, this value is 2 (auto/not applicable).
        order_hint_bits_minus_1 (int): Number of bits used for order hint, minus 1.
            If 0, `OrderHintBits` is 0. Otherwise `OrderHintBits` is `order_hint_bits_minus_1 + 1`.
        enable_superres (int): If 1, super-resolution is enabled.
        enable_cdef (int): If 1, Constrained Directional Enhancement Filter (CDEF) is enabled.
        enable_restoration (int): If 1, Loop Restoration filter is enabled.
        color_config (ColorConfig): Color configuration parameters.
        film_grain_params_present (int): If 1, film grain parameters are present in frame headers.
        FrameWidth (int): Width of the frame in pixels. (Derived by C parser based on other fields)
        FrameHeight (int): Height of the frame in pixels. (Derived by C parser based on other fields)
        OrderHintBits (int): Number of bits for order hint. (Derived by C parser based on `enable_order_hint`
            and `order_hint_bits_minus_1`)
        _c_seq_header (_c_wrapper.OBPSequenceHeader): Internal reference to the underlying CTypes struct.
    """
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
    """
    Represents a parsed AV1 Frame Header OBU or the header part of a Frame OBU.

    This class provides a Pythonic interface to the data contained in a
    Frame Header, as defined by the AV1 specification. It is initialized
    from a C-level `OBPFrameHeader` struct populated by the C parser.

    Args:
        c_fh (_c_wrapper.OBPFrameHeader): The ctypes structure from the C parser
            containing the frame header data.
        sequence_header (SequenceHeader): The associated Python `SequenceHeader`
            object for this frame, providing context (e.g., for film grain params).

    Attributes:
        show_existing_frame (int): Flag indicating if this frame shows an existing frame.
        frame_to_show_map_idx (int): Index of the frame to show if `show_existing_frame` is true.
        temporal_point_info_present (int): Flag from C wrapper, indicates if presentation time is valid.
        frame_presentation_time (int): Presentation time of the frame.
        display_frame_id (int): ID of the frame to be displayed.
        frame_type (_c_wrapper.OBPFrameType): Type of the frame (e.g., Key, Inter).
        show_frame (int): Flag indicating if this frame is to be shown.
        showable_frame (int): Flag indicating if this frame can be shown (not an overlay).
            (This field is from the C wrapper, may be derived).
        error_resilient_mode (int): Flag indicating if error resilient mode is enabled.
        disable_cdf_update (int): Flag indicating if CDF update is disabled.
        allow_screen_content_tools (int): Flag indicating if screen content tools are allowed.
        force_integer_mv (int): Flag indicating if integer MVs are forced.
        current_frame_id (int): ID of the current frame.
        frame_size_override_flag (int): Flag indicating if frame size is overridden.
        order_hint (int): Order hint for this frame.
        primary_ref_frame (int): Primary reference frame index.
        buffer_removal_time_present_flag (int): Flag indicating if buffer removal time is present.
        buffer_removal_time (list[int]): Buffer removal times for operating points.
        refresh_frame_flags (int): Bitmask indicating which reference frames are refreshed.
        ref_order_hint (list[int]): Order hints for reference frames.
        frame_width_minus_1 (int): Frame width minus 1.
        frame_height_minus_1 (int): Frame height minus 1.
        superres_params (SuperresParams): Super-resolution parameters.
        render_and_frame_size_different (int): Flag indicating if render size differs from frame size.
        render_width_minus_1 (int): Render width minus 1.
        render_height_minus_1 (int): Render height minus 1.
        FrameWidth (int): Actual width of the frame. (Derived by C parser)
        FrameHeight (int): Actual height of the frame. (Derived by C parser)
        allow_intrabc (int): Flag indicating if intra block copy is allowed.
        frame_refs_short_signaling (int): Flag for short signaling of reference frames.
        last_frame_idx (int): Index of the last reference frame.
        gold_frame_idx (int): Index of the golden reference frame.
        ref_frame_idx (list[int]): Indices of reference frames.
        delta_frame_id_minus_1 (list[int]): Delta frame IDs minus 1 for reference frames.
        found_ref (int): Flag indicating if a reference frame was found.
            (Derived by C parser internal state).
        allow_high_precision_mv (int): Flag indicating if high precision MVs are allowed.
        interpolation_filter (InterpolationFilter): Interpolation filter parameters.
        is_motion_mode_switchable (int): Flag indicating if motion mode is switchable.
        use_ref_frame_mvs (int): Flag indicating if reference frame MVs are used.
        disable_frame_end_update_cdf (int): Flag indicating if frame end CDF update is disabled.
        MiCols (int): Number of columns in MI units. (Derived by C parser)
        MiRows (int): Number of rows in MI units. (Derived by C parser)
        tile_info (TileInfo): Tile information.
        quantization_params (QuantizationParams): Quantization parameters.
        segmentation_params (SegmentationParams): Segmentation parameters.
        delta_q_params (DeltaQParams): Delta Q parameters.
        delta_lf_params (DeltaLFParams): Delta LF parameters.
        loop_filter_params (LoopFilterParams): Loop filter parameters.
        cdef_params (CdefParams): CDEF parameters.
        lr_params (LrParams): Loop Restoration parameters.
        tx_mode_select (int): TX mode selection.
        skip_mode_present (int): Flag indicating if skip mode is present.
        reference_select (int): Reference selection mode.
        allow_warped_motion (int): Flag indicating if warped motion is allowed.
        reduced_tx_set (int): Flag indicating if reduced TX set is used.
        global_motion_params (list[GlobalMotionParams]): List of global motion parameters
            for reference frames.
        film_grain_params (FilmGrainParameters | None): Film grain parameters, if present.
    """
    def __init__(self, c_fh: _c_wrapper.OBPFrameHeader, sequence_header: SequenceHeader):
        self._c_frame_header = c_fh # Keep ref for other functions
        self._py_sequence_header = sequence_header # Keep ref for context

        self.show_existing_frame: int = c_fh.show_existing_frame
        self.frame_to_show_map_idx: int = c_fh.frame_to_show_map_idx
        self.temporal_point_info_present: int = c_fh.temporal_point_info_present # From wrapper
        self.frame_presentation_time: int = c_fh.frame_presentation_time # From wrapper (flattened)
        self.display_frame_id: int = c_fh.display_frame_id
        
        self.frame_type: _c_wrapper.OBPFrameType = _c_wrapper.OBPFrameType(c_fh.frame_type)
        
        self.show_frame: int = c_fh.show_frame
        self.showable_frame: int = c_fh.showable_frame # Not in C OBPFrameHeader, but in wrapper
        self.error_resilient_mode: int = c_fh.error_resilient_mode
        self.disable_cdf_update: int = c_fh.disable_cdf_update
        self.allow_screen_content_tools: int = c_fh.allow_screen_content_tools
        self.force_integer_mv: int = c_fh.force_integer_mv
        self.current_frame_id: int = c_fh.current_frame_id
        self.frame_size_override_flag: int = c_fh.frame_size_override_flag
        self.order_hint: int = c_fh.order_hint
        self.primary_ref_frame: int = c_fh.primary_ref_frame
        
        self.buffer_removal_time_present_flag: int = c_fh.buffer_removal_time_present_flag 
        self.buffer_removal_time: list[int] = _c_array_to_list(c_fh.buffer_removal_time) 

        self.refresh_frame_flags: int = c_fh.refresh_frame_flags
        self.ref_order_hint: list[int] = _c_array_to_list(c_fh.ref_order_hint)

        # Frame size and superres
        self.frame_width_minus_1: int = c_fh.frame_width_minus_1
        self.frame_height_minus_1: int = c_fh.frame_height_minus_1
        self.superres_params: SuperresParams = SuperresParams(c_fh.superres_params)
        self.render_and_frame_size_different: int = c_fh.render_and_frame_size_different 
        self.render_width_minus_1: int = c_fh.render_width_minus_1
        self.render_height_minus_1: int = c_fh.render_height_minus_1
        self.FrameWidth: int = c_fh.FrameWidth # Derived
        self.FrameHeight: int = c_fh.FrameHeight # Derived

        # Reference frame signaling
        self.allow_intrabc: int = c_fh.allow_intrabc
        self.frame_refs_short_signaling: int = c_fh.frame_refs_short_signaling 
        self.last_frame_idx: int = c_fh.last_frame_idx 
        self.gold_frame_idx: int = c_fh.gold_frame_idx 
        self.ref_frame_idx: list[int] = _c_array_to_list(c_fh.ref_frame_idx) 
        self.delta_frame_id_minus_1: list[int] = _c_array_to_list(c_fh.delta_frame_id_minus_1) 
        self.found_ref: int = c_fh.found_ref 

        # Motion vector and interpolation
        self.allow_high_precision_mv: int = c_fh.allow_high_precision_mv
        self.interpolation_filter: InterpolationFilter = InterpolationFilter(c_fh.interpolation_filter)
        self.is_motion_mode_switchable: int = c_fh.is_motion_mode_switchable
        self.use_ref_frame_mvs: int = c_fh.use_ref_frame_mvs
        self.disable_frame_end_update_cdf: int = c_fh.disable_frame_end_update_cdf
        
        self.MiCols: int = c_fh.MiCols # Derived
        self.MiRows: int = c_fh.MiRows # Derived

        self.tile_info: TileInfo = TileInfo(c_fh.tile_info)
        self.quantization_params: QuantizationParams = QuantizationParams(c_fh.quantization_params)
        self.segmentation_params: SegmentationParams = SegmentationParams(c_fh.segmentation_params)
        self.delta_q_params: DeltaQParams = DeltaQParams(c_fh.delta_q_params)
        self.delta_lf_params: DeltaLFParams = DeltaLFParams(c_fh.delta_lf_params)
        self.loop_filter_params: LoopFilterParams = LoopFilterParams(c_fh.loop_filter_params)
        self.cdef_params: CdefParams = CdefParams(c_fh.cdef_params)
        self.lr_params: LrParams = LrParams(c_fh.lr_params)

        self.tx_mode_select: int = c_fh.tx_mode_select 
        self.skip_mode_present: int = c_fh.skip_mode_present
        self.reference_select: int = c_fh.reference_select
        self.allow_warped_motion: int = c_fh.allow_warped_motion
        self.reduced_tx_set: int = c_fh.reduced_tx_set
        
        self.global_motion_params: list[GlobalMotionParams] = [
            GlobalMotionParams(c_fh.global_motion_params[i]) for i in range(8) # TOTAL_REFS_PER_FRAME
        ]

        if sequence_header.film_grain_params_present: # This flag is from SequenceHeader
            self.film_grain_params: FilmGrainParameters | None = FilmGrainParameters(c_fh.film_grain_params)
        else:
            self.film_grain_params = None
        
        # self.large_scale_tile: int = c_fh.large_scale_tile # Removed, not in C OBPFrameHeader
        self._c_frame_header = c_fh # Store reference to C struct for potential internal use

    def __repr__(self) -> str:
        return (f"FrameHeader(type={self.frame_type}, width={self.FrameWidth}, height={self.FrameHeight}, "
                f"show_frame={self.show_frame}, order_hint={self.order_hint})")

class TileGroup:
    """
    Represents a parsed AV1 Tile Group OBU.

    A Tile Group OBU contains one or more tiles of a coded frame.
    The `data` attribute holds the combined payload of these tiles.

    Args:
        c_tg (_c_wrapper.OBPTileGroup): The ctypes structure from the C parser
            containing the tile group data. This structure is expected to be
            populated by functions like `obp_parse_frame` or `obp_parse_tile_group`.

    Attributes:
        NumTiles (int): Number of tiles in this tile group, as read from the
            OBU header or inferred by the C parser.
        obu_size (int): Size of the OBU payload this TileGroup was parsed from.
            This typically includes the tile group header and the tile data itself.
        data (bytes): The raw byte data of the tile(s) in this tile group,
            after the tile group header.
        tg_start (int): The index of the first tile in this tile group.
            This value is meaningful in the context of the frame's total tile layout.
        tg_end (int): The index of the last tile in this tile group.
        _c_tile_group (_c_wrapper.OBPTileGroup): Internal reference to the underlying CTypes struct.
    """
    def __init__(self, c_tg: _c_wrapper.OBPTileGroup):
        """
        Initializes the TileGroup object from a C-level OBPTileGroup struct.

        Args:
            c_tg (_c_wrapper.OBPTileGroup): The ctypes structure from C.
        """
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
    """
    Represents a parsed AV1 Metadata OBU.

    AV1 Metadata OBUs can carry various types of metadata, such as HDR CLL,
    HDR MDCV, scalability information, ITU-T T.35 registered data, timecodes,
    or user-private unregistered data. This class provides access to the
    specific metadata type parsed.

    Args:
        c_meta (_c_wrapper.OBPMetadata): The ctypes structure from the C parser
            populated by `obp_parse_metadata`.
        obu_payload (bytes): The raw payload of the Metadata OBU (the data passed
            to `obp_parse_metadata`). This is stored as `self.data`.

    Attributes:
        type (_c_wrapper.OBPMetadataType | int): The type of metadata contained in this OBU.
            This will be an `OBPMetadataType` enum member if the type is known and defined
            in the enum, otherwise, it will be the raw integer value of the metadata type.
        metadata_itut_t35 (MetadataITUTT35 | None): An instance of `MetadataITUTT35`
            if `type` is `OBP_METADATA_TYPE_ITUT_T35`, otherwise `None`.
        metadata_hdr_cll (MetadataHDRCLL | None): An instance of `MetadataHDRCLL`
            if `type` is `OBP_METADATA_TYPE_HDR_CLL`, otherwise `None`.
        metadata_hdr_mdcv (MetadataHDRMDCV | None): An instance of `MetadataHDRMDCV`
            if `type` is `OBP_METADATA_TYPE_HDR_MDCV`, otherwise `None`.
        metadata_scalability (MetadataScalability | None): An instance of `MetadataScalability`
            if `type` is `OBP_METADATA_TYPE_SCALABILITY`, otherwise `None`.
        metadata_timecode (MetadataTimecode | None): An instance of `MetadataTimecode`
            if `type` is `OBP_METADATA_TYPE_TIMECODE`, otherwise `None`.
        unregistered (MetadataUnregistered | None): An instance of `MetadataUnregistered`
            if the metadata type is not one of the specifically handled known types but the
            C parser successfully parsed it as generic unregistered data. This typically
            captures the raw buffer of such metadata.
        data (bytes): The raw payload of the entire Metadata OBU. Useful for accessing
            the underlying data directly if needed.
        _c_metadata (_c_wrapper.OBPMetadata): Internal reference to the underlying CTypes struct.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadata, obu_payload: bytes):
        """
        Initializes the Metadata object from a C-level OBPMetadata struct
        and the raw OBU payload.

        Args:
            c_meta (_c_wrapper.OBPMetadata): The ctypes structure from C.
            obu_payload (bytes): The raw payload of the Metadata OBU.
        """
        self._c_metadata = c_meta
        self.type: int = c_meta.metadata_type # OBPMetadataType enum, was c_meta.type
        # self.obu_size: int = c_meta.obu_size # obu_size was removed from _c_wrapper.OBPMetadata
                                            # The size of the OBU payload is len(obu_payload)

        # `c_meta.data` was removed from _c_wrapper.OBPMetadata.
        # The obu_payload itself is the data.
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

        try:
            # self.type should now correctly be an OBPMetadataType enum instance if conversion in C worked
            # or an int if it was an unknown value not in the enum.
            # The C function obp_parse_metadata directly fills metadata_type as an enum value.
            metadata_type_enum = _c_wrapper.OBPMetadataType(self.type) # Ensure it's an enum for comparison
            if metadata_type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_ITUT_T35:
                self.metadata_itut_t35 = MetadataITUTT35(c_meta.metadata_itut_t35)
            elif metadata_type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_HDR_CLL:
                self.metadata_hdr_cll = MetadataHDRCLL(c_meta.metadata_hdr_cll)
            elif metadata_type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_HDR_MDCV:
                self.metadata_hdr_mdcv = MetadataHDRMDCV(c_meta.metadata_hdr_mdcv)
            elif metadata_type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_SCALABILITY:
                self.metadata_scalability = MetadataScalability(c_meta.metadata_scalability)
            elif metadata_type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_TIMECODE:
                self.metadata_timecode = MetadataTimecode(c_meta.metadata_timecode)
            else:
                # This case is for valid enum members not explicitly handled above.
                # Or if new types are added to enum but not to this if/elif chain.
                # Attempt to populate 'unregistered' if the C struct seems to contain data for it.
                # This relies on the C parser filling c_meta.unregistered for such cases.
                if hasattr(c_meta, 'unregistered') and \
                   (c_meta.unregistered.payload_byte_count > 0 or \
                    (hasattr(c_meta.unregistered, 'uuid') and any(c_meta.unregistered.uuid))):
                    self.unregistered = MetadataUnregistered(c_meta.unregistered)
        except ValueError:
            # self.type is not a valid member of OBPMetadataType enum (e.g., it's in the 6-31 range for user-private).
            # Assume it's an unregistered type and try to populate from c_meta.unregistered.
            # This relies on the C parser filling c_meta.unregistered for types it doesn't explicitly handle in its switch.
            if hasattr(c_meta, 'unregistered') and \
               (c_meta.unregistered.payload_byte_count > 0 or \
                (hasattr(c_meta.unregistered, 'uuid') and any(c_meta.unregistered.uuid))):
                self.unregistered = MetadataUnregistered(c_meta.unregistered)
        
        # Raw data of the metadata OBU's payload (after OBU header)
        # The full OBU payload is passed as 'obu_payload' argument to this constructor.
        self.data: bytes = obu_payload


    def __repr__(self) -> str:
        return f"Metadata(type={self.type}, obu_size={len(self.data)}, specific_metadata_present={self._get_specific_metadata_repr()})"

    def _get_specific_metadata_repr(self) -> str:
        if self.metadata_itut_t35: return repr(self.metadata_itut_t35)
        if self.metadata_hdr_cll: return repr(self.metadata_hdr_cll)
        if self.metadata_hdr_mdcv: return repr(self.metadata_hdr_mdcv)
        if self.metadata_scalability: return repr(self.metadata_scalability)
        if self.metadata_timecode: return repr(self.metadata_timecode)
        if self.unregistered: return repr(self.unregistered)
        return "None"

class TileList:
    """
    Represents a parsed AV1 Tile List OBU.

    A Tile List OBU provides a list of tiles, including their anchor frame reference
    and coded data. This OBU type is particularly useful for scenarios requiring
    access to individual tiles, such as large-scale tile coding or certain
    error resilience mechanisms.

    Args:
        c_tl (_c_wrapper.OBPTileList): The ctypes structure from the C parser,
            populated by `obp_parse_tile_list`.
        obu_payload (bytes): The raw payload of the Tile List OBU. This is necessary
            because `TileListEntry.coded_tile_data` is extracted directly from this
            payload using pointers provided by the C parser.

    Attributes:
        output_frame_width_in_tiles_minus_1 (int): The width of the output frame
            in units of tiles, minus 1.
        output_frame_height_in_tiles_minus_1 (int): The height of the output frame
            in units of tiles, minus 1.
        tile_count_minus_1 (int): The number of tiles in the list, minus 1.
            The actual number of tiles is `tile_count_minus_1 + 1`.
        tile_list_entries (list[TileListEntry]): A list of `TileListEntry` objects,
            each describing a tile in the list. The data for each tile is copied
            into `TileListEntry.coded_tile_data`.
        _c_tile_list (_c_wrapper.OBPTileList): Internal reference to the underlying CTypes struct.
    """
    def __init__(self, c_tl: _c_wrapper.OBPTileList, obu_payload: bytes):
        """
        Initializes the TileList object from a C-level OBPTileList struct
        and the raw OBU payload.

        Args:
            c_tl (_c_wrapper.OBPTileList): The ctypes structure from C.
            obu_payload (bytes): The raw payload of the Tile List OBU.
        """
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
    """
    Manages an instance of the C-level `OBPState` structure.

    The `OBPState` structure is used by some C parsing functions (like
    `obp_parse_frame_header` and `obp_parse_frame`) to maintain state
    across calls, especially for parsing sequences of OBUs that depend on
    previous ones (e.g., reference frame information).

    An instance of this wrapper should be created and passed consistently
    when parsing related frame or frame header OBUs. The C library initializes
    and updates the state internally. Python code typically does not need to
    directly access fields within the `OBPState` structure.
    """
    def __init__(self):
        """Initializes the OBPStateWrapper, creating and zero-initializing the C struct."""
        self._c_state_instance = _c_wrapper.OBPState()
        if _c_wrapper._lib and hasattr(_c_wrapper._lib, 'obp_state_init'):
            # obp_state_init is not a standard part of obuparse.h API,
            # but if it were provided for custom initialization, it could be called here.
            # For standard obuparse, zero-initializing is typical for the public OBPState.
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
        # Provide a minimal representation, avoid accessing fields not guaranteed by public OBPState
        return f"OBPStateWrapper(c_state_instance_addr=0x{ctypes.addressof(self._c_state_instance):x})"


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
    """
    Parses a Sequence Header OBU.

    Args:
        data (bytes): The raw byte data of the Sequence Header OBU payload
            (i.e., excluding the OBU common header).

    Returns:
        SequenceHeader: A `SequenceHeader` object representing the parsed data.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
    """
    Parses a Frame Header OBU or the header part of a Frame OBU.

    Args:
        data (bytes): The raw byte data of the Frame Header OBU payload.
        sequence_header_obj (SequenceHeader): The `SequenceHeader` object associated
            with the current video sequence.
        state_wrapper (OBPStateWrapper): An `OBPStateWrapper` object that maintains
            parsing state across calls, especially for dependent frames.
        temporal_id (int): The temporal ID of the OBU.
        spatial_id (int): The spatial ID of the OBU.

    Returns:
        FrameHeader: A `FrameHeader` object representing the parsed data.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
    """
    Parses a Frame OBU, which includes a frame header and tile group data.

    Args:
        data (bytes): The raw byte data of the Frame OBU payload.
        sequence_header_obj (SequenceHeader): The associated `SequenceHeader`.
        state_wrapper (OBPStateWrapper): State manager for parsing.
        temporal_id (int): The temporal ID of the OBU.
        spatial_id (int): The spatial ID of the OBU.

    Returns:
        Tuple[FrameHeader, TileGroup]: A tuple containing the parsed `FrameHeader`
        and `TileGroup` objects.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
    """
    Parses a Tile Group OBU.

    Args:
        data (bytes): The raw byte data of the Tile Group OBU payload.
        frame_header_obj (FrameHeader): The `FrameHeader` object for the frame
            to which this tile group belongs.

    Returns:
        TileGroup: A `TileGroup` object representing the parsed data.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
    """
    Parses a Metadata OBU.

    Args:
        data (bytes): The raw byte data of the Metadata OBU payload.

    Returns:
        Metadata: A `Metadata` object representing the parsed data.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
    """
    Parses a Tile List OBU.

    Args:
        data (bytes): The raw byte data of the Tile List OBU payload.

    Returns:
        TileList: A `TileList` object representing the parsed data.

    Raises:
        OBUParseError: If the C library is not loaded or if parsing fails.
    """
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
# No longer need _PY_OBP_OBU_TYPE_MAP, as OBPOBUType enum will be used directly.

def iter_obus(data: bytes):
    """
    Generates OBU information from a byte stream.

    This function iterates over a byte stream that may contain multiple OBUs.
    For each OBU found, it yields information about its header and its payload.
    It uses the `obp_get_next_obu` C function to identify OBU boundaries and
    extract header fields.

    Args:
        data (bytes): A byte string containing one or more OBUs.

    Yields:
        Tuple[_c_wrapper.OBPOBUType | int, int, int, bytes]: A tuple for each OBU found:
            - obu_type: The type of the OBU (an `OBPOBUType` enum member if known,
              otherwise an int).
            - temporal_id: The temporal ID of the OBU.
            - spatial_id: The spatial ID of the OBU.
            - obu_payload_bytes: The raw byte payload of the OBU (excluding the
              OBU common header).

    Raises:
        OBUParseError: If the C library is not loaded or if an error occurs
            during OBU iteration (e.g., malformed OBU structure).
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

        # Get the current slice of data.
        current_data_slice_bytes = data[current_pos:]
        remaining_data_size = len(current_data_slice_bytes)

        # If there's no data left, stop.
        if remaining_data_size == 0:
            break

        # Cast the current data slice to the POINTER(c_uint8_t) type expected by the C function.
        # This is how other parsing functions in this file prepare their data pointers.
        input_buffer_ptr = ctypes.cast(current_data_slice_bytes, ctypes.POINTER(_c_wrapper.c_uint8_t))

        if takes_spatial_id_arg:
             ret_code = c_lib.obp_get_next_obu(
                input_buffer_ptr, remaining_data_size,
                ctypes.byref(obu_type_cval), ctypes.byref(obu_offset_cval),
                ctypes.byref(obu_size_cval), ctypes.byref(obu_has_size_field_cval),
                ctypes.byref(temporal_id_cval), ctypes.byref(spatial_id_cval), # Pass spatial_id
                ctypes.byref(err_struct)
            )
        else: # Fallback if _c_wrapper.py's obp_get_next_obu is old (8 args)
            temp_argtypes = c_lib.obp_get_next_obu.argtypes
            c_lib.obp_get_next_obu.argtypes = temp_argtypes[:7] + temp_argtypes[8:] # Remove spatial_id arg
            ret_code = c_lib.obp_get_next_obu(
                input_buffer_ptr, remaining_data_size,
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
        # Directly use the enum member if possible, otherwise the raw int value.
        try:
            py_obu_type_enum = _c_wrapper.OBPOBUType(obu_type_cval.value)
        except ValueError:
            py_obu_type_enum = obu_type_cval.value # Fallback to raw int if not in enum

        yield (
            py_obu_type_enum,
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
