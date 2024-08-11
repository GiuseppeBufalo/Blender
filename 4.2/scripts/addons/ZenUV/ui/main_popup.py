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

""" Zen UV Main Popup Menu """
import bpy
from ZenUV.ico import icon_get
from ZenUV.ui.labels import ZuvLabels


bl_info = {
    "name": "Zen UV Popup Menu",
    "version": (0, 1),
    "description": "Zen UV Main Popup Menu",
    "blender": (2, 80, 0),
    "category": "UV"
}


class ZenUV_MT_Main_Popup(bpy.types.Menu):
    bl_label = "Zen UV Menu"
    bl_idname = "ZUV_MT_Main_Popup"

    def draw(self, context):
        layout = self.layout
        area_type = context.area.type

        # Zen Unwrap Section
        layout.operator(
            "uv.zenuv_unwrap",
            icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO)).action = "DEFAULT"
        # Seams Section
        layout.operator("uv.zenuv_auto_mark")
        layout.operator(
            "uv.zenuv_mark_seams",
            icon_value=icon_get(ZuvLabels.OT_MARK_ICO))
        layout.operator(
            "uv.zenuv_unmark_seams",
            icon_value=icon_get(ZuvLabels.OT_UNMARK_ICO))
        layout.operator("uv.zenuv_unmark_all")
        layout.operator("uv.zenuv_seams_by_uv_islands")
        layout.operator("uv.zenuv_seams_by_sharp")
        layout.operator("uv.zenuv_sharp_by_seams")

        layout.operator("view3d.zenuv_set_smooth_by_sharp")

        # Finished Section
        layout.separator()
        layout.operator("uv.zenuv_islands_sorting", text=ZuvLabels.SORTING_LABEL)
        layout.operator("uv.zenuv_tag_finished")
        layout.operator("uv.zenuv_untag_finished")
        layout.operator("uv.zenuv_select_finished")
        layout.operator("uv.zenuv_display_finished")

        # Quadrify Section
        layout.separator()
        layout.operator("uv.zenuv_quadrify", icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))

        # Select Section
        layout.separator()

        layout.operator("uv.zenuv_select_island")
        layout.operator("uv.zenuv_isolate_island")

        layout.operator("uv.zenuv_select_uv_overlap")
        layout.operator("uv.zenuv_select_flipped")

        layout.operator("mesh.zenuv_select_seams")
        layout.operator("mesh.zenuv_select_sharp")
        layout.operator("uv.zenuv_select_loop")

        # Pack Section
        layout.separator()
        layout.operator("uv.zenuv_pack").display_uv = True

        # Checker Section
        layout.separator()

        layout.operator("view3d.zenuv_checker_toggle",
                        icon_value=icon_get(ZuvLabels.ZEN_CHECKER_ICO))
        layout.operator("view3d.zenuv_checker_remove")

        # Prefs Section
        layout.separator()
        if area_type == 'VIEW_3D':
            layout.prop(context.space_data.overlay, "show_edge_seams", text='Show Seams')
            layout.prop(context.space_data.overlay, "show_edge_sharp", text='Show Sharp Edges')
            layout.prop(context.space_data.overlay, "show_edge_bevel_weight", text='Show Bevel Weights')
            layout.prop(context.space_data.overlay, "show_edge_crease", text='Show Crease Edges')


if __name__ == "__main__":
    pass
