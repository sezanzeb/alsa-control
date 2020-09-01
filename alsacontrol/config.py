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
from alsacontrol.alsa import get_default_card, get_card


_config = None


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
    setting = f'{key}={value}'
    for i, line in enumerate(split):
        strip = line.strip()
        if strip.startswith('#'):
            continue
        if strip.startswith(f'{key}='):
            # replace the setting
            logger.debug('Overwriting "%s=%s" in config', key, value)
            split[i] = setting
            found = True
            break
    if not found:
        logger.debug('Adding "%s=%s" to config', key, value)
        split.append(setting)
    return '\n'.join(split)


def input_exists():
    """Check if the configured input card and mixer  is available."""
    # might be a pcm name with plugin and device
    card = get_card(get_config().get('pcm_input', None))
    if not card in alsaaudio.cards():
        logger.error('Could not find the input card')
        return False
    if get_config().get('input_use_softvol', True):
        if 'alsacontrol-input-volume' not in alsaaudio.mixers():
            logger.error('Could not find the input softvol mixer')
            return False
    return True


def output_exists():
    """Check if the configured output card and mixer is available."""
    # might be a pcm name with plugin and device
    card = get_card(get_config().get('pcm_output', None))
    if not card in alsaaudio.cards():
        logger.error('Could not find the output card')
        return False
    if get_config().get('output_use_softvol', True):
        if 'alsacontrol-output-volume' not in alsaaudio.mixers():
            logger.error('Could not find the output softvol mixer')
            return False
    return True


class Config:
    def __init__(self):
        self._path = os.path.expanduser('~/.config/alsacontrol/config')
        self._config = {}

        # create an empty config if it doesn't exist
        if not os.path.exists(os.path.dirname(self._path)):
            os.makedirs(os.path.dirname(self._path))
        if not os.path.exists(self._path):
            logger.info('Creating config file "%s"', self._path)
            os.mknod(self._path)
            # add all default values
            # input
            self.set('pcm_input', get_default_card(alsaaudio.PCM_CAPTURE))
            self.set('input_use_softvol', True)
            self.set('input_use_dsnoop', True)
            # output
            self.set('pcm_output', get_default_card(alsaaudio.PCM_PLAYBACK))
            self.set('output_use_softvol', True)
            self.set('output_use_dmix', True)

        self.load_config()

    def load_config(self):
        """Read the config file."""
        self._config = {}
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
        if key in self._config and self._config[key] == value:
            logger.debug('Setting "%s" is already "%s"', key, value)
            return False
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
            return True


def get_config():
    """Ask for the config. Initialize it if not yet done so."""
    # don't initialize it right away in the global scope, to avoid having
    # the wrong logging verbosity.
    global _config
    if _config is None:
        _config = Config()
    return _config
