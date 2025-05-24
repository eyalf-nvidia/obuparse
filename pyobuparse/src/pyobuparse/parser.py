"""
High-level Pythonic interface for parsing AV1 OBU (Open Bitstream Unit) data.

This module provides classes and functions to parse different types of OBUs
as defined in the AV1 specification. It uses the low-level C functions
exposed via `_c_wrapper.py` and presents the parsed data in more accessible
Python objects.

Main features:
- Iterating through OBUs in a byte stream using `iter_obus`.
- Parsing specific OBU types like Sequence Headers, Frame Headers, Metadata, etc.
- Pythonic data classes representing the structure and content of various OBUs.
- Custom exception `OBUParseError` for parsing-related errors.

The primary entry point for most use cases is the `iter_obus` generator,
which yields information about each OBU found in the input data. Specific parsing
functions like `parse_sequence_header` can then be used on the payload of
these OBUs.
"""
import ctypes
from typing import Sequence, Tuple, Any, Iterator, Union # Added Iterator, Union
from . import _c_wrapper

# --- Custom Exception ---
class OBUParseError(Exception):
    """
    Custom exception raised for errors during OBU parsing.

    This exception is raised when the underlying C library encounters an error
    while parsing an OBU, or when the Python wrapper detects an issue
    (e.g., data extending beyond buffer limits).
    """
    pass

# --- Helper function to copy C array to Python list ---
def _c_array_to_list(c_array: ctypes.Array, length: int | None = None) -> list:
    """
    Converts a ctypes Array to a Python list.

    :param c_array: The ctypes Array to convert.
    :type c_array: ctypes.Array
    :param length: The number of elements to copy from the array.
                   If None, and the c_array has a `_length_` attribute (typically
                   for fixed-size arrays within structures), that length is used.
                   Otherwise, a ValueError is raised.
    :type length: int, optional
    :return: A Python list containing elements from the c_array.
    :rtype: list
    :raises ValueError: If `length` is None and the array type doesn't have `_length_`.
    """
    if not c_array:
        return []
    if length is None:
        # This part is tricky and depends on array type. For now, require length for non-char pointers.
        # For ctypes arrays with _length_ attribute (fixed size arrays in structs)
        if hasattr(c_array, '_length_'):
             return [c_array[i] for i in range(getattr(c_array, '_length_'))]
        raise ValueError("Length must be provided for C arrays not part of a structure field with _length_")
    return [c_array[i] for i in range(length)]

# --- Helper Python classes for SequenceHeader nested structures ---

class TimingInfo:
    """
    Represents the timing_info structure from an AV1 Sequence Header OBU.

    Corresponds to the `timing_info` struct in the AV1 specification.
    This information is crucial for determining frame rates and presentation times.

    :ivar num_units_in_display_tick: Number of time units of a clock operating at time_scale Hz that corresponds to one display tick.
    :ivar time_scale: The number of time units that pass in one second.
    :ivar equal_picture_interval: Indicates if the picture interval is equal for all pictures.
    :ivar num_ticks_per_picture_minus_1: Number of clock ticks per picture interval minus 1.
    """
    def __init__(self, c_timing_info: _c_wrapper.OBPTimingInfo):
        """
        Initializes TimingInfo from a ctypes OBPTimingInfo object.

        :param c_timing_info: The ctypes OBPTimingInfo structure.
        :type c_timing_info: _c_wrapper.OBPTimingInfo
        """
        self.num_units_in_display_tick: int = c_timing_info.num_units_in_display_tick
        self.time_scale: int = c_timing_info.time_scale
        self.equal_picture_interval: int = c_timing_info.equal_picture_interval
        self.num_ticks_per_picture_minus_1: int = c_timing_info.num_ticks_per_picture_minus_1

    def __repr__(self) -> str:
        """Return a string representation of the TimingInfo object."""
        return (
            f"TimingInfo(num_units_in_display_tick={self.num_units_in_display_tick}, "
            f"time_scale={self.time_scale}, equal_picture_interval={self.equal_picture_interval}, "
            f"num_ticks_per_picture_minus_1={self.num_ticks_per_picture_minus_1})"
        )

class DecoderModelInfo:
    """
    Represents the decoder_model_info structure from an AV1 Sequence Header OBU.

    Corresponds to the `decoder_model_info` struct in the AV1 specification,
    providing parameters for decoder buffer management.

    :ivar buffer_delay_length_minus_1: Specifies the length of the buffer_delay syntax element in bits, minus 1.
    :ivar num_units_in_decoding_tick: Number of time units of a clock operating at time_scale Hz that corresponds to one decoding tick.
    :ivar buffer_removal_time_length_minus_1: Specifies the length of the buffer_removal_time syntax element in bits, minus 1.
    :ivar frame_presentation_time_length_minus_1: Specifies the length of the frame_presentation_time syntax element in bits, minus 1.
    """
    def __init__(self, c_decoder_model_info: _c_wrapper.OBPDecoderModelInfo):
        """
        Initializes DecoderModelInfo from a ctypes OBPDecoderModelInfo object.

        :param c_decoder_model_info: The ctypes OBPDecoderModelInfo structure.
        :type c_decoder_model_info: _c_wrapper.OBPDecoderModelInfo
        """
        self.buffer_delay_length_minus_1: int = c_decoder_model_info.buffer_delay_length_minus_1
        self.num_units_in_decoding_tick: int = c_decoder_model_info.num_units_in_decoding_tick
        self.buffer_removal_time_length_minus_1: int = c_decoder_model_info.buffer_removal_time_length_minus_1
        self.frame_presentation_time_length_minus_1: int = c_decoder_model_info.frame_presentation_time_length_minus_1

    def __repr__(self) -> str:
        """Return a string representation of the DecoderModelInfo object."""
        return (
            f"DecoderModelInfo(buffer_delay_length_minus_1={self.buffer_delay_length_minus_1}, "
            # (repr was too long, shortened for brevity)
            f"..., frame_presentation_time_length_minus_1={self.frame_presentation_time_length_minus_1})"
        )

class OperatingParametersInfo:
    """
    Represents operating_parameters_info for an operating point in a Sequence Header.

    Corresponds to the `operating_parameters_info` struct in the AV1 specification,
    detailing buffer and delay information for a specific operating point.

    :ivar decoder_buffer_delay: Specifies the size of the decoder buffer for this operating point.
    :ivar encoder_buffer_delay: Specifies the size of the encoder buffer for this operating point.
    :ivar low_delay_mode_flag: Indicates if low delay mode is active for this operating point.
    """
    def __init__(self, c_op_info: _c_wrapper.OBPOperatingParametersInfo):
        """
        Initializes OperatingParametersInfo from a ctypes OBPOperatingParametersInfo object.

        :param c_op_info: The ctypes OBPOperatingParametersInfo structure.
        :type c_op_info: _c_wrapper.OBPOperatingParametersInfo
        """
        self.decoder_buffer_delay: int = c_op_info.decoder_buffer_delay
        self.encoder_buffer_delay: int = c_op_info.encoder_buffer_delay
        self.low_delay_mode_flag: int = c_op_info.low_delay_mode_flag

    def __repr__(self) -> str:
        """Return a string representation of the OperatingParametersInfo object."""
        return (
            f"OperatingParametersInfo(decoder_buffer_delay={self.decoder_buffer_delay}, "
            f"encoder_buffer_delay={self.encoder_buffer_delay}, low_delay_mode_flag={self.low_delay_mode_flag})"
        )

class ColorConfig:
    """
    Represents the color_config structure from an AV1 Sequence Header OBU.

    Corresponds to the `color_config` struct in the AV1 specification, detailing
    color format and characteristics.

    :ivar high_bitdepth: Indicates if the bit depth is greater than 8.
    :ivar twelve_bit: Indicates if 12-bit color is used (valid if high_bitdepth is true).
    :ivar mono_chrome: Indicates if the video is monochrome.
    :ivar BitDepth: The bit depth of the video (e.g., 8, 10, 12).
    :ivar NumPlanes: The number of color planes.
    :ivar color_description_present_flag: Flag indicating if color primaries, transfer characteristics, and matrix coefficients are present.
    :ivar color_primaries: The color primaries of the video, if present. See :class:`~._c_wrapper.OBPColorPrimaries`.
    :ivar transfer_characteristics: The transfer characteristics of the video, if present. See :class:`~._c_wrapper.OBPTransferCharacteristics`.
    :ivar matrix_coefficients: The matrix coefficients of the video, if present. See :class:`~._c_wrapper.OBPMatrixCoefficients`.
    :ivar color_range: Indicates studio swing (0) or full swing (1) of color values.
    :ivar subsampling_x: Chroma subsampling value in the x-direction (valid if not monochrome).
    :ivar subsampling_y: Chroma subsampling value in the y-direction (valid if not monochrome).
    :ivar chroma_sample_position: The chroma sample position, if relevant. See :class:`~._c_wrapper.OBPChromaSamplePosition`.
    :ivar separate_uv_delta_q: Indicates if separate delta quantization is used for UV planes.
    """
    def __init__(self, c_color_config: _c_wrapper.OBPColorConfig):
        """
        Initializes ColorConfig from a ctypes OBPColorConfig object.

        :param c_color_config: The ctypes OBPColorConfig structure.
        :type c_color_config: _c_wrapper.OBPColorConfig
        """
        self.high_bitdepth: int = c_color_config.high_bitdepth
        self.twelve_bit: int = c_color_config.twelve_bit # Only relevant if high_bitdepth is true
        self.mono_chrome: int = c_color_config.mono_chrome
        self.BitDepth: int = c_color_config.BitDepth # Actual bit depth (8, 10, 12)
        self.NumPlanes: int = c_color_config.NumPlanes # Number of color planes

        self.color_description_present_flag: int = c_color_config.color_description_present_flag
        # The following are valid only if color_description_present_flag is true
        self.color_primaries: _c_wrapper.OBPColorPrimaries | int = (
            _c_wrapper.OBPColorPrimaries(c_color_config.color_primaries)
            if self.color_description_present_flag else c_color_config.color_primaries
        )
        self.transfer_characteristics: _c_wrapper.OBPTransferCharacteristics | int = (
            _c_wrapper.OBPTransferCharacteristics(c_color_config.transfer_characteristics)
            if self.color_description_present_flag else c_color_config.transfer_characteristics
        )
        self.matrix_coefficients: _c_wrapper.OBPMatrixCoefficients | int = (
            _c_wrapper.OBPMatrixCoefficients(c_color_config.matrix_coefficients)
            if self.color_description_present_flag else c_color_config.matrix_coefficients
        )
        
        self.color_range: int = c_color_config.color_range # Studio swing (0) or full swing (1)
        
        # Subsampling parameters are valid only if NumPlanes > 1 (not monochrome)
        self.subsampling_x: int = c_color_config.subsampling_x if not self.mono_chrome else 0
        self.subsampling_y: int = c_color_config.subsampling_y if not self.mono_chrome else 0
        self.chroma_sample_position: _c_wrapper.OBPChromaSamplePosition | int = (
            _c_wrapper.OBPChromaSamplePosition(c_color_config.chroma_sample_position)
            if not self.mono_chrome else c_color_config.chroma_sample_position
        )
        
        self.separate_uv_delta_q: int = c_color_config.separate_uv_delta_q


    def __repr__(self) -> str:
        """Return a string representation of the ColorConfig object."""
        return (
            f"ColorConfig(BitDepth={self.BitDepth}, NumPlanes={self.NumPlanes}, mono_chrome={self.mono_chrome}, "
            f"primaries={self.color_primaries if self.color_description_present_flag else 'N/A'}, "
            f"subsampling_x={self.subsampling_x if not self.mono_chrome else 'N/A'})"
        )

# --- Helper Python classes for FrameHeader nested structures ---

class SuperresParams:
    """
    Represents super-resolution parameters from an AV1 Frame Header.

    Corresponds to the `superres_params` struct in the AV1 specification.

    :ivar use_superres: Indicates if super-resolution is used for this frame.
    :ivar coded_denom: Denominator for upscaling factor (fixed point `8 + coded_denom`).
    :ivar superres_upscaled_width: Upscaled width of the frame after super-resolution.
    :ivar superres_upscaled_height: Upscaled height of the frame after super-resolution.
    """
    def __init__(self, c_params: _c_wrapper.OBPSuperresParams):
        """
        Initializes SuperresParams from a ctypes OBPSuperresParams object.

        :param c_params: The ctypes OBPSuperresParams structure.
        :type c_params: _c_wrapper.OBPSuperresParams
        """
        self.use_superres: int = c_params.use_superres
        self.coded_denom: int = c_params.coded_denom
        self.superres_upscaled_width: int = c_params.superres_upscaled_width
        self.superres_upscaled_height: int = c_params.superres_upscaled_height
    def __repr__(self) -> str:
        """Return a string representation of the SuperresParams object."""
        return f"SuperresParams(use_superres={self.use_superres}, coded_denom={self.coded_denom}, upscaled_width={self.superres_upscaled_width}, upscaled_height={self.superres_upscaled_height})"

class InterpolationFilter:
    """
    Represents the interpolation_filter value from an AV1 Frame Header.

    This is a simple wrapper for the integer value representing the filter type.
    See AV1 specification section 6.8.8 for interpolation filter semantics.

    :ivar value: The integer value of the interpolation filter.
    """
    def __init__(self, c_filter: _c_wrapper.OBPInterpolationFilter):
        """
        Initializes InterpolationFilter from a ctypes OBPInterpolationFilter object.

        :param c_filter: The ctypes OBPInterpolationFilter structure.
        :type c_filter: _c_wrapper.OBPInterpolationFilter
        """
        self.value: int = c_filter.value
    def __repr__(self) -> str:
        """Return a string representation of the InterpolationFilter object."""
        return f"InterpolationFilter(value={self.value})"

class TileInfo:
    """
    Represents tile information from an AV1 Frame Header.

    Corresponds to the `tile_info` struct in the AV1 specification.

    :ivar uniform_tile_spacing_flag: Indicates if tile spacing is uniform.
    :ivar MiColStarts: List of column start positions for tiles in mi_units.
    :ivar MiRowStarts: List of row start positions for tiles in mi_units.
    :ivar width_in_sbs_minus_1: List of tile widths in superblocks minus 1.
    :ivar height_in_sbs_minus_1: List of tile heights in superblocks minus 1.
    :ivar context_update_tile_id: ID of the tile used for context updates.
    :ivar tile_cols: Number of tile columns.
    :ivar tile_rows: Number of tile rows.
    """
    def __init__(self, c_info: _c_wrapper.OBPTileInfo):
        """
        Initializes TileInfo from a ctypes OBPTileInfo object.

        :param c_info: The ctypes OBPTileInfo structure.
        :type c_info: _c_wrapper.OBPTileInfo
        """
        self.uniform_tile_spacing_flag: int = c_info.uniform_tile_spacing_flag
        self.MiColStarts: list[int] = _c_array_to_list(c_info.MiColStarts)
        self.MiRowStarts: list[int] = _c_array_to_list(c_info.MiRowStarts)
        self.width_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.width_in_sbs_minus_1)
        self.height_in_sbs_minus_1: list[int] = _c_array_to_list(c_info.height_in_sbs_minus_1)
        self.context_update_tile_id: int = c_info.context_update_tile_id
        self.tile_cols: int = c_info.tile_cols
        self.tile_rows: int = c_info.tile_rows
    def __repr__(self) -> str:
        """Return a string representation of the TileInfo object."""
        return f"TileInfo(tile_cols={self.tile_cols}, tile_rows={self.tile_rows}, uniform_spacing={self.uniform_tile_spacing_flag}, ...)"

class QuantizationParams:
    """
    Represents quantization parameters from an AV1 Frame Header.

    Corresponds to the `quantization_params` struct in the AV1 specification.

    :ivar base_q_idx: Base quantization index.
    :ivar DeltaQYDc: DC quantization parameter delta for Y plane.
    :ivar DeltaQUDc: DC quantization parameter delta for U plane.
    :ivar DeltaQUAc: AC quantization parameter delta for U plane.
    :ivar DeltaQVDc: DC quantization parameter delta for V plane.
    :ivar DeltaQVAc: AC quantization parameter delta for V plane.
    :ivar using_qmatrix: Flag indicating if a quantization matrix is used.
    :ivar qm_y: Quantization matrix level for Y plane.
    :ivar qm_u: Quantization matrix level for U plane.
    :ivar qm_v: Quantization matrix level for V plane.
    """
    def __init__(self, c_params: _c_wrapper.OBPQuantizationParams):
        """
        Initializes QuantizationParams from a ctypes OBPQuantizationParams object.

        :param c_params: The ctypes OBPQuantizationParams structure.
        :type c_params: _c_wrapper.OBPQuantizationParams
        """
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
        """Return a string representation of the QuantizationParams object."""
        return f"QuantizationParams(base_q_idx={self.base_q_idx}, using_qmatrix={self.using_qmatrix}, ...)"

class SegmentationParams:
    """
    Represents segmentation parameters from an AV1 Frame Header.

    Corresponds to the `segmentation_params` struct in the AV1 specification.

    :ivar segmentation_enabled: Flag indicating if segmentation is enabled.
    :ivar segmentation_update_map: Flag indicating if the segmentation map is updated.
    :ivar segmentation_temporal_update: Flag indicating if temporal updates for segmentation are used.
    :ivar segmentation_update_data: Flag indicating if segmentation data is updated.
    :ivar feature_enabled: List of lists indicating which features are enabled for each segment.
    :ivar feature_data: List of lists containing data for each enabled feature in each segment.
    """
    def __init__(self, c_params: _c_wrapper.OBPSegmentationParams):
        """
        Initializes SegmentationParams from a ctypes OBPSegmentationParams object.

        :param c_params: The ctypes OBPSegmentationParams structure.
        :type c_params: _c_wrapper.OBPSegmentationParams
        """
        self.segmentation_enabled: int = c_params.segmentation_enabled
        self.segmentation_update_map: int = c_params.segmentation_update_map
        self.segmentation_temporal_update: int = c_params.segmentation_temporal_update
        self.segmentation_update_data: int = c_params.segmentation_update_data
        self.feature_enabled: list[list[int]] = [_c_array_to_list(c_params.feature_enabled[i]) for i in range(4)] # SEG_LVL_MAX = 4 in AV1 spec; C struct has 8 segments, 8 features
        self.feature_data: list[list[int]] = [_c_array_to_list(c_params.feature_data[i]) for i in range(4)] # C struct has 8 segments, 8 features
    def __repr__(self) -> str:
        """Return a string representation of the SegmentationParams object."""
        return f"SegmentationParams(enabled={self.segmentation_enabled}, update_map={self.segmentation_update_map}, ...)"

class DeltaQParams:
    """
    Represents delta quantization parameters from an AV1 Frame Header.

    Corresponds to the `delta_q_params` struct in the AV1 specification.

    :ivar delta_q_present: Flag indicating if delta quantization values are present.
    :ivar delta_q_res: Resolution of delta quantization values.
    """
    def __init__(self, c_params: _c_wrapper.OBPDeltaQParams):
        """
        Initializes DeltaQParams from a ctypes OBPDeltaQParams object.

        :param c_params: The ctypes OBPDeltaQParams structure.
        :type c_params: _c_wrapper.OBPDeltaQParams
        """
        self.delta_q_present: int = c_params.delta_q_present
        self.delta_q_res: int = c_params.delta_q_res
    def __repr__(self) -> str:
        """Return a string representation of the DeltaQParams object."""
        return f"DeltaQParams(present={self.delta_q_present}, res={self.delta_q_res})"

class DeltaLFParams:
    """
    Represents delta loop filter parameters from an AV1 Frame Header.

    Corresponds to the `delta_lf_params` struct in the AV1 specification.

    :ivar delta_lf_present: Flag indicating if delta loop filter values are present.
    :ivar delta_lf_res: Resolution of delta loop filter values.
    :ivar delta_lf_multi: Indicates if separate delta loop filter values are present for horizontal luma, vertical luma, U, and V planes.
    """
    def __init__(self, c_params: _c_wrapper.OBPDeltaLFParams):
        """
        Initializes DeltaLFParams from a ctypes OBPDeltaLFParams object.

        :param c_params: The ctypes OBPDeltaLFParams structure.
        :type c_params: _c_wrapper.OBPDeltaLFParams
        """
        self.delta_lf_present: int = c_params.delta_lf_present
        self.delta_lf_res: int = c_params.delta_lf_res
        self.delta_lf_multi: int = c_params.delta_lf_multi
    def __repr__(self) -> str:
        """Return a string representation of the DeltaLFParams object."""
        return f"DeltaLFParams(present={self.delta_lf_present}, res={self.delta_lf_res}, multi={self.delta_lf_multi})"

class LoopFilterParams:
    """
    Represents loop filter parameters from an AV1 Frame Header.

    Corresponds to the `loop_filter_params` struct in the AV1 specification.

    :ivar loop_filter_level: Array of loop filter levels for Y_HORZ, Y_VERT, U, V.
    :ivar loop_filter_sharpness: Loop filter sharpness level.
    :ivar loop_filter_delta_enabled: Flag indicating if loop filter delta values are enabled.
    :ivar loop_filter_ref_deltas: List of loop filter reference deltas.
    :ivar loop_filter_mode_deltas: List of loop filter mode deltas.
    """
    def __init__(self, c_params: _c_wrapper.OBPLoopFilterParams):
        """
        Initializes LoopFilterParams from a ctypes OBPLoopFilterParams object.

        :param c_params: The ctypes OBPLoopFilterParams structure.
        :type c_params: _c_wrapper.OBPLoopFilterParams
        """
        self.loop_filter_level: list[int] = _c_array_to_list(c_params.loop_filter_level)
        self.loop_filter_sharpness: int = c_params.loop_filter_sharpness
        self.loop_filter_delta_enabled: int = c_params.loop_filter_delta_enabled
        self.loop_filter_ref_deltas: list[int] = _c_array_to_list(c_params.loop_filter_ref_deltas)
        self.loop_filter_mode_deltas: list[int] = _c_array_to_list(c_params.loop_filter_mode_deltas)
    def __repr__(self) -> str:
        """Return a string representation of the LoopFilterParams object."""
        return f"LoopFilterParams(level_y_v={self.loop_filter_level[1]}, sharpness={self.loop_filter_sharpness}, ...)"

class CdefParams:
    """
    Represents Constrained Directional Enhancement Filter (CDEF) parameters from an AV1 Frame Header.

    Corresponds to the `cdef_params` struct in the AV1 specification.

    :ivar cdef_damping_minus_3: CDEF damping value minus 3.
    :ivar cdef_bits: Number of CDEF bits.
    :ivar cdef_y_pri_strength: List of CDEF primary strengths for Y plane.
    :ivar cdef_y_sec_strength: List of CDEF secondary strengths for Y plane.
    :ivar cdef_uv_pri_strength: List of CDEF primary strengths for UV planes.
    :ivar cdef_uv_sec_strength: List of CDEF secondary strengths for UV planes.
    """
    def __init__(self, c_params: _c_wrapper.OBPCdefParams):
        """
        Initializes CdefParams from a ctypes OBPCdefParams object.

        :param c_params: The ctypes OBPCdefParams structure.
        :type c_params: _c_wrapper.OBPCdefParams
        """
        self.cdef_damping_minus_3: int = c_params.cdef_damping_minus_3
        self.cdef_bits: int = c_params.cdef_bits
        self.cdef_y_pri_strength: list[int] = _c_array_to_list(c_params.cdef_y_pri_strength)
        self.cdef_y_sec_strength: list[int] = _c_array_to_list(c_params.cdef_y_sec_strength)
        self.cdef_uv_pri_strength: list[int] = _c_array_to_list(c_params.cdef_uv_pri_strength)
        self.cdef_uv_sec_strength: list[int] = _c_array_to_list(c_params.cdef_uv_sec_strength)
    def __repr__(self) -> str:
        """Return a string representation of the CdefParams object."""
        return f"CdefParams(damping={self.cdef_damping_minus_3+3}, bits={self.cdef_bits}, ...)"

class LrParams:
    """
    Represents Loop Restoration (LR) parameters from an AV1 Frame Header.

    Corresponds to the `lr_params` struct in the AV1 specification.

    :ivar lr_type: List of loop restoration types for Y, U, V planes.
    :ivar lr_unit_shift: Loop restoration unit shift value.
    :ivar lr_uv_shift: Loop restoration UV shift value (if subsampling is present).
    """
    def __init__(self, c_params: _c_wrapper.OBPLrParams):
        """
        Initializes LrParams from a ctypes OBPLrParams object.

        :param c_params: The ctypes OBPLrParams structure.
        :type c_params: _c_wrapper.OBPLrParams
        """
        self.lr_type: list[int] = _c_array_to_list(c_params.lr_type)
        self.lr_unit_shift: int = c_params.lr_unit_shift
        self.lr_uv_shift: int = c_params.lr_uv_shift
    def __repr__(self) -> str:
        """Return a string representation of the LrParams object."""
        return f"LrParams(type_y={self.lr_type[0]}, unit_shift={self.lr_unit_shift}, uv_shift={self.lr_uv_shift})"

class GlobalMotionParams:
    """
    Represents global motion parameters for a single reference frame.

    Part of the `global_motion_params` table in an AV1 Frame Header.

    :ivar gm_type: Type of global motion model for this reference frame.
    :ivar gm_params: List of global motion parameters (6 integers for affine/rotation/translation).
    """
    def __init__(self, gm_type: int, gm_params: Sequence[int]):
        """
        Initializes GlobalMotionParams.

        :param gm_type: Integer type of the global motion model.
        :type gm_type: int
        :param gm_params: Sequence of 6 integer global motion parameters.
        :type gm_params: Sequence[int]
        """
        self.gm_type: int = gm_type
        self.gm_params: list[int] = list(gm_params) # Should be 6 elements
    def __repr__(self) -> str:
        """Return a string representation of the GlobalMotionParams object."""
        return f"GlobalMotionParams(type={self.gm_type}, params={self.gm_params[:2]}...)"

class FilmGrainParameters:
    """
    Represents film grain synthesis parameters from an AV1 Frame Header.

    Corresponds to the `film_grain_params` struct in the AV1 specification.
    This class holds all parameters necessary for applying film grain synthesis.

    :ivar apply_grain: Flag indicating if film grain should be applied.
    :ivar grain_seed: Starting seed for pseudo-random grain generation.
    :ivar update_grain: Flag indicating if film grain parameters are updated in this frame.
    :ivar film_grain_params_ref_idx: Reference index for film grain parameters.
    :ivar num_y_points: Number of points for the Y plane piece-wise linear scaling function.
    :ivar point_y_value: List of Y component values for piece-wise linear scaling.
    :ivar point_y_scaling: List of scaling values for Y component piece-wise linear function.
    :ivar chroma_scaling_from_luma: Flag indicating if chroma scaling is derived from luma.
    :ivar num_cb_points: Number of points for the Cb plane piece-wise linear scaling function.
    :ivar point_cb_value: List of Cb component values for piece-wise linear scaling.
    :ivar point_cb_scaling: List of scaling values for Cb component piece-wise linear function.
    :ivar num_cr_points: Number of points for the Cr plane piece-wise linear scaling function.
    :ivar point_cr_value: List of Cr component values for piece-wise linear scaling.
    :ivar point_cr_scaling: List of scaling values for Cr component piece-wise linear function.
    :ivar grain_scaling_minus_8: Grain scaling factor minus 8.
    :ivar ar_coeff_lag: Lag for auto-regressive coefficients.
    :ivar ar_coeffs_y_plus_128: Auto-regressive coefficients for Y plane, offset by 128.
    :ivar ar_coeffs_cb_plus_128: Auto-regressive coefficients for Cb plane, offset by 128.
    :ivar ar_coeffs_cr_plus_128: Auto-regressive coefficients for Cr plane, offset by 128.
    :ivar ar_coeff_shift_minus_6: Bit shift for auto-regressive coefficients, minus 6.
    :ivar grain_scale_shift: Shift value for grain scaling.
    :ivar cb_mult: Multiplier for Cb component grain.
    :ivar cb_luma_mult: Multiplier for Cb component based on luma.
    :ivar cb_offset: Offset for Cb component grain.
    :ivar cr_mult: Multiplier for Cr component grain.
    :ivar cr_luma_mult: Multiplier for Cr component based on luma.
    :ivar cr_offset: Offset for Cr component grain.
    :ivar overlap_flag: Flag indicating if overlap is applied during grain synthesis.
    :ivar clip_to_restricted_range: Flag indicating if output should be clipped to restricted color range.
    """
    def __init__(self, c_params: _c_wrapper.OBPFilmGrainParameters):
        """
        Initializes FilmGrainParameters from a ctypes OBPFilmGrainParameters object.

        :param c_params: The ctypes OBPFilmGrainParameters structure.
        :type c_params: _c_wrapper.OBPFilmGrainParameters
        """
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

    Corresponds to the `metadata_itut_t35` structure in AV1 specification.

    :ivar itu_t_t35_country_code: Country code as defined in ITU-T T.35 Annex A.
    :ivar itu_t_t35_terminal_provider_code: Terminal provider code.
    :ivar itu_t_t35_terminal_provider_oriented_code: Terminal provider oriented code.
    :ivar itu_t_t35_payload_bytes: Payload bytes of the T.35 metadata.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataITUTT35):
        """
        Initializes MetadataITUTT35 from a ctypes OBPMetadataITUTT35 object.

        :param c_meta: The ctypes OBPMetadataITUTT35 structure.
        :type c_meta: _c_wrapper.OBPMetadataITUTT35
        """
        self.itu_t_t35_country_code: int = c_meta.itu_t_t35_country_code
        self.itu_t_t35_terminal_provider_code: int = c_meta.itu_t_t35_terminal_provider_code
        self.itu_t_t35_terminal_provider_oriented_code: int = c_meta.itu_t_t35_terminal_provider_oriented_code
        payload_size = c_meta.itu_t_t35_payload_byte_count
        self.itu_t_t35_payload_bytes: bytes = ctypes.string_at(c_meta.itu_t_t35_payload_bytes, payload_size) if c_meta.itu_t_t35_payload_bytes and payload_size > 0 else b""
    def __repr__(self) -> str:
        """Return a string representation of the MetadataITUTT35 object."""
        return f"MetadataITUTT35(country_code={self.itu_t_t35_country_code}, provider_code={self.itu_t_t35_terminal_provider_code}, payload_len={len(self.itu_t_t35_payload_bytes)})"

class MetadataHDRCLL:
    """
    Represents HDR Content Light Level (CLL) metadata from an AV1 Metadata OBU.

    Corresponds to the `metadata_hdr_cll` structure in AV1 specification.

    :ivar max_cll: Maximum Content Light Level.
    :ivar max_fall: Maximum Frame-Average Light Level.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRCLL):
        """
        Initializes MetadataHDRCLL from a ctypes OBPMetadataHDRCLL object.

        :param c_meta: The ctypes OBPMetadataHDRCLL structure.
        :type c_meta: _c_wrapper.OBPMetadataHDRCLL
        """
        self.max_cll: int = c_meta.max_cll
        self.max_fall: int = c_meta.max_fall
    def __repr__(self) -> str:
        """Return a string representation of the MetadataHDRCLL object."""
        return f"MetadataHDRCLL(max_cll={self.max_cll}, max_fall={self.max_fall})"

class MetadataHDRMDCV:
    """
    Represents HDR Mastering Display Color Volume (MDCV) metadata from an AV1 Metadata OBU.

    Corresponds to the `metadata_hdr_mdcv` structure in AV1 specification.

    :ivar primary_chromaticity_x: List of X coordinates for primary chromaticities.
    :ivar primary_chromaticity_y: List of Y coordinates for primary chromaticities.
    :ivar white_point_chromaticity_x: X coordinate for white point chromaticity.
    :ivar white_point_chromaticity_y: Y coordinate for white point chromaticity.
    :ivar luminance_max: Maximum mastering display luminance.
    :ivar luminance_min: Minimum mastering display luminance.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataHDRMDCV):
        """
        Initializes MetadataHDRMDCV from a ctypes OBPMetadataHDRMDCV object.

        :param c_meta: The ctypes OBPMetadataHDRMDCV structure.
        :type c_meta: _c_wrapper.OBPMetadataHDRMDCV
        """
        self.primary_chromaticity_x: list[int] = _c_array_to_list(c_meta.primary_chromaticity_x)
        self.primary_chromaticity_y: list[int] = _c_array_to_list(c_meta.primary_chromaticity_y)
        self.white_point_chromaticity_x: int = c_meta.white_point_chromaticity_x
        self.white_point_chromaticity_y: int = c_meta.white_point_chromaticity_y
        self.luminance_max: int = c_meta.luminance_max # Stored as u32 in c_wrapper for flexibility
        self.luminance_min: int = c_meta.luminance_min # Stored as u32 in c_wrapper for flexibility
    def __repr__(self) -> str:
        """Return a string representation of the MetadataHDRMDCV object."""
        return f"MetadataHDRMDCV(wp_x={self.white_point_chromaticity_x}, lum_max={self.luminance_max}, ...)"

class ScalabilityStructure:
    """
    Represents scalability structure information from an AV1 Scalability Metadata OBU.

    This is part of the `metadata_scalability` structure.

    :ivar spatial_layers_cnt_minus_1: Number of spatial layers minus 1.
    :ivar spatial_layer_dimensions_present_flag: Flag indicating if spatial layer dimensions are present.
    :ivar spatial_layer_description_present_flag: Flag indicating if spatial layer descriptions are present.
    :ivar temporal_group_description_present_flag: Flag indicating if temporal group descriptions are present.
    :ivar scalability_structure_reserved_3bits: Reserved bits.
    """
    def __init__(self, c_struct: _c_wrapper.OBPScalabilityStructure):
        """
        Initializes ScalabilityStructure from a ctypes OBPScalabilityStructure object.

        :param c_struct: The ctypes OBPScalabilityStructure structure.
        :type c_struct: _c_wrapper.OBPScalabilityStructure
        """
        self.spatial_layers_cnt_minus_1: int = c_struct.spatial_layers_cnt_minus_1
        self.spatial_layer_dimensions_present_flag: int = c_struct.spatial_layer_dimensions_present_flag
        self.spatial_layer_description_present_flag: int = c_struct.spatial_layer_description_present_flag
        self.temporal_group_description_present_flag: int = c_struct.temporal_group_description_present_flag
        self.scalability_structure_reserved_3bits: int = c_struct.scalability_structure_reserved_3bits
    def __repr__(self) -> str:
        """Return a string representation of the ScalabilityStructure object."""
        return f"ScalabilityStructure(spatial_layers={self.spatial_layers_cnt_minus_1+1}, ...)"

class MetadataScalability:
    """
    Represents scalability metadata from an AV1 Metadata OBU.

    Corresponds to the `metadata_scalability` structure in AV1 specification.

    :ivar scalability_mode_idc: Scalability mode identifier.
    :ivar scalability_structure: Nested :class:`ScalabilityStructure` object.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataScalability):
        """
        Initializes MetadataScalability from a ctypes OBPMetadataScalability object.

        :param c_meta: The ctypes OBPMetadataScalability structure.
        :type c_meta: _c_wrapper.OBPMetadataScalability
        """
        self.scalability_mode_idc: int = c_meta.scalability_mode_idc
        self.scalability_structure: ScalabilityStructure = ScalabilityStructure(c_meta.scalability_structure)
    def __repr__(self) -> str:
        """Return a string representation of the MetadataScalability object."""
        return f"MetadataScalability(mode_idc={self.scalability_mode_idc}, structure={self.scalability_structure})"

class MetadataTimecode:
    """
    Represents timecode metadata from an AV1 Metadata OBU.

    Corresponds to the `metadata_timecode` structure in AV1 specification.

    :ivar counting_type: Type of time counting used.
    :ivar full_timestamp_flag: Flag for full timestamp presence.
    :ivar discontinuity_flag: Flag indicating a discontinuity in timecode.
    :ivar cnt_dropped_flag: Flag indicating dropped frames.
    :ivar n_frames: Number of frames in timecode.
    :ivar seconds_value: Seconds value of timecode.
    :ivar minutes_value: Minutes value of timecode.
    :ivar hours_value: Hours value of timecode.
    :ivar seconds_flag: Flag indicating seconds value is present.
    :ivar minutes_flag: Flag indicating minutes value is present.
    :ivar hours_flag: Flag indicating hours value is present.
    :ivar time_offset_length: Length of the time offset value.
    :ivar time_offset_value: Time offset value.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataTimecode):
        """
        Initializes MetadataTimecode from a ctypes OBPMetadataTimecode object.

        :param c_meta: The ctypes OBPMetadataTimecode structure.
        :type c_meta: _c_wrapper.OBPMetadataTimecode
        """
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
        """Return a string representation of the MetadataTimecode object."""
        return f"MetadataTimecode(h={self.hours_value}, m={self.minutes_value}, s={self.seconds_value}, f={self.n_frames}, ...)"

class MetadataUnregistered:
    """
    Represents unregistered user-private metadata from an AV1 Metadata OBU.

    Corresponds to the `unregistered` part of the `metadata` structure when the
    metadata type is not one of the specifically defined types.

    :ivar uuid: 16-byte UUID identifying the unregistered metadata format.
    :ivar payload: Payload bytes of the unregistered metadata.
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadataUnregistered):
        """
        Initializes MetadataUnregistered from a ctypes OBPMetadataUnregistered object.

        :param c_meta: The ctypes OBPMetadataUnregistered structure.
        :type c_meta: _c_wrapper.OBPMetadataUnregistered
        """
        self.uuid: bytes = bytes(c_meta.uuid) # c_uint8_t * 16
        payload_size = c_meta.payload_byte_count
        self.payload: bytes = ctypes.string_at(c_meta.payload, payload_size) if c_meta.payload and payload_size > 0 else b""
    def __repr__(self) -> str:
        """Return a string representation of the MetadataUnregistered object."""
        return f"MetadataUnregistered(uuid={self.uuid.hex()}, payload_len={len(self.payload)})"


# --- Helper Python classes for TileList OBU nested structures ---
class TileListEntry:
    """
    Represents a single entry in a Tile List OBU.

    Each entry describes a tile from an anchor frame to be copied.

    :ivar anchor_frame_idx: Index of the anchor frame.
    :ivar anchor_tile_row: Row index of the tile in the anchor frame.
    :ivar anchor_tile_col: Column index of the tile in the anchor frame.
    :ivar tile_data_size_minus_1: Size of the coded tile data minus 1.
    :ivar coded_tile_data: The actual bytes of the coded tile data.
    """
    def __init__(self, c_entry: _c_wrapper.OBPTileListEntry):
        """
        Initializes TileListEntry from a ctypes OBPTileListEntry object.

        :param c_entry: The ctypes OBPTileListEntry structure.
        :type c_entry: _c_wrapper.OBPTileListEntry
        """
        self.anchor_frame_idx: int = c_entry.anchor_frame_idx
        self.anchor_tile_row: int = c_entry.anchor_tile_row
        self.anchor_tile_col: int = c_entry.anchor_tile_col
        self.tile_data_size_minus_1: int = c_entry.tile_data_size_minus_1
        # self.tile_data_size_minus_1 is for information; actual data size comes from c_entry.coded_tile_data_size

        if c_entry.coded_tile_data and c_entry.coded_tile_data_size > 0:
            self.coded_tile_data: bytes = ctypes.string_at(c_entry.coded_tile_data, c_entry.coded_tile_data_size)
        else:
            self.coded_tile_data: bytes = b""

    def __repr__(self) -> str:
        """Return a string representation of the TileListEntry object."""
        return f"TileListEntry(anchor_idx={self.anchor_frame_idx}, row={self.anchor_tile_row}, col={self.anchor_tile_col}, size={len(self.coded_tile_data)})"


# --- Main Python OBU Classes ---
class SequenceHeader:
    """
    Represents a parsed AV1 Sequence Header OBU.

    This class provides access to all parameters defined in the sequence header,
    which are essential for initializing a decoder and understanding the
    bitstream's global properties. It wraps the `OBPSequenceHeader` C structure
    from `_c_wrapper.py`.

    Many attributes correspond directly to fields in the AV1 specification
    for the sequence_header_obu() syntax.

    :ivar seq_profile: AV1 profile of the bitstream.
    :ivar still_picture: Indicates if the video is a still picture.
    :ivar reduced_still_picture_header: Indicates if a reduced header is used for still pictures.
    :ivar timing_info_present_flag: Flag for presence of :class:`TimingInfo`.
    :ivar timing_info: Optional :class:`TimingInfo` object.
    :ivar decoder_model_info_present_flag: Flag for presence of :class:`DecoderModelInfo`.
    :ivar decoder_model_info: Optional :class:`DecoderModelInfo` object.
    :ivar initial_display_delay_present_flag: Flag for initial display delay presence.
    :ivar operating_points_cnt_minus_1: Number of operating points minus 1.
    :ivar operating_point_idc: List of IDC for each operating point.
    :ivar seq_level_idx: List of sequence level indices for each operating point.
    :ivar seq_tier: List of sequence tiers for each operating point.
    :ivar decoder_model_present_for_this_op: List of flags indicating if decoder model info is present for each OP.
    :ivar initial_display_delay_present_for_this_op: List of flags indicating if initial display delay is present for each OP.
    :ivar operating_parameters_info: List of :class:`OperatingParametersInfo` objects for each OP.
    :ivar initial_display_delay_minus_1: List of initial display delays minus 1 for each OP.
    :ivar frame_width_bits_minus_1: Bits to represent frame width minus 1.
    :ivar frame_height_bits_minus_1: Bits to represent frame height minus 1.
    :ivar max_frame_width_minus_1: Maximum frame width minus 1.
    :ivar max_frame_height_minus_1: Maximum frame height minus 1.
    :ivar frame_id_numbers_present_flag: Flag for presence of frame ID numbers.
    :ivar delta_frame_id_length_minus_2: Length of delta frame ID minus 2.
    :ivar additional_frame_id_length_minus_1: Length of additional frame ID minus 1.
    :ivar use_128x128_superblock: Flag for use of 128x128 superblocks.
    :ivar enable_filter_intra: Flag for enabling intra filter.
    :ivar enable_intra_edge_filter: Flag for enabling intra edge filter.
    :ivar enable_interintra_compound: Flag for enabling inter-intra compound.
    :ivar enable_masked_compound: Flag for enabling masked compound.
    :ivar enable_warped_motion: Flag for enabling warped motion.
    :ivar enable_dual_filter: Flag for enabling dual filter.
    :ivar enable_order_hint: Flag for enabling order hint.
    :ivar enable_jnt_comp: Flag for enabling joint compound.
    :ivar enable_ref_frame_mvs: Flag for enabling reference frame MVs.
    :ivar seq_choose_screen_content_tools: Flag for choosing screen content tools.
    :ivar seq_force_screen_content_tools: Flag for forcing screen content tools.
    :ivar seq_choose_integer_mv: Flag for choosing integer MV.
    :ivar seq_force_integer_mv: Flag for forcing integer MV.
    :ivar order_hint_bits_minus_1: Number of order hint bits minus 1.
    :ivar enable_superres: Flag for enabling super-resolution.
    :ivar enable_cdef: Flag for enabling Constrained Directional Enhancement Filter.
    :ivar enable_restoration: Flag for enabling Loop Restoration filter.
    :ivar color_config: :class:`ColorConfig` object.
    :ivar film_grain_params_present: Flag for presence of film grain parameters.
    :ivar FrameWidth: Calculated frame width based on max_frame_width_minus_1. (Note: This is a property of the sequence, specific frames can have different dimensions if frame_size_override_flag is set in FrameHeader)
    :ivar FrameHeight: Calculated frame height based on max_frame_height_minus_1.
    :ivar OrderHintBits: Calculated number of bits for order hint.
    """
    def __init__(self, c_seq_header: _c_wrapper.OBPSequenceHeader):
        """
        Initializes SequenceHeader from a ctypes OBPSequenceHeader object.

        :param c_seq_header: The ctypes OBPSequenceHeader structure.
        :type c_seq_header: _c_wrapper.OBPSequenceHeader
        """
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
    Represents a parsed AV1 Frame Header OBU.

    This class wraps the `OBPFrameHeader` C structure from `_c_wrapper.py` and
    provides access to frame-specific parameters. Many attributes correspond
    directly to fields in the AV1 specification for `uncompressed_header_obu()`.

    :ivar show_existing_frame: Flag indicating if this frame shows an existing frame.
    :vartype show_existing_frame: int
    :ivar frame_to_show_map_idx: Index of the reference frame to show (if show_existing_frame is true).
    :vartype frame_to_show_map_idx: int
    :ivar frame_presentation_time: Presentation time of the frame.
        Validity depends on sequence header's `timing_info_present_flag` and not `show_existing_frame`.
    :vartype frame_presentation_time: int
    :ivar display_frame_id: Display ID for the frame.
    :vartype display_frame_id: int
    :ivar frame_type: Type of the frame (e.g., Key, Inter). See :class:`~._c_wrapper.OBPFrameType`.
    :vartype frame_type: _c_wrapper.OBPFrameType | int
    :ivar show_frame: Flag indicating if this frame is to be shown.
    :vartype show_frame: int
    :ivar showable_frame: Flag indicating if this frame can be shown (used with show_existing_frame).
    :vartype showable_frame: int
    :ivar error_resilient_mode: Flag indicating if error resilient mode is enabled.
    :vartype error_resilient_mode: int
    :ivar disable_cdf_update: Flag to disable CDF update for this frame.
    :vartype disable_cdf_update: int
    :ivar allow_screen_content_tools: Flag allowing screen content tools for this frame.
    :vartype allow_screen_content_tools: int
    :ivar force_integer_mv: Flag forcing integer motion vectors.
    :vartype force_integer_mv: int
    :ivar current_frame_id: ID of the current frame.
    :vartype current_frame_id: int
    :ivar frame_size_override_flag: Flag indicating if frame size is overridden.
    :vartype frame_size_override_flag: int
    :ivar order_hint: Order hint for this frame.
    :vartype order_hint: int
    :ivar primary_ref_frame: Primary reference frame index.
    :vartype primary_ref_frame: int
    :ivar refresh_frame_flags: Bitmask indicating which reference frames are refreshed.
    :vartype refresh_frame_flags: int
    :ivar ref_order_hint: List of order hints for reference frames.
    :vartype ref_order_hint: list[int]
    :ivar allow_high_precision_mv: Flag allowing high precision motion vectors.
    :vartype allow_high_precision_mv: int
    :ivar interpolation_filter: :class:`InterpolationFilter` object.
    :vartype interpolation_filter: InterpolationFilter
    :ivar is_motion_mode_switchable: Flag indicating if motion mode is switchable.
    :vartype is_motion_mode_switchable: int
    :ivar use_ref_frame_mvs: Flag to use reference frame motion vectors.
    :vartype use_ref_frame_mvs: int
    :ivar disable_frame_end_update_cdf: Flag to disable CDF update at frame end.
    :vartype disable_frame_end_update_cdf: int
    :ivar allow_intrabc: Flag allowing intra block copy.
    :vartype allow_intrabc: int
    :ivar palette_mode_enabled: Flag indicating if palette mode is enabled.
    :vartype palette_mode_enabled: int
    :ivar frame_width_minus_1: Frame width minus 1.
    :vartype frame_width_minus_1: int
    :ivar frame_height_minus_1: Frame height minus 1.
    :vartype frame_height_minus_1: int
    :ivar superres_params: :class:`SuperresParams` object.
    :vartype superres_params: SuperresParams
    :ivar render_width_minus_1: Render width minus 1.
    :vartype render_width_minus_1: int
    :ivar render_height_minus_1: Render height minus 1.
    :vartype render_height_minus_1: int
    :ivar FrameWidth: Calculated frame width.
    :vartype FrameWidth: int
    :ivar FrameHeight: Calculated frame height.
    :vartype FrameHeight: int
    :ivar MiCols: Frame width in Minimum Information units (mi_size).
    :vartype MiCols: int
    :ivar MiRows: Frame height in Minimum Information units (mi_size).
    :vartype MiRows: int
    :ivar tile_info: :class:`TileInfo` object.
    :vartype tile_info: TileInfo
    :ivar quantization_params: :class:`QuantizationParams` object.
    :vartype quantization_params: QuantizationParams
    :ivar segmentation_params: :class:`SegmentationParams` object.
    :vartype segmentation_params: SegmentationParams
    :ivar delta_q_params: :class:`DeltaQParams` object for quantization.
    :vartype delta_q_params: DeltaQParams
    :ivar delta_lf_params: :class:`DeltaLFParams` object for loop filter.
    :vartype delta_lf_params: DeltaLFParams
    :ivar loop_filter_params: :class:`LoopFilterParams` object.
    :vartype loop_filter_params: LoopFilterParams
    :ivar cdef_params: :class:`CdefParams` object for Constrained Directional Enhancement Filter.
    :vartype cdef_params: CdefParams
    :ivar lr_params: :class:`LrParams` object for Loop Restoration.
    :vartype lr_params: LrParams
    :ivar skip_mode_present: Flag indicating if skip mode is present.
    :vartype skip_mode_present: int
    :ivar reference_select: Flag for reference select.
    :vartype reference_select: int
    :ivar allow_warped_motion: Flag allowing warped motion.
    :vartype allow_warped_motion: int
    :ivar reduced_tx_set: Flag indicating if reduced transform set is used.
    :vartype reduced_tx_set: int
    :ivar global_motion_params: List of :class:`GlobalMotionParams` objects for reference frames.
    :vartype global_motion_params: list[GlobalMotionParams]
    :ivar film_grain_params: Optional :class:`FilmGrainParameters` object if film grain is present in sequence header.
    :vartype film_grain_params: FilmGrainParameters, optional
    :ivar large_scale_tile: Flag indicating if large scale tile mode is used.
    :vartype large_scale_tile: int
    """
    def __init__(self, c_fh: _c_wrapper.OBPFrameHeader, sequence_header: SequenceHeader):
        """
        Initializes FrameHeader from a ctypes OBPFrameHeader object and its associated SequenceHeader.

        :param c_fh: The ctypes OBPFrameHeader structure.
        :type c_fh: _c_wrapper.OBPFrameHeader
        :param sequence_header: The parsed :class:`SequenceHeader` object for context.
        :type sequence_header: SequenceHeader
        """
        self._c_frame_header = c_fh # Keep ref for other functions
        self._py_sequence_header = sequence_header # Keep ref for context

        self.show_existing_frame: int = c_fh.show_existing_frame
        self.frame_to_show_map_idx: int = c_fh.frame_to_show_map_idx
        
        # Access frame_presentation_time from the nested struct
        # Validity depends on sequence_header.timing_info_present_flag and not show_existing_frame
        self.frame_presentation_time: int = c_fh.temporal_point_info.frame_presentation_time
        
        self.display_frame_id: int = c_fh.display_frame_id
        try:
            self.frame_type: _c_wrapper.OBPFrameType | int = _c_wrapper.OBPFrameType(c_fh.frame_type)
        except ValueError:
            self.frame_type = c_fh.frame_type # Store as int if not a known enum member
        self.show_frame: int = c_fh.show_frame
        self.showable_frame: int = c_fh.showable_frame # If not show_frame, this is for show_existing_frame
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
        # TOTAL_REFS_PER_FRAME is 8 (LAST_FRAME to ALTREF_FRAME)
        # The C struct OBPGlobalMotionTable has gm_type[8] and gm_params[8][6]
        for i in range(8): 
            # Access members of the nested OBPGlobalMotionTable struct
            gm_type_val = c_fh.global_motion_params.gm_type[i]
            # gm_params is an array of 8 arrays, each of 6 int32_t.
            # So, c_fh.global_motion_params.gm_params[i] is a c_int32_t_Array_6
            gm_params_for_ref = _c_array_to_list(c_fh.global_motion_params.gm_params[i])
            self.global_motion_params.append(GlobalMotionParams(gm_type_val, gm_params_for_ref))

        if sequence_header.film_grain_params_present:
            self.film_grain_params: FilmGrainParameters | None = FilmGrainParameters(c_fh.film_grain_params)
        else:
            self.film_grain_params = None
        
        self.large_scale_tile: int = c_fh.large_scale_tile

    def __repr__(self) -> str:
        return (f"FrameHeader(type={self.frame_type}, width={self.FrameWidth}, height={self.FrameHeight}, "
                f"show_frame={self.show_frame}, order_hint={self.order_hint})")

class TileGroup:
    """
    Represents a parsed AV1 Tile Group OBU.

    This class wraps the `OBPTileGroup` C structure from `_c_wrapper.py`.
    It provides information about the tiles within a tile group, primarily their sizes.
    The actual tile data is not stored directly within this object but can be
    extracted from the larger OBU payload using the provided tile sizes.

    :ivar NumTiles: The number of tiles in this group.
    :vartype NumTiles: int
    :ivar tile_start_and_end_present_flag: Flag indicating if `tg_start` and `tg_end` are present.
    :vartype tile_start_and_end_present_flag: int
    :ivar tg_start: Optional start tile index for this group (valid if `tile_start_and_end_present_flag` is true).
    :vartype tg_start: int, optional
    :ivar tg_end: Optional end tile index for this group (valid if `tile_start_and_end_present_flag` is true).
    :vartype tg_end: int, optional
    :ivar TileSize: List of sizes for each tile in this group. The length of the list is `NumTiles`.
    :vartype TileSize: list[int]
    """
    def __init__(self, c_tg: _c_wrapper.OBPTileGroup):
        """
        Initializes TileGroup from a ctypes OBPTileGroup object.

        :param c_tg: The ctypes OBPTileGroup structure.
        :type c_tg: _c_wrapper.OBPTileGroup
        """
        self._c_tile_group = c_tg # Keep a reference if needed later, though unlikely for this class
        self.NumTiles: int = c_tg.NumTiles
        self.tile_start_and_end_present_flag: int = c_tg.tile_start_and_end_present_flag
        
        # tg_start and tg_end are only valid if tile_start_and_end_present_flag is true
        self.tg_start: int | None = c_tg.tg_start if self.tile_start_and_end_present_flag else None
        self.tg_end: int | None = c_tg.tg_end if self.tile_start_and_end_present_flag else None
        
        # TileSize is an array of uint64_t of size 4096 in C.
        # We should only copy up to NumTiles.
        self.TileSize: list[int] = _c_array_to_list(c_tg.TileSize, self.NumTiles)
        
    def __repr__(self) -> str:
        """Return a string representation of the TileGroup object."""
        repr_str = f"TileGroup(NumTiles={self.NumTiles}"
        if self.tile_start_and_end_present_flag:
            repr_str += f", tg_start={self.tg_start}, tg_end={self.tg_end}"
        repr_str += f", TileSizes_count={len(self.TileSize)})"
        return repr_str

class Metadata:
    """
    Represents a parsed AV1 Metadata OBU.

    This class wraps the `OBPMetadata` C structure. Depending on the
    `type_enum` (which corresponds to `OBPMetadataType`), one of the specific
    metadata attributes (e.g., `metadata_itut_t35`, `metadata_hdr_cll`) will be populated.

    :ivar type: The integer type of the metadata OBU.
    :vartype type: int
    :ivar type_enum: The metadata type as an :class:`~._c_wrapper.OBPMetadataType` enum member,
                     or the raw integer type if it's an unknown/reserved type.
    :vartype type_enum: _c_wrapper.OBPMetadataType | int
    :ivar obu_size: Size of the metadata OBU's payload (excluding the OBU header).
    :vartype obu_size: int
    :ivar metadata_itut_t35: Optional :class:`MetadataITUTT35` object if type is `OBP_METADATA_TYPE_ITUT_T35`.
    :vartype metadata_itut_t35: MetadataITUTT35, optional
    :ivar metadata_hdr_cll: Optional :class:`MetadataHDRCLL` object if type is `OBP_METADATA_TYPE_HDR_CLL`.
    :vartype metadata_hdr_cll: MetadataHDRCLL, optional
    :ivar metadata_hdr_mdcv: Optional :class:`MetadataHDRMDCV` object if type is `OBP_METADATA_TYPE_HDR_MDCV`.
    :vartype metadata_hdr_mdcv: MetadataHDRMDCV, optional
    :ivar metadata_scalability: Optional :class:`MetadataScalability` object if type is `OBP_METADATA_TYPE_SCALABILITY`.
    :vartype metadata_scalability: MetadataScalability, optional
    :ivar metadata_timecode: Optional :class:`MetadataTimecode` object if type is `OBP_METADATA_TYPE_TIMECODE`.
    :vartype metadata_timecode: MetadataTimecode, optional
    :ivar unregistered: Optional :class:`MetadataUnregistered` object if the type is not one of the known specific types.
                        The C library populates the `unregistered` field of the C struct in such cases.
    :vartype unregistered: MetadataUnregistered, optional
    :ivar data: Raw bytes of the OBU payload (content after OBU header).
    :vartype data: bytes
    """
    def __init__(self, c_meta: _c_wrapper.OBPMetadata, obu_payload: bytes):
        """
        Initializes Metadata from a ctypes OBPMetadata object and the OBU payload.

        :param c_meta: The ctypes OBPMetadata structure.
        :type c_meta: _c_wrapper.OBPMetadata
        :param obu_payload: The raw byte payload of the OBU this metadata was parsed from.
                            This is used by some metadata types that point within this buffer.
        :type obu_payload: bytes
        """
        self._c_metadata = c_meta
        self.type = c_meta.type # Keep as int initially from C
        try:
            self.type_enum: _c_wrapper.OBPMetadataType | int = _c_wrapper.OBPMetadataType(c_meta.type)
        except ValueError:
            self.type_enum = c_meta.type # Store as int if not a known enum member
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

        # Use the enum for comparison
        if self.type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_ITUT_T35:
            self.metadata_itut_t35 = MetadataITUTT35(c_meta.metadata_itut_t35)
        elif self.type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_HDR_CLL:
            self.metadata_hdr_cll = MetadataHDRCLL(c_meta.metadata_hdr_cll)
        elif self.type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_HDR_MDCV:
            self.metadata_hdr_mdcv = MetadataHDRMDCV(c_meta.metadata_hdr_mdcv)
        elif self.type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_SCALABILITY:
            self.metadata_scalability = MetadataScalability(c_meta.metadata_scalability)
        elif self.type_enum == _c_wrapper.OBPMetadataType.OBP_METADATA_TYPE_TIMECODE:
            self.metadata_timecode = MetadataTimecode(c_meta.metadata_timecode)
        # For unregistered, we check if it's not any of the known types.
        # The C library doesn't define a specific type for "unregistered" in the enum.
        # It's usually inferred. For now, if it's not any of the above, and
        # the C struct has data in `unregistered` part (which it always will, it's not a pointer),
        # the high-level Python API might choose to populate `self.unregistered` if the type is not a known one.
        # The C parser fills `unregistered.buf` and `unregistered.buf_size` for metadata_type > 5 (or specific other types).
        # Let's assume if it's not any of the above standard types, it could be unregistered or reserved.
        # The `obuparse.c` fills `metadata->unregistered.buf = buf; metadata->unregistered.buf_size = obu_size;`
        # for types not specifically handled.
        else: # Potentially unregistered or reserved
            # Check if the type is outside the standard known enum range.
            # This logic might need refinement based on how obuparse.c truly behaves for all cases.
            # For now, if it's not a specific type, and data exists, populate unregistered.
            # The C obp_parse_metadata stores the raw OBU payload into metadata->unregistered
            # if the type is not one of the specific known ones.
            self.unregistered = MetadataUnregistered(c_meta.unregistered)
        
        # Raw data of the metadata OBU's payload (after OBU header)
        # c_meta.data points to the start of the OBU's content (after OBU header)
        # c_meta.obu_size is the size of the OBU's content (matching len(obu_payload))
        if c_meta.data and self.obu_size > 0:
            self.data: bytes = ctypes.string_at(c_meta.data, self.obu_size)
        else:
            self.data: bytes = b""


    def __repr__(self) -> str:
        """Return a string representation of the Metadata object."""
        return f"Metadata(type={self.type}, obu_size={self.obu_size}, specific_metadata_present={self._get_specific_metadata_repr()})"

    def _get_specific_metadata_repr(self) -> str:
        """Helper to get representation of the specific metadata type present."""
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

    This class wraps the `OBPTileList` C structure from `_c_wrapper.py`.
    It contains a list of :class:`TileListEntry` objects, each describing a tile
    to be copied from an anchor frame.

    :ivar output_frame_width_in_tiles: Width of the output frame in tiles.
    :vartype output_frame_width_in_tiles: int
    :ivar output_frame_height_in_tiles: Height of the output frame in tiles.
    :vartype output_frame_height_in_tiles: int
    :ivar tile_count_minus_1: Number of tiles in the list minus 1.
    :vartype tile_count_minus_1: int
    :ivar tile_list_entries: List of :class:`TileListEntry` objects.
    :vartype tile_list_entries: list[TileListEntry]
    """
    def __init__(self, c_tl: _c_wrapper.OBPTileList, obu_payload: bytes):
        """
        Initializes TileList from a ctypes OBPTileList object and the OBU payload.

        :param c_tl: The ctypes OBPTileList structure.
        :type c_tl: _c_wrapper.OBPTileList
        :param obu_payload: The raw byte payload of the OBU this tile list was parsed from.
                           (Currently unused but kept for potential future needs if TileListEntry needs it).
        :type obu_payload: bytes
        """
        self._c_tile_list = c_tl
        self.output_frame_width_in_tiles: int = c_tl.output_frame_width_in_tiles
        self.output_frame_height_in_tiles: int = c_tl.output_frame_height_in_tiles
        self.tile_count_minus_1: int = c_tl.tile_count_minus_1
        
        self.tile_list_entries: list[TileListEntry] = []
        if c_tl.tile_list_entries:
            num_entries = self.tile_count_minus_1 + 1
            for i in range(num_entries):
                c_entry_ptr = c_tl.tile_list_entries[i] # This is a pointer to OBPTileListEntry
                # Create Python TileListEntry directly from the C entry object
                # The TileListEntry.__init__ will handle copying the data.
                self.tile_list_entries.append(TileListEntry(c_entry_ptr))

    def __repr__(self) -> str:
        """Return a string representation of the TileList object."""
        return f"TileList(width_tiles={self.output_frame_width_in_tiles}, height_tiles={self.output_frame_height_in_tiles}, count={self.tile_count_minus_1+1})"


# --- OBPState Wrapper ---
class OBPStateWrapper:
    def __init__(self):
        self._c_state_instance = _c_wrapper.OBPState()
        if _c_wrapper._lib and hasattr(_c_wrapper._lib, 'obp_state_init'):
            _c_wrapper._lib.obp_state_init(ctypes.byref(self._c_state_instance))
        else:
            # Manual basic initialization if obp_state_init is not available or lib not loaded.
            # This is a fallback and might not be sufficient for complex states,
            # but zeroing out is a common practice.
            ctypes.memset(ctypes.byref(self._c_state_instance), 0, ctypes.sizeof(_c_wrapper.OBPState))
            # No specific fields need to be set here after zeroing, as the C library
            # is responsible for managing the state content via obp_state_init.
            # The prev_filled field in C OBPState might be relevant, but obp_state_init handles it.

    @property
    def c_state(self) -> _c_wrapper.OBPState:
        return self._c_state_instance

    def __repr__(self) -> str:
        # Provide a generic representation as its contents are C-managed.
        return f"OBPStateWrapper(<C OBPState object at {ctypes.addressof(self._c_state_instance):#x}>)"


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
    # This map is now for documentation/reference; direct enum usage is preferred.
    # _PY_OBP_OBU_TYPE_MAP = {
    #     _c_wrapper.OBPOBUType.OBP_OBU_SEQUENCE_HEADER: _c_wrapper.OBPOBUType.OBP_OBU_SEQUENCE_HEADER,
    #     ... (all other enum members)
    # }
} # Removed _PY_OBP_OBU_TYPE_MAP as direct enum usage is better.

def iter_obus(data: bytes):
    """
    Generates OBU information from a byte stream.
    Yields tuples of (obu_type_enum, temporal_id, spatial_id, obu_payload_bytes).
    obu_type_enum will be a member of the _c_wrapper.OBPOBUType enum, or int if unknown.
    """
    if not _c_wrapper._lib:
        raise OBUParseError("C library not loaded.")
    
    c_lib = _c_wrapper._lib
    # The _c_wrapper.py's obp_get_next_obu.argtypes is now fixed to 8 arguments.
    # No runtime check for arity or obu_has_size_field needed.

    data_len = len(data)
    current_pos = 0
    
    while current_pos < data_len:
        obu_type_cval = _c_wrapper.c_int_t()
        obu_offset_cval = _c_wrapper.c_ptrdiff_t() 
        obu_size_cval = _c_wrapper.c_size_t()    
        # obu_has_size_field_cval is removed as it's not part of the C API for obp_get_next_obu
        temporal_id_cval = _c_wrapper.c_int_t()
        spatial_id_cval = _c_wrapper.c_int_t(0) 
        
        err_struct = _c_wrapper.OBPError()

        current_data_slice_bytes = data[current_pos:]
        remaining_data_size = len(current_data_slice_bytes)

        if remaining_data_size == 0:
            break

        input_buffer_ptr = ctypes.cast(current_data_slice_bytes, ctypes.POINTER(_c_wrapper.c_uint8_t))

        ret_code = c_lib.obp_get_next_obu(
            input_buffer_ptr, remaining_data_size,
            ctypes.byref(obu_type_cval), 
            ctypes.byref(obu_offset_cval),
            ctypes.byref(obu_size_cval), 
            ctypes.byref(temporal_id_cval), 
            ctypes.byref(spatial_id_cval),
            ctypes.byref(err_struct)
        )

        if ret_code != 0:
            error_message = f"Failed to get next OBU (code {ret_code})"
            if err_struct.error:
                error_message += f": {err_struct.error.decode('utf-8', errors='replace')}"
                if hasattr(c_lib, 'obp_free_error_string'):
                    _c_wrapper.free_obp_error_string(err_struct)
            
            if remaining_data_size < 1 and ret_code !=0 : # Smallest OBU header is 1 byte. If less, likely EOF.
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
        
        try:
            # Attempt to convert the integer OBU type to an OBPOBUType enum member.
            py_obu_type = _c_wrapper.OBPOBUType(obu_type_cval.value)
        except ValueError:
            # If the integer value doesn't correspond to any enum member (e.g., reserved types),
            # yield the raw integer type. This allows handling of unknown or future OBU types.
            py_obu_type = obu_type_cval.value


        yield (
            py_obu_type, # Now yields the enum member or raw int if unknown/reserved
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
