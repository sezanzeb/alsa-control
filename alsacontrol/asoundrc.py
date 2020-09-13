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

"""Utilities needed to modify the .asoundrc configuration."""


import os

from alsacontrol.data import get_data_path
from alsacontrol.config import get_config
from alsacontrol.logger import logger
from alsacontrol.cards import get_pcms


alsactl_asoundrc = os.path.expanduser('~/.config/alsacontrol/asoundrc')


def setup_asoundrc():
    """Sets up the .asoundrc include and files in home."""
    check_asoundrc()
    create_asoundrc()
    add_include()


def add_include():
    """Adds the include line for this to ~/.asoundrc."""
    dot_asoundrc_path = os.path.expanduser('~/.asoundrc')
    if os.path.exists(dot_asoundrc_path):
        with open(dot_asoundrc_path, 'r') as file:
            contents = file.read()
    else:
        contents = ''

    with open(dot_asoundrc_path, 'a') as file:
        include = f'<{alsactl_asoundrc}>'
        if include not in contents:
            file.write(include)


def check_asoundrc():
    """If conflicting configurations exist in .asoundrc, throw a warning."""
    # check if they change the default card
    dot_asoundrc_path = os.path.expanduser('~/.asoundrc')

    if not os.path.exists(dot_asoundrc_path):
        return

    with open(dot_asoundrc_path, 'r') as file:
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
                        'already having a default card conflicts with '
                        'ALSA-Control'
                    )
                if 'alsacontrol-' in line:
                    logger.warning(
                        'your rule "%s" conflicts with ALSA-Control',
                        line
                    )


def should_use_dmix(pcm_output):
    """Check if, according to config, dmix should and can be used."""
    # use dmix only for hardware devices,
    # if the config is on and if the plugin is hw
    hardware_device = 'CARD=' in pcm_output
    output_use_dmix = get_config().get('output_use_dmix')
    output_plugin_hw = pcm_output.startswith('hw:')
    return hardware_device and output_use_dmix and output_plugin_hw


def should_use_dsnoop(pcm_input):
    """Check if, according to config, dsnoop should and can be used."""
    hardware_device = 'CARD=' in pcm_input
    input_use_dmix = get_config().get('input_use_dsnoop')
    input_plugin_hw = pcm_input.startswith('hw:')
    return hardware_device and input_use_dmix and input_plugin_hw


def create_asoundrc():
    """Create and populate ~/.config/alsacontrol/asoundrc."""
    pcm_input, pcm_output = get_pcms()

    if pcm_output == 'jack':
        last_output_step = 'alsacontrol-plug'
    elif should_use_dmix(pcm_output):
        last_output_step = 'alsacontrol-dmix'
    else:
        last_output_step = pcm_output
    # either from asym directly to the last step, or over softvol
    if get_config().get('output_use_softvol'):
        output_pcm_asym = 'alsacontrol-output-softvol'
        output_pcm_softvol = last_output_step
    else:
        output_pcm_asym = last_output_step
        output_pcm_softvol = 'null'

    if pcm_input == 'jack':
        last_input_step = 'alsacontrol-plug'
    elif should_use_dsnoop(pcm_input):
        last_input_step = 'alsacontrol-dsnoop'
    else:
        last_input_step = pcm_input
    # either from asym directly to the last step, or over softvol
    if get_config().get('input_use_softvol'):
        input_pcm_asym = 'alsacontrol-output-softvol'
        input_pcm_softvol = last_input_step
    else:
        input_pcm_asym = last_input_step
        input_pcm_softvol = 'null'

    # dmix and dsnoop always have to be the last step
    asoundrc_config = {
        'output_pcm_asym': output_pcm_asym,
        'output_pcm_softvol': output_pcm_softvol,
        'output_pcm': pcm_output,
        'output_channels': get_config().get('output_channels'),

        'input_pcm_asym': input_pcm_asym,
        'input_pcm_softvol': input_pcm_softvol,
        'input_pcm': pcm_input,
    }

    template_path = os.path.join(get_data_path(), 'asoundrc-template')
    with open(template_path, 'r') as template_file:
        template = template_file.read()

    asoundrc_content = template.format(**asoundrc_config)

    with open(alsactl_asoundrc, 'w+') as asoundrc_file:
        logger.info('Writing file %s', alsactl_asoundrc)
        asoundrc_file.write(asoundrc_content)
