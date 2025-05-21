"""
PyObuParse: A Python wrapper for the obuparse AV1 OBU parsing library.
"""
import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    try:
        from ._version import version as __version__
    except ImportError:
        __version__ = "0.1.0.dev0"

from .parser import (
    OBUParseError, OBPStateWrapper,
    TimingInfo, DecoderModelInfo, OperatingParametersInfo, ColorConfig, SequenceHeader,
    SuperresParams, InterpolationFilter, TileInfo, QuantizationParams, SegmentationParams,
    DeltaQParams, DeltaLFParams, LoopFilterParams, CdefParams, LrParams,
    GlobalMotionParams, FilmGrainParameters, FrameHeader,
    TileGroup,
    MetadataITUTT35, MetadataHDRCLL, MetadataHDRMDCV, ScalabilityStructure,
    MetadataScalability, MetadataTimecode, MetadataUnregistered, Metadata,
    TileListEntry, TileList,
    parse_sequence_header, parse_frame_header, parse_frame, parse_tile_group,
    parse_metadata, parse_tile_list, iter_obus
)

__all__ = [
    "__version__",
    "OBUParseError", "OBPStateWrapper",
    "TimingInfo", "DecoderModelInfo", "OperatingParametersInfo", "ColorConfig", "SequenceHeader",
    "SuperresParams", "InterpolationFilter", "TileInfo", "QuantizationParams", "SegmentationParams",
    "DeltaQParams", "DeltaLFParams", "LoopFilterParams", "CdefParams", "LrParams",
    "GlobalMotionParams", "FilmGrainParameters", "FrameHeader",
    "TileGroup",
    "MetadataITUTT35", "MetadataHDRCLL", "MetadataHDRMDCV", "ScalabilityStructure",
    "MetadataScalability", "MetadataTimecode", "MetadataUnregistered", "Metadata",
    "TileListEntry", "TileList",
    "parse_sequence_header", "parse_frame_header", "parse_frame", "parse_tile_group",
    "parse_metadata", "parse_tile_list", "iter_obus",
]
