# -*- coding: utf-8 -*-
import os.path
import re
import warnings
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.5.0'

news = os.path.join(os.path.dirname(__file__), 'docs', 'news.rst')
news = open(news).read()
parts = re.split(r'([0-9\.]+)\s*\n\r?-+\n\r?', news)
found_news = ''
for i in range(len(parts) - 1):
    if parts[i] == version:
        found_news = parts[i + i]
        break
if not found_news:
    warnings.warn('No news for this version found.')

long_description = """
stravalib is a Python 2.x and 3.x library that provides a simple API for interacting
with the Strava activity tracking website.
"""

if found_news:
    title = 'Changes in %s' % version
    long_description += '\n%s\n%s\n' % (title, '-' * len(title))
    long_description += found_news

setup(
    name='stravalib',
    version=version,
    author='Hans Lellelid',
    author_email='hans@xmpl.org',
    url='http://github.com/hozn/stravalib',
    license='Apache',
    description='Python library for interacting with Strava v3 REST API',
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    package_data={'stravalib': ['tests/resources/*']},
    install_requires=['python-dateutil{0}'.format('>=2.0,<3.0dev' if sys.version_info[0] == 3 else '>=1.5,<2.0dev'),  # version 1.x is for python 2 and version 2.x is for python 3.
                      'pytz',
                      'requests>=2.0,<3.0dev',
                      'beautifulsoup4>=4.0,<5.0dev',
                      'units'],
    tests_require=['nose>=1.0.3'],
    test_suite='stravalib.tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    use_2to3=True,
    zip_safe=False  # Technically it should be fine, but there are issues w/ 2to3
)
