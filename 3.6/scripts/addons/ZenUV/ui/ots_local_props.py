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

""" Zen UV Operatopr local properties (Popups)"""
import bpy
from ZenUV.ui.labels import ZuvLabels
from ZenUV.prop.zuv_preferences import get_prefs


class STACK_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV STACK Section Properties"""
    bl_idname = "STACK_PT_Properties"
    bl_label = "Stack Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        layout.prop(addon_prefs, "stackMoveOnly")
        layout.separator()
        layout.label(text="Stack Offset:")
        layout.prop(addon_prefs, "stack_offset", text="")
        layout.label(text="Unstack Direction:")
        layout.prop(addon_prefs, "unstack_direction", text="")


class STACK_PT_DrawProperties(bpy.types.Panel):
    """ Internal Popover Zen UV STACK Section Properties"""
    bl_idname = "STACK_PT_DrawProperties"
    bl_label = "Stack Draw Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        pointer = context.scene.zen_display.stack_display_mode
        # print(pointer.stack_display_mode)
        if pointer == 'SIMILAR':
            layout.prop(addon_prefs, "UnstackableColor")
        if pointer == 'SELECTED':
            pass
        if pointer == 'STACKED':
            layout.prop(addon_prefs, "StackedColor")
            layout.prop(context.scene.zen_display, "st_uv_area_only")


class TD_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Texel Density Properties"""
    bl_idname = "TD_PT_Properties"
    bl_label = "Texel Density Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        # col = layout.column(align=True)
        row = layout.row(align=True)
        row.label(text=ZuvLabels.PREF_UNITS_LABEL + ": ")
        row.prop(addon_prefs, "td_unit", text="")
        # col = layout.column(align=True)
        row = layout.row(align=True)
        row.label(text=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL + ": ")
        # row.prop(addon_prefs, 'TD_TextureSizeX', text="")
        row.prop(addon_prefs, 'td_im_size_presets', text="")
        if addon_prefs.td_im_size_presets == 'Custom':
            col = layout.column(align=True)
            col.prop(addon_prefs, 'TD_TextureSizeX', text="Custom Res X")
            # row = layout.row(align=True)
            col.prop(addon_prefs, 'TD_TextureSizeY', text="Custom Res Y")
            # row.label(text="  px")


class TD_PT_Checker_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Texel Density Properties"""
    bl_idname = "TD_PT_Checker_Properties"
    bl_label = "Texel Checker Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        row = layout.row(align=True)
        row.label(text=ZuvLabels.PREF_TD_CHECKER_LABEL + ":   ")
        row.prop(addon_prefs, "td_checker", text="")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text=ZuvLabels.TD_COLOR_LESS_LABEL)
        row.label(text=ZuvLabels.TD_COLOR_EQUAL_LABEL)
        row.label(text=ZuvLabels.TD_COLOR_OVER_LABEL)
        row = col.row(align=True)
        row.prop(addon_prefs, "td_color_less", text='')
        row.prop(addon_prefs, "td_color_equal", text='')
        row.prop(addon_prefs, "td_color_over", text='')


class TR_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Texel Density Properties"""
    bl_idname = "TR_PT_Properties"
    bl_label = "Transform Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        prop = context.scene.zen_uv
        layout.prop(prop, "tr_space_mode")


class MARK_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV  MARK Section Properties"""
    bl_idname = "MARK_PT_Properties"
    bl_label = "Mark Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        layout.prop(addon_prefs, "useGlobalMarkSettings")
        box = layout.box()
        if addon_prefs.useGlobalMarkSettings:
            box.prop(addon_prefs, 'markSeamEdges')
            box.prop(addon_prefs, 'markSharpEdges')
        else:
            box.label(text="Settings in Local mode.")


class FINISHED_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV FINISHED Section Properties"""
    bl_idname = "FINISHED_PT_Properties"
    bl_label = "Finished Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        row = layout.row(align=True)
        row.prop(addon_prefs, 'autoFinishedToPinned')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'sortAutoSorting')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'FinishedColor')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'UnFinishedColor')


class QUADRIFY_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV QUADRIFY Section Properties"""
    bl_idname = "QUADRIFY_PT_Properties"
    bl_label = "Quadrify Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout

        row = layout.row(align=True)
        row.prop(addon_prefs, 'autoPinQuadrified')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'packAfQuadrify')
        # row = layout.row(align=True)
        # row.prop(addon_prefs, 'quadrifyOrientToWorld')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'mark_borders')
        row = layout.row(align=True)
        row.prop(addon_prefs, 'QuadrifyBySelected')


class RELAX_PT_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Relax Section Properties"""
    bl_idname = "RELAX_PT_Properties"
    bl_label = "Relax Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = get_prefs()
        layout = self.layout
        layout.prop(addon_prefs, 'use_zensets')


# class PACK_PT_Properties(bpy.types.Panel):
#     """ Internal Popover Zen UV PACK Section Properties"""
#     bl_idname = "PACK_PT_Properties"
#     bl_label = "Pack Properties"
#     bl_context = "mesh_edit"
#     bl_space_type = 'PROPERTIES'
#     bl_region_type = 'WINDOW'

#     def draw(self, context):
#         addon_prefs = get_prefs()
#         layout = self.layout
#         if not addon_prefs.packEngine == "UVPACKER":
#             layout.prop(addon_prefs, 'margin_show_in_px')

#         # Select Engine
#         row = layout.row(align=True)
#         row.label(text=ZuvLabels.PREF_PACK_ENGINE_LABEL + ':')
#         row = layout.row(align=True)
#         row.prop(addon_prefs, "packEngine", text="")

#         # Sync settings to UVP
#         if addon_prefs.packEngine == 'UVP':
#             row.operator("uv.zenuv_sync_to_uvp", text="", icon="FILE_REFRESH")

#         # # Custom Engine Settings
#         # if addon_prefs.packEngine == "CUSTOM":
#         #     layout.prop(addon_prefs, "customEngine", text="")


if __name__ == '__main__':
    pass
