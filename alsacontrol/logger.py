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


import logging


class Formatter(logging.Formatter):
    def format(self, record):
        debug = logger.level == logging.DEBUG
        if record.levelno == logging.INFO and not debug:
            # if not launched with --debug, then don't print "INFO:"
            self._style._fmt = '%(msg)s'  # noqa
        else:
            # see https://en.wikipedia.org/wiki/ANSI_escape_code#3/4_bit
            # for those numbers
            color = {
                logging.WARNING: 33,
                logging.ERROR: 31,
                logging.FATAL: 31,
                logging.DEBUG: 36,
                logging.INFO: 32,
            }.get(record.levelno, 0)
            if debug:
                self._style._fmt = (  # noqa
                    '\033[{}m%(levelname)s\033[0m: '
                    '%(filename)s, line %(lineno)d, %(msg)s'
                ).format(color)
            else:
                self._style._fmt = (  # noqa
                    '\033[{}m%(levelname)s\033[0m: %(msg)s'
                ).format(color)
        return super().format(record)


logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(Formatter())
logger.addHandler(handler)


def update_verbosity(debug):
    """Set the logging verbosity according to the settings object."""
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
