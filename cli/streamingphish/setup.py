#!/usr/bin/python3

"""StreamingPhish software installer"""

import os
from setuptools import setup, find_packages

# TODO read from README.
long_description = """
streamingphish is a utility that uses supervised machine learning to detect phishing domains from the Certificate Transparency log network. The firehose of domain names and SSL certificates are made available thanks to the certstream network (certstream.calidog.io).

As a prototype and educational utility, this package also includes a Jupyter notebook to help explain each step of the supervised machine learning lifecycle.
"""

# Function to get non-data files.
# Data and Example Files
def get_files(dir_name):
    """
    Takes a directory name and returns a list of all files inside of it.
    """
    return [(os.path.join('.', d), [os.path.join(d, f) for f in files]) for d, _, files in os.walk(dir_name)]

setup(
    name = 'streamingphish',
    version = '0.4',
    url = 'https://github.com/wesleyraptor/streamingphish/',
    author = 'Wes Connell',
    author_email = 'wes@raptorlabs.io',
    description = 'streamingphish is a utility that uses machine learning to identify phishing domains.',
    long_description = long_description,
    packages = find_packages(),
    include_package_data=True,
    data_files=get_files('data') + get_files('config'),
    entry_points = {
        'console_scripts': ['streamingphish=streamingphish.__main__:main'],
    },
    license='MIT License',
    classifiers = [
        "Development Status :: 4 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: Information Analysis"
    ],
    keywords='phishing certstream machine learning'
)
