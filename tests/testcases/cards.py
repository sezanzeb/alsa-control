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


import unittest

from alsacontrol.config import get_config
from alsacontrol.cards import input_exists, get_current_card, get_card


class CardsTest(unittest.TestCase):
    def test_null_input(self):
        config = get_config()
        config.set('pcm_input', 'null')

        self.assertFalse(input_exists('test_null_input'))
        self.assertIsNone(get_current_card('pcm_input')[0])
        self.assertIsNone(get_current_card('pcm_input')[1])
        self.assertIsNone(get_card(config.get('pcm_input')))

    def test_null_output(self):
        config = get_config()
        config.set('pcm_output', 'null')

        self.assertFalse(input_exists('test_null_output'))
        self.assertIsNone(get_current_card('pcm_output')[0])
        self.assertIsNone(get_current_card('pcm_output')[1])
        self.assertIsNone(get_card(config.get('pcm_output')))


if __name__ == "__main__":
    unittest.main()
