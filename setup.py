import os
import sys
from shutil import rmtree
from pathlib import Path

from setuptools import find_packages, setup, Command

import cyberserver

here = Path(__file__).absolute()

meta_data = dict(
    NAME = 'cyberserver',
    VERSION = cyberserver.__version__,
    DESCRIPTION = 'Server for Cyber Attacks Map application',
    URL = 'https://github.com/csd3345/cybermap-server',
    EMAIL = 'csd3345@csd.uoc.gr',
    AUTHOR = 'Latsis Ilias',
    REQUIRES_PYTHON = '>=3.6.0',
    REQUIRED = [
        'tornado>=6.0.3',
        'redis>=3.3.11',
        'aioredis>=1.3.0',
        'Click>=7.0',
        'click_help_colors',
        'colored',
        'cryptography',
        'options',
        'colorama>=0.4.1',
        'coloredlogs>=10.0',
        'maxminddb>=1.5.1',
        'six>=1.12.0',
        
    ],
)

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in MANIFEST.in file!
try:
    readme_path = here.joinpath("README.md")
    if not readme_path.exists():
        raise FileNotFoundError
    with readme_path.open(encoding = 'utf-8') as f:
        long_description = '\n' + f.read()
        long_description_content_type = 'text/markdown'
except FileNotFoundError:
    long_description = meta_data["DESCRIPTION"]
    long_description_content_type = 'text/plain'

# Load the package's __version__.py module as a dictionary.
about = {}
if not meta_data["VERSION"]:
    project_slug = meta_data["NAME"].lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = meta_data["VERSION"]

# Where the magic happens:
setup(
    name = meta_data["NAME"],
    version = about['__version__'],
    description = meta_data["DESCRIPTION"],
    long_description = long_description,
    long_description_content_type = long_description_content_type,
    author = meta_data["AUTHOR"],
    author_email = meta_data["EMAIL"],
    python_requires = meta_data["REQUIRES_PYTHON"],
    url = meta_data["URL"],
    # packages = ['cyberserver', 'cyberserver.servers'],
    packages = find_packages(
        exclude = ["tests", "*.tests", "*.tests.*", "tests.*"]
    ),
    # package_dir={'cybermap': 'cybermap'},
    include_package_data = True,
    package_data = {
        #'cyberserver.servers': ['databases/*.mmdb'],
        'cyberserver': ['databases/*.mmdb']
    },
    entry_points = {
        'console_scripts': [
            'cybermap=cyberserver.servers.SSE_test:main',
            'proxy=cyberserver.servers.proxy:main',
            'generator=cyberserver.servers.attacks_generator:main'
        ],
    },
    install_requires = meta_data["REQUIRED"],
    license = 'MIT',
    classifiers = [
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
)
