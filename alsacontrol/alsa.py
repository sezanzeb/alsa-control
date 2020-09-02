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


def get_level(pcm):
    """Get the current level of recording."""
    length, data = pcm.read()
    if length > 0:
        samples = np.frombuffer(data, dtype=np.int16)
        level = np.max(np.abs(samples))
        # in percent
        return level / ((2 ** 16) / 2)
    return None


def play_silence():
    """In order to make alsa see the mixers, play some silent audio.

    Otherwise 'Unable to find mixer control alsacontrol-output-mute'
    will be thrown at the start.
    """
    logger.debug('Trying to play sound to make the output mixers visible')
    try:
        pcm = alsaaudio.PCM(
            type=alsaaudio.PCM_PLAYBACK,
            channels=1,
            periodsize=32,
            device='default'
        )
        data = b'\x00' * 32
        pcm.write(data)
    except alsaaudio.ALSAAudioError as error:
        error = str(error)
        logger.error(error)
        if 'resource busy' in error:
            logger.error(
                'Your specified output is currently busy, is jack using it?'
            )
        logger.error(
            'Could not initialize output mixer, '
            'try setting a different device.'
        )


def record_to_nowhere():
    """Similar problem as in play_silence with the input mixer.

    Otherwise 'Unable to find mixer control alsacontrol-input-mute'
    will be thrown at the start.
    """
    logger.debug('Trying to capture sound to make the input mixers visible')
    try:
        pcm = alsaaudio.PCM(
            type=alsaaudio.PCM_CAPTURE,
            device='default'
        )
        pcm.read()
    except alsaaudio.ALSAAudioError as error:
        error = str(error)
        logger.error(error)
        if 'resource busy' in error:
            logger.error(
                'Your specified input is currently busy, are jack or pulse'
                'using it?'
            )
        logger.error(
            'Could not initialize input mixer. '
            'Try setting a different device.'
        )


def set_volume(volume, pcm_type, nonlinear=False):
    """Change the mixer volume.

    Parameters
    ----------
    volume : float
        New value between 0 and 1
    pcm_type : int
        0 for output (PCM_PLAYBACK), 1 for input (PCM_CAPTURE)
    nonlinear : bool
        if True, will apply to_mixer_volume
    """
    if pcm_type == alsaaudio.PCM_PLAYBACK:
        mixer_name = OUTPUT_VOLUME
    elif pcm_type == alsaaudio.PCM_CAPTURE:
        mixer_name = INPUT_VOLUME
    else:
        raise ValueError(f'Unsupported PCM {pcm_type}')

    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return

    if nonlinear:
        volume = to_mixer_volume(volume)

    mixer_volume = min(100, max(0, round(volume * 100)))

    mixer = alsaaudio.Mixer(mixer_name)

    current_mixer_volume = mixer.getvolume(pcm_type)[0]
    if mixer_volume == current_mixer_volume:
        return

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
        raise ValueError(f'Unsupported PCM {pcm}')

    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        raise ValueError(f'Could not find mixer {mixer_name}')

    mixer = alsaaudio.Mixer(mixer_name)
    mixer_volume = mixer.getvolume(pcm)[0] / 100

    if nonlinear:
        return to_perceived_volume(mixer_volume)

    return mixer_volume


def toggle_mute(mixer_name):
    """Mute or unmute.

    Returns None if it fails.
    """
    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return None

    mixer = alsaaudio.Mixer(mixer_name)
    if mixer.getmute()[0]:
        mixer.setmute(0)
        return False
    mixer.setmute(1)
    return True


def set_mute(mixer_name, state):
    """Set if the mixer should be muted or not."""
    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return
    mixer = alsaaudio.Mixer(mixer_name)
    mixer.setmute(state)


def is_muted(mixer_name=OUTPUT_MUTE):
    """Figure out if the output is muted or not."""
    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return False

    mixer = alsaaudio.Mixer(mixer_name)
    return mixer.getmute()[0] == 1
