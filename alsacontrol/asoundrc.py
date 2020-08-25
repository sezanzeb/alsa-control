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

"""Utilities needed to modify .asoundrc files."""


import os

from alsacontrol.data import get_data_path
from alsacontrol.logger import logger


alsactl_asoundrc = os.path.expanduser('~/.config/alsacontrol/.asoundrc')


def setup():
    """Sets up the .asoundrc include and files in home."""
    check_asoundrc()
    create_asoundrc()
    add_include()


def add_include():
    """Adds the include line for this to ~/.asoundrc."""
    with open(os.path.expanduser('~/.asoundrc'), 'r') as file:
        contents = file.read()

    with open(os.path.expanduser('~/.asoundrc'), 'a') as file:
        include = '<{}>'.format(alsactl_asoundrc)
        if include not in contents:
            file.write(include)


def check_asoundrc():
    """If conflicting configurations exist in .asoundrc, throw a warning."""
    # check if they change the default device
    with open(os.path.expanduser('~/.asoundrc'), 'r') as file:
        for line in file:
            # get all uncommented lines
            if not line.strip().startswith('#'):
                if '.asoundrc.asoundconf>' in line:
                    logger.warning(
                        'asoundconf might break ALSA-Control, '
                        'try to comment it with # in .asoundrc.'
                    )
                if 'pcm.!default' in line:
                    logger.warning(
                        'already having a default device conflicts with '
                        'ALSA-Control'
                    )
                if 'alsacontrol-' in line:
                    logger.warning(
                        'your rule "{}" '.format(line) +
                        'conflicts with ALSA-Control'
                    )


def create_asoundrc():
    """Create and populate ~/.config/alsacontrol/.asoundrc."""
    input_softvol = False
    pcm_input = 'sysdefault:CARD=UR22C'

    output_softvol = True
    pcm_output = 'sysdefault:CARD=UR22C'

    asoundrc_config = {
        'input_pcm_1': 'alsacontrol-input' if input_softvol else pcm_input,
        'output_pcm_1': 'alsacontrol-output' if output_softvol else pcm_output,
        'input_pcm_2': pcm_input,
        'output_pcm_2': pcm_output
    }

    template_path = os.path.join(get_data_path(), '.asoundrc')
    with open(template_path, 'r') as template_file:
        template = template_file.read()

    asoundrc_content = template.format(**asoundrc_config)

    with open(alsactl_asoundrc, 'w+') as asoundrc_file:
        print('writing file', alsactl_asoundrc)
        asoundrc_file.write(asoundrc_content)



