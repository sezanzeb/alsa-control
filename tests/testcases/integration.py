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


import os
import sys
import unittest
from unittest.mock import patch
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

import alsaaudio
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from alsacontrol.config import get_config
from alsacontrol import services
from fakes import UseFakes, fake_config_path


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

        # doesn't do much except avoid some Gtk assertion error, whatever:
        Gtk.main_quit = lambda: None

    def setUp(self):
        self.fakes = UseFakes()
        self.fakes.patch()
        self.window = launch()

    def tearDown(self):
        self.window.on_close()
        self.window.window.destroy()
        gtk_iteration()
        self.fakes.restore()
        if os.path.exists(fake_config_path):
            os.remove(fake_config_path)
        config = get_config()
        config.create_config_file()
        config.load_config()

    def test_fakes(self):
        self.assertEqual(alsaaudio.cards(), ['FakeCard1', 'FakeCard2'])
        self.assertTrue(services.is_jack_running())

    def test_can_start(self):
        self.assertIsNotNone(self.window)
        self.assertTrue(self.window.window.get_visible())

    def test_toggle_input(self):
        input_row = self.window.input_rows[0]
        input_card_name = self.window.builder.get_object('input_card_name')

        # since the config starts with 'null' as default,
        # no card should be selected
        self.assertEqual(get_config().get('pcm_input'), 'null')
        self.assertIn('No card selected', input_card_name.get_label())

        input_row.select_callback(input_row.card)
        self.assertNotEqual(get_config().get('pcm_input'), 'null')
        self.assertNotIn('No card selected', input_card_name.get_label())

        input_row.select_callback(input_row.card)
        self.assertEqual(get_config().get('pcm_input'), 'null')
        self.assertIn('No card selected', input_card_name.get_label())

    def test_select_output(self):
        cards = alsaaudio.cards()
        card_index = 0
        config = get_config()

        class FakeDropdown:
            """Acts like a Gtk.ComboBoxText object."""
            def get_active_text(self):
                return cards[card_index]

        self.window.on_output_card_selected(FakeDropdown())
        self.assertEqual(
            config.get('pcm_output'),
            f'hw:CARD={cards[card_index]}'
        )

        card_index = 1
        config.set('output_plugin', 'ab')
        self.window.on_output_card_selected(FakeDropdown())
        self.assertEqual(
            config.get('pcm_output'),
            f'ab:CARD={cards[card_index]}'
        )

    def test_select_input(self):
        cards = alsaaudio.cards()
        config = get_config()

        self.window.on_input_card_selected(cards[0])
        self.assertEqual(
            config.get('pcm_input'),
            f'hw:CARD={cards[0]}'
        )

        # selecting it a second time unselects it
        self.window.on_input_card_selected(cards[0])
        self.assertEqual(config.get('pcm_input'), 'null')

        config.set('input_plugin', 'ab')
        self.window.on_input_card_selected(cards[1])
        self.assertEqual(
            config.get('pcm_input'),
            f'ab:CARD={cards[1]}'
        )

    def test_go_to_input_page(self):
        # should start at the output page, no monitoring should be active now
        self.assertEqual([
            input_row._input_level_monitor.running
            for input_row
            in self.window.input_rows
        ], [False, False, False])

        notebook = self.window.get('tabs')

        notebook.set_current_page(1)
        # at least one should be monitoring now. The second card is
        # configured to raise an error for this test.
        self.assertEqual([
            input_row._input_level_monitor.running
            for input_row
            in self.window.input_rows
        ], [True, False, True])

        notebook.set_current_page(0)
        # and back to stopping them all
        self.assertEqual([
            input_row._input_level_monitor.running
            for input_row
            in self.window.input_rows
        ], [False, False, False])


if __name__ == "__main__":
    unittest.main()
