from setuptools import setup
from nbpy.version import (
    version,
    title,
    description,
    author,
    author_email,
    license,
)

# Requirements
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


setup(
    name=title,
    version=version,
    description=description,
    author=author,
    author_email=author_email,
    license=license,
    packages=['nbpy'],
    install_requires=requirements,
)
