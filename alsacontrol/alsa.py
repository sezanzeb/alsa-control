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


"""Helperfunctions to talk to alsa and further simplify pyalsaaudio."""


import re
import subprocess

import alsaaudio
from alsacontrol.logger import logger


EXP = 3


def get_sysdefault(pcm_type):
    """Of a list of pcm devices, return the one being the sysdefault or null.

    Parameters
    ----------
    pcm_type : string
        one of alsaaudio.PCM_CAPTURE or alsaaudio.PCM_PLAYBACK
    """
    pcm_list = alsaaudio.pcms(pcm_type)
    for pcm in pcm_list:
        if pcm.startswith('sysdefault:'):
            return pcm
    else:
        return 'null'


def set_volume(volume):
    """Change the mixer volume.

    Parameters
    ----------
    volume : float
        New value between 0 and 1
    """
    mixer_volume = min(100, max(0, round(volume * 100)))
    logger.debug('setting the mixer value to %s%%', mixer_volume)
    mixer = alsaaudio.Mixer('alsacontrol-output-volume')
    mixer.setvolume(mixer_volume)


def get_volume():
    """Get the current mixer volume between 0 and 1."""
    mixer = alsaaudio.Mixer('alsacontrol-output-volume')
    mixer_volume = mixer.getvolume(alsaaudio.PCM_PLAYBACK)[0]
    return mixer_volume / 100


def toggle_mute():
    """Mute or unmute."""
    mixer = alsaaudio.Mixer('alsacontrol-output-mute')
    if mixer.getmute()[0]:
        mixer.setmute(0)
        return False
    else:
        mixer.setmute(1)
        return True


def is_muted():
    """Figure out if the output is muted or not."""
    mixer = alsaaudio.Mixer('alsacontrol-output-mute')
    return mixer.getmute()[0] == 1
