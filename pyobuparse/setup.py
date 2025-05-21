import platform
from setuptools import setup
# Extension is removed

# The old Extension definition is removed:
# obuparse_extension = Extension(
#     name='pyobuparse._obuparse_c',
#     sources=['src/pyobuparse/obuparse.c'],
#     include_dirs=['src/pyobuparse'],
#     extra_compile_args=['-fPIC'] if platform.system() != "Windows" else [],
# )

# Placeholder for custom build_clib if needed later for output control
# class custom_build_clib(build_clib):
#    def finalize_options(self):
#        self.set_undefined_options('build', ('build_lib', 'build_clib'))
#        build_clib.finalize_options(self)
#    def run(self):
#        build_clib.run(self)
#        # Example: copy built library to package
#        # target_dir = os.path.join(self.build_lib, 'pyobuparse') 
#        # self.mkpath(target_dir)
#        # self.copy_file(os.path.join(self.build_temp, self.get_library_names()[0]), target_dir)

setup(
    # Most metadata is in pyproject.toml
    
    # Define obuparse.c as a C library
    libraries=[(
        '_obuparse_c_lib', { # This will be the base name of the library file
            'sources': ['src/pyobuparse/obuparse.c'],
            'include_dirs': ['src/pyobuparse'],
            # extra_compile_args might be needed for specific C features or warnings,
            # but -fPIC is generally for shared objects that are Python extensions,
            # and might not be necessary or correctly handled by build_clib for all platforms
            # when building a standalone library. For Windows DLLs, it's not used.
            # Keep it minimal for now.
            # 'extra_compile_args': ['-fPIC'] if platform.system() != "Windows" else [],
        }
    )],
    # ext_modules=[obuparse_extension], # Removed
    # cmdclass={'build_clib': custom_build_clib}, # If custom_build_clib is defined and needed
    # For now, rely on default build_clib behavior.
    # It's specified that build_clib should run. If setuptools doesn't run it automatically
    # due to 'libraries' being present, users might need to invoke it manually or
    # this setup.py might need to be augmented with a custom build process
    # that ensures build_clib is called.
    # A common way to ensure it runs is to include it in the build process
    # via a custom build_py or build_ext command, or by ensuring the distribution
    # type (e.g. wheel) triggers it.
    # For now, this matches the requested structure.
)
