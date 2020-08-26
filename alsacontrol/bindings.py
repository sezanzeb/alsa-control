#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ALSA-Control - ALSA configuration interface
# Copyright (C) 2020 sezanzeb <proxima@hip70890b.de>
#
# This file is part of ALSA-Control.
#
# ALSA-Control is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ALSA-Control is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ALSA-Control.  If not, see <https://www.gnu.org/licenses/>.


"""All GUI events call this module, independent from the used toolkit."""


import sys
from optparse import OptionParser
from gettext import gettext as _
import pkg_resources

from alsacontrol.logger import logger, update_verbosity


class Bindings:
    """Do everything the ui code wants to do without using ui libs."""
    def __init__(self):
        """Parse argv, print version, execute command if possible."""
        parser = OptionParser()
        parser.add_option(
            '-d', '--debug', action='store_true', dest='debug',
            help=_('Displays additional debug information'),
            default=False
        )

        # read values from setup.py
        VERSION = pkg_resources.require('alsacontrol')[0].version
        NAME = pkg_resources.require('alsacontrol')[0].project_name

        (options, args) = parser.parse_args(sys.argv[1:])
        update_verbosity(options.debug)

        logger.info(('{} {}'.format(NAME, VERSION)))
