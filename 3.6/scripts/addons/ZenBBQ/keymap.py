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

# <pep8 compliant>

# Created by Oleg Stepanov (DotBow)

import bpy


def _keymap():
    keymap = []

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    modes = {'Mesh', 'Object Mode'}
    for mode in modes:
        km = kc.keymaps.new(name=mode, space_type='EMPTY')

        # keymap.append((km, km.keymap_items.new('object.zen_bbq_callpie_geometry_options', 'X', 'PRESS', ctrl=True, shift=True)))

        if mode == 'Object Mode':
            keymap.append((km, km.keymap_items.new('object.zen_bbq_callpie_geometry_options', 'X', 'PRESS', ctrl=True, shift=True)))
        else:
            keymap.append((km, km.keymap_items.new('object.zen_bbq_callpie_geometry_options', 'X', 'PRESS', ctrl=True, shift=True)))
            keymap.append((km, km.keymap_items.new('zbbq.draw_highlight', 'F', 'PRESS', ctrl=True, shift=True)))

    return keymap
