from setuptools import setup

setup(
    name='obuparse',
    version='0.1.0',
    package_dir={'': 'python'},
    packages=['obuparse'],
    cffi_modules=['python/ffi_builder.py:ffibuilder'],
    setup_requires=['cffi>=1.0'],
    install_requires=['cffi>=1.0'],
    entry_points={'console_scripts': ['obudump=obuparse.cli:main']},
)
