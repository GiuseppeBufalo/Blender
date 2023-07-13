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


class ZenUV_MT_ZenChecker_Popup(bpy.types.Menu):
    bl_label = "Zen Checker"
    bl_idname = "ZUV_MT_ZenChecker_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        layout.label(text=ZuvLabels.ZEN_CHECKER_POPUP_LABEL_PART_1)
        layout.label(text=ZuvLabels.ZEN_CHECKER_POPUP_LABEL_PART_2)
        layout.operator("view3d.zenuv_checker_reset")
        layout.label(text=ZuvLabels.ZEN_CHECKER_POPUP_LABEL_PART_3)
        layout.operator("view3d.zenuv_checker_open_editor")


if __name__ == "__main__":
    pass
