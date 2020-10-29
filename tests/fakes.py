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


"""Patch alsaaudio to get reproducible tests."""


from unittest.mock import patch

import alsaaudio

from alsacontrol import services
from alsacontrol.config import get_config
from alsacontrol.cards import get_card


fake_config_path = '/tmp/alsacontrol-test-config'


class FakeMixer:
    """Fake mixer object."""
    def __init__(self, name):
        self.name = name
        self.mute = False
        self.volume = 50
        self.channels = 2

    def getmute(self):
        return [self.mute] * self.channels

    def getvolume(self, pcm):
        """The direction arguments are unused, because I have one mixer
        for each direction instead of unidirectional ones.
        """
        # two channels
        return [self.volume] * self.channels

    def setmute(self, mute):
        self.mute = mute

    def setvolume(self, volume):
        self.volume = volume


class FakePCM:
    def __init__(self, type, device, *args, **kwargs):
        self.type = type
        config_key = {
            alsaaudio.PCM_CAPTURE: 'pcm_input',
            alsaaudio.PCM_PLAYBACK: 'pcm_output'
        }[type]
        if device is None or device == 'default':
            self.card = get_card(get_config().get(config_key))
            if self.card is None:
                raise ValueError(
                    'I don\'t think the PCM constructor should '
                    'be called when no device is set'
                )
        else:
            self.card = device

    def write(self, data):
        if 'FakeCard2' in self.card:
            raise alsaaudio.ALSAAudioError()
        if self.type == alsaaudio.PCM_CAPTURE:
            raise ValueError('tried to read on a capture PCM')

    def read(self):
        if 'FakeCard2' in self.card:
            raise alsaaudio.ALSAAudioError()
        if self.type == alsaaudio.PCM_PLAYBACK:
            raise ValueError('tried to write on a playback PCM')
        # this is a subset of some random stuff that this function
        # returned at some point.
        return 3, b'\x01\x00\x01\x00\x00\x00\xff\xff\xff\xff\xff\xff'


class UseFakes:
    """Provides fake functionality for alsaaudio and some services."""
    def __init__(self):
        self.patches = []

    def patch(self):
        """Replace the functions of alsaaudio with various fakes."""
        # alsaaudio patches
        self.patches.append(patch.object(alsaaudio, 'cards', self.cards))
        self.patches.append(patch.object(alsaaudio, 'PCM', FakePCM))
        self.patches.append(patch.object(alsaaudio, 'mixers', self.mixers))
        self.patches.append(patch.object(alsaaudio, 'Mixer', FakeMixer))

        # service patches
        self.patches.append(
            patch.object(services, 'is_jack_running', lambda: True)
        )

        for p in self.patches:
            p.__enter__()

    def restore(self):
        """Restore alsaaudios functionality."""
        for p in self.patches:
            p.__exit__(None, None, None)
        self.patches = []

    @staticmethod
    def mixers():
        config = get_config()
        mixers = []
        if config.get('input_use_softvol'):
            mixers.append('alsacontrol-input-volume')
            mixers.append('alsacontrol-input-mute')
        if config.get('output_use_softvol'):
            mixers.append('alsacontrol-output-volume')
            mixers.append('alsacontrol-output-mute')
        return mixers

    @staticmethod
    def cards():
        return ['FakeCard1', 'FakeCard2']