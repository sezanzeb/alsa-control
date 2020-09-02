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


"""To test the speaker setup."""

import os
import signal
import subprocess

from alsacontrol.logger import logger
from alsacontrol.config import get_config


class SpeakerTest:
    """Speaker testing state and utilities."""
    def __init__(self):
        """Initialize speakertest."""
        self.speaker_test_process = None

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

                stderr = self._read_from_std(self.speaker_test_process.stderr)
                stdout = self._read_from_std(self.speaker_test_process.stdout)

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

    def _read_from_std(self, source):
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
