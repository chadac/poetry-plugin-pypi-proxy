import os
from distutils.core import setup


setup(
    name="sample-dependency",
    version=os.environ["PKG_VERSION"],
    author="Test",
)
