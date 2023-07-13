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
import rna_keymap_ui

from .keymap import _keymap

addon_keymap = []


def get_hotkey_entry_item(km, kmi_name, kmi_value, handled_kmi):
    for km_item in km.keymap_items:
        if km_item in handled_kmi:
            continue
        if km_item.idname == kmi_name:
            if kmi_value is None:
                return km_item
            elif ('name' in km_item.properties) and (km_item.properties.name == kmi_value):
                return km_item

    return None


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        addon_keymap.extend(_keymap())


def unregister():
    for km, kmi in addon_keymap:
        km.keymap_items.remove(kmi)

    addon_keymap.clear()


def draw_keymaps(context, layout):
    wm = context.window_manager
    kc = wm.keyconfigs.user
    box = layout.box()
    split = box.split()
    col = split.column()
    col.label(text='Setup Keymap')

    km_tree = {}
    for _km, _kmi in addon_keymap:
        if _km.name not in km_tree:
            km_tree[_km.name] = []

        km_tree[_km.name].append((_kmi.idname, _kmi.properties.name if 'name' in _kmi.properties else None))

    """ Special case for Tool keymap """

    # (Not present in Zen BBQ yet)

    for _km in kc.keymaps:
        if 'Zen BBQ' in _km.name:
            if _km.name not in km_tree:
                km_tree[_km.name] = []

            for _kmi in _km.keymap_items:
                km_tree[_km.name].append(_kmi)

    handled_kmi = set()
    for km_name, kmi_items in km_tree.items():
        km = kc.keymaps.get(km_name)
        if km:
            col.context_pointer_set("keymap", km)
            col.separator()
            row = col.row(align=True)
            row.label(text=km_name)

            if km.is_user_modified:
                subrow = row.row()
                subrow.alignment = 'RIGHT'
                subrow.operator("preferences.keymap_restore", text="Restore")

            for kmi_node in kmi_items:
                kmi = get_hotkey_entry_item(km, kmi_node[0], kmi_node[1], handled_kmi) if isinstance(kmi_node, tuple) else kmi_node
                col.separator()

                if kmi:
                    handled_kmi.add(kmi)
                    rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
                else:
                    row = col.row(align=True)
                    row.separator(factor=2.0)
                    row.label(text=f"Keymap item for '{kmi_node[0]} ' in '{km_name}' not found",
                              icon='ERROR')
