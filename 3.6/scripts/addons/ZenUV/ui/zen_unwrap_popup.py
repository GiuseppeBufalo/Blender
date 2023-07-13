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
from ZenUV.ui.labels import ZuvLabels


class ZenUV_MT_ZenUnwrap_Popup(bpy.types.Menu):
    bl_label = "Zen Unwrap"
    bl_idname = "ZUV_MT_ZenUnwrap_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        layout.label(text=ZuvLabels.ZEN_UNWRAP_POPUP_LABEL)
        layout.separator
        layout.operator("uv.zenuv_unwrap", text=ZuvLabels.ZEN_UNWRAP_AUTO_MODE_LABEL).action = "AUTO"
        layout.operator("uv.zenuv_auto_mark")
        layout.operator("uv.zenuv_seams_by_sharp")
        layout.operator("uv.zenuv_seams_by_uv_islands")


if __name__ == "__main__":
    pass
