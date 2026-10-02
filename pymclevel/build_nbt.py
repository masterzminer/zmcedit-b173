# Small script to build the Cython nbt library

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension(
        "pymclevel._nbt",
        ["pymclevel/_nbt.pyx"],
        include_dirs=[numpy.get_include()],
    )
]

setup(
    ext_modules=cythonize(extensions),
)