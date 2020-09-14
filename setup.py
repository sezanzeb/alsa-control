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


import DistUtilsExtra.auto


DistUtilsExtra.auto.setup(
    name='alsacontrol',
    version='0.1.0',
    description='ALSA configuration interface',
    license='GPL-3.0',
    data_files=[
        ('share/alsacontrol/', ['data/asoundrc-template']),
        ('share/applications/', ['data/alsacontrol.desktop']),
        ('/etc/xdg/autostart/', ['data/alsacontrol-daemon.desktop']),
    ],
)
