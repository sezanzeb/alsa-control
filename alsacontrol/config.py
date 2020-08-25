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
import json


class Config:
    def __init__(self):
        self._path = os.path.expanduser('~/.config/alsacontrol/config')

        # create an empty config if it doesn't exist
        if not os.path.exists(self._path):
            with open(self._path, 'w+') as config_file:
                json.dump({}, config_file)

        # load config
        with open(self._path) as config_file:
            self._config = json.load(config_file)

    def get(self, key, default):
        """Read a value from the configuration."""
        return self._config.get(key, default)

    def set(self, key, value):
        """Write a setting into memory and ~/.config/alsacontrol/config."""
        self._config[key] = value
        with open(self._path, 'w+') as config_file:
            json.dump(self._config, config_file)
