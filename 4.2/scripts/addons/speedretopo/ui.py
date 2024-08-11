# -*- coding:utf-8 -*-

# SpeedRetopo Add-on
# Copyright (C) 2016 Cedric Lepiller aka Pitiwazou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# <pep8 compliant>

import bpy
from bpy.types import Menu, Header
from .icon.icons import load_icons
from bpy.types import Object
import bmesh

def get_addon_preferences():
    addon_key = __package__.split(".")[0]
    return bpy.context.preferences.addons[addon_key].preferences

# UI
class SPEEDRETOPO_PT_ui(bpy.types.Panel):
    bl_label = "SpeedRetopo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"

    def draw_header(self, context):
        layout = self.layout
        icons = load_icons()
        icon = icons.get("icon_speedretopo")
        layout.label(text="", icon_value=icon.icon_id)

    def draw(self, context):
        layout = self.layout
        if context.object is not None and len(context.selected_objects) == 1:
            SpeedRetopo(self, context)
        elif len(context.selected_objects) == 0:
            layout.label(text="Select An Object", icon='ERROR')
        else:
            layout.label(text="Selection Only One Object", icon='ERROR')

# Panel
def SpeedRetopo(self, context):
    layout = self.layout
    tool_settings = context.tool_settings
    overlay = context.space_data.overlay
    shading = context.space_data.shading
    addonPref = get_addon_preferences()
    use_color_shader = addonPref.use_color_shader
    buttons_size = addonPref.buttons_size
    icons = load_icons()
    reference_nbf = addonPref.reference_nbf

    self.has_mirror = False
    for mod in context.object.modifiers:
        if mod.type == 'MIRROR':
            self.has_mirror = True

    self.huge_faces = False
    if not context.active_object.speedretopo_ref_object :
        if context.object.mode == "OBJECT":
            for obj in context.selected_objects:
                if len(obj.data.polygons)> reference_nbf:
                    self.huge_faces = True

    if self.huge_faces :
        box = layout.box()
        split = box.split()
        col = split.column(align=True)
        col.label(text="Decrease the number of")
        col.label(text="vertices of")
        col.label(text="the Reference Object")

        decimate = False
        for mod in context.active_object.modifiers:
            if mod.type == "DECIMATE":
                decimate = True

        if not decimate:
            row=box.row()
            row.scale_y = 1.3
            icon = icons.get("icon_decimate")
            row.operator("object.speedretopo_decimate", text="Decimate", icon_value=icon.icon_id)

            if addonPref.show_help_buttons:
                row.operator("speedretopo.help_decimate", icon='HELP')
        else:
            row = col.row(align=True)
            row.scale_y = 1.3
            icon = icons.get("icon_valid")
            row.operator("object.speedretopo_apply_decimate", text="Apply Decimate", icon_value=icon.icon_id)
            row.prop(context.active_object.modifiers["Decimate"], "show_viewport", text="",icon='RESTRICT_VIEW_ON')
            row.operator("object.speedretopo_remove_decimate", text="", icon='X')
            row = col.row(align=True)
            row.prop(context.active_object.modifiers["Decimate"], "ratio", text="Ratio")
            row = col.row(align=True)
            row.label(text="Face Count:" + str(context.active_object.modifiers["Decimate"].face_count))

    # REF object
    box = layout.box()
    row = box.row(align=True)
    row.label(text="SET REFERENCE")
    row = box.row()
    obj = context.active_object
    row.scale_y = 1.3
    row.prop(obj, "speedretopo_ref_object", text="", icon='MESH_MONKEY')

    if addonPref.show_help_buttons:
        row.operator("speedretopo.help_reference_object", icon='HELP')

    if context.object.mode == "OBJECT":
        if context.object.mode in {'OBJECT', 'SCULPT'}:
            box = layout.box()
            split = box.split()
            col = split.column(align=True)
            row = col.row()
            row.scale_y = 1
            row.prop(addonPref, "show_start_menu", text="START RETOPO",
                     icon='DISCLOSURE_TRI_DOWN' if addonPref.show_start_menu else 'SNAP_GRID')
            if addonPref.show_help_buttons:
                row.operator("speedretopo.help_start_retopo", icon='HELP')

            if addonPref.show_start_menu:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = 1.3
                row.operator("object.speedretopo_create_retopo", text="START RETOPO", icon='GREASEPENCIL')

                # SETTINGS
                box = layout.box()
                split = box.split()
                col = split.column(align=True)

                row = col.row(align=True)
                row.label(text="START RETOPO WITH", icon='TOOL_SETTINGS')
                row = col.row(align=True)
                row.scale_y = 1.5
                row.prop(addonPref, "start_from", text="")

                box = layout.box()
                split = box.split()
                col = split.column(align=True)
                row = col.row(align=True)
                row.label(text="RETOPO SETTINGS", icon='PRESET')
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.prop(addonPref, "auto_add_mirror", text="Add Mirror Modifier")

                if not addonPref.start_from == 'POLYBUILD':
                    row = col.row(align=True)
                    row.scale_y = 1.2
                    row.prop(addonPref, "auto_add_shrinkwrap", text="Add Shrinkwrap Modifier")

                row = col.row(align=True)
                row.scale_y = buttons_size
                row.prop(addonPref, "smooth_shading", text="Use Smooth Shading")

                if bpy.app.version < (3, 6, 0):
                    row = col.row(align=True)
                    row.scale_y = buttons_size
                    row.prop(addonPref, "hidden_wire", text="Use Hidden Wire")
                else:
                    row = col.row(align=True)
                    row.scale_y = buttons_size
                    row.prop(addonPref, "retopology_shading", text="Retopology Shading")

                row = col.row(align=True)
                row.scale_y = buttons_size
                row.prop(addonPref, "use_in_front", text="Use In front")

                row = col.row(align=True)
                row.scale_y = buttons_size
                row.prop(addonPref, "use_wireframe", text="Show Wireframe")

                if not addonPref.retopology_shading:
                    row = col.row(align=True)
                    row.prop(addonPref, "use_color_shader", text="Use Color Shader")
                    if use_color_shader:
                        row.scale_y = buttons_size
                        row.prop(addonPref, "obj_color", text="")

    # MODIFIERS
    if context.object.mode in {'OBJECT','EDIT', 'SCULPT'}:
        mirror = context.active_object.modifiers.get("Mirror")
        box = layout.box()
        split = box.split()
        col = split.column(align=True)
        row = col.row()
        row.scale_y = 1
        row.prop(addonPref, "show_modifiers_menu", text="MODIFIERS",
                 icon='DISCLOSURE_TRI_DOWN' if addonPref.show_modifiers_menu else 'MODIFIER')

        if addonPref.show_help_buttons:
            row.operator("speedretopo.help_modifiers", icon='HELP')

        if addonPref.show_modifiers_menu:
            if mirror:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.scale_x = 1.2
                if context.object.modifiers["Mirror"].show_viewport == False:
                    row.prop(context.active_object.modifiers["Mirror"], "show_viewport", text="Mirror")
                elif context.object.modifiers["Mirror"].show_viewport == True:
                    row.prop(context.active_object.modifiers["Mirror"], "show_viewport", text="Mirror")
                icon = icons.get("icon_clipping")
                row.prop(context.active_object.modifiers["Mirror"], "use_clip", text="", icon_value=icon.icon_id)
                icon = icons.get("icon_valid")
                row.operator("object.speedretopo_apply_mirror", text="", icon_value=icon.icon_id)
                icon = icons.get("icon_delete")
                row.operator("object.speedretopo_remove_mirror", text="", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.prop(context.active_object.modifiers["Mirror"], "merge_threshold", text="Merge Limit")
            else:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.operator("object.speedretopo_add_mirror", text="Add Mirror", icon='MOD_MIRROR')

            #shrinkwrap
            shrinkwrap = context.active_object.modifiers.get("Shrinkwrap")
            if shrinkwrap :
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.scale_x = 1.2
                if context.object.modifiers["Shrinkwrap"].show_viewport == False:
                    row.prop(context.active_object.modifiers["Shrinkwrap"], "show_viewport", text="Shrinkwrap")
                elif context.object.modifiers["Shrinkwrap"].show_viewport == True:
                    row.prop(context.active_object.modifiers["Shrinkwrap"], "show_viewport", text="Shrinkwrap")
                icon = icons.get("icon_valid")
                row.operator("object.speedretopo_apply_shrinkwrap", text="", icon_value=icon.icon_id)
                icon = icons.get("icon_delete")
                row.operator("object.speedretopo_remove_shrinkwrap", text="", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.prop(context.active_object.modifiers["Shrinkwrap"], "offset", text = "Shrinkwrap Offset")
                row = col.row(align=True)
                icon = icons.get("icon_update")
                row.operator("object.speedretopo_update_shrinkwrap", text="Update Shrinkwrap", icon_value=icon.icon_id)
            else:
                if context.object.speedretopo_ref_object is not None:
                    row = col.row(align=True)
                    row.separator()
                    row = col.row(align=True)
                    row.scale_y = buttons_size
                    row.operator("object.speedretopo_add_shrinkwrap", text="Add shrinkwrap", icon = 'MOD_SHRINKWRAP')
                    for mod in context.object.modifiers:
                        if mod.type =='SHRINKWRAP':
                            row = col.row(align=True)
                            icon = icons.get("icon_valid")
                            row.operator("object.speedretopo_add_apply_shrinkwrap", text="Update Shrinkwrap", icon_value=icon.icon_id)

            # Subsurf
            subsurf = context.active_object.modifiers.get("Subsurf")

            if subsurf:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.scale_x = 1.2
                if context.object.modifiers["Subsurf"].show_viewport == False:
                    row.prop(context.active_object.modifiers["Subsurf"], "show_viewport", text="Subsurf")
                elif context.object.modifiers["Subsurf"].show_viewport == True:
                    row.prop(context.active_object.modifiers["Subsurf"], "show_viewport", text="Subsurf")
                icon = icons.get("icon_optimal_display")
                row.prop(context.active_object.modifiers["Subsurf"], "show_only_control_edges", text="",
                         icon_value=icon.icon_id)
                row.prop(context.active_object.modifiers["Subsurf"], "show_in_editmode", text="", icon='EDITMODE_HLT')
                icon = icons.get("icon_valid")
                row.operator("object.speedretopo_apply_subsurf", text="", icon_value=icon.icon_id)
                icon = icons.get("icon_delete")
                row.operator("object.speedretopo_remove_subsurf", text="", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.prop(context.active_object.modifiers["Subsurf"], "levels", text="Levels")

            else:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.operator("object.speedretopo_add_subsurf", text="Add Subsurf", icon='MOD_SUBSURF')

    # TOOLS
    box = layout.box()
    split = box.split()
    col = split.column(align=True)
    row = col.row()
    row.scale_y = 1
    row.prop(addonPref, "show_tools_menu", text="TOOLS",
             icon='DISCLOSURE_TRI_DOWN' if addonPref.show_tools_menu else 'TOOL_SETTINGS')

    if addonPref.show_help_buttons:
        row.operator("speedretopo.help_tools", icon='HELP')

    if addonPref.show_tools_menu:
        if context.object.mode in {'OBJECT', 'SCULPT'}:
            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_recalculate_normals_outside")
            row.operator("object.speedretopo_recalculate_normals_outside", text="Recalculate Normals Outside", icon_value=icon.icon_id)
            row = col.row(align=True)
            icon = icons.get("icon_recalculate_normals_inside")
            row.operator("object.speedretopo_recalculate_normals_inside", text="Recalculate Normals Inside", icon_value=icon.icon_id)

            if not self.has_mirror:
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size + 0.3
                row.operator("object.speedretopo_symmetrize", text="Symmetrize", icon='MOD_MIRROR')

        elif context.object.mode == "EDIT":
            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size  + 0.3
            if context.scene.bsurfaces.SURFSK_mesh == bpy.data.objects[context.object.name]:
                icon = icons.get("icon_bsurface")
                row.operator("mesh.surfsk_add_surface", text="Add BSurface", icon_value=icon.icon_id)
            else:
                icon = icons.get("icon_error")
                row.operator("object.speedretopo_set_bsurface", text="Click To Set Bsurface Mesh", icon_value=icon.icon_id)

            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size + 0.3
            icon = icons.get("icon_align_to_x")
            row.operator("object.speedretopo_align_center_edges", text="Align Vertices to Center", icon_value=icon.icon_id)

            if hasattr(bpy.types, "MESH_OT_retopomt"):
                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = buttons_size
                icon = icons.get("icon_retopomt")
                row.operator("mesh.retopomt", icon_value=icon.icon_id)

            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_space")
            row.operator("object.speedretopo_space_relax", text="Space", icon_value=icon.icon_id)
            row.scale_y = buttons_size
            icon = icons.get("icon_relax")
            row.operator("mesh.speedretopo_relax", text="Relax", icon_value=icon.icon_id)
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_gstretch")
            row.operator("object.speedretopo_gstretch", text="GStretch", icon_value=icon.icon_id)
            row.scale_y = buttons_size
            icon = icons.get("icon_curve")
            row.operator("mesh.looptools_curve", text="Curve", icon_value=icon.icon_id)
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_bridge")
            row.operator("mesh.looptools_bridge", text="Bridge", icon_value=icon.icon_id)
            row.scale_y = buttons_size
            icon = icons.get("icon_gridfill")
            row.operator("mesh.fill_grid", text="Grid Fill", icon_value=icon.icon_id)
            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.operator("object.speedretopo_remove_double", text="Remove Double", icon='STICKY_UVS_VERT')
            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_recalculate_normals_outside")
            row.operator("object.speedretopo_recalculate_normals_outside", text="Recalculate Normals Outside", icon_value=icon.icon_id)
            row = col.row(align=True)
            icon = icons.get("icon_recalculate_normals_inside")
            row.operator("object.speedretopo_recalculate_normals_inside", text="Recalculate Normals Inside", icon_value=icon.icon_id)
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_flip_normals")
            row.operator("mesh.flip_normals", text="Flip Normals", icon_value=icon.icon_id)
            row = col.row(align=True)
            row.separator()
            row = col.row(align=True)
            row.scale_y = buttons_size + 0.3
            row.operator("object.speedretopo_symmetrize", text="Symmetrize", icon='MOD_MIRROR')
            row = col.row(align=True)
            row.separator()

            # AUTO MERGE
            row = col.row(align=True)
            row.scale_y = buttons_size
            row.prop(context.tool_settings, "use_mesh_automerge", text="Auto Merge")
            if context.scene.tool_settings.use_mesh_automerge == True:
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.prop(tool_settings, "double_threshold", text="Threshold")
                row = col.row(align=True)
                row.scale_y = buttons_size
                row.operator("object.speedretopo_double_threshold_minus", text="0.001")
                row.operator("object.speedretopo_double_threshold_plus", text="0.1")

            # CENTER TOOLS
            box = layout.box()
            split = box.split()
            col = split.column(align=True)
            col.prop(addonPref, "show_center_tools", text="CENTER TOOLS",
                     icon='DISCLOSURE_TRI_DOWN' if addonPref.show_center_tools else 'THREE_DOTS')
            if addonPref.show_center_tools:
                row = col.row(align=True)

                me = context.object.data
                bm = bmesh.from_edit_mesh(me)
                if [v for v in bm.verts if v.select] :
                    row.operator("object.speedretopo_set_unset_center", text='Set', icon='LAYER_ACTIVE').set_unset_center = "set"
                    row.operator("object.speedretopo_set_unset_center", text='UnSet', icon='IPO_LINEAR').set_unset_center = "unset"
                row = col.row(align=True)
                row.operator("object.speedretopo_set_unset_center", text='Select', icon='GROUP_VERTEX').set_unset_center = "select"
                row.operator("object.speedretopo_set_unset_center", text='Clear', icon='SELECT_SET').set_unset_center = "clear"

            # FREEZING
            if context.active_object.speedretopo_ref_object:
                box = layout.box()
                split = box.split()
                col = split.column(align=True)
                col.prop(addonPref, "show_freeze_unfreeze", text="FREEZING TOOLS",
                         icon='DISCLOSURE_TRI_DOWN' if addonPref.show_freeze_unfreeze else 'FREEZE')
                if addonPref.show_freeze_unfreeze:

                    row = col.row(align=True)

                    me = context.object.data
                    bm = bmesh.from_edit_mesh(me)
                    if [v for v in bm.verts if v.select] :
                        row.operator("object.speedretopo_freeze_unfreeze", text='Freeze', icon='FREEZE').freeze_unfreeze = "freeze"
                        row.operator("object.speedretopo_freeze_unfreeze", text='UnFreeze', icon='IPO_LINEAR').freeze_unfreeze = "unfreeze"
                    row = col.row(align=True)
                    row.operator("object.speedretopo_freeze_unfreeze", text='Select', icon='GROUP_VERTEX').freeze_unfreeze = "select"
                    row.operator("object.speedretopo_freeze_unfreeze", text='Clear', icon='SELECT_SET').freeze_unfreeze = "clear"

    # SHADING
    box = layout.box()
    split = box.split()
    col = split.column(align=True)
    row = col.row()
    row.scale_y = 1
    row.prop(addonPref, "show_shading_menu", text="SHADING",
             icon='DISCLOSURE_TRI_DOWN' if addonPref.show_shading_menu else 'SHADING_TEXTURE')

    if addonPref.show_help_buttons:
        row.operator("speedretopo.help_shading", icon='HELP')

    if addonPref.show_shading_menu:

        row = col.row(align=True)
        row.separator()
        row = col.row(align=True)
        if bpy.app.version < (4, 1, 0):
            if context.object.data.use_auto_smooth == False:
                row.operator("object.speedretopo_smooth_flat", text="Smooth Shading", icon='SHADING_RENDERED')
            elif context.object.data.use_auto_smooth == True:
                row.operator("object.speedretopo_smooth_flat", text="Flat Shading", icon='SHADING_WIRE')
        else:
            row.operator("object.speedretopo_set_smooth", text="Smooth Shading", icon='SHADING_RENDERED')
            row = col.row(align=True)
            row.operator("object.speedretopo_set_flat", text="Flat Shading", icon='SHADING_WIRE')

        if context.object.mode == "EDIT":
            row = col.row(align=True)
            row.scale_y = buttons_size

            if bpy.app.version < (3, 6, 0):
                icon = 'RADIOBUT_ON' if overlay.show_occlude_wire else 'RADIOBUT_OFF'
                row.prop(overlay, "show_occlude_wire", text="Hidden Wire", icon=icon)
            else:
                icon = 'RADIOBUT_ON' if overlay.show_retopology else 'RADIOBUT_OFF'
                row.prop(overlay, "show_retopology", text="Retopology", icon=icon)
                if overlay.show_retopology:
                    row = col.row(align=True)
                    row.prop(overlay, "retopology_offset")

        row = col.row(align=True)
        row.scale_y = buttons_size
        if context.object.show_in_front == False:
            row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_OFF')
        elif context.object.show_in_front == True:
            row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_ON')

        row = col.row(align=True)
        row.scale_y = buttons_size
        if context.object.show_wire == False:
            row.prop(context.object, "show_wire", text="Object Wireframe", icon='RADIOBUT_OFF')
        elif context.object.show_wire == True:
            row.prop(context.object, "show_wire", text="Object Wireframe", icon='RADIOBUT_ON')

        row = col.row(align=True)
        row.scale_y = buttons_size
        if shading.show_backface_culling == False:
            row.prop(shading, "show_backface_culling", text="Back Face Culling", icon='RADIOBUT_OFF')
        elif shading.show_backface_culling == True:
            row.prop(shading, "show_backface_culling", text="Back Face Culling", icon='RADIOBUT_ON')

        if not context.space_data.overlay.show_retopology:
            row = col.row(align=True)
            row.scale_y = buttons_size
            if context.active_object.color[3] != 1:
                row.scale_y = buttons_size
                row.prop(context.object, "color", text="")
                icon = icons.get("icon_delete")
                row.operator("object.speedretopo_remove_color", text="", icon_value=icon.icon_id)
            else:
                if context.active_object.speedretopo_ref_object:
                    icon = icons.get("icon_color")
                    row.operator("object.speedretopo_add_color", text="Add Color", icon_value=icon.icon_id)

        if context.object.mode == 'SCULPT':
            box = layout.box()
            split = box.split()
            col = split.column(align=True)
            row = col.row(align=True)
            row.scale_y = buttons_size
            icon = icons.get("icon_recalculate_normals_outside")
            row.operator("object.speedretopo_recalculate_normals_outside", text="Recalculate Normals Outside", icon_value=icon.icon_id)
            row = col.row(align=True)
            icon = icons.get("icon_recalculate_normals_inside")
            row.operator("object.speedretopo_recalculate_normals_inside", text="Recalculate Normals Inside", icon_value=icon.icon_id)

class SPEEDRETOPO_PT_start_retopo_settings(bpy.types.Operator):
    bl_idname = "view3d.start_retopo_settings"
    bl_label = "Start Retopo Settings"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.object.mode == "OBJECT"

    def invoke(self, context, event):
        self.dpi_value = context.preferences.system.dpi
        context.window_manager.windows[0].cursor_warp(x=int(event.mouse_x - (self.dpi_value*2/2)), y=int(event.mouse_y +200))
        popup = context.window_manager.invoke_popup(self, width=int(self.dpi_value*2))
        context.window_manager.windows[0].cursor_warp(x=event.mouse_x, y=event.mouse_y)
        return popup

    def draw(self, context):
        layout = self.layout
        addonPref = get_addon_preferences()
        use_color_shader = addonPref.use_color_shader
        obj = context.active_object

        if context.object is not None and context.object.mode == "OBJECT":

            box = layout.box()
            row = box.row(align=True)
            row.label(text="SET REFERENCE")
            row = box.row(align=True)
            # row = layout.row(align=True)
            row.scale_y = 1.3
            row.prop(obj, "speedretopo_ref_object", text="", icon='MESH_MONKEY')
            box = layout.box()
            row = box.row(align=True)
            row.scale_y = 1.3
            row.operator("object.speedretopo_create_retopo", text="START RETOPO", icon='GREASEPENCIL')
            box = layout.box()
            row = box.row(align=True)
            row.label(text="START RETOPO WITH", icon='TOOL_SETTINGS')
            row = box.row(align=True)
            row.scale_y = 1.5
            row.prop(addonPref, "start_from", text="")

            row = box.row(align=True)
            row.label(text="RETOPO SETTINGS", icon='MOD_HUE_SATURATION')
            row = box.row(align=True)
            row.scale_y = 1.2
            row.prop(addonPref, "auto_add_mirror", text="Add Mirror Modifier")

            if not addonPref.start_from == 'POLYBUILD':
                row = box.row(align=True)
                row.scale_y = 1.2
                row.prop(addonPref, "auto_add_shrinkwrap", text="Add Shrinkwrap Modifier")

            if bpy.app.version < (3, 6, 0):
                row = box.row(align=True)
                row.scale_y = 1.2
                row.prop(addonPref, "hidden_wire", text="Use Hidden Wire")
            else:
                row = box.row(align=True)
                row.scale_y = 1.2
                row.prop(addonPref, "retopology_shading", text="Use Retopology Shading")

            row = box.row(align=True)
            row.scale_y = 1.2
            row.prop(addonPref, "use_in_front", text="Use In front")

            row = box.row(align=True)
            row.scale_y = 1.2
            row.prop(addonPref, "use_wireframe", text="Show Wireframe")

            if not addonPref.retopology_shading:
                row = box.row(align=True)
                row.prop(addonPref, "use_color_shader", text="Use Color Shader")
                if use_color_shader:
                    row.scale_y = 1.2
                    row.prop(addonPref, "obj_color", text="")

class SPEEDRETOPO_PT_popup_menu(bpy.types.Operator):
    bl_idname = "view3d.speedretopo_popup_menu"
    bl_label = "Edit Menu"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        return len([obj for obj in context.selected_objects if context.object is not None if obj.type == 'MESH']) == 1

    def invoke(self, context, event):
        self.dpi_value = context.preferences.system.dpi
        context.window_manager.windows[0].cursor_warp(x=int(event.mouse_x - (self.dpi_value*1.5/2)), y=int(event.mouse_y))
        popup = context.window_manager.invoke_popup(self, width=int(self.dpi_value*1.5))
        context.window_manager.windows[0].cursor_warp(x=event.mouse_x, y=event.mouse_y)
        return popup

    def draw(self, context):
        layout = self.layout

        SpeedRetopo(self, context)

class SPEEDRETOPO_OT_start_or_edit(bpy.types.Operator):
    bl_idname = 'object.speedretopo_ot_start_or_edit'
    bl_label = "Speedretopo"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return len([obj for obj in context.selected_objects if context.object is not None if obj.type == 'MESH']) == 1


    def execute(self, context):
        addonPref = get_addon_preferences()
        use_menu_or_pie_menu = addonPref.use_menu_or_pie_menu

        if context.object.mode == 'EDIT':
            if use_menu_or_pie_menu == 'menu':
                bpy.ops.view3d.speedretopo_popup_menu('INVOKE_DEFAULT')
            else:
                bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name="SPEEDRETOPO_MT_pie_menu")

        elif context.object.mode != 'EDIT':
            if context.active_object.speedretopo_ref_object:
                bpy.ops.object.mode_set(mode='EDIT')
                if use_menu_or_pie_menu == 'menu':
                    bpy.ops.view3d.speedretopo_popup_menu('INVOKE_DEFAULT')
                else:
                    bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name="SPEEDRETOPO_MT_pie_menu")
            else:
                bpy.ops.view3d.start_retopo_settings('INVOKE_DEFAULT')

        elif context.object.mode == 'SCULPT':
            if context.active_object.speedretopo_ref_object:
                if use_menu_or_pie_menu == 'menu':
                    bpy.ops.view3d.speedretopo_popup_menu('INVOKE_DEFAULT')
                else:
                    bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name="SPEEDRETOPO_MT_pie_menu")
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.view3d.start_retopo_settings('INVOKE_DEFAULT')
        return {'FINISHED'}

def speedretopo_pie_menus_modifiers(self, context):
    pie = self.layout.menu_pie()
    icons = load_icons()

    # ------Mirror
    col = pie.column(align=True)
    mirror = context.active_object.modifiers.get("Mirror")
    if mirror:
        row = col.row(align=True)
        row.label(text="", icon='MOD_MIRROR')
        row.scale_x = 1.3
        row.scale_y = 1.2
        if context.object.modifiers["Mirror"].show_viewport == False:
            row.prop(context.active_object.modifiers["Mirror"], "show_viewport", text="")
        elif context.object.modifiers["Mirror"].show_viewport == True:
            row.prop(context.active_object.modifiers["Mirror"], "show_viewport", text="")
        icon = icons.get("icon_clipping")
        row.prop(context.active_object.modifiers["Mirror"], "use_clip", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_valid")
        row.operator("object.speedretopo_apply_mirror", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_delete")
        row.operator("object.speedretopo_remove_mirror", text="", icon_value=icon.icon_id)

    # ------shrinkwrap
    shrinkwrap = context.active_object.modifiers.get("Shrinkwrap")
    if shrinkwrap:
        row = col.row(align=True)
        row.label(text="", icon='MOD_SHRINKWRAP')
        row.scale_x = 1.3
        row.scale_y = 1.2
        if context.object.modifiers["Shrinkwrap"].show_viewport == False:
            row.prop(context.active_object.modifiers["Shrinkwrap"], "show_viewport", text="")
        elif context.object.modifiers["Shrinkwrap"].show_viewport == True:
            row.prop(context.active_object.modifiers["Shrinkwrap"], "show_viewport", text="")
        icon = icons.get("icon_update")
        row.operator("object.speedretopo_update_shrinkwrap", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_valid")
        row.operator("object.speedretopo_apply_shrinkwrap", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_delete")
        row.operator("object.speedretopo_remove_shrinkwrap", text="", icon_value=icon.icon_id)

    # Subsurf
    subsurf = context.active_object.modifiers.get("Subsurf")
    if subsurf:
        row = col.row(align=True)
        row.label(text="", icon='MOD_SUBSURF')
        row.scale_x = 1.3
        row.scale_y = 1.2
        if context.object.modifiers["Subsurf"].show_viewport == False:
            row.prop(context.active_object.modifiers["Subsurf"], "show_viewport", text="")
        elif context.object.modifiers["Subsurf"].show_viewport == True:
            row.prop(context.active_object.modifiers["Subsurf"], "show_viewport", text="")
        icon = icons.get("icon_optimal_display")
        row.prop(context.active_object.modifiers["Subsurf"], "show_only_control_edges", text="",
                 icon_value=icon.icon_id)
        icon = icons.get("icon_valid")
        row.operator("object.speedretopo_apply_subsurf", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_delete")
        row.operator("object.speedretopo_remove_subsurf", text="", icon_value=icon.icon_id)

    if not mirror:
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("object.speedretopo_add_mirror", text="Add Mirror", icon='MOD_MIRROR')

    if not shrinkwrap:
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("object.speedretopo_add_shrinkwrap", text="Add shrinkwrap", icon='MOD_SHRINKWRAP')
        icon = icons.get("icon_valid")
        row.operator("object.speedretopo_add_apply_shrinkwrap", text="", icon_value=icon.icon_id)

    if not subsurf:
        row = col.row(align=True)
        row.scale_y = 1.2
        row.operator("object.speedretopo_add_subsurf", text="Add Subsurf", icon='MOD_SUBSURF')

class SPEEDRETOPO_MT_pie_menu(Menu):
    bl_label = "SPEEDRETOPO"

    @classmethod
    def poll(cls, context):
        return len(context.object is not None and context.selected_objects) == 1

    def draw(self, context):
        pie = self.layout.menu_pie()
        icons = load_icons()

        if len(context.object is not None and context.selected_objects) == 1:
            # OBJECT_MODE
            if context.object.mode in {"OBJECT","SCULPT"}:

                #4 - LEFT
                speedretopo_pie_menus_modifiers(self, context)

                #6 - RIGHT
                pie.separator()

                #2 - BOTTOM
                split = pie.split()
                col = split.column(align=True)
                row = col.row(align=True)
                row.scale_y = 1.2
                icon = icons.get("icon_recalculate_normals_outside")
                row = col.row(align=True)
                row.operator("object.speedretopo_recalculate_normals_outside", text="Recalculate Normals Outside", icon_value=icon.icon_id)
                row = col.row(align=True)
                icon = icons.get("icon_recalculate_normals_inside")
                row.operator("object.speedretopo_recalculate_normals_inside", text="Recalculate Normals Inside", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.scale_y = 1.2
                shading = context.space_data.shading

                row = col.row(align=True)
                row.scale_y = 1.2
                if context.object.show_in_front == False:
                    row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_OFF')
                elif context.object.show_in_front == True:
                    row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_ON')

                row = col.row(align=True)
                row.scale_y = 1.3
                if context.object.show_wire == False:
                    row.prop(context.object, "show_wire", text="Wireframe", icon='RADIOBUT_OFF')
                elif context.object.show_wire == True:
                    row.prop(context.object, "show_wire", text="Wireframe", icon='RADIOBUT_ON')

                row = col.row(align=True)
                row.scale_y = 1.2
                if shading.show_backface_culling == False:
                    row.prop(shading, "show_backface_culling", text="Back Face Culling", icon='RADIOBUT_OFF')
                elif shading.show_backface_culling == True:
                    row.prop(shading, "show_backface_culling", text="Back Face Culling", icon='RADIOBUT_ON')

                #8 - TOP
                col = pie.column(align=True)
                # row = col.row(align=True)
                # row.label(text="SET REFERENCE")
                # obj = context.active_object
                # row = col.row(align=True)
                # row.scale_y = 1.2
                # row.prop(obj, "speedretopo_ref_object", text="", icon='MESH_MONKEY')

                row = col.row(align=True)
                row.scale_y = 1.2
                icon = icons.get("icon_continue")
                row.operator("object.speedretopo_continue_retopo", text="CONTINUE RETOPO", icon_value=icon.icon_id)

                #7 - TOP - LEFT
                col = pie.column(align=True)
                row = col.row(align=True)
                row.scale_y = 1.2
                # icon = icons.get("icon_valid")
                # row.operator("object.speedretopo_finalize_retopo", text="FINALIZE", icon_value=icon.icon_id)
                # row.operator("object.speedretopo_exit_retopo", text="EXIT RETOPO", icon='PAUSE')

                row = col.row(align=True)
                row.prop(context.active_object, "speedretopo_ref_object")

                #9 - TOP - RIGHT
                pie.separator()

                #1 - BOTTOM - LEFT
                pie.separator()

                #3 - BOTTOM - RIGHT
                pie.separator()


            # EDIT_MODE
            if context.object.mode == "EDIT":
                speedretopo_pie_menus_modifiers(self, context)

                #6 - RIGHT
                icon = icons.get("icon_align_to_x")
                pie.operator("object.speedretopo_align_center_edges", text="Align Vertices to Center", icon_value=icon.icon_id)

                #2 - BOTTOM
                split = pie.split()
                col = split.column(align=True)
                col.separator()
                if hasattr(bpy.types, "MESH_OT_retopomt"):
                    row = col.row(align=True)
                    row.scale_y = 1.2
                    icon = icons.get("icon_retopomt")
                    row.operator("mesh.retopomt", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.scale_y = 1.2
                icon = icons.get("icon_recalculate_normals_outside")
                row.operator("object.speedretopo_recalculate_normals_outside", text="Recalculate Normals Outside", icon_value=icon.icon_id)
                row = col.row(align=True)
                icon = icons.get("icon_recalculate_normals_inside")
                row.operator("object.speedretopo_recalculate_normals_inside", text="Recalculate Normals Inside", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.scale_y = 1.2
                icon = icons.get("icon_flip_normals")
                row.operator("mesh.flip_normals", text="Flip Normals", icon_value=icon.icon_id)

                row = col.row(align=True)
                row.separator()
                row = col.row(align=True)
                row.scale_y = 1.2
                if bpy.app.version < (4, 1, 0):
                    if context.object.data.use_auto_smooth == False:
                        row.operator("object.speedretopo_smooth_flat", text="Smooth Shading", icon='SHADING_RENDERED')
                    elif context.object.data.use_auto_smooth == True:
                        row.operator("object.speedretopo_smooth_flat", text="Flat Shading", icon='SHADING_WIRE')
                else:
                    row.operator("object.speedretopo_set_smooth", text="Smooth Shading", icon='SHADING_RENDERED')
                    row = col.row(align=True)
                    row.operator("object.speedretopo_set_flat", text="Flat Shading", icon='SHADING_WIRE')
                    # row.operator("object.shade_smooth", text="Smooth Shading", icon='SHADING_RENDERED')
                    # row = col.row(align=True)
                    # row.operator("object.shade_flat", text="Flat Shading", icon='SHADING_WIRE')


                row = col.row(align=True)
                row.scale_y = 1.2
                overlay = context.space_data.overlay
                shading = context.space_data.shading
                if bpy.app.version < (3, 6, 0):
                    icon = 'RADIOBUT_ON' if overlay.show_occlude_wire else 'RADIOBUT_OFF'
                    row.prop(overlay, "show_occlude_wire", text="Hidden Wire", icon=icon)
                else:
                    icon = 'RADIOBUT_ON' if overlay.show_retopology else 'RADIOBUT_OFF'
                    row.prop(overlay, "show_retopology", text="Retopology", icon=icon)
                    if overlay.show_retopology:
                        row = col.row(align=True)
                        row.prop(overlay, "retopology_offset")

                row = col.row(align=True)
                row.scale_y = 1.2
                if context.object.show_in_front == False:
                    row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_OFF')
                elif context.object.show_in_front == True:
                    row.prop(context.object, "show_in_front", text="In Front", icon='RADIOBUT_ON')

                row = col.row(align=True)
                row.scale_y = 1.2
                if context.object.show_wire == False:
                    row.prop(context.object, "show_wire", text="Wireframe", icon='RADIOBUT_OFF')
                elif context.object.show_wire == True:
                    row.prop(context.object, "show_wire", text="Wireframe", icon='RADIOBUT_ON')

                row = col.row(align=True)
                row.scale_y = 1.2
                if shading.show_backface_culling == False :
                    row.prop(shading, "show_backface_culling", text = "Back Face Culling", icon='RADIOBUT_OFF')
                elif shading.show_backface_culling == True :
                    row.prop(shading, "show_backface_culling", text = "Back Face Culling", icon='RADIOBUT_ON')

                # Center
                row = col.row(align=True)
                row.label(text='Center Tools', icon='THREE_DOTS')
                row = col.row(align=True)
                me = context.object.data
                bm = bmesh.from_edit_mesh(me)
                if [v for v in bm.verts if v.select] :
                    row.operator("object.speedretopo_set_unset_center", text='Set', icon='LAYER_ACTIVE').set_unset_center = "set"
                    row.operator("object.speedretopo_set_unset_center", text='UnSet', icon='IPO_LINEAR').set_unset_center = "unset"
                row = col.row(align=True)
                row.operator("object.speedretopo_set_unset_center", text='Select', icon='GROUP_VERTEX').set_unset_center = "select"
                row.operator("object.speedretopo_set_unset_center", text='Clear', icon='SELECT_SET').set_unset_center = "clear"

                # freeze
                row = col.row(align=True)
                row.label(text='Freezing Tools', icon='FREEZE')
                row = col.row(align=True)
                me = context.object.data
                bm = bmesh.from_edit_mesh(me)
                if [v for v in bm.verts if v.select] :
                    row.operator("object.speedretopo_freeze_unfreeze", text='Freeze', icon='FREEZE').freeze_unfreeze = "freeze"
                    row.operator("object.speedretopo_freeze_unfreeze", text='UnFreeze', icon='IPO_LINEAR').freeze_unfreeze = "unfreeze"
                row = col.row(align=True)
                row.operator("object.speedretopo_freeze_unfreeze", text='Select', icon='GROUP_VERTEX').freeze_unfreeze = "select"
                row.operator("object.speedretopo_freeze_unfreeze", text='Clear', icon='SELECT_SET').freeze_unfreeze = "clear"

                #8 - TOP
                col = pie.column(align=True)
                row = col.row(align=True)

                if context.scene.bsurfaces.SURFSK_mesh == bpy.data.objects[context.object.name]:
                    icon = icons.get("icon_bsurface")
                    row.scale_y = 1.3
                    row.operator("mesh.surfsk_add_surface", text="Add BSurface", icon_value=icon.icon_id)
                else:
                    icon = icons.get("icon_error")
                    row.scale_y = 1.3
                    row.operator("object.speedretopo_set_bsurface", text="Click to Set Bsurface Mesh", icon_value=icon.icon_id)
                # icon = icons.get("icon_bsurface")
                # row.operator("object.speedretopo_add_bsurface", text="Add BSurface", icon_value=icon.icon_id)
                # row.operator("mesh.surfsk_add_surface", text="Add BSurface", icon_value=icon.icon_id)

                #7 - TOP - LEFT
                col = pie.column(align=True)
                row=col.row(align=True)
                row.scale_y = 1.2
                # icon = icons.get("icon_valid")
                # row.operator("object.speedretopo_finalize_retopo", text="FINALIZE", icon_value=icon.icon_id)
                # row.operator("object.speedretopo_exit_retopo", text="EXIT RETOPO", icon='PAUSE')

                row = col.row(align=True)
                row.prop(context.active_object, "speedretopo_ref_object")

                #------Threshold
                row=col.row(align=True)
                row.scale_y = 1.2
                row.scale_x = 1
                row.prop(context.tool_settings, "use_mesh_automerge", text="Auto Merge")
                row.operator("object.speedretopo_double_threshold_plus", text="0.1")
                row.operator("object.speedretopo_double_threshold_minus", text="0.001")

                #9 - TOP - RIGHT
                icon = icons.get("icon_space")
                pie.operator("object.speedretopo_space_relax", text="Space", icon_value=icon.icon_id)

                #1 - BOTTOM - LEFT
                split = pie.split()
                col = split.column(align=True)
                row = col.row(align=True)
                icon = icons.get("icon_gstretch")
                row.operator("object.speedretopo_gstretch", text="GStretch", icon_value=icon.icon_id)
                icon = icons.get("icon_bridge")
                row.operator("mesh.looptools_bridge", text="Bridge", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.scale_x = 1.3
                icon = icons.get("icon_curve")
                row.operator("mesh.looptools_curve", text="Curve", icon_value=icon.icon_id)
                icon = icons.get("icon_gridfill")
                row.operator("mesh.fill_grid", text="Grid Fill", icon_value=icon.icon_id)
                row = col.row(align=True)
                row.operator("object.speedretopo_remove_double", text="Remove Double", icon='STICKY_UVS_VERT')

                #3 - BOTTOM - RIGHT
                icon = icons.get("icon_relax")
                pie.operator("mesh.speedretopo_relax", text="Relax", icon_value=icon.icon_id)

        elif len(context.selected_objects) == 0:
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.select_all", text="Select An Object", icon='ERROR').action = 'DESELECT'
            pie.separator()
            pie.separator()
            pie.separator()
            pie.separator()

        else:
            pie.separator()
            pie.separator()
            pie.separator()
            pie.operator("object.select_all", text="Select Only One Object", icon='ERROR').action = 'DESELECT'
            pie.separator()
            pie.separator()
            pie.separator()
            pie.separator()

# -----------------------------------------------------------------------------
#    Help
# -----------------------------------------------------------------------------
class SPEEDRETOPO_MT_help_reference_object(bpy.types.Operator):
    bl_idname = "speedretopo.help_reference_object"
    bl_label = ""
    bl_description = "Help Reference Object, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):
        icons = load_icons()
        layout = self.layout

        layout.label(text="The reference object is connected to your retopo object.")
        layout.label(text="It is used as reference for the modifiers, Mirror and Shrinkwrap.")
        layout.label(text="You can remove it and change it.")

        layout.separator()
        layout.label(text="Note: The addon needs it to use modifiers.", icon='WORDWRAP_ON')

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_reference_object.mp4"

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.view.ui_scale
        coef = dpi_value * (-175) + 525
        return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

class SPEEDRETOPO_MT_help_start_retopo(bpy.types.Operator):
    bl_idname = "speedretopo.help_start_retopo"
    bl_label = ""
    bl_description = "Help Starting Retopology, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):

        icons = load_icons()

        layout = self.layout


        layout.label(text="To start your Retopology, you need to select the reference object first.")

        layout.separator()
        layout.label(text="Note: This object will be connected to your Retopo Object.", icon='WORDWRAP_ON')

        layout.separator()
        icon = icons.get("icon_decimate")
        layout.label(text="DECIMATE", icon_value=icon.icon_id)
        layout.label(text="If you object has too many vertices, it can decrease performances.")
        layout.label(text="Then, you can Decimate it with the Decimate Modifier.")
        layout.label(text="Click on the button en set the ratio to something lighter.")
        layout.label(text="Once the number of vertices is ok,")
        layout.label(text="click on Apply and start your retopology.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=2111"

        layout.separator()
        layout.label(text="You will now see a menu to Start the Retopology.")
        layout.operator("wm.url_open", text="IMAGE",
                     icon='IMAGE_DATA').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_001.jpg"
        layout.label(text="You will be able to choose the tool you want to use.")
        layout.operator("wm.url_open", text="IMAGE",
                     icon='IMAGE_DATA').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_002.jpg"

        layout.separator()
        icon = icons.get("icon_bsurface")
        layout.label(text="BSURFACE", icon_value=icon.icon_id)
        layout.label(text="Bsurface is a well known Addon that allows you")
        layout.label(text="to draw lines and create faces on your Retopology.")
        layout.label(text="By pressing D key and draw, you will create lines.")
        layout.label(text="Once your lines are created,")
        layout.label(text="you can press Add Bsurface button in the Menu.")
        layout.label(text="That will create the first faces of your retopology.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=899"

        layout.separator()
        layout.label(text="Tools so Start")
        layout.operator("wm.url_open", text="VIDEO",
                        icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=374"
        layout.separator()
        icon = icons.get("icon_vertex")
        layout.label(text="VERTEX", icon_value=icon.icon_id)
        layout.label(text="That Vertex tool is a simple vertex, as simple as that!")
        layout.label(text="You can place it where you want on your reference mesh.")
        layout.label(text="After that you just have to extrude it")
        layout.label(text="and use normal poly editing tools.")

        layout.separator()
        icon = icons.get("icon_face")
        layout.label(text="FACE", icon_value=icon.icon_id)
        layout.label(text="That Face tool is a simple face that you will be able to place on the surface of your mesh")

        layout.separator()
        icon = icons.get("icon_polybuild")
        layout.label(text="POLYBUILD", icon_value=icon.icon_id)
        layout.label(text="Polybuild is an inside tool from Blender")
        layout.label(text="to help you create and edit your retopology.")
        layout.label(text="It's a several in one tool using shortcuts")
        layout.label(text="to extrude faces and move vertices")

        layout.separator()
        layout.label(text="SpeedRetopo automatize things for you,")
        layout.label(text="it will automatically create modifiers like Mirror and Shrinkwrap.")
        layout.label(text="You just have to start and edit your retopology.")
        layout.separator()
        layout.label(text="So, when you have created your first faces with the tool of you choice,")
        layout.label(text="you will have the edit menu.")
        layout.label(text="With it, you will be able to edit modifiers and your mesh.")


    def invoke(self, context, event):
            dpi_value = bpy.context.preferences.view.ui_scale
            coef = dpi_value * (-175) + 525
            return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

class SPEEDRETOPO_MT_help_modifiers(bpy.types.Operator):
    bl_idname = "speedretopo.help_modifiers"
    bl_label = ""
    bl_description = "Help Modifiers, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):
        icons = load_icons()
        layout = self.layout

        layout.label(text="You will be able to edit the modifiers.")
        layout.label(text="Apply them, remove them and add them again if necessary.")
        layout.label(text="You will be able to align the center Vertices to .")

        layout.separator()
        layout.label(text="MIRROR", icon='MOD_MIRROR')
        layout.label(text="The Mirror Modifiers create a mirror of your object on the X axis.")
        layout.label(text="You can Apply it, remove it, use the clipping setting")
        layout.label(text="to keep the middle vertices at the center of the scene.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_mirror_modifier.mp4"

        layout.separator()
        layout.label(text="SHRINKWRAP", icon='MOD_SHRINKWRAP')
        layout.label(text="The Shrinkwrap Modifiers projects your retopology on the surface")
        layout.label(text="of the reference object.")
        layout.label(text="You can Apply it, remove it and update it.")

        layout.separator()
        layout.label(text="Note: This Modifiers needs to be updated regularly to be efficient.", icon='WORDWRAP_ON')
        layout.label(text="Note: The modifier auto align to center the vertices", icon='WORDWRAP_ON')
        layout.label(text="you have setted as center.")

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_shrinkwrap_modifier.mp4"

        layout.separator()
        layout.label(text="SUBSURF", icon='MOD_SUBSURF')
        layout.label(text="The Subsurf Modifiers subdivide your surface")
        layout.label(text="it's useful to see if the retopology is correct.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=2271"

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.view.ui_scale
        coef = dpi_value * (-175) + 525
        return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

class SPEEDRETOPO_MT_help_tools(bpy.types.Operator):
    bl_idname = "speedretopo.help_tools"
    bl_label = ""
    bl_description = "Help Tools, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):
        icons = load_icons()
        layout = self.layout

        layout.label(text="In Edit Mode you have differents tools.")

        layout.separator()
        icon = icons.get("icon_bsurface")
        layout.label(text="BSURFACE", icon_value=icon.icon_id)
        layout.label(text="Listed previously, allow you to draw lines to create faces.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_bsurface_in_action.mp4"

        layout.separator()
        icon = icons.get("icon_align_to_x")
        layout.label(text="ALING TO X", icon_value=icon.icon_id)
        layout.label(text="Align the center vertices to the center of the scene.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_align_to_x.mp4"

        layout.separator()
        icon = icons.get("icon_retopomt")
        layout.label(text="RETOPO MT", icon_value=icon.icon_id)
        layout.label(text="Special tool for retopology.")

        layout.separator()
        layout.label(text="Note: You need to activate it in the preferences.", icon='WORDWRAP_ON')

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_retopo_mt.mp4"

        layout.separator()
        icon = icons.get("icon_space")
        layout.label(text="SPACE", icon_value=icon.icon_id)
        layout.label(text="This tool keep the vertices on a loop at the same space.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_space_tool.mp4"

        layout.separator()
        icon = icons.get("icon_relax")
        layout.label(text="RELAX", icon_value=icon.icon_id)
        layout.label(text="Relax the selection to make it better.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_relax_tool.mp4"

        layout.separator()
        icon = icons.get("icon_gstretch")
        layout.label(text="GSTRETCH", icon_value=icon.icon_id)
        layout.label(text="This tool aligns vertices with grease pencil lines.")

        layout.separator()
        layout.label(text="Note: Seems not to work on latest builds of blender.", icon='WORDWRAP_ON')

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_gstretch_tool.mp4"

        layout.separator()
        icon = icons.get("icon_curve")
        layout.label(text="CURVE", icon_value=icon.icon_id)
        layout.label(text="This tool creates a curve on 3 points selection on a loop.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_curve_tool.mp4"

        layout.separator()
        icon = icons.get("icon_bridge")
        layout.label(text="BRIDGE", icon_value=icon.icon_id)
        layout.label(text="This tool creates faces between too selected loops.")

        layout.separator()
        layout.label(text="Note: Better to have the same amount of vertices.", icon='WORDWRAP_ON')

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_bridge_tool.mp4"

        layout.separator()
        icon = icons.get("icon_gridfill")
        layout.label(text="GRIDFILL", icon_value=icon.icon_id)
        layout.label(text="This tool creates faces in holes.")
        layout.label(text="you need to select 2 loops with the same number of vertices.")

        layout.separator()
        layout.label(text="Note: Check the looptools documentation to learn more about it.", icon='WORDWRAP_ON')

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_bridge_tool.mp4"

        layout.separator()
        icon = icons.get("icon_recalculate_normals")
        layout.label(text="RECALCULATE NORMALS", icon_value=icon.icon_id)
        layout.label(text="This tool flips the normals of the mesh Outside or Inside.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_recalculate_normals.mp4"

        layout.separator()
        icon = icons.get("icon_flip_normals")
        layout.label(text="FLIP NORMALS", icon_value=icon.icon_id)
        layout.label(text="This tool flips the normals of the selected faces.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_flip_normals.mp4"

        layout.separator()
        layout.label(text="CENTER TOOLS", icon='THREE_DOTS')
        layout.label(text="Center tools allows you too set some vertices as center.")
        layout.label(text="That's mean, those vertices will always be at the center of the grid when you will")
        layout.label(text="update the Shrinkwrap modifier.")
        layout.separator()
        layout.label(text="You can set or Unset the selection.")
        layout.label(text="Also Select and clear the entire set to remove all vertices from the set.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_center_tools.mp4"

        layout.separator()
        layout.label(text="FREEZING TOOLS", icon='FREEZE')
        layout.label(text="Freezing tools allows you too freeze some vertices.")
        layout.label(text="That's mean, those vertices will be used for the Shrinkwrap modifier.")
        layout.separator()
        layout.label(text="You can Freeze or Unfreeze the selection.")
        layout.label(text="Also Select and clear the entire set to remove all vertices from the set.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_freezing_tools.mp4"

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.view.ui_scale
        coef = dpi_value * (-175) + 525
        return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

class SPEEDRETOPO_MT_help_shading(bpy.types.Operator):
    bl_idname = "speedretopo.help_shading"
    bl_label = ""
    bl_description = "Help Shading, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):
        icons = load_icons()
        layout = self.layout

        layout.label(text="The shading part help you to better see your retopology")
        layout.label(text="on the reference object.")
        layout.operator("wm.url_open", text="VIDEO",
                     icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=1950"

        layout.separator()
        if bpy.app.version < (3, 6, 0):
            layout.label(text="HIDDEN WIRE")
            layout.label(text="Will hide faces to only see the wireframe of your object.")
        else:
            layout.label(text="RETOPOLOGY SHADING")
            layout.label(text="Will make faces transparent to let you see your reference object.")

        layout.separator()
        layout.label(text="IN FRONT")
        layout.label(text="You will always see the retopo object on top of the reference object.")

        layout.separator()
        layout.label(text="WIREFRAME")
        layout.label(text="Will show the wireframe of your object.")

        layout.separator()
        layout.label(text="BACK FACE CULLING")
        layout.label(text="You will see through the back of the faces of your object.")

        layout.separator()
        layout.label(text="COLOR")
        layout.label(text="It will add a color shader with transparency to your object.")
        layout.label(text="You can change the color and remove it.")


    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.view.ui_scale
        coef = dpi_value * (-175) + 525
        return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

class SPEEDRETOPO_MT_help_decimate(bpy.types.Operator):
    bl_idname = "speedretopo.help_decimate"
    bl_label = ""
    bl_description = "Help Decimate, click on the button"

    def execute(self, context):
        return {'FINISHED'}

    def check(self, context):
        return True

    def draw(self, context):
        icons = load_icons()
        layout = self.layout

        icon = icons.get("icon_decimate")
        layout.label(text="DECIMATE", icon_value=icon.icon_id)
        layout.label(text="If you object has too many vertices, it can decrease performances.")
        layout.label(text="Then, you can Decimate it with the Decimate Modifier.")
        layout.label(text="Click on the button en set the ratio to something lighter.")
        layout.label(text="Once the number of vertices is ok, ")
        layout.label(text="click on Apply and start your retopology.")

        layout.separator()
        layout.label(text="Note: You can change the value that will check the mesh", icon='WORDWRAP_ON')
        layout.label(text="in the addon preferences.")

        layout.separator()
        layout.operator("wm.url_open", text="VIDEO",
                        icon='FILE_MOVIE').url = "https://youtu.be/cKhZNOFc4Us?t=2111"

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.view.ui_scale
        coef = dpi_value * (-175) + 525
        return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))

# class SPEEDRETOPO_MT_help_quadriflow(bpy.types.Operator):
#     bl_idname = "speedretopo.help_quadriflow"
#     bl_label = ""
#     bl_description = "Help Quadriflow, click on the button"
#
#     def execute(self, context):
#         return {'FINISHED'}
#
#     def check(self, context):
#         return True
#
#     def draw(self, context):
#         icons = load_icons()
#         layout = self.layout
#
#         layout.label(text="Quadriflow is a build-in tool for auto-retopology.")
#         layout.label(text="Set the settings you want to use and the number of desired faces")
#         layout.label(text="and click on the Quadriflow Remesh button.")
#         layout.label(text="it will edit the mesh wire to the desired number of faces.")
#
#         layout.separator()
#         layout.label(text="Note: It works better with closed meshes", icon='WORDWRAP_ON')
#
#         layout.separator()
#         layout.operator("wm.url_open", text="VIDEO",
#                         icon='FILE_MOVIE').url = "http://blscripts.com/speedretopo/screenshots/speedretopo_reference_object.mp4"
#
#     def invoke(self, context, event):
#         dpi_value = bpy.context.preferences.view.ui_scale
#         coef = dpi_value * (-175) + 525
#         return context.window_manager.invoke_popup(self, width=int(dpi_value * coef))
# -----------------------------------------------------
# REGISTER/UNREGISTER
# -----------------------------------------------------
CLASSES =  [SPEEDRETOPO_PT_ui,
            SPEEDRETOPO_MT_pie_menu,
            SPEEDRETOPO_OT_start_or_edit,
            SPEEDRETOPO_PT_start_retopo_settings,
            SPEEDRETOPO_PT_popup_menu,
            SPEEDRETOPO_MT_help_start_retopo,
            SPEEDRETOPO_MT_help_reference_object,
            SPEEDRETOPO_MT_help_modifiers,
            SPEEDRETOPO_MT_help_tools,
            SPEEDRETOPO_MT_help_shading,
            SPEEDRETOPO_MT_help_decimate]

def register():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except:
            print(f"{cls.__name__} already registred")


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass