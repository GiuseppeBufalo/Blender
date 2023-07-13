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

# Original idea Oleg Stepanov (DotBow)

import bpy
from ZenUV.ui import ui_call
from ZenUV.ui.pie import ZUV_OT_PieMenu
from ZenUV.zen_checker.checker import ZUVChecker_OT_CheckerToggle


def _keymap():
    keymap = []

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name='Mesh', space_type='EMPTY')

    kmi = km.keymap_items.new(ZUV_OT_PieMenu.bl_idname,
                              'U', 'PRESS', ctrl=False, shift=False, alt=True)
    keymap.append((km, kmi))

    kmi = km.keymap_items.new(ui_call.ZUV_OT_Main_Popup_call.bl_idname,
                              'U', 'PRESS', ctrl=False, shift=True, alt=False)
    keymap.append((km, kmi))

    km = kc.keymaps.new(name='UV Editor', space_type='EMPTY')

    kmi = km.keymap_items.new(ZUV_OT_PieMenu.bl_idname,
                              'U', 'PRESS', ctrl=False, shift=False, alt=True)
    keymap.append((km, kmi))

    kmi = km.keymap_items.new(ui_call.ZUV_OT_Main_Popup_call.bl_idname,
                              'U', 'PRESS', ctrl=False, shift=True, alt=False)
    keymap.append((km, kmi))

    km = kc.keymaps.new(name='Window', space_type='EMPTY')

    kmi = km.keymap_items.new(ZUVChecker_OT_CheckerToggle.bl_idname,
                              'T', 'PRESS', alt=True)
    keymap.append((km, kmi))

    # Sticky UV Editor Keymap
    km = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km.keymap_items.new("wm.sticky_uv_editor", "T", "PRESS", shift=True)
    kmi.properties.ui_button = False
    keymap.append((km, kmi))
    # Splitted Sticky UV Editor
    km = kc.keymaps.new(name='Window', space_type='EMPTY')
    kmi = km.keymap_items.new("wm.sticky_uv_editor_split", "T", "PRESS", shift=True, alt=True)
    keymap.append((km, kmi))

    return keymap
