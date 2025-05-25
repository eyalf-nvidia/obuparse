from setuptools import setup, Extension
import platform

obuparse_extension = Extension(
    name='pyobuparse._obuparse_c',  # Fully qualified name for the .pyd/.so file
    sources=[
        'src/pyobuparse/_obuparse_module.c', # The new C shim
        '../obuparse.c'          # The original C library
    ],
    include_dirs=['src/pyobuparse', '..'], # For obuparse.h
    define_macros=[('OBUPARSE_EXPORTS', '1')], # Added for symbol export control
    extra_compile_args=['-fPIC'] if platform.system() != "Windows" else [],
    # language='c', # Default, but can be explicit
)

setup(
    # Most metadata is in pyproject.toml
    ext_modules=[obuparse_extension],
    # Remove the 'libraries' argument if it was present from a previous attempt
    # libraries=[(
    #     '_obuparse_c_lib', { 
    #         'sources': ['src/pyobuparse/obuparse.c'],
    #         'include_dirs': ['src/pyobuparse'],
    #     }
    # )],
)
