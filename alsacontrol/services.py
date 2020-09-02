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


"""To check if services like pulseaudio are up and running."""


import os

import dbus

from alsacontrol.dbus import get_bus


def is_pulse_running():
    """Test if pulseaudio is running.

    If it does, then things might not work as expected.
    """
    return_code = os.system('pulseaudio --check')
    return return_code == 0


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


def is_daemon_running():
    """Test if the alsacontrol daemon is running."""
    try:
        get_bus().get_object(
            'com.alsacontrol.Volume',
            '/'
        )
        print('yes')
        return True
    except dbus.exceptions.DBusException:
        print('no')
        return False
