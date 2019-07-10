#  Copyright (c) 2019 Giacomo Lacava <giac@autoepm.com>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from pathlib import Path

from setuptools import setup

import djxero

BASEDIR = Path(__file__).parent

# load readme contents
README = open(BASEDIR / 'README.md').read()
# read requirements from requirements.txt
REQUIREMENTS = []
with open(BASEDIR / 'requirements.txt', 'r', encoding='utf-8') as reqtxt:
    for line in reqtxt:
        reqline = line.strip()
        if reqline and not reqline.startswith('#'):
            REQUIREMENTS.append(reqline)

setup(
    name=djxero.__title__,
    version=djxero.__version__,
    packages=['djxero', ],
    include_package_data=True,
    license=djxero.__license__,
    description=djxero.__doc__,
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/toyg/django-xero',
    author=djxero.__author__,
    author_email='giac@autoepm.com',
    install_requires=REQUIREMENTS,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Session',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Accounting',
    ]
)
