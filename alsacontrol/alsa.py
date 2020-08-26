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


import time

import alsaaudio


def get_sysdefault(type):
    """Of a list of pcm devices, return the one being the sysdefault or null.

    Parameters
    ----------
    type : string
        one of alsaaudio.PCM_CAPTURE or alsaaudio.PCM_PLAYBACK
    """
    pcm_list = alsaaudio.pcms(type)
    for pcm in pcm_list:
        if pcm.startswith('sysdefault:'):
            return pcm
    else:
        return 'null'


def change_volume(volume):
    """Change the current output volume.

    Doesn't return the mixer volume, but rather the volume before a non-linear
    function is applied,

    Parameters
    ----------
    volume : int
        Relative change. Between -100 and 100
    """
    print('change_volume')
    volume = int(volume)
    mixer = alsaaudio.Mixer('alsacontrol-output-volume')
    current_volume = mixer.getvolume()[0]

    exp = 3

    current_volume_linear = (current_volume / 100)**exp
    new_volume_linear = current_volume_linear + (volume / 100)
    new_volume_linear = min(1, max(0, new_volume_linear))

    new_volume = (new_volume_linear**(1 / exp)) * 100
    new_volume = min(100, max(0, int(new_volume)))

    mixer.setvolume(new_volume)
    return new_volume_linear * 100


def get_volume():
    """Get the current output volume."""
    mixer = alsaaudio.Mixer('alsacontrol-output-volume')
    return mixer.getvolume()[0]


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
