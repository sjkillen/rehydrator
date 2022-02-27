# Rehydrator: Opinionated and simple bpy utility library for linking Python data types to blender collections and objects
# Copyright (C) 2022  Spencer Killen
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Rehydrator",
    "author": "Spencer Killen",
    "description": "Opinionated and simple bpy utility library for linking Python data types to blender collections and objects",
    "blender": (2, 80, 0),
    "version": (0, 0, 2),
    "location": "Press F3 and search for 'Rehydrator'",
    "warning": "",
    "category": "Misc",
    "doc_url": "https://github.com/sjkillen/Rehydrator",
    "tracker_url": "https://github.com/sjkillen/Rehydrator/issues",
}

from . import auto_load

auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
