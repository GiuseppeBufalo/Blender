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


class ZenUV_MT_ZenMark_Popup(bpy.types.Menu):
    bl_label = "Zen Mark"
    bl_idname = "ZUV_MT_ZenMark_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        area_type = context.area.type
        layout.label(text="Nothing is produced. Selected polygons do not have a borders. You can use following functions:")
        layout.separator

        layout.operator("uv.zenuv_unwrap", text="Auto Mark & Unwrap").action = "AUTO"
        layout.operator("uv.zenuv_auto_mark")
        layout.operator("uv.zenuv_seams_by_sharp")


if __name__ == "__main__":
    pass
