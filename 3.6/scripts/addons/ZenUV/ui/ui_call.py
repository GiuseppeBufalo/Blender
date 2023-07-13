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

""" Zen UV Call Operators """
import bpy


# class ZUV_OT_Main_Pie_call(bpy.types.Operator):
#     bl_idname = "zenuv.call_pie"
#     bl_label = "Zen UV Pie Menu"
#     bl_description = "Call Zen UV Pie menu. You can setup custom hotkey: RMB on the button > Change Shortcut"

#     bl_options = {"REGISTER", "UNDO"}

#     def invoke(self, context, event):
#         return self.execute(context)

#     def execute(self, context):
#         # bpy.ops.wm.call_menu_pie(name="ZUV_MT_Main_Pie")
#         bpy.ops.wm.call_menu_pie(name="ZUV_MT_BasicPie")
#         return {"FINISHED"}


class ZUV_OT_Main_Popup_call(bpy.types.Operator):
    bl_idname = "zenuv.call_popup"
    bl_label = "Zen UV Popup Menu"
    bl_description = "Call Zen UV Popup menu. You can setup custom hotkey: RMB on the button > Change Shortcut"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        bpy.ops.wm.call_menu(name="ZUV_MT_Main_Popup")
        return {"FINISHED"}
