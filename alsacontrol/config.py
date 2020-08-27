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

"""Query settings."""


import os

import alsaaudio

from alsacontrol.logger import logger
from alsacontrol.alsa import get_sysdefault


def _modify_config(config_contents, key, value):
    """Write settings into a config files contents.

    Parameters
    ----------
    config_contents : string
        Contents of the config file in ~/.config/alsacontrol/config
    key : string
        Settings key that should be modified
    value : string, int
        Value to write
    """
    logger.info('Setting "%s" to "%s"', key, value)
    split = config_contents.split('\n')
    if split[-1] == '':
        split = split[:-1]

    found = False
    setting = '{}={}'.format(key, value)
    for i, line in enumerate(split):
        strip = line.strip()
        if strip.startswith('#'):
            continue
        if strip.startswith('{}='.format(key)):
            # replace the setting
            logger.debug('Overwriting "%s=%s" in config', key, value)
            split[i] = setting
            found = True
            break
    if not found:
        logger.debug('Adding "%s=%s" to config', key, value)
        split.append(setting)
    return '\n'.join(split)


_config = None


class Config:
    def __init__(self):
        self._path = os.path.expanduser('~/.config/alsacontrol/config')
        self._config = {}

        # create an empty config if it doesn't exist
        if not os.path.exists(self._path):
            logger.info('Creating config file "%s"', self._path)
            os.mknod(self._path)
            # add all default values. Don't guess those values during
            # operation to avoid suddenly changing the output device.
            self.set('pcm_input', get_sysdefault(alsaaudio.PCM_CAPTURE))
            self.set('pcm_output', get_sysdefault(alsaaudio.PCM_PLAYBACK))

        # load config
        with open(self._path, 'r') as config_file:
            for line in config_file:
                line = line.strip()
                if not line.startswith('#'):
                    split = line.split('=', 1)
                    if len(split) == 2:
                        key = split[0]
                        value = split[1]
                    else:
                        key = split[0]
                        value = None
                self._config[key] = value

    def get(self, key, default=None):
        """Read a value from the configuration."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Write a setting into memory and ~/.config/alsacontrol/config."""
        if key in value and self._config[key] == value:
            logger.debug('Setting "%s" is already "%s"', key, value)
        else:
            self._config[key] = value

            with open(self._path, 'r+') as config_file:
                config_contents = config_file.read()
                config_contents = _modify_config(config_contents, key, value)

            # overwrite completely
            with open(self._path, 'w') as config_file:
                if not config_contents.endswith('\n'):
                    config_contents += '\n'
                config_file.write(config_contents)


def get_config():
    """Ask for the config. Initialize it if not yet done so."""
    # don't initialize it right away in the global scope, to avoid having
    # the wrong logging verbosity.
    global _config
    if _config is None:
        _config = Config()
    return _config
