import argparse
from . import ffi, lib


def parse_ivf(path, verbose=False):
    with open(path, 'rb') as f:
        f.seek(32)  # skip IVF header
        packet_number = 0
        while True:
            frame_header = f.read(12)
            if len(frame_header) < 12:
                break
            packet_size = int.from_bytes(frame_header[0:4], 'little')
            packet = f.read(packet_size)
            if len(packet) < packet_size:
                raise IOError('Truncated packet')
            packet_pos = 0
            while packet_pos < packet_size:
                err_buf = ffi.new('char[1024]')
                err = ffi.new('OBPError *', {'error': err_buf, 'size': 1024})
                obu_type = ffi.new('OBPOBUType *')
                offset = ffi.new('ptrdiff_t *')
                obu_size = ffi.new('size_t *')
                temporal_id = ffi.new('int *')
                spatial_id = ffi.new('int *')
                ret = lib.obp_get_next_obu(
                    ffi.from_buffer(packet, writable=False)[packet_pos:],
                    packet_size - packet_pos,
                    obu_type,
                    offset,
                    obu_size,
                    temporal_id,
                    spatial_id,
                    err,
                )
                if ret != 0:
                    raise RuntimeError(ffi.string(err.error).decode())
                if verbose:
                    print({
                        'obu_type': int(obu_type[0]),
                        'offset': int(offset[0]),
                        'obu_size': int(obu_size[0]),
                        'temporal_id': int(temporal_id[0]),
                        'spatial_id': int(spatial_id[0]),
                    })
                packet_pos += obu_size[0] + offset[0]
            packet_number += 1


def main(argv=None):
    parser = argparse.ArgumentParser(description='Dump OBUs from an IVF file')
    parser.add_argument('input', help='Input IVF file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args(argv)
    parse_ivf(args.input, args.verbose)


if __name__ == '__main__':
    main()
