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


"""Global dbus object."""


import dbus

_bus = None


def set_bus(mainloop):
    """Set the global bus object."""
    global _bus
    _bus = dbus.SessionBus(mainloop=mainloop)


def get_bus():
    """Only one bus object seems to work at a time, so use the global one."""
    global _bus
    if _bus is None:
        raise ValueError('Bus was not initialized')
    return _bus


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
