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


"""Keep track of added or removed cards."""


from alsacontrol.cards import get_cards
from alsacontrol.logger import logger


class CardsTracker:
    """To keep track of added or removed cards."""
    def __init__(self):
        """Create it without doing anything yet."""
        self.cards = None

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
