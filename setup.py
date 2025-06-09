from setuptools import setup
from setuptools.command.build_ext import build_ext
import subprocess
import sys


class BuildExt(build_ext):
    """Build CFFI extension and native tools."""

    def run(self):
        super().run()
        try:
            subprocess.check_call(["make", "tools"])
        except Exception as exc:
            print("warning: failed to build native tools:", exc, file=sys.stderr)

setup(
    name='obuparse',
    version='0.1.0',
    package_dir={'': 'python'},
    packages=['obuparse', 'pyobuparse'],
    cffi_modules=['python/ffi_builder.py:ffibuilder'],
    setup_requires=['cffi>=1.0'],
    install_requires=['cffi>=1.0'],
    entry_points={'console_scripts': ['obudump=obuparse.cli:main']},
    data_files=[('bin', ['tools/obudump'])],
    cmdclass={'build_ext': BuildExt},
)
