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


"""All GUI events call this module, independent from the used toolkit."""


import os
import signal
import subprocess
import sys
from argparse import ArgumentParser

import alsaaudio

from alsacontrol.alsa import get_num_output_channels, get_full_pcm_name, \
    get_devices, get_device, get_ports, get_port
from alsacontrol.logger import logger, update_verbosity, log_info
from alsacontrol.config import get_config
from alsacontrol.asoundrc import setup_asoundrc


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
        return '{}%'.format(round(volume * 100))
    else:
        return 'muted'


def get_error_advice(error):
    """Get some help for errors."""
    if 'resource busy' in error:
        return (
            'You can try to run `lsof | grep /dev/snd/` to '
            'see which process is blocking it.'
        )
    if 'No such device' in error:
        pcm_output = get_config().get('pcm_output')
        return (
            'The pcm device "{}" does not exist. '.format(pcm_output) +
            'Try to select something different.'
        )
    return None


def select_pcm(device, port):
    """Write this pcm to the configuration and generate asoundrc.

    Parameters
    ----------
    device : string
        "Generic", "jack", ...
    port : string, None
        "sysdefault", "front", etc.
        If "" or None, will select the first possible pcm for that device.
        For jack there are no output options, so "" or None work there.
    """
    pcm_name = get_full_pcm_name(device, port, alsaaudio.PCM_PLAYBACK)
    get_config().set('pcm_output', pcm_name)
    setup_asoundrc()


def get_current_output():
    """Get a tuple describing the current output selection based on config.

    Returns
    -------
    A tuple of (d, device, p, port) with d and p being the index in
    the list of options from get_devices and get_ports.
    """
    pcm_output = get_config().get('pcm_output', None)
    if pcm_output is None:
        return None, None, None, None

    devices = get_devices(alsaaudio.PCM_PLAYBACK)
    if len(devices) == 0:
        logger.error('Could not find any output pcm')
        return
    device = get_device(pcm_output)
    if device not in devices:
        logger.warning('Found unknown device %s in config', device)
        return None, None, None, None
    d = devices.index(device)

    ports = get_ports(device, alsaaudio.PCM_PLAYBACK)
    port = get_port(pcm_output)
    p = ports.index(port)
    if port not in ports:
        logger.warning(
            'Found unknown port %s for device %s in config', port, device
        )
        return d, device, None, None

    return d, device, p, port


class Bindings:
    """Do everything the ui code wants to do without using ui libs."""
    def __init__(self):
        """Parse argv, print version, execute command if possible."""
        parser = ArgumentParser()
        parser.add_argument(
            '-d', '--debug', action='store_true', dest='debug',
            help='Displays additional debug information',
            default=False
        )

        options = parser.parse_args(sys.argv[1:])
        update_verbosity(options.debug)
        log_info()

        self.output_volume = 0
        self.speaker_test_process = None

        self.pcms = None

    def toggle_speaker_test(self):
        """Run the speaker-test script or stop it, if it is running.

        Returns the subprocess or False if it has been stopped.
        """
        if self.speaker_test_process is None:
            num_channels = get_num_output_channels()
            cmd = 'speaker-test -D default -c {} -twav'.format(num_channels)
            logger.info('Testing speakers, %d channels', num_channels)
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            self.speaker_test_process = process
            return process

        self.stop_speaker_test()
        return False

    def check_speaker_test(self):
        """Return a tuple of (running, error) for the speaker test."""
        if self.speaker_test_process is None:
            return False, None

        return_code = self.speaker_test_process.poll()
        if return_code is not None:
            if return_code != 0:
                # speaker-test had an error, try to read it from its output
                lastline = None
                while True:
                    line = self.speaker_test_process.stdout.readline()
                    if len(line) == 0:
                        break
                    lastline = line
                lastline = lastline[:-1].decode()
                logger.error('speaker-test failed: %s', lastline)
                self.speaker_test_process = None
                return False, lastline

            if return_code == 0:
                self.speaker_test_process = None
                return False, None

            if return_code is None:
                return True, None

        return True, None

    def stop_speaker_test(self):
        """Stop the speaker test if it is running."""
        if self.speaker_test_process is None:
            return False

        return_code = self.speaker_test_process.poll()
        if return_code is None:
            pid = self.speaker_test_process.pid
            logger.info('Stopping speaker test')
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except ProcessLookupError:
                logger.debug(
                    'Tried to stop speaker-test process that has already '
                    'been stopped'
                )
                # It has already been stopped
                pass

    def log_new_pcms(self):
        """Write to the console if new devices are added. Return True if so."""
        inputs = set(alsaaudio.pcms(alsaaudio.PCM_CAPTURE))
        outputs = set(alsaaudio.pcms(alsaaudio.PCM_PLAYBACK))
        pcms = inputs.union(outputs)
        changes = 0
        if self.pcms is None:
            # first time running, don't log yet
            pass
        else:
            for pcm in self.pcms.difference(pcms):
                logger.info('Removed pcm %s', pcm)
                changes += 1
            for pcm in pcms.difference(self.pcms):
                logger.info('Found new pcm %s', pcm)
                changes += 1
        self.pcms = inputs.union(outputs)
        return changes > 0
