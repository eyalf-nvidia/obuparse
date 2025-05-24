#!/usr/bin/env python3
"""
Python AV1 OBU Dump Tool (obudump_py)

This script parses AV1 Open Bitstream Units (OBUs) from an IVF (Indeo Video Format)
file and prints information about each OBU in JSON format. It aims to replicate
the functionality of the C `tools/obudump.c` utility, using the `pyobuparse` library.
"""

import argparse
import json
import sys
import os
from typing import Union # Added Union

# Attempt to import from the installed package, fallback for local testing
try:
    from pyobuparse.parser import (
        iter_obus,
        parse_sequence_header,
        parse_frame_header,
        parse_tile_group,
        parse_metadata,
        parse_tile_list,
        parse_frame,
        OBPStateWrapper,
        OBUParseError,
        SequenceHeader as PySequenceHeader, # Alias to avoid clash with C types if used directly
        FrameHeader as PyFrameHeader,
        TileGroup as PyTileGroup,
        Metadata as PyMetadata,
        TileList as PyTileList
    )
    from pyobuparse._c_wrapper import OBPOBUType
except ImportError:
    # This allows running the script directly from the repository root for development.
    # Calculate the path to the 'src' directory: pyobuparse/src/pyobuparse/cli/obudump_py.py -> pyobuparse/src
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(os.path.join(current_script_dir, "..", "..")) # Up two levels
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from pyobuparse.parser import (
        iter_obus,
        parse_sequence_header,
        parse_frame_header,
        parse_tile_group,
        parse_metadata,
        parse_tile_list,
        parse_frame,
        OBPStateWrapper,
        OBUParseError,
        SequenceHeader as PySequenceHeader,
        FrameHeader as PyFrameHeader,
        TileGroup as PyTileGroup,
        Metadata as PyMetadata,
        TileList as PyTileList
    )
    from pyobuparse._c_wrapper import OBPOBUType


def obu_type_to_str(obu_type: Union[OBPOBUType, int], verbose: bool) -> str:
    """
    Converts an OBU type (enum or int) to its string representation if verbose.
    Otherwise, returns the integer value as a string.
    """
    if verbose:
        if isinstance(obu_type, OBPOBUType):
            return obu_type.name
        else:
            # Try to convert int to enum name, fallback to "UNKNOWN"
            try:
                return OBPOBUType(obu_type).name
            except ValueError:
                return f"OBU_UNKNOWN_{obu_type}"
    return str(obu_type) # Return integer value as string if not verbose

# --- JSON Conversion Helper Functions ---

def _obj_to_dict_recursive(obj, verbose: bool):
    """
    Recursively converts an object's attributes to a dictionary.
    Handles nested objects, lists of objects, and enums.
    """
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    if isinstance(obj, bytes):
        # For bytes, decide on a representation, e.g., a short hex string or length
        return f"bytes[len={len(obj)}]" # Placeholder
    if isinstance(obj, list):
        return [_obj_to_dict_recursive(item, verbose) for item in obj]
    if isinstance(obj, dict): # Should not happen if objects are well-defined
        return {k: _obj_to_dict_recursive(v, verbose) for k, v in obj.items()}
    if hasattr(obj, '__dict__'): # For most custom Python objects
        data = {}
        for key, value in obj.__dict__.items():
            if key.startswith('_c_'): # Skip internal ctypes references
                continue
            data[key] = _obj_to_dict_recursive(value, verbose)
        return data
    if isinstance(obj, enum.Enum): # Handle enums from _c_wrapper
        return obu_type_to_str(obj, verbose) # Use existing helper for consistency
    # For ctypes basic types that might not have __dict__ but are not primitives
    if isinstance(obj, (ctypes.c_int, ctypes.c_uint, ctypes.c_float, ctypes.c_double, ctypes.c_bool,
                        ctypes.c_char, ctypes.c_wchar, ctypes.c_byte, ctypes.c_ubyte,
                        ctypes.c_short, ctypes.c_ushort, ctypes.c_long, ctypes.c_ulong,
                        ctypes.c_longlong, ctypes.c_ulonglong,
                        ctypes.c_size_t, ctypes.c_ssize_t, ctypes.c_void_p)):
        return obj.value
    if isinstance(obj, ctypes.Array):
        return [_obj_to_dict_recursive(item, verbose) for item in obj]

    # Fallback for types not explicitly handled (e.g., other ctypes)
    try:
        # If it's a ctypes structure, try to iterate _fields_
        # This is a basic attempt and might need refinement for complex ctypes.
        if hasattr(obj, '_fields_'):
            data = {}
            for field_name, field_type in obj._fields_:
                if field_name.startswith('_'): continue # Skip private-like fields
                data[field_name] = _obj_to_dict_recursive(getattr(obj, field_name), verbose)
            return data
    except Exception:
        pass # If iteration fails, fallback to string representation

    return repr(obj) # Fallback: string representation for unknown types

def sequence_header_to_dict(sh: PySequenceHeader, verbose: bool) -> dict:
    """Converts a PySequenceHeader object to a JSON-serializable dictionary."""
    return _obj_to_dict_recursive(sh, verbose)

def frame_header_to_dict(fh: PyFrameHeader, verbose: bool) -> dict:
    """Converts a PyFrameHeader object to a JSON-serializable dictionary."""
    return _obj_to_dict_recursive(fh, verbose)

def tile_group_to_dict(tg: PyTileGroup, verbose: bool) -> dict:
    """Converts a PyTileGroup object to a JSON-serializable dictionary."""
    return _obj_to_dict_recursive(tg, verbose)

def metadata_to_dict(md: PyMetadata, verbose: bool) -> dict:
    """Converts a PyMetadata object to a JSON-serializable dictionary."""
    # PyMetadata has specific sub-structures based on type, _obj_to_dict_recursive should handle it.
    return _obj_to_dict_recursive(md, verbose)

def tile_list_to_dict(tl: PyTileList, verbose: bool) -> dict:
    """Converts a PyTileList object to a JSON-serializable dictionary."""
    return _obj_to_dict_recursive(tl, verbose)


def main():
    """
    Main function for the obudump_py CLI tool.
    Parses arguments, processes the IVF file, and prints OBU information as JSON.
    """
    parser = argparse.ArgumentParser(
        description="AV1 OBU Dumper (Python version). Parses IVF files and outputs OBU info as JSON.",
        epilog="Mimics the functionality of the C tools/obudump.c utility."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Output OBU type as string instead of integer."
    )
    parser.add_argument(
        "input_file",
        metavar="<encoded_filename>.ivf",
        help="Path to the input IVF file."
    )

    args = parser.parse_args()

    try:
        with open(args.input_file, "rb") as infile:
            # Skip IVF global header (32 bytes)
            ivf_header = infile.read(32)
            if len(ivf_header) < 32:
                print(f"Error: IVF file '{args.input_file}' is too short to contain a valid header.", file=sys.stderr)
                sys.exit(1)
            
            if ivf_header[:4] != b'DKIF':
                print(f"Error: '{args.input_file}' does not appear to be a valid IVF file (missing 'DKIF' signature).", file=sys.stderr)
                sys.exit(1)

            print("[", end="") # Start of JSON array output

            first_obu_in_file = True
            state_wrapper = OBPStateWrapper()
            current_sequence_header: PySequenceHeader | None = None

            frame_count = 0
            while True:
                ivf_frame_header = infile.read(12)
                if not ivf_frame_header:
                    break # End of file
                
                if len(ivf_frame_header) < 12:
                    print(f"\nError: Incomplete IVF frame header at end of file (frame {frame_count}). Expected 12 bytes, got {len(ivf_frame_header)}.", file=sys.stderr)
                    break

                packet_size = int.from_bytes(ivf_frame_header[:4], byteorder='little')
                # pts = int.from_bytes(ivf_frame_header[4:], byteorder='little') # PTS not used by dumper

                packet_buf = infile.read(packet_size)
                if len(packet_buf) < packet_size:
                    print(f"\nError: Incomplete IVF frame data (frame {frame_count}). Expected {packet_size} bytes, got {len(packet_buf)}.", file=sys.stderr)
                    break
                
                obu_offset_in_packet = 0
                for obu_type_enum_or_int, temporal_id, spatial_id, obu_payload_bytes in iter_obus(packet_buf):
                    obu_size = len(obu_payload_bytes) # iter_obus gives payload, size is its length
                    
                    if not first_obu_in_file:
                        print(",", end="")
                    print() # Newline for each OBU JSON object
                    first_obu_in_file = False

                    basic_obu_info = {
                        "obu_type": obu_type_to_str(obu_type_enum_or_int, args.verbose),
                        "offset_in_ivf_packet": obu_offset_in_packet,
                        "obu_size": obu_size, # This is payload size, header size is implicitly handled by iter_obus
                        "temporal_id": temporal_id,
                        "spatial_id": spatial_id
                    }
                    
                    # Placeholder for detailed parsing
                    detailed_info = {}

                    # TODO: Implement detailed parsing and JSON conversion for each OBU type
                    # For now, just print basic info.
                    # Example for Sequence Header:
                    # if obu_type_enum_or_int == OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
                    #     try:
                    #         parsed_sh = parse_sequence_header(obu_payload_bytes)
                    #         current_sequence_header = parsed_sh
                    # Process specific OBU types for detailed parsing
                    if obu_type_enum_or_int == OBPOBUType.OBP_OBU_SEQUENCE_HEADER:
                        try:
                            parsed_sh = parse_sequence_header(obu_payload_bytes)
                            current_sequence_header = parsed_sh  # Store for context for subsequent OBUs
                            detailed_info["sequence_header"] = sequence_header_to_dict(parsed_sh, args.verbose)
                        except OBUParseError as e:
                            detailed_info["parse_error"] = str(e)
                    
                    elif obu_type_enum_or_int == OBPOBUType.OBP_OBU_FRAME_HEADER or \
                         obu_type_enum_or_int == OBPOBUType.OBP_OBU_REDUNDANT_FRAME_HEADER:
                        if current_sequence_header:
                            try:
                                # Note: OBPStateWrapper is passed to parse_frame_header
                                parsed_fh = parse_frame_header(obu_payload_bytes, current_sequence_header, state_wrapper, temporal_id, spatial_id)
                                # TODO: Store this frame header if it's needed as context for standalone tile groups later in the same IVF frame.
                                # current_ivf_frame_header = parsed_fh 
                                detailed_info["frame_header"] = frame_header_to_dict(parsed_fh, args.verbose)
                            except OBUParseError as e:
                                detailed_info["parse_error"] = str(e)
                        else:
                            detailed_info["parse_error"] = "Sequence Header not seen yet, cannot parse Frame Header."
                    
                    elif obu_type_enum_or_int == OBPOBUType.OBP_OBU_TILE_GROUP:
                        # Standalone Tile Group OBU. Requires Frame Header context.
                        # This assumes `current_ivf_frame_header` has been set by a preceding Frame Header OBU
                        # within the same IVF Packet. This state is NOT carried across IVF packets.
                        # A more robust implementation might need to ensure current_ivf_frame_header is from *this* IVF packet.
                        # For now, we'll assume if a Frame OBU was parsed, its FH is implicitly the context.
                        # If only a Frame Header OBU was parsed, that's the context.
                        # This part is tricky because tile group parsing depends on an active frame header.
                        # The C obudump has `sh`, `fh`, `state` as globalish contexts.
                        # We simulate this by `current_sequence_header` and `state_wrapper`.
                        # We'd need a `current_frame_header_object_for_tile_group_context`
                        # that is reset per IVF frame or when a new Frame OBU starts.
                        # This is simplified here: if a Frame OBU was parsed, its FH is the implicit context.
                        # If a standalone FH OBU was parsed, that's the context.
                        # This logic is not fully robust for all valid AV1 streams with standalone TG OBUs.
                        if hasattr(state_wrapper, '_last_parsed_fh_for_tg'): # A way to get context
                            try:
                                parsed_tg = parse_tile_group(obu_payload_bytes, state_wrapper._last_parsed_fh_for_tg)
                                detailed_info["tile_group"] = tile_group_to_dict(parsed_tg, args.verbose)
                            except OBUParseError as e:
                                detailed_info["parse_error"] = str(e)
                            except AttributeError: # If _last_parsed_fh_for_tg doesn't exist or is None
                                detailed_info["parse_error"] = "Frame Header context not available for Tile Group."
                        else:
                             detailed_info["info"] = "Standalone Tile Group (parsing requires active Frame Header context from a prior OBU in this IVF frame; this dumper may not fully provide it unless it was part of a Frame OBU)."


                    elif obu_type_enum_or_int == OBPOBUType.OBP_OBU_METADATA:
                        try:
                            parsed_md = parse_metadata(obu_payload_bytes)
                            detailed_info["metadata"] = metadata_to_dict(parsed_md, args.verbose)
                        except OBUParseError as e:
                            detailed_info["parse_error"] = str(e)
                    
                    elif obu_type_enum_or_int == OBPOBUType.OBP_OBU_TILE_LIST:
                        try:
                            parsed_tl = parse_tile_list(obu_payload_bytes)
                            detailed_info["tile_list"] = tile_list_to_dict(parsed_tl, args.verbose)
                        except OBUParseError as e:
                            detailed_info["parse_error"] = str(e)

                    elif obu_type_enum_or_int == OBPOBUType.OBP_OBU_FRAME:
                        if current_sequence_header:
                            try:
                                parsed_fh_from_frame, parsed_tg_from_frame = parse_frame(
                                    obu_payload_bytes, current_sequence_header, state_wrapper,
                                    temporal_id, spatial_id
                                )
                                # Store the parsed frame header from this Frame OBU as context for potential subsequent standalone Tile Group OBUs
                                # This is a simple way to provide context within an IVF frame.
                                state_wrapper._last_parsed_fh_for_tg = parsed_fh_from_frame 
                                detailed_info["frame_obu"] = {
                                    "frame_header": frame_header_to_dict(parsed_fh_from_frame, args.verbose),
                                    "tile_group": tile_group_to_dict(parsed_tg_from_frame, args.verbose)
                                }
                            except OBUParseError as e:
                                detailed_info["parse_error"] = str(e)
                        else:
                            detailed_info["parse_error"] = "Sequence Header not seen yet, cannot parse Frame OBU."
                    
                    # Merge basic and detailed info, ensuring detailed_info is primary if keys overlap (though they shouldn't here)
                    full_obu_info = {**basic_obu_info, **detailed_info} # Python 3.5+
                    json.dump(full_obu_info, sys.stdout, indent=4 if args.verbose else None)

                    # This offset calculation was a rough estimate and is not accurate for iter_obus.
                    # iter_obus handles advancing past each OBU (header + payload) correctly.
                    # The offset printed should be relative to the start of the IVF packet.
                    # iter_obus itself doesn't provide the header size, only the payload.
                    # For accurate offset_in_ivf_packet, we need to track it based on total OBU sizes.
                    # This will be tricky as OBU header size can vary.
                    # For now, this offset will be an approximation or just the start of payload.
                    # The C version calculates it as `pos - packet_buf` where pos is advanced.
                    # `obu_offset_in_packet` should be the start of the current OBU's payload.
                    # Let's adjust how it's updated.
                    # iter_obus yields payload. The next OBU starts after this payload + its header.
                    # The C dumper gets header size + payload size from get_next_obu.
                    # Our iter_obus abstracts header size.
                    # For simplicity, we'll consider offset_in_ivf_packet as the start of payload.
                    # The next payload will start after this one.
                    # This needs a more robust way to get total OBU size (header + payload) if exact offsets are needed.
                    # For now, we'll just increment by payload size for the next offset.
                    obu_offset_in_packet += len(obu_payload_bytes) # This is not correct for next OBU's start.
                                                                   # A better way: iter_obus should yield total consumed size or header size.
                                                                   # For now, this is a known limitation.
                                                                        # This offset is just informational for the JSON output.
                                                                        # iter_obus handles actual OBU boundary detection.

                frame_count += 1
            
            print("\n]", end="") # End of JSON array output

    except FileNotFoundError:
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except OBUParseError as e:
        print(f"\nOBU Parsing Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
