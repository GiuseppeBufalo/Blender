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

""" Init Zen UV """
import bpy
from ZenUV import ops
from ZenUV import ui
from ZenUV import prop
from ZenUV import zen_checker
from ZenUV import stacks
from ZenUV import draw
import ZenUV.ico as ico
from ZenUV import sticky_uv_editor
from ZenUV.utils import clib
from ZenUV.utils.tests import addon_test
# from ZenUV.utils.clib.lib_init import unregister_library
from ZenUV.utils.tests import system_operators

from ZenUV.ui.keymap_manager import register_keymap, unregister_keymap

from ZenUV.utils.blender_zen_utils import ZenPolls

bl_info = {
    "name": "Zen UV",
    "author": "Valeriy Yatsenko, Alex Zhornyak, Sergey Tyapkin, Viktor [VAN] Teplov",
    "version": (3, 1, 1, 0),
    "description": "Optimize UV mapping workflow",
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Zen UV",
    "category": "UV",
    "tracker_url": "https://discordapp.com/invite/wGpFeME",
    "wiki_url": "https://zen-masters.github.io/Zen-UV/"
}

classes = [
    ui,
    # clib,
    ops,
    stacks,
    draw,
    sticky_uv_editor,
    prop
]


def register():
    """ Register classes """

    if bpy.app.version >= (3, 2, 0):
        ZenPolls.version_greater_3_2_0 = True

    ico.register()
    for c in classes:
        c.register()

    zen_checker.register()

    register_keymap()

    addon_test.register()

    # Register Library
    clib.register()

    system_operators.register()


def unregister():
    # Unregister Library
    clib.unregister()

    """ Unregister classes """
    for c in classes:
        c.unregister()

    zen_checker.unregister()

    unregister_keymap()

    ico.unregister()

    addon_test.unregister()

    system_operators.unregister()


if __name__ == "__main__":
    register()
