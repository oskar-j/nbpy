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
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Environment :: Web Environment',
        'Environment :: Other Environment',
        'Operating System :: OS Independent',

        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',

    ],
)
