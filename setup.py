from setuptools import setup
from setuptools.command.build_ext import build_ext
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
import os
import subprocess
import sys


class BuildExt(build_ext):
    """Build CFFI extension and the native obudump tool."""

    def run(self):
        super().run()
        self.build_obudump()

    def build_obudump(self):
        compiler = new_compiler()
        customize_compiler(compiler)
        sources = [
            os.path.join("tools", "obudump.c"),
            os.path.join("tools", "json.c"),
            "obuparse.c",
        ]
        objects = compiler.compile(sources, output_dir=self.build_temp, include_dirs=[".", "tools"])
        exe_name = os.path.join(self.build_lib, "obudump")
        compiler.link_executable(objects, exe_name)
        self.distribution.data_files = self.distribution.data_files or []
        self.distribution.data_files.append(("bin", [exe_name]))

setup(
    name="obuparse",
    use_scm_version=True,
    package_dir={"": "python"},
    packages=["obuparse", "pyobuparse"],
    cffi_modules=["python/ffi_builder.py:ffibuilder"],
    setup_requires=["cffi>=1.0", "setuptools_scm"],
    install_requires=["cffi>=1.0"],
    entry_points={"console_scripts": ["obudump=obuparse.cli:main"]},
    cmdclass={"build_ext": BuildExt},
)
