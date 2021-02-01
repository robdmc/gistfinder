# import multiprocessing to avoid this bug (http://bugs.python.org/issue15881#msg170215)
import multiprocessing
assert multiprocessing
import re
from setuptools import setup, find_packages


def get_version():
    """
    Extracts the version number from the version.py file.
    """
    VERSION_FILE = 'gistfinder/version.py'
    mo = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', open(VERSION_FILE, 'rt').read(), re.M)
    if mo:
        return mo.group(1)
    else:
        raise RuntimeError('Unable to find version string in {0}.'.format(VERSION_FILE))


install_requires = [
    'Pygments',
    'click',
    'dataset',
    'fuzzywuzzy',
    'prompt_toolkit',
    'python-Levenshtein',
    'pytz',
    'requests',
    'tqdm',
]

tests_require = [
    'coverage',
    'flake8',
    'mock',
    'nose',
    'wheel',
]

docs_require = [
    'Sphinx',
    'sphinx_rtd_theme'
]

extras_require = {
    'dev': tests_require + docs_require,
}

setup(
    name='gistfinder',
    version=get_version(),
    description='A CLI tool for searching your gists',
    long_description='A CLI tool for searching your gists',
    url='https://github.com/robdmc/gistfinder',
    author='Rob deCarvalho',
    author_email='unlisted@unlisted.net',
    keywords='',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    license='MIT',
    include_package_data=True,
    test_suite='nose.collector',
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'gistfinder = gistfinder.console:cli',
            'gf = gistfinder.console:cli',
        ],
    }
)
