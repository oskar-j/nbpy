import sys
from setuptools import setup
from nbpy.version import (
    version,
    title,
    description,
    author,
    author_email,
    license,
)

if not sys.version_info >= (3, 3):
    sys.exit("NBPy supports only Python 3.3 and above.")

# Requirements
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

# Long description (from README.rst)
with open('README.rst', 'r') as readme:
    long_description = readme.read()

setup(
    name=title,
    version=version,
    description=description,
    long_description=long_description,
    author=author,
    author_email=author_email,
    license=license,
    packages=['nbpy'],
    install_requires=requirements,
    python_requires='>=3.3',
)
