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

""" Zen UV Panel In UV Layout """
import bpy
from ZenUV.utils.generic import ZUV_PANEL_CATEGORY, ZUV_REGION_TYPE
from ZenUV.ui.labels import ZuvLabels
from ZenUV.prop.zuv_preferences import get_prefs, draw_panels_enabler
from ZenUV.ui.panel_draws import (
    draw_select,
    draw_texel_density,
    draw_pack,
    draw_copy_paste,
    # draw_simple_stack,
    draw_stack,
    draw_transform_panel,
    uv_draw_unwrap,
    draw_finished_section,
    draw_packer_props,
    draw_fit_region_section
)


class ZUV_PT_UVL_Preferences(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Preferences"
    bl_label = ZuvLabels.PANEL_PREFERENCES_LABEL
    # bl_context = ZUV_CONTEXT
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_preferences

    def draw(self, context):
        # layout = self.layout
        # layout.label(text="TEST")
        pass


class DATA_PT_UVL_Panels_Switch(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Panels"
    bl_parent_id = "ZUV_PT_UVL_Preferences"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "DATA_PT_UVL_Panels_Switch"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        draw_panels_enabler(self, context, layout, "uv")


class ZUV_PT_UVL_Transform(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Transform"
    bl_label = ZuvLabels.PANEL_TRANSFORM_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_transform and context.mode == 'EDIT_MESH'

    def draw(self, context):
        draw_transform_panel(self, context)


class ZUV_PT_UVL_Texel_Density(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Texel_Density"
    bl_label = ZuvLabels.PANEL_TEXEL_DENSITY_LABEL
    # bl_context = "mesh_edit"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_texel_density and context.mode == 'EDIT_MESH'

    def draw(self, context):
        draw_texel_density(self, context)


class ZUV_PT_UVL_Pack(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Pack"
    bl_label = ZuvLabels.PANEL_PACK_LABEL
    # bl_context = "mesh_edit"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_pack and context.mode == 'EDIT_MESH'

    def draw(self, context):
        draw_pack(self, context)


class ZUV_PT_UVL_Stack(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Stack"
    bl_label = ZuvLabels.PANEL_STACK_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    # def draw_header(self, context):
    #     self.layout.label(text="Stack")
    #     draw_progress_bar(self, context)

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_stack and context.mode == 'EDIT_MESH'

    def draw(self, context):
        draw_stack(self, context)
        draw_copy_paste(self, context)
        # draw_simple_stack(self, context)


class ZUV_PT_UVL_Unwrap(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Unwrap"
    bl_label = ZuvLabels.PANEL_UNWRAP_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_unwrap and context.mode == 'EDIT_MESH'

    def draw(self, context):
        uv_draw_unwrap(self, context)


class ZUV_PT_UVL_Select(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Select"
    bl_label = ZuvLabels.PANEL_SELECT_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.uv_enable_pt_select and context.mode == 'EDIT_MESH'

    def draw(self, context):
        draw_select(self, context)


class SYSTEM_PT_Finished_UV(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Finished"
    bl_parent_id = "ZUV_PT_UVL_Unwrap"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_Finished_UV"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    # def draw_header(self, context):
    #     layout = self.layout
    #     row = layout.row(align=True)
    #     row.split()
    #     row.label(text="Finished")
    #     row.operator("uv.zenuv_tag_finished", icon='KEYFRAME_HLT', text="")
    #     row.operator("uv.zenuv_untag_finished", icon='KEYFRAME', text="")
    #     row.operator("uv.zenuv_islands_sorting", text="", icon='SORTSIZE')
    #     row.operator("uv.zenuv_select_finished", icon='RESTRICT_SELECT_OFF', text="")
    #     row.prop(context.scene.zen_display, "finished", toggle=True, icon='HIDE_OFF', text="")

    def draw(self, context):
        draw_finished_section(self, context)


class SYSTEM_PT_FitRegion_UV(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Fit Region"
    bl_parent_id = "ZUV_PT_UVL_Transform"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_FitRegion_UV"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        return context.scene.zen_uv.tr_mode == "FIT"

    def draw(self, context):
        draw_fit_region_section(self, context)


class PROPS_PT_UVL_Packer(bpy.types.Panel):
    bl_idname = "PROPS_PT_UVL_Packer"
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Pack Engine"
    bl_parent_id = "ZUV_PT_UVL_Pack"
    bl_region_type = ZUV_REGION_TYPE
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_packer_props(self, context)
