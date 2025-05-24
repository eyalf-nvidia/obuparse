"""
Command-Line Interface (CLI) for pyobuparse.

Provides the `obudump` tool to parse and display OBU information from IVF files.
"""
import argparse
import struct
import sys

from . import parser # Use . to import from the same package
from . import _c_wrapper # For OBPOBUType enum if needed directly

def parse_ivf_header(f):
    """
    Parses the 32-byte IVF file header from a file object.

    Args:
        f (file object): An opened binary file object positioned at the start
            of the IVF header.

    Returns:
        dict: A dictionary containing key IVF header fields like 'fourcc',
              'width', 'height', 'framecount'.

    Raises:
        ValueError: If the IVF header is incomplete or has an invalid signature.
    """
    header_data = f.read(32)
    if len(header_data) < 32:
        raise ValueError("IVF file header is incomplete.")
    
    signature = header_data[0:4]
    if signature != b'DKIF':
        raise ValueError(f"Invalid IVF signature: {signature!r}. Expected b'DKIF'.")
    
    version = struct.unpack('<H', header_data[4:6])[0]
    if version != 0:
        print(f"Warning: IVF version is {version}, expected 0.", file=sys.stderr)
        # Depending on strictness, could raise ValueError here.
        
    header_length = struct.unpack('<H', header_data[6:8])[0]
    fourcc = header_data[8:12] # Keep as bytes
    width = struct.unpack('<H', header_data[12:14])[0]
    height = struct.unpack('<H', header_data[14:16])[0]
    framerate_num = struct.unpack('<L', header_data[16:20])[0] # Numerator
    framerate_den = struct.unpack('<L', header_data[20:24])[0] # Denominator
    framecount = struct.unpack('<L', header_data[24:28])[0]
    # unused = header_data[28:32]
    
    print(f"IVF Header: Version={version}, Length={header_length}, Codec={fourcc!r}, "
          f"WxH={width}x{height}, FPS={framerate_num}/{framerate_den}, Frames={framecount}", file=sys.stderr)
    return {
        "fourcc": fourcc,
        "width": width,
        "height": height,
        "framecount": framecount
    }

def parse_ivf_frame_header(f):
    """Parses the 12-byte IVF frame header. Returns (frame_size, pts) or (None, None) on EOF."""
    frame_header_data = f.read(12)
    if not frame_header_data: # EOF
        return None, None
    if len(frame_header_data) < 12:
        raise ValueError("IVF frame header is incomplete.")
        
    frame_size = struct.unpack('<L', frame_header_data[0:4])[0]
    pts = struct.unpack('<Q', frame_header_data[4:12])[0]
    return frame_size, pts

def main():
    """
    Main function for the obudump CLI tool.

    Parses command-line arguments, reads an IVF file, iterates through OBUs,
    and prints OBU information. Supports a verbose mode for more detailed
    OBU parsing.
    """
    arg_parser = argparse.ArgumentParser(
        description="Parse and display OBU (Object Bitstream Unit) data from an IVF (Indeo Video Format) file. "
                    "Useful for inspecting AV1 bitstreams.",
        epilog="Example: obudump video.ivf -v --max-obus 10"
    )
    arg_parser.add_argument(
        "filename", 
        help="Path to the IVF input file."
    )
    arg_parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Print detailed information about parsed OBUs. "
             "This attempts to parse the OBU payload using pyobuparse's parsing functions."
    )
    arg_parser.add_argument(
        "--max-obus", 
        type=int, 
        default=None, 
        metavar="N",
        help="Maximum number of OBUs to print per IVF frame (for brevity). "
             "If not specified, all OBUs are processed."
    )
    args = arg_parser.parse_args()

    try:
        with open(args.filename, "rb") as f:
            ivf_info = parse_ivf_header(f)
            
            # For AV1, common FOURCCs are AV01, AV1X. Allow these.
            # Other codecs might be signaled by other FOURCCs (e.g. VP80, VP90)
            # For this tool, we primarily care about AV1.
            if ivf_info["fourcc"] not in [b'AV01', b'AV1X']:
                 print(f"Warning: IVF FourCC is {ivf_info['fourcc']!r}, which might not be AV1. "
                       "Attempting to parse as AV1 OBUs anyway.", file=sys.stderr)

            frame_num = 0
            # Initialize state needed for parsing functions that require context
            # (e.g., FrameHeader parsing needs SequenceHeader and OBPState)
            current_sequence_header_obj = None
            obu_state_wrapper = parser.OBPStateWrapper()

            while True:
                frame_size, pts = parse_ivf_frame_header(f)
                if frame_size is None: # EOF
                    break
                
                frame_num += 1
                print(f"\nIVF Frame {frame_num}: Size={frame_size}, PTS={pts}")
                
                frame_data = f.read(frame_size)
                if len(frame_data) < frame_size:
                    print(f"Warning: Could not read full frame data for frame {frame_num}. "
                          f"Expected {frame_size}, got {len(frame_data)}.", file=sys.stderr)
                    break

                obus_printed_for_frame = 0
                try:
                    for obu_type, temporal_id, spatial_id, obu_payload in parser.iter_obus(frame_data):
                        if args.max_obus is not None and obus_printed_for_frame >= args.max_obus:
                            print(f"  ... (further OBUs in frame {frame_num} truncated due to --max-obus)")
                            break
                        
                        obu_type_name = obu_type.name if isinstance(obu_type, _c_wrapper.OBPOBUType) else f"UNKNOWN_TYPE_{obu_type}"
                        print(f"  OBU: Type={obu_type_name} ({obu_type}), "
                              f"Size={len(obu_payload)}, TID={temporal_id}, SID={spatial_id}")
                        obus_printed_for_frame += 1

                        if args.verbose:
                            try:
                                if obu_type == _c_wrapper.OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
                                    seq_header = parser.parse_sequence_header(obu_payload)
                                    current_sequence_header_obj = seq_header # Store for context
                                    print(f"    Parsed SequenceHeader: profile={seq_header.seq_profile}, "
                                          f"max_width={seq_header.max_frame_width_minus_1+1}, "
                                          f"max_height={seq_header.max_frame_height_minus_1+1}")
                                    # Consider printing more fields from seq_header or its repr
                                
                                elif obu_type == _c_wrapper.OBPOBUType.OBP_OBU_FRAME_HEADER or \
                                     obu_type == _c_wrapper.OBPOBUType.OBP_OBU_REDUNDANT_FRAME_HEADER:
                                    if current_sequence_header_obj:
                                        frame_header = parser.parse_frame_header(
                                            obu_payload, current_sequence_header_obj,
                                            obu_state_wrapper, temporal_id, spatial_id
                                        )
                                        print(f"    Parsed FrameHeader: type={frame_header.frame_type.name if isinstance(frame_header.frame_type, _c_wrapper.OBPFrameType) else frame_header.frame_type}, "
                                              f"width={frame_header.FrameWidth}, height={frame_header.FrameHeight}, "
                                              f"order_hint={frame_header.order_hint}")
                                    else:
                                        print("    Skipping FrameHeader parsing: No prior SequenceHeader found in this stream.")
                                
                                elif obu_type == _c_wrapper.OBPOBUType.OBP_OBU_FRAME: # Frame OBU (FH + TG)
                                    if current_sequence_header_obj:
                                        # `parse_frame` handles both FH and TG internally
                                        frame_header, tile_group = parser.parse_frame(
                                            obu_payload, current_sequence_header_obj,
                                            obu_state_wrapper, temporal_id, spatial_id
                                        )
                                        print(f"    Parsed Frame (as FH+TG): FH type={frame_header.frame_type.name if isinstance(frame_header.frame_type, _c_wrapper.OBPFrameType) else frame_header.frame_type}, "
                                              f"TG NumTiles={tile_group.NumTiles}, TG data_len={len(tile_group.data)}")
                                    else:
                                        print("    Skipping Frame OBU parsing: No prior SequenceHeader found in this stream.")
                                
                                elif obu_type == _c_wrapper.OBPOBUType.OBP_OBU_TILE_GROUP:
                                    # Requires a FrameHeader from the current frame, which might not be available
                                    # if iterating OBUs directly. This is tricky.
                                    # For now, we'll just print that we found it.
                                    # A more robust parser would need to manage frame context.
                                    print("    Found TileGroup OBU (verbose parsing not yet implemented for standalone TG here)")

                                elif obu_type == _c_wrapper.OBPOBUType.OBP_OBU_METADATA:
                                    metadata = parser.parse_metadata(obu_payload)
                                    metadata_type_name = metadata.type.name if isinstance(metadata.type, _c_wrapper.OBPMetadataType) else f"UNKNOWN_META_TYPE_{metadata.type}"
                                    print(f"    Parsed Metadata: type={metadata_type_name}")
                                    # Could add more detail based on metadata.type
                                
                                elif obu_type == _c_wrapper.OBPOBUType.OBP_OBU_TILE_LIST:
                                    tile_list = parser.parse_tile_list(obu_payload)
                                    print(f"    Parsed TileList: count={tile_list.tile_count_minus_1+1}")

                                # No specific parsers for TEMPORAL_DELIMITER (empty payload) or PADDING
                                # Other OBU types might not have dedicated parsers in obuparse.h
                            except parser.OBUParseError as e:
                                print(f"    Verbose parse error: {e}")
                            except Exception as e:
                                print(f"    Unexpected error during verbose parse: {e}")
                
                except parser.OBUParseError as e:
                    print(f"  Error iterating OBUs in frame {frame_num}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"  Unexpected error iterating OBUs in frame {frame_num}: {e}", file=sys.stderr)


            print(f"\nProcessed {frame_num} frames from IVF file.", file=sys.stderr)

    except FileNotFoundError:
        print(f"Error: File not found: {args.filename}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error processing IVF file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
