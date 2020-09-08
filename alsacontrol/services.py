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
import subprocess

import dbus

from alsacontrol.dbus import get_bus
from alsacontrol.logger import logger


def is_pulse_running():
    """Test if pulseaudio is running.

    If it does, then things might not work as expected.
    """
    return_code = os.system('pulseaudio --check')
    return return_code == 0


def stop_pulse():
    """Stop the pulseaudio service using systemctl."""
    if is_pulse_running():
        logger.info('Stopping pulseaudio')
        os.system('systemctl --user stop pulseaudio.service')
        os.system('systemctl --user stop pulseaudio.socket')
        os.system('pulseaudio -k')
    else:
        logger.info('Pulseaudio is not running')


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
        return True
    except dbus.exceptions.DBusException:
        return False


def toggle_daemon():
    """Start or stop the daemon."""
    if is_daemon_running():
        stop_daemon()
    else:
        start_daemon()


def stop_daemon():
    """Stop the alsacontrol daemon."""
    # stops alsacontrol-daemon-gtk or alsacontrol-daemon-qt if that should
    # ever exist in the future
    logger.info('Stopping the alsacontrol daemon')
    os.system('pkill -f alsacontrol-daemon')


def start_daemon(debug=True):
    """Start the alsacontrol daemon."""
    logger.info('Starting the alsacontrol daemon')
    cmd = ['alsacontrol-daemon-gtk']
    if debug:
        cmd.append('-d')
    subprocess.Popen(cmd)
