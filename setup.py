import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command


# Package meta-data.
NAME = 'cybermap-server'
DESCRIPTION = 'Server for Cyber Attacks Map application'
URL = 'https://github.com/me/myproject'
EMAIL = 'csd3345@csd.uoc.gr'
AUTHOR = 'Latsis Ilias'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = '1.0.1'

# What packages are required for this module to be executed?
REQUIRED = [
    # 'requests', 'maya', 'records', 'tqdm',
    'Click>=7.0',
    'colorama>=0.4.1',
    'coloredlogs>=10.0',
    'maxminddb>=1.5.1',
    'redis>=3.3.11',
    'aioredis>=1.3.0',
    'six>=1.12.0',
    'tornado>=6.0.3',
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}
here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding = 'utf-8') as f:
        long_description = '\n' + f.read()
        long_description_content_type = 'text/markdown'
except FileNotFoundError:
    long_description = DESCRIPTION
    long_description_content_type = 'text/plain'

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


class UploadCommand(Command):
    """Support setup.py upload.
    
    Note: To use the 'upload' functionality of this file, you must:
          $ pipenv install twine --dev
    """
    
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
    name = NAME,
    version = about['__version__'],
    description = DESCRIPTION,
    long_description = long_description,
    long_description_content_type = long_description_content_type,
    author = AUTHOR,
    author_email = EMAIL,
    python_requires = REQUIRES_PYTHON,
    url = URL,
    packages = ['cybermap', 'cybermap.servers', ''],
    # find_packages(
    #     exclude = ["tests", "*.tests", "*.tests.*", "tests.*"]
    # ),
    # package_dir={'cybermap': 'cybermap'},
    package_data = {'cybermap.servers': ['databases/*.mmdb']},
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'cybermap=cybermap.servers.SSE_test:main',
            'proxy=cybermap.servers.proxy:main',
            'generator=cybermap.servers.attacks_generator:main'
        ],
    },
    install_requires = REQUIRED,
    extras_require = {
        # 'fancy feature': ['django'],
    },
    license = 'MIT',
    classifiers = [
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        # If you change the License, remember to change the Trove Classifier as well.
        'License :: OSI Approved :: MIT License',
    ],
    cmdclass = {
        'upload': UploadCommand,  # $ setup.py publish support.
    },
)
