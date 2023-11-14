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

import bpy
import addon_utils
from ZenUV.prop.zuv_preferences import get_prefs


class ZUV_OT_Keymaps(bpy.types.Operator):
    bl_idname = "ops.zenuv_show_prefs"
    bl_label = "Zen UV Show Prefs"
    bl_options = {'INTERNAL'}
    bl_description = "Set Shortcuts for Zen UV Menus"

    tabs: bpy.props.EnumProperty(
        items=[
            ("KEYMAP", "Keymap", ""),
            ("PANELS", "Panels", ""),
            # ("PIE_MENU", "Pie Menu", ""),
            ("MODULES", "Modules", ""),
            ("STK_UV_EDITOR", "Sticky UV Editor", ""),
            ("HELP", "Help", ""),
        ],
        default="KEYMAP"
    )

    def execute(self, context):

        addon_utils.modules_refresh()

        try:
            mod = addon_utils.addons_fake_modules.get("ZenUV")
            info = addon_utils.module_bl_info(mod)
            info["show_expanded"] = True  # or False to Collapse
        except Exception as e:
            print(e)

        addon_prefs = get_prefs()
        addon_prefs.tabs = self.tabs

        context.preferences.active_section = "ADDONS"
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        bpy.data.window_managers['WinMan'].addon_search = "Zen UV"

        return {'FINISHED'}
