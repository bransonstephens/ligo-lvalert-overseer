#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) Branson Stephens (2015)
#
# This file is part of lvalert-overseer
#
# It is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# It is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LIGO.ORG.  If not, see <http://www.gnu.org/licenses/>.

import os
#from setuptools import setup
from distutils.core import setup

version = "0.1"

AUTHOR = 'Branson Stephens'
AUTHOR_EMAIL = 'branson.stephens@ligo.org'
LICENSE = 'GPLv3'

description = "LVAlert Overseer"
long_description = "An overseer for sending LVAlert messages and logging their return with latency info."


setup(
    name="ligo-lvalert-overseer",
    version=version,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=description,
    long_description=long_description,
    url=None,
    license=LICENSE,
    provides=['ligo', 'ligo.overseer'],
#    namespace_packages=['ligo'],
    packages=['ligo', 'ligo.overseer'],
    scripts=['bin/lvalert_overseer', 'bin/overseer_test_client'],
    requires=['pyxmpp','twisted'],
)
