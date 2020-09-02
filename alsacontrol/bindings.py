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


"""Functions only relevant for user interfaces, independent of toolkit."""


from alsacontrol.config import get_config


def get_volume_icon(volume, muted):
    """Return an icon name for use in GUIs.

    Parameters
    ----------
    volume : float
        between 0 and 1.
    muted : bool
        True, if no sound plays currently.
    """
    if muted or volume <= 0:
        icon = 'audio-volume-muted'
    elif volume < 0.5:
        icon = 'audio-volume-low'
    elif volume < 1.0:
        icon = 'audio-volume-medium'
    else:
        icon = 'audio-volume-high'
    return icon


def get_volume_string(volume, muted):
    """Return a string representing the current output state."""
    if not muted:
        return f'{round(volume * 100)}%'
    return 'muted'


def get_error_advice(error):
    """Get some help for errors."""
    if 'resource busy' in error:
        return (
            'You can try to run `lsof +D /dev/snd/` to '
            'see which process is blocking it. It might be jack'
            'or pulseaudio.'
        )
    if 'No such card' in error:
        pcm_output = get_config().get('pcm_output')
        return (
            f'The pcm card "{pcm_output}" does not exist. ' +
            'Try to select something different.'
        )
    return None
