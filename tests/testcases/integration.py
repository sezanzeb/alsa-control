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


import sys
import unittest
from unittest.mock import patch
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

from alsacontrol.config import get_config
from alsacontrol.cards import input_exists, get_current_card, get_card

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def gtk_iteration():
    """Iterate while events are pending."""
    while Gtk.events_pending():
        Gtk.main_iteration()


def launch(argv=None, bin_path='bin/alsacontrol-gtk'):
    """Start alsacontrol-gtk with the command line argument array argv."""
    print('Launching UI')
    if not argv:
        argv = ['-d']

    with patch.object(sys, 'argv', [''] + [str(arg) for arg in argv]):
        loader = SourceFileLoader('__main__', bin_path)
        spec = spec_from_loader('__main__', loader)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

    gtk_iteration()

    return module.window


class Integration(unittest.TestCase):
    """For tests that use the window.

    Try to modify the configuration and .asoundrc only by calling
    functions of the window.
    """
    @classmethod
    def setUpClass(cls):
        # iterate a few times when Gtk.main() is called, but don't block
        # there and just continue to the tests while the UI becomes
        # unresponsive
        Gtk.main = gtk_iteration
        Gtk.main_quit = lambda: None

    def setUp(self):
        self.window = launch()

    def tearDown(self):
        self.window.on_close()
        gtk_iteration()

    def test_can_start(self):
        self.assertIsNotNone(self.window)
        self.assertTrue(self.window.window.get_visible())

    def test_toggle_input(self):
        input_row = self.window.input_rows[0]
        input_card_name = self.window.builder.get_object('input_card_name')

        # since the config starts with 'null' as default, no card should be selected
        self.assertEqual(get_config().get('pcm_input'), 'null')
        self.assertIn('No card selected', input_card_name.get_label())

        input_row.select_callback(input_row.card)
        self.assertNotEqual(get_config().get('pcm_input'), 'null')
        self.assertNotIn('No card selected', input_card_name.get_label())

        input_row.select_callback(input_row.card)
        self.assertEqual(get_config().get('pcm_input'), 'null')
        self.assertIn('No card selected', input_card_name.get_label())


if __name__ == "__main__":
    unittest.main()
