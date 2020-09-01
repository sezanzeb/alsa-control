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


"""Stuff that honestly should be separated into multiple files."""


import os
import signal
import subprocess
import sys
from argparse import ArgumentParser

import alsaaudio

from alsacontrol.alsa import get_cards, get_card, play_silence, \
    record_to_nowhere
from alsacontrol.logger import logger, update_verbosity, log_info
from alsacontrol.config import get_config
from alsacontrol.asoundrc import setup_asoundrc
from alsacontrol.dbus import get_bus
from alsacontrol.config import output_exists, input_exists


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


def select_output_pcm(card):
    """Write this pcm to the configuration and generate asoundrc.

    Parameters
    ----------
    card : string
        "Generic", "jack", ...
    """
    # figure out if this is an actual hardware device or not
    cards = alsaaudio.cards()
    if card in cards:
        plugin = get_config().get('output_plugin', 'hw')
        pcm_name = f'{plugin}:CARD={card}'
    else:
        pcm_name = card  # otherwise probably jack
    get_config().set('pcm_output', pcm_name)
    setup_asoundrc()


def select_input_pcm(card):
    """Write this pcm to the configuration and generate asoundrc.

    Parameters
    ----------
    card : string
        "Generic", "jack", ...
    """
    # figure out if this is an actual hardware device or not
    cards = alsaaudio.cards()
    if card in cards:
        plugin = get_config().get('input_plugin', 'sysdefault')
        pcm_name = f'{plugin}:CARD={card}'
    else:
        pcm_name = card  # otherwise probably jack
    get_config().set('pcm_input', pcm_name)
    setup_asoundrc()


def get_current_card(source):
    """Get a tuple describing the current card selection based on config.

    Parameters
    ----------
    source : string
        one of 'pcm_input' or 'pcm_output'

    Returns
    -------
    A tuple of (d, card) with d being the index in
    the list of options from get_cards.
    """
    pcm_name = get_config().get(source, 'null')
    if pcm_name == 'null':
        logger.warning('No input selected')
        return None, None

    cards = get_cards()
    if len(cards) == 0:
        logger.error('Could not find any card')
        return None, None

    card = get_card(pcm_name)
    if card not in cards:
        logger.warning('Found unknown %s "%s" in config', source, pcm_name)
        return None, None

    index = cards.index(card)
    return index, card


def read_from_std(source):
    """Read all the contents from stderr or stdout of the speaker test."""
    lines = []
    while True:
        line = source.readline()
        if len(line) == 0:
            break
        line = line[:-1].decode()
        if len(line) > 0:
            lines.append(line)
    return lines


def eavesdrop_volume_notifications(callback):
    """Listen on the notification DBus for ALSA-Control messages."""
    bus = get_bus()
    bus.add_match_string_non_blocking(','.join([
        "interface='org.freedesktop.Notifications'",
        "member='Notify'",
        "eavesdrop='true'"
    ]))

    def message_eavsedropped(_, msg):
        """Now figure out if this message is from ALSA-Control."""
        args = msg.get_args_list()
        if len(args) > 0:
            application = str(args[0])
            if application == 'ALSA-Control':
                callback()

    bus.add_message_filter(message_eavsedropped)


def only_with_existing_input(func):
    """Decorator to only execute the function when the input exists."""
    def inner(*args, **kwargs):
        if input_exists():
            return func(*args, **kwargs)
        else:
            return
    return inner


def only_with_existing_output(func):
    """Decorator to only execute the function when the output exists."""
    def inner(*args, **kwargs):
        if output_exists():
            return func(*args, **kwargs)
        else:
            return
    return inner


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
        setup_asoundrc()

        # discover mixers
        play_silence()
        record_to_nowhere()

        self.output_volume = 0
        self.speaker_test_process = None

        self.cards = None

    def toggle_speaker_test(self):
        """Run the speaker-test script or stop it, if it is running.

        Returns the subprocess or False if it has been stopped.
        """
        if self.speaker_test_process is None:
            num_channels = get_config().get('num_output_channels', 2)
            cmd = f'speaker-test -D default -c {num_channels} -twav'.split()
            logger.info('Testing speakers, %d channels', num_channels)
            process = subprocess.Popen(
                cmd,
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
            if return_code == -15:
                # the test was stopped by hand
                return False, None

            if return_code != 0:
                # speaker-test had an error, try to read it from its output
                logger.error('speaker-test failed (code %d):', return_code)
                msg = []

                stderr = read_from_std(self.speaker_test_process.stderr)
                stdout = read_from_std(self.speaker_test_process.stdout)

                self.speaker_test_process = None

                if len(stderr) > 0:
                    msg.append('Errors:')
                    for line in stderr:
                        logger.error('speaker-test stderr: %s', line)
                        msg.append(line)

                if len(stdout) > 0:
                    msg += ['', 'Output:']
                    for line in stdout:
                        logger.error('speaker-test stdout: %s', line)
                        msg.append(line)

                if len(msg) == 0:
                    msg = f'Unknown error. Exit code {return_code}'
                else:
                    msg = '\n'.join(msg)

                return False, msg

            if return_code == 0:
                self.speaker_test_process = None
                return False, None

            if return_code is None:
                return True, None

        return True, None

    def stop_speaker_test(self):
        """Stop the speaker test if it is running."""
        if self.speaker_test_process is None:
            return

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
            self.speaker_test_process = None

    def log_new_pcms(self):
        """Write to the console if new cards are added. Return True if so."""
        # using .cards() isntead of .pcms() is MUCH faster
        cards = set(get_cards())
        changes = 0
        if self.cards is None:
            # first time running, don't log yet
            pass
        else:
            for pcm in self.cards.difference(cards):
                logger.info('PCM %s was removed', pcm)
                changes += 1
            for pcm in cards.difference(self.cards):
                logger.info('Found new PCM %s', pcm)
                changes += 1
        self.cards = cards
        return changes > 0
