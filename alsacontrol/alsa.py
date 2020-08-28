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


import numpy as np

import alsaaudio
from alsacontrol.logger import logger


INPUT_VOLUME = 'alsacontrol-input-volume'
INPUT_MUTE = 'alsacontrol-input-mute'
OUTPUT_VOLUME = 'alsacontrol-output-volume'
OUTPUT_MUTE = 'alsacontrol-output-mute'


def to_perceived_volume(volume):
    """For a mixer volume of 0.5, figure out the perceived volume."""
    return max(0, min(1, volume ** 2))


def to_mixer_volume(volume):
    """For a perceived volume of 0.5, figure out the mixers volume."""
    return max(0, min(1, volume ** (1 / 2)))


def get_num_output_channels():
    """Get the number of channels."""
    # TODO everything has only been tested with stereo so far
    mixer = alsaaudio.Mixer(OUTPUT_MUTE)
    return len(mixer.getmute())


def get_level():
    """Get the current level of recording."""
    # defaults to 2 channels and 16 bit on the default device
    pcm = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)

    while True:
        length, data = pcm.read()
        if length > 0:
            samples = np.frombuffer(data, dtype=np.int16)
            level = np.max(np.abs(samples))
            # in percent
            return level / ((2 ** 16) / 2)


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
    return 'null'


def set_volume(volume, pcm, nonlinear=False):
    """Change the mixer volume.

    Parameters
    ----------
    volume : float
        New value between 0 and 1
    pcm : int
        0 for output (PCM_PLAYBACK), 1 for input (PCM_CAPTURE)
    nonlinear : bool
        if True, will apply to_mixer_volume
    """
    if pcm == alsaaudio.PCM_PLAYBACK:
        mixer_name = OUTPUT_VOLUME
    elif pcm == alsaaudio.PCM_CAPTURE:
        mixer_name = INPUT_VOLUME
    else:
        raise ValueError('unsupported pcm {}'.format(pcm))

    if nonlinear:
        volume = to_mixer_volume(volume)

    mixer_volume = min(100, max(0, round(volume * 100)))
    logger.debug('setting the "%s" value to %s%%', mixer_name, mixer_volume)
    mixer = alsaaudio.Mixer(mixer_name)
    mixer.setvolume(mixer_volume)


def get_volume(pcm, nonlinear=False):
    """Get the current mixer volume between 0 and 1.

    Parameters
    ----------
    pcm : int
        0 for output (PCM_PLAYBACK), 1 for input (PCM_CAPTURE)
    nonlinear : bool
        if True, will apply to_perceived_volume
    """
    if pcm == alsaaudio.PCM_PLAYBACK:
        mixer_name = OUTPUT_VOLUME
    elif pcm == alsaaudio.PCM_CAPTURE:
        mixer_name = INPUT_VOLUME
    else:
        raise ValueError('unsupported pcm {}'.format(pcm))

    if mixer_name not in alsaaudio.mixers():
        logger.warning('Could not find mixer %s', mixer_name)
        return 0

    # TODO in order for the input mixer to be known, it seems like some sound
    #  needs to be captured, similar to I need to run the alsa test to
    #  see the output-volume mixer
    mixer = alsaaudio.Mixer(mixer_name)
    mixer_volume = mixer.getvolume(pcm)[0] / 100

    if nonlinear:
        return to_perceived_volume(mixer_volume)

    return mixer_volume


def toggle_mute():
    """Mute or unmute."""
    mixer = alsaaudio.Mixer(OUTPUT_MUTE)
    if mixer.getmute()[0]:
        mixer.setmute(0)
        return False
    mixer.setmute(1)
    return True


def is_muted():
    """Figure out if the output is muted or not."""
    mixer = alsaaudio.Mixer(OUTPUT_MUTE)
    return mixer.getmute()[0] == 1
