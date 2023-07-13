# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2022, Dmitry Aleksandrovich Maslov (ABTOMAT)

""" Init Zen BBQ """

from . import keymap_manager
from . import ico
from . import preferences
from . import overlay
from . import sceneConfig
from . import operators
from . import ui
from . import eventHandling

bl_info = {
    "name": "Zen BBQ",
    "author": "Valeriy Yatsenko, Sergey Tyapkin, Viktor [VAN] Teplov, Alex Zhornyak,  Dmitry [ABTOMAT] Maslov",
    "version": (1, 0, 1),
    "description": "Create, adjust and visually control bevel effect without actually changing geometry.",
    "blender": (3, 00, 0),
    "location": "View3D > Sidebar > Zen BBQ > Zen BBQ",
    "warning": "",
    "category": "Mesh",
    "tracker_url": "",
    "wiki_url": ""
}

# ORDER IS IMPORTANT !
modules = [
    ico,
    keymap_manager,
    preferences,
    sceneConfig,
    overlay,
    operators,
    ui,
    eventHandling
]


def register():
    """ Register classes """

    for m in modules:
        m.register()


def unregister():
    """ Unregister classes """

    for m in reversed(modules):
        m.unregister()


if __name__ == "__main__":
    pass
