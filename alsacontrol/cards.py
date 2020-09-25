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


"""Utilities to get and test cards."""


import alsaaudio

from alsacontrol.alsa import play_silence, record_to_nowhere
from alsacontrol.services import is_jack_running
from alsacontrol.logger import logger
from alsacontrol.config import get_config


def input_exists(func, testcard=True, testmixer=True):
    """Check if the configured input card and mixer is available."""
    # might be a pcm name with plugin and device
    card = get_card(get_config().get('pcm_input'))
    if testcard and not card in alsaaudio.cards():
        logger.error('%s, Could not find the input card "%s"', func, card)
        return False
    if testmixer and get_config().get('input_use_softvol'):
        if 'alsacontrol-input-volume' not in alsaaudio.mixers():
            logger.error('%s, Could not find the input softvol mixer', func)
            record_to_nowhere()
            return False
    return True


def output_exists(func, testcard=True, testmixer=True):
    """Check if the configured output card and mixer is available."""
    # might be a pcm name with plugin and device
    card = get_card(get_config().get('pcm_output'))
    if testcard and not card in get_cards():
        logger.error('%s, Could not find the output card "%s"', func, card)
        return False
    if testmixer and get_config().get('output_use_softvol'):
        if 'alsacontrol-output-volume' not in alsaaudio.mixers():
            logger.error('%s, Could not find the output softvol mixer', func)
            play_silence()
            return False
    return True


def get_pcms():
    """Return the configured input and output pcm string."""
    pcm_input = get_config().get('pcm_input')
    pcm_output = get_config().get('pcm_output')
    if pcm_input == 'null':
        logger.warning('No input specified')
    else:
        logger.info('Using input %s', pcm_input)
    if pcm_output == 'null':
        logger.warning('No output specified')
    else:
        logger.info('Using output %s', pcm_output)
    return pcm_input, pcm_output


def get_card(pcm):
    """Split the card from a pcm string.

    get "Generic" from iec958:CARD=Generic,DEV=0
    or sysdefault:CARD=Generic
    or "jack" from "jack"
    """
    if pcm == 'jack':
        return pcm
    if ':CARD=' in pcm:
        card = pcm.split(':CARD=')[1].split(',')[0]
        return card
    # unsupported card
    logger.warning(
        'Encountered unsupported non-hw pcm "%s". Did you mean to set '
        'the config to "hw:CARD=%s"?',
        pcm,
        pcm
    )
    return pcm


def get_cards():
    """List all cards, including options such as jack."""
    cards = alsaaudio.cards()
    if is_jack_running():
        cards.append('jack')
    if len(cards) == 0:
        logger.error('Could not find any card')
    return cards


def card_exists(card):
    """Check if the card is available."""
    # might be a pcm name with plugin and device
    return get_card(card) in alsaaudio.cards()


def get_current_card(source):
    """Get a tuple describing the current card selection based on config.

    Parameters
    ----------
    source : string
        one of 'pcm_input' or 'pcm_output'

    Returns
    -------
    A tuple of (d, card) with d being the index in the list of options
    from get_cards.
    """
    print('get_current_card')
    pcm_name = get_config().get(source)
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
        print('a', card)
        return None, card

    index = cards.index(card)
    return index, card


def only_with_existing_input(func):
    """Decorator to only execute the function when the input exists."""
    def inner(*args, **kwargs):
        if input_exists(func.__name__):
            return func(*args, **kwargs)
        return None
    return inner


def only_with_existing_output(func):
    """Decorator to only execute the function when the output exists."""
    def inner(*args, **kwargs):
        if output_exists(func.__name__):
            return func(*args, **kwargs)
        return None
    return inner


def select_output_pcm(card):
    """Write this pcm to the configuration.

    Parameters
    ----------
    card : string
        "Generic", "jack", ...
    """
    # figure out if this is an actual hardware device or not
    cards = alsaaudio.cards()
    if card is None:
        card = 'null'
    if card in cards:
        plugin = get_config().get('output_plugin')
        pcm_name = f'{plugin}:CARD={card}'
    else:
        pcm_name = card  # otherwise probably jack
    get_config().set('pcm_output', pcm_name)


def select_input_pcm(card):
    """Write this pcm to the configuration.

    Parameters
    ----------
    card : string
        "Generic", "jack", ...
    """
    # figure out if this is an actual hardware device or not
    cards = alsaaudio.cards()
    if card is None:
        card = 'null'
    if card in cards:
        plugin = get_config().get('input_plugin')
        pcm_name = f'{plugin}:CARD={card}'
    else:
        pcm_name = card  # otherwise probably jack
    get_config().set('pcm_input', pcm_name)
