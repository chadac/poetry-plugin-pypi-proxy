import sys
from distutils.core import setup

version = sys.argv[1]
del sys.argv[1]
setup(
    name="sample-dependency",
    version=version,
)
