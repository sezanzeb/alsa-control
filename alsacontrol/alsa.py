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

import dbus
import alsaaudio
from alsacontrol.logger import logger
from alsacontrol.dbus import get_bus


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
    try:
        pcm = alsaaudio.PCM(
            type=alsaaudio.PCM_PLAYBACK,
            channels=1,
            periodsize=32,
            device='default'
        )
        data = b'\x00' * 32
        pcm.write(data)
    except alsaaudio.ALSAAudioError:
        logger.error(
            'Could not initialize output mixer. '
            'Try setting a different device.'
        )
        pass


def record_to_nowhere():
    """Similar problem as in play_silence with the input mixer.

    Otherwise 'Unable to find mixer control alsacontrol-input-mute'
    will be thrown at the start.
    """
    try:
        pcm = alsaaudio.PCM(
            type=alsaaudio.PCM_CAPTURE,
            device='default'
        )
        pcm.read()
    except alsaaudio.ALSAAudioError:
        logger.error(
            'Could not initialize input mixer. '
            'Try setting a different device.'
        )
        pass


def get_default_card(pcm_type):
    """Return some card that can work as default.

    Parameters
    ----------
    pcm_type : int
        one of alsaaudio.PCM_CAPTURE or alsaaudio.PCM_PLAYBACK
    """
    pcms = alsaaudio.pcms()
    for pcm in pcms:
        if 'Generic' in pcm:
            return pcm
        if 'CARD=' in pcm:
            return pcm
    logger.error('Could not find a default card')


def get_card(pcm):
    """Split the card from a pcm string.

    get "Generic" from iec958:CARD=Generic,DEV=0
    or sysdefault:CARD=Generic
    or "jack" from "jack"
    """
    if pcm == 'jack':
        return pcm
    if ':CARD=' in pcm:
        card = pcm.split(':CARD=')[1].split(',')[0]
        return card
    # unsupported card
    return None


def is_jack_running():
    """Test if jack is running."""
    try:
        remote_object = get_bus().get_object(
            'org.jackaudio.service',
            '/org/jackaudio/Controller'
        )
        started = remote_object.IsStarted()
        return started
    except dbus.exceptions.DBusException:
        return False


def get_cards():
    """List all cards, including options such as jack."""
    cards = alsaaudio.cards()
    if is_jack_running():
        cards.append('jack')
    if len(cards) == 0:
        logger.error('Could not find any card')
    return cards


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
        raise ValueError('Unsupported PCM {}'.format(pcm_type))

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
        raise ValueError('Unsupported PCM {}'.format(pcm))

    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return 0

    mixer = alsaaudio.Mixer(mixer_name)
    mixer_volume = mixer.getvolume(pcm)[0] / 100

    if nonlinear:
        return to_perceived_volume(mixer_volume)

    return mixer_volume


def toggle_mute(mixer_name):
    """Mute or unmute."""
    if mixer_name not in alsaaudio.mixers():
        logger.error('Could not find mixer %s', mixer_name)
        return False

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
