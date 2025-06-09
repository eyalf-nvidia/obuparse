from cffi import FFI
import os

ffibuilder = FFI()

header_path = os.path.join(os.path.dirname(__file__), '..', 'obuparse.h')
with open(header_path) as f:
    lines = []
    for line in f:
        if line.startswith('#'):
            continue
        lines.append(line)
    header = ''.join(lines)

ffibuilder.cdef(header)

ffibuilder.set_source(
    'obuparse._obulib',
    '#include "obuparse.h"',
    sources=[os.path.join(os.path.dirname(__file__), '..', 'obuparse.c')],
    include_dirs=[os.path.join(os.path.dirname(__file__), '..')],
)

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
