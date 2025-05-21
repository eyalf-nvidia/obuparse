import platform
from setuptools import setup, Extension

obuparse_extension = Extension(
    name='pyobuparse._obuparse_c',
    sources=['src/pyobuparse/obuparse.c'],
    include_dirs=['src/pyobuparse'],
    extra_compile_args=['-fPIC'] if platform.system() != "Windows" else [],
)

setup(
    ext_modules=[obuparse_extension],
)
