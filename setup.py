# -*- coding: utf-8 -*-
# see twine for releases, https://pypi.org/project/twine/

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!

with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}

with open(os.path.join(here, 'transistor', '__version__.py')) as f:
    exec(f.read(), about)

# Package meta-data.
NAME = about['__title__']
DESCRIPTION = about['__description__']
URL = about['__url__']
EMAIL = about['__author_email__']
AUTHOR = about['__author__']
REQUIRES_PYTHON = '>=3.6.0'


# What packages are required for this module to be executed?
REQUIRED = [
    'mechanicalsoup>=0.11.0,<0.13.0',
    'requests>=2.20.1,<3.0',
    'urllib3>=1.24.1,<2.0',
    'keyring>=17.0.0,<20.0',
    'kombu>=4.2.1',
    'lxml>=4.2.5,<5.0',
    'lz4>=2.1.2,<3.0',
    'openpyxl>=2.5.0,<2.7.0',
    'pyexcel>=0.5.15,<0.6.0',
    'pyexcel-io>=0.5.19,<0.6.0',
    'pyexcel-ods3>=0.5.3,<0.6.0',
    'pyexcel-webio>=0.1.4,<0.2.0',
    'pyexcel-xls>=0.5.8,<0.6.0',
    'pyexcel-xlsx>=0.5.7,<0.6.0',
    'cookiecutter>=1.6.0,<2.0',
    'cssselect>=1.0.3,<2.0',
    'w3lib>=1.19.0,<2.0',
    'pycryptodome>=3.7.2,<4.0',
    'gevent>=1.3.7,<2.0',

]

test_requirements = [
    'pytest>=4.0.1,<5.0',
    'pytest-cov==2.6.0,<3.0',
    'coverage==4.5.2,<5.0',
    'mock==2.0.0,<3.0'
]

# What packages are optional?
EXTRAS = {
    'newt.db': [
        'newt.db>=0.9.0',
        'zodbpickle>=1.0.2',
        'persistent>=4.4.3',
        'zodb>=5.5.1'
    ],
    'redis':[
        'redis>=3.0.1'
    ]
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    download_url='https://github.com/bomquote/transistor/archive/v0.2.2.tar.gz',
    keywords=['scraping', 'crawling', 'spiders', 'requests', 'beautifulsoup4',
              'mechanicalsoup', 'framework', 'headless-browser'],
    packages=find_packages(exclude=('tests',)),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['transistor'],

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license=about['__license__'],
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)