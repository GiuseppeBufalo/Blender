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
import bmesh
from mathutils import *
import math
from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatVectorProperty,
                       FloatProperty,
                       EnumProperty,
                       IntProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty)
from .ui import get_addon_preferences

# -----------------------------------------------------------------------------
#    SETUP RETOPO
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_create_speedretopo(bpy.types.Operator):
    bl_idname = "object.speedretopo_create_retopo"
    bl_label = "Create Speed Retopo"
    bl_description = "Start Retopology"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        addonPref = get_addon_preferences()
        self.hidden_wire = addonPref.hidden_wire
        self.obj_color = addonPref.obj_color
        self.use_color_shader = addonPref.use_color_shader
        start_from = addonPref.start_from
        auto_add_mirror = addonPref.auto_add_mirror
        auto_add_shrinkwrap = addonPref.auto_add_shrinkwrap
        use_in_front = addonPref.use_in_front
        use_wireframe = addonPref.use_wireframe
        tool_settings = context.scene.tool_settings
        new_ref_object = context.active_object

        #Activate Addons
        bpy.ops.preferences.addon_enable(module="mesh_bsurfaces")
        bpy.ops.preferences.addon_enable(module="mesh_looptools")
        bpy.ops.preferences.addon_enable(module="mesh_f2")
        bpy.ops.wm.save_userpref()

        # Prepare Grease Pencil
        tool_settings.annotation_stroke_placement_view3d = 'SURFACE'

        # Add snap
        tool_settings.use_snap = True
        tool_settings.snap_elements = {'FACE'}
        tool_settings.use_snap_translate = True

        # Create Empty mesh
        bpy.ops.mesh.primitive_plane_add(size=0.4, enter_editmode=False, location=(0, 0, 0))
        bpy.ops.object.location_clear(clear_delta=True)
        bpy.ops.object.rotation_clear(clear_delta=True)
        bpy.ops.object.scale_clear(clear_delta=True)

        context.active_object.name = new_ref_object.name + "_Retopo"
        context.object.data.name = new_ref_object.name + "_Retopo"

        self.retopo = context.active_object

        # Shade Auto smooth
        if bpy.app.version < (4, 1, 0):
            if addonPref.smooth_shading:
                bpy.ops.object.shade_smooth(use_auto_smooth=True)
                bpy.context.object.data.auto_smooth_angle = 1.0472
            else:
                bpy.ops.object.shade_flat()
        else:
            if addonPref.smooth_shading:
                bpy.ops.object.shade_smooth()
            else:
                bpy.ops.object.shade_flat()

        # SET CUSTOM PROP
        context.active_object.speedretopo_ref_object = new_ref_object
        context.scene.bsurfaces.SURFSK_mesh = self.retopo
        bpy.ops.object.mode_set(mode='EDIT')
        if addonPref.smooth_shading:
            context.scene.bsurfaces.SURFSK_shade_smooth = True
        else:
            context.scene.bsurfaces.SURFSK_shade_smooth = False

        # SHADING
        if use_wireframe:
            context.object.show_wire = True
            context.object.show_all_edges = True

        if use_in_front:
            context.object.show_in_front = True
            context.scene.bsurfaces.SURFSK_in_front = True

        if self.hidden_wire and not self.use_color_shader:
            if bpy.app.version < (3, 6, 0):
                context.space_data.overlay.show_occlude_wire = True
            else:
                context.space_data.overlay.show_retopology = True

        elif self.use_color_shader and not self.hidden_wire:
            context.space_data.shading.light = 'MATCAP'
            context.space_data.shading.color_type = 'OBJECT'
            context.object.color = self.obj_color
            if bpy.app.version < (3, 6, 0):
                context.space_data.overlay.show_occlude_wire = False
            else:
                context.space_data.overlay.show_retopology = False

        elif self.use_color_shader and self.hidden_wire:
            self.hidden_wire = False
            context.space_data.shading.light = 'MATCAP'
            context.space_data.shading.color_type = 'OBJECT'
            context.object.color = self.obj_color
            if bpy.app.version < (3, 6, 0):
                context.space_data.overlay.show_occlude_wire = False
            else:
                context.space_data.overlay.show_retopology = False

        elif not self.use_color_shader and not self.hidden_wire:
            if bpy.app.version < (3, 6, 0):
                context.space_data.overlay.show_occlude_wire = False
            else:
                context.space_data.overlay.show_retopology = False

        if start_from == 'FACE':
            tool_settings.snap_target = 'CENTER'
            tool_settings.use_mesh_automerge = False
        elif start_from in  {'BSURFACE', 'POLYBUILD'}:
            tool_settings.use_mesh_automerge = True
            bpy.ops.mesh.delete(type='FACE')
        elif start_from == 'VERTEX':
            tool_settings.use_mesh_automerge = True
            bpy.ops.mesh.merge(type='CENTER')

        if addonPref.change_selection_tool:
            if start_from in {'BSURFACE', 'VERTEX', 'FACE'}:
                bpy.ops.wm.tool_set_by_id(name="builtin.select", cycle=False, space_type='VIEW_3D')
            elif start_from == 'POLYBUILD':
                bpy.ops.wm.tool_set_by_id(name="mesh_tool.poly_build", cycle=False, space_type='VIEW_3D')

        bpy.ops.object.mode_set(mode='OBJECT')

        context.scene.bsurfaces.SURFSK_mesh = self.retopo
        context.scene.bsurfaces.SURFSK_guide = 'Annotation'

        # Add Mirror
        if auto_add_mirror:
            mod_mirror = self.retopo.modifiers.new("Mirror", 'MIRROR')
            mod_mirror.show_on_cage = True
            mod_mirror.mirror_object = new_ref_object

            mod_mirror.use_axis[0] = addonPref.use_axis_x
            mod_mirror.use_axis[1] = addonPref.use_axis_y
            mod_mirror.use_axis[2] = addonPref.use_axis_z

            mod_mirror.use_bisect_axis[0] = addonPref.use_bisect_axis_x
            mod_mirror.use_bisect_axis[1] = addonPref.use_bisect_axis_y
            mod_mirror.use_bisect_axis[2] = addonPref.use_bisect_axis_z

            mod_mirror.use_bisect_flip_axis[0] = addonPref.use_bisect_flip_axis_x
            mod_mirror.use_bisect_flip_axis[1] = addonPref.use_bisect_flip_axis_y
            mod_mirror.use_bisect_flip_axis[2] = addonPref.use_bisect_flip_axis_z

            mod_mirror.use_clip = addonPref.use_clip

            if start_from in {'VERTEX', 'BSURFACE','POLYBUILD'}:
                mod_mirror.use_mirror_merge = True
                mod_mirror.merge_threshold = 0.001
            else:
                mod_mirror.use_mirror_merge = False

        bpy.ops.object.modifier_move_to_index(modifier='Mirror', index=0)

        #create the vgroup
        has_vgroup = False
        for vgroup in self.retopo.vertex_groups:
            if vgroup.name == "Speedretopo_freeze_unfreeze":
                has_vgroup = True
                continue
        if not has_vgroup:
            self.retopo.vertex_groups.new(name="Speedretopo_freeze_unfreeze")

        # Add Shrinkwrap
        if not addonPref.start_from == 'POLYBUILD':
            if auto_add_shrinkwrap:
                mod_shrinkwrap = self.retopo.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
                mod_shrinkwrap.target = new_ref_object

                mod_shrinkwrap.wrap_method = addonPref.wrap_method
                mod_shrinkwrap.wrap_mode = addonPref.snap_mode

                mod_shrinkwrap.offset = addonPref.shrinkwrap_offset

                if addonPref.wrap_method == 'PROJECT':
                    mod_shrinkwrap.project_limit = addonPref.project_limit
                    mod_shrinkwrap.subsurf_levels = addonPref.shrinkwrap_subsurf_levels
                    # AXIS
                    mod_shrinkwrap.use_project_x = addonPref.shrinkwrap_axis_x
                    mod_shrinkwrap.use_project_y = addonPref.shrinkwrap_axis_y
                    mod_shrinkwrap.use_project_z = addonPref.shrinkwrap_axis_z

                    mod_shrinkwrap.use_negative_direction = addonPref.use_negative_direction
                    mod_shrinkwrap.use_positive_direction = addonPref.use_positive_direction

                    mod_shrinkwrap.cull_face = addonPref.cull_face
                    if addonPref.cull_face:
                        mod_shrinkwrap.use_invert_cull = addonPref.use_invert_cull

                mod_shrinkwrap.show_on_cage = True
                mod_shrinkwrap.vertex_group = "Speedretopo_freeze_unfreeze"
                mod_shrinkwrap.invert_vertex_group = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

        if start_from in {'VERTEX', 'FACE'}:
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.view3d.cursor3d('INVOKE_DEFAULT')
            if start_from == 'VERTEX':
                bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
            bpy.ops.transform.translate('INVOKE_DEFAULT')

            # CLEAR CURSOR
            context.scene.cursor.location[:] = context.scene.cursor.rotation_euler[:] = (0, 0, 0)

        return {"FINISHED"}

# -----------------------------------------------------------------------------
#    Align to X
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_align_center_edges(bpy.types.Operator):
    bl_idname = "object.speedretopo_align_center_edges"
    bl_label = "Align Center Edges"
    bl_description = "Align Vertices to the center of the grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        '''
        # suppression des edges internes
        boundary_edges = get_edges_boundary_loop(bm, 1)
        for e in bm.edges:
            if e.select and not e in boundary_edges:
        '''

        ob = context.object
        current_mode = ob.mode
        bpy.ops.object.mode_set(mode = 'EDIT')


        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        for v in bm.verts:
            if len([v for v in bm.verts if v.select]) >= 1:
                if v.select:
                    v.co[0] = 0

            else:
                v.select_set(abs(v.co[0]) < 0.01)

                bm.edges.ensure_lookup_table()
                e = bm.edges[0]
                for loop in e.link_loops: # select loop
                    if len(loop.vert.link_edges) == 4:
                        e.select = True

                        while len(loop.vert.link_edges) == 4:
                            loop = loop.link_loop_prev.link_loop_radial_prev.link_loop_prev
                            e_next = loop.edge
                            e_next.select = True

                if v.select:
                    v.co[0] = 0


        bm.select_mode |= {'VERT'}
        bmesh.update_edit_mesh(me)
        bm.select_flush_mode()

        bpy.ops.object.mode_set(mode = current_mode)

        return {'FINISHED'}

# -----------------------------------------------------------------------------
#    SUBSURF
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_add_subsurf(bpy.types.Operator):
    bl_idname = "object.speedretopo_add_subsurf"
    bl_label = "Add Subsurf Modifier"
    bl_description = "Add Subsurf Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addonPref = get_addon_preferences()
        act_obj = context.active_object

        mod_subsurf = act_obj.modifiers.new("Subsurf", 'SUBSURF')
        mod_subsurf.show_only_control_edges = True
        mod_subsurf.show_in_editmode = False
        mod_subsurf.show_expanded = False

        mod_subsurf.levels = addonPref.subsurf_levels
        mod_subsurf.show_only_control_edges = addonPref.show_only_control_edges

        shrinkwrap = context.active_object.modifiers.get("Shrinkwrap")
        if shrinkwrap:
            bpy.ops.object.modifier_move_up(modifier="Subsurf")
        return {'FINISHED'}

class SPEEDRETOPO_OT_remove_subsurf(bpy.types.Operator):
    bl_idname = "object.speedretopo_remove_subsurf"
    bl_label = "Remove Subsurf Modifier"
    bl_description = "Remove Subsurf Modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.modifier_remove(modifier="Subsurf")
        return {"FINISHED"}

class SPEEDRETOPO_OT_apply_subsurf(bpy.types.Operator):
    bl_idname = "object.speedretopo_apply_subsurf"
    bl_label = "Apply Subsurf Modifier"
    bl_description = "Apply Subsurf Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "OBJECT":
            if bpy.app.version >= (2, 90, 0):
                bpy.ops.object.modifier_apply(modifier="Subsurf")
            else:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subsurf")
        elif context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            if bpy.app.version >= (2, 90, 0):
                bpy.ops.object.modifier_apply(modifier="Subsurf")
            else:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Subsurf")
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

# -----------------------------------------------------------------------------
#    MIRROR
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_add_mirror(bpy.types.Operator):
    """ Automatically cut an object along an axis """
    bl_idname = "object.speedretopo_add_mirror"
    bl_label = "Add Mirror Modifier"
    bl_description = "Add Mirror Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        act_obj = context.active_object
        addonPref = get_addon_preferences()

        mod_mirror = act_obj.modifiers.new("Mirror", 'MIRROR')
        mod_mirror.show_expanded = False
        mod_mirror.show_on_cage = True
        mod_mirror.mirror_object = context.active_object.speedretopo_ref_object

        mod_mirror.use_axis[0] = addonPref.use_axis_x
        mod_mirror.use_axis[1] = addonPref.use_axis_y
        mod_mirror.use_axis[2] = addonPref.use_axis_z

        mod_mirror.use_bisect_axis[0] = addonPref.use_bisect_axis_x
        mod_mirror.use_bisect_axis[1] = addonPref.use_bisect_axis_y
        mod_mirror.use_bisect_axis[2] = addonPref.use_bisect_axis_z

        mod_mirror.use_bisect_flip_axis[0] = addonPref.use_bisect_flip_axis_x
        mod_mirror.use_bisect_flip_axis[1] = addonPref.use_bisect_flip_axis_y
        mod_mirror.use_bisect_flip_axis[2] = addonPref.use_bisect_flip_axis_z

        mod_mirror.use_clip = addonPref.use_clip
        mod_mirror.use_mirror_merge = addonPref.use_merge
        if addonPref.use_merge:
            mod_mirror.merge_threshold = addonPref.merge_threshold

        shrinkwrap = context.active_object.modifiers.get("Shrinkwrap")
        subsurf = context.active_object.modifiers.get("Subsurf")
        if shrinkwrap:
            bpy.ops.object.modifier_move_up(modifier=mod_mirror.name)
        if subsurf:
            bpy.ops.object.modifier_move_up(modifier=mod_mirror.name)
        return {'FINISHED'}

class SPEEDRETOPO_OT_apply_mirror(bpy.types.Operator):
    bl_idname = "object.speedretopo_apply_mirror"
    bl_label = "Apply Mirror Modifier"
    bl_description = "Apply Mirror Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "OBJECT":
            if bpy.app.version >= (2, 90, 0):
                bpy.ops.object.modifier_apply(modifier="Mirror")
            else:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")

        elif context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            if bpy.app.version >= (2, 90, 0):
                bpy.ops.object.modifier_apply(modifier="Mirror")
            else:
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class SPEEDRETOPO_OT_remove_mirror(bpy.types.Operator):
    bl_idname = "object.speedretopo_remove_mirror"
    bl_label = "Remove Mirror Modifier"
    bl_description = "Remove Mirror Modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.modifier_remove(modifier="Mirror")
        return {"FINISHED"}

# -----------------------------------------------------------------------------
#    SHRINKWRAP
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_remove_shrinkwrap(bpy.types.Operator):
    bl_idname = "object.speedretopo_remove_shrinkwrap"
    bl_label = "Remove Shrinkwrap Modifier"
    bl_description = "Remove Shrinkwrap Modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.modifier_remove(modifier="Shrinkwrap")
        return {"FINISHED"}

class SPEEDRETOPO_OT_add_and_apply_shrinkwrap(bpy.types.Operator):
    bl_idname = "object.speedretopo_add_apply_shrinkwrap"
    bl_label = "Add and Apply Shrinkwrap Modifier"
    bl_description = "Add and Apply Shrinkwrap Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.speedretopo_add_shrinkwrap()
        bpy.ops.object.speedretopo_apply_shrinkwrap()
        return {'FINISHED'}

class SPEEDRETOPO_OT_apply_shrinkwrap(bpy.types.Operator):
    bl_idname = "object.speedretopo_apply_shrinkwrap"
    bl_label = "Apply Shrinkwrap Modifier"
    bl_description = "Apply Shrinkwrap Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        for mod in context.object.modifiers:
            if mod.type == 'SHRINKWRAP':
                ref = mod.target
                context.active_object.speedretopo_ref_object = ref

        if context.object.mode in {"OBJECT", 'SCULPT'}:
            bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
        elif context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class SPEEDRETOPO_OT_add_shrinkwrap(bpy.types.Operator):
    bl_idname = "object.speedretopo_add_shrinkwrap"
    bl_label = "Add Shrinkwrap Modifier"
    bl_description = "Add Shrinkwrap Modifier"
    bl_options = {"REGISTER", 'UNDO'}

    def execute(self, context):
        addonPref = get_addon_preferences()
        act_obj = context.active_object

        self.mirror = False
        self.bisect_x = False
        self.bisect_y = False
        self.bisect_z = False
        for mod in act_obj.modifiers:
            if mod.type == 'MIRROR':
                self.mirror = True
                if mod.use_bisect_axis[0]:
                    self.bisect_x = True
                if mod.use_bisect_axis[1]:
                    self.bisect_y = True
                if mod.use_bisect_axis[2]:
                    self.bisect_z = True

        # Créer un groupe de sommets s'il n'existe pas
        if "Speedretopo_freeze_unfreeze" not in act_obj.vertex_groups:
            act_obj.vertex_groups.new(name="Speedretopo_freeze_unfreeze")

        if context.active_object.speedretopo_ref_object:
            # Ajouter le modificateur Shrinkwrap
            mod_shrinkwrap = act_obj.modifiers.new("Shrinkwrap", 'SHRINKWRAP')
            mod_shrinkwrap.show_expanded = False
            mod_shrinkwrap.target = context.active_object.speedretopo_ref_object
            mod_shrinkwrap.wrap_method = addonPref.wrap_method
            mod_shrinkwrap.wrap_mode = addonPref.snap_mode
            mod_shrinkwrap.offset = addonPref.shrinkwrap_offset

            if addonPref.wrap_method == 'PROJECT':
                mod_shrinkwrap.project_limit = addonPref.project_limit
                mod_shrinkwrap.subsurf_levels = addonPref.shrinkwrap_subsurf_levels
                # AXIS
                mod_shrinkwrap.use_project_x = addonPref.shrinkwrap_axis_x
                mod_shrinkwrap.use_project_y = addonPref.shrinkwrap_axis_y
                mod_shrinkwrap.use_project_z = addonPref.shrinkwrap_axis_z

                mod_shrinkwrap.use_negative_direction = addonPref.use_negative_direction
                mod_shrinkwrap.use_positive_direction = addonPref.use_positive_direction

                mod_shrinkwrap.cull_face = addonPref.cull_face
                if addonPref.cull_face:
                    mod_shrinkwrap.use_invert_cull = addonPref.use_invert_cull

            mod_shrinkwrap.show_on_cage = True
            mod_shrinkwrap.vertex_group = "Speedretopo_freeze_unfreeze"
            mod_shrinkwrap.invert_vertex_group = True

            if "Speedretopo_freeze_unfreeze" in act_obj.vertex_groups:
                mod_shrinkwrap.vertex_group = "Speedretopo_freeze_unfreeze"
                mod_shrinkwrap.invert_vertex_group = True

            if self.mirror:
                if not any((self.bisect_x, self.bisect_y, self.bisect_z)):
                    bpy.ops.object.modifier_move_to_index(modifier=mod_shrinkwrap.name, index=0)


            # Sélectionner et aligner les sommets du centre
            act_obj_mode = context.active_object.mode
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')

            if "Speedretopo_set_unset_center" in act_obj.vertex_groups:
                bpy.ops.object.vertex_group_set_active(group='Speedretopo_set_unset_center')
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.speedretopo_align_center_edges()

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode=act_obj_mode)
        else:
            self.report({'WARNING'}, "No active object, could not finish")

        return {'FINISHED'}

def copy_shrinkwrap_modifier_and_apply():
    exclude = ('name', 'type', 'bl_rna', 'rna_type')

    active_obj = bpy.context.active_object
    # Ensure the active object is the intended target
    if active_obj is None:
        print("No active object.")
        return

    # Update the scene to ensure all data is current
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)

    active_modifier = active_obj.modifiers.get("Shrinkwrap")
    if active_modifier and active_modifier.type == 'SHRINKWRAP':
        for prop in [prop.identifier for prop in active_modifier.bl_rna.properties if prop.identifier not in exclude]:
            print(f"{prop}: {getattr(active_modifier, prop)}")

        # Copy and apply the active object's Shrinkwrap modifier
        bpy.ops.object.modifier_add(type=active_modifier.type)
        new_modifier = active_obj.modifiers[-1]

        for prop in [prop.identifier for prop in active_modifier.bl_rna.properties if prop.identifier not in exclude]:
            try:
                setattr(new_modifier, prop, getattr(active_modifier, prop))
            except AttributeError:
                print(f"Skipping read-only attribute: {prop}")

        # Apply the modifier with its current settings
        bpy.ops.object.modifier_apply(modifier=new_modifier.name)


    else:
        print("No active Shrinkwrap modifier found.")

class SPEEDRETOPO_OT_update_shrinkwrap(bpy.types.Operator):
    bl_idname = "object.speedretopo_update_shrinkwrap"
    bl_label = "Update shrinkwrap Modifier"
    bl_description = "Update shrinkwrap Modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mode = context.object.mode

        if context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Example usage on the active object
        copy_shrinkwrap_modifier_and_apply()
        for mod in bpy.context.object.modifiers:
            if mod.type == "SHRINKWRAP":
                mod.name = "Shrinkwrap"
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)

        bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}

# -----------------------------------------------------------------------------
#    OTHERS
# -----------------------------------------------------------------------------
class SPEEDRETOPO_OT_recalculate_normals_outside(bpy.types.Operator):
    bl_idname = "object.speedretopo_recalculate_normals_outside"
    bl_label = "Recalculate Normals Outside"
    bl_description = "Recalculate Normals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        act_obj = context.active_object
        mode = act_obj.mode
        bpy.ops.object.mode_set(mode='EDIT')
        me = act_obj.data
        bm = bmesh.from_edit_mesh(me)

        vert_selected = ([v for v in bm.verts if v.select])

        # RECALCULATE NORMAL OUTSIDE
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.select_all(action='DESELECT')

        for v in vert_selected:
            v.select = True

        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.app.version < (4, 1, 0):
            bpy.ops.object.shade_smooth(use_auto_smooth=True)
            context.object.data.auto_smooth_angle = 1.0472
        else:
            bpy.ops.object.shade_smooth()

        bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}

class SPEEDRETOPO_OT_recalculate_normals_inside(bpy.types.Operator):
    bl_idname = "object.speedretopo_recalculate_normals_inside"
    bl_label = "Recalculate Normals Inside"
    bl_description = "Recalculate Normals"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        act_obj = context.active_object
        mode = act_obj.mode
        bpy.ops.object.mode_set(mode='EDIT')
        me = act_obj.data
        bm = bmesh.from_edit_mesh(me)

        vert_selected = ([v for v in bm.verts if v.select])

        # RECALCULATE NORMAL OUTSIDE
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=True)
        bpy.ops.mesh.select_all(action='DESELECT')

        for v in vert_selected:
            v.select = True

        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.app.version < (4, 1, 0):
            bpy.ops.object.shade_smooth(use_auto_smooth=True)
            bpy.context.object.data.auto_smooth_angle = 1.0472
        else:
            bpy.ops.object.shade_smooth()

        bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}

class SPEEDRETOPO_OT_srrelax(bpy.types.Operator):
    bl_idname = "mesh.speedretopo_relax"
    bl_label = "Relax"
    bl_description = "Smoothing mesh keeping volume"
    bl_options = {'REGISTER', 'UNDO'}

    Repeat: bpy.props.IntProperty(
        name="Repeat",
        description="Repeat how many times",
        default=5,
        min=1,
        max=100)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

    def invoke(self, context, event):

        # smooth #Repeat times
        for i in range(self.Repeat):
            self.do_laprelax()

        # bpy.ops.mesh.select_all(action='DESELECT')
        return {'FINISHED'}

    def do_laprelax(self):

        context = bpy.context
        region = context.region
        area = context.area
        selobj = bpy.context.active_object
        mesh = selobj.data
        bm = bmesh.from_edit_mesh(mesh)
        bmprev = bm.copy()
        vertices = [v for v in bmprev.verts if v.select]

        if not vertices:
            bpy.ops.mesh.select_all(action='SELECT')

        for v in bmprev.verts:

            if v.select:

                tot = Vector((0, 0, 0))
                cnt = 0
                for e in v.link_edges:
                    for f in e.link_faces:
                        if not (f.select):
                            cnt = 1
                    if len(e.link_faces) == 1:
                        cnt = 1
                        break
                if cnt:
                    # dont affect border edges: they cause shrinkage
                    continue

                # find Laplacian mean
                for e in v.link_edges:
                    tot += e.other_vert(v).co
                tot /= len(v.link_edges)

                # cancel movement in direction of vertex normal
                delta = (tot - v.co)
                if delta.length != 0:
                    ang = delta.angle(v.normal)
                    deltanor = math.cos(ang) * delta.length
                    nor = v.normal
                    nor.length = abs(deltanor)
                    bm.verts.ensure_lookup_table()
                    bm.verts[v.index].co = tot + nor

        mesh.update()
        bm.free()
        bmprev.free()
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

class SPEEDRETOPO_OT_space_relax(bpy.types.Operator):
    bl_idname = "object.speedretopo_space_relax"
    bl_label = "Space Relax"
    bl_description = "Relax Vertices"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.mesh.looptools_space()
        bpy.ops.mesh.looptools_relax()

        return {"FINISHED"}

class SPEEDRETOPO_OT_symmetrize(bpy.types.Operator):
    bl_idname = 'object.speedretopo_symmetrize'
    bl_label = "Symmetrize MEsh"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        actobj_mode = context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        for mod in context.object.modifiers:
            if mod.type == 'MIRROR':
                bpy.ops.object.modifier_apply(modifier="Mirror")

        if context.object.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.symmetrize(direction='POSITIVE_X')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode=actobj_mode)

        return {'FINISHED'}

class SPEEDRETOPO_OT_double_threshold_plus(bpy.types.Operator):
    bl_idname = "object.speedretopo_double_threshold_plus"
    bl_label = "Double Threshold 01"
    bl_description = "Set the Double Threshold at 01"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.tool_settings.double_threshold = 0.1
        return {'FINISHED'}

class SPEEDRETOPO_OT_double_threshold_minus(bpy.types.Operator):
    bl_idname = "object.speedretopo_double_threshold_minus"
    bl_label = "Double Threshold 0001"
    bl_description = "Set the Double Threshold at 0001"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.tool_settings.double_threshold = 0.001
        return {'FINISHED'}

class SPEEDRETOPO_OT_set_bsurface(bpy.types.Operator):
    bl_idname = 'object.speedretopo_set_bsurface'
    bl_label = "Set Bsurface"
    bl_description = "Set the Retopo Mesh for Bsurface"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):

        context.scene.bsurfaces.SURFSK_mesh = context.active_object
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class SPEEDRETOPO_OT_add_color(bpy.types.Operator):
    bl_idname = 'object.speedretopo_add_color'
    bl_label = "Add Color"
    bl_description = "Add Color Shading to the Retopo Mesh"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if len([obj for obj in context.selected_objects if context.object is not None if obj.type == 'MESH']) == 1:
            return True

    def execute(self, context):
        addonPref = get_addon_preferences()
        self.obj_color = addonPref.obj_color

        context.space_data.shading.color_type = 'OBJECT'
        context.object.color = self.obj_color
        if bpy.app.version < (3, 6, 0):
            context.space_data.overlay.show_occlude_wire = False
        else:
            context.space_data.overlay.show_retopology = False

        return {'FINISHED'}

class SPEEDRETOPO_OT_remove_color(bpy.types.Operator):
    bl_idname = 'object.speedretopo_remove_color'
    bl_label = "Remove Color"
    bl_description = "Remove Color Shading from the Retopo Mesh"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if [obj for obj in context.selected_objects if context.object is not None if obj.type == 'MESH']:
            return True

    def execute(self, context):
        addonPref = get_addon_preferences()
        self.obj_color = addonPref.obj_color

        context.object.color = (1, 1, 1, 1)

        # if bpy.app.version < (3, 6, 0):
        #     context.space_data.overlay.show_occlude_wire = True
        # else:
        #     context.space_data.overlay.show_retopology = True

        return {'FINISHED'}

class SPEEDRETOPO_OT_gstretch(bpy.types.Operator):
    bl_idname = 'object.speedretopo_gstretch'
    bl_label = "Gstretch"
    bl_options = {'REGISTER'}

    @classmethod

    def poll(cls, context):
        return True

    def execute(self, context):

        lt = bpy.context.window_manager.looptools
        lt.gstretch_use_guide = 'Annotation'

        gp = context.active_object
        gp.active_material_index = 0

        bpy.ops.mesh.looptools_gstretch(conversion='limit_vertices', conversion_distance=0.1, conversion_max=32, conversion_min=8, conversion_vertices=32, delete_strokes=False, influence=100, lock_x=False, lock_y=False, lock_z=False, method='regular')

        bpy.ops.remove.annotation()
        return {'FINISHED'}

class SPEEDRETOPO_OT_decimate(bpy.types.Operator):
    bl_idname = "object.speedretopo_decimate"
    bl_label = "Decimate Object"
    bl_description = "Decimate for lighter object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object

        for obj in context.selected_objects:
            context.view_layer.objects.active = obj
            decimate = context.object.modifiers.get("Decimate")
            if not decimate :
                mod_decim = obj.modifiers.new("Decimate", 'DECIMATE')
                mod_decim.ratio = 0.2
                context.object.show_wire = True

        return {"FINISHED"}

class SPEEDRETOPO_OT_apply_decimate(bpy.types.Operator):
    bl_idname = "object.speedretopo_apply_decimate"
    bl_label = "Apply Decimate Modifier"
    bl_description = "Apply Decimate Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode == "OBJECT":
            bpy.ops.object.modifier_apply(modifier="Decimate")

        elif context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.modifier_apply(modifier="Decimate")
            bpy.ops.object.mode_set(mode='EDIT')

        context.object.show_wire = False
        return {'FINISHED'}

class SPEEDRETOPO_OT_remove_decimate(bpy.types.Operator):
    bl_idname = "object.speedretopo_remove_decimate"
    bl_label = "Remove Decimate Modifier"
    bl_description = "Remove Decimate Modifier"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.object.modifier_remove(modifier="Decimate")
        context.object.show_wire = False
        return {"FINISHED"}

class SPEEDRETOPO_OT_freeze_unfreeze(bpy.types.Operator):
    bl_idname = "object.speedretopo_freeze_unfreeze"
    bl_label = "Freeze/Unfreeze Selection"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    freeze_unfreeze : EnumProperty(
        items=(('freeze', "freeze", ""),
               ('unfreeze', "unfreeze", ""),
               ('clear', "clear", ""),
               ('select', "select", ""),),
        default='freeze'
    )

    def execute(self, context):
        obj = context.active_object

        has_vgroup = False
        for vgroup in obj.vertex_groups:
            if vgroup.name == "Speedretopo_freeze_unfreeze":
                bpy.ops.object.vertex_group_set_active(group='Speedretopo_freeze_unfreeze')
                has_vgroup = True
                continue

        if not has_vgroup:
            obj.vertex_groups.new(name="Speedretopo_freeze_unfreeze")

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        if [v for v in bm.verts if v.select] :
            if self.freeze_unfreeze == 'freeze':
                bpy.ops.object.vertex_group_assign()
            elif self.freeze_unfreeze == 'unfreeze':
                bpy.ops.object.vertex_group_remove_from()
            elif self.freeze_unfreeze == 'select':
                bpy.ops.mesh.select_all(action='DESELECT')


        if self.freeze_unfreeze == 'clear':
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_remove_from(use_all_verts=True)

        if self.freeze_unfreeze == 'select':
            bpy.ops.object.vertex_group_select()

        return {"FINISHED"}

class SPEEDRETOPO_OT_set_unset_center(bpy.types.Operator):
    bl_idname = "object.speedretopo_set_unset_center"
    bl_label = "Set/UnSet Center"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    set_unset_center : EnumProperty(
        items=(('set', "set", ""),
               ('unset', "unset", ""),
               ('clear', "clear", ""),
               ('select', "select", ""),),
        default='set'
    )

    def execute(self, context):
        obj = context.active_object

        has_vgroup = False
        for vgroup in obj.vertex_groups:
            if vgroup.name == "Speedretopo_set_unset_center":
                bpy.ops.object.vertex_group_set_active(group='Speedretopo_set_unset_center')
                has_vgroup = True
                continue

        if not has_vgroup:
            obj.vertex_groups.new(name="Speedretopo_set_unset_center")

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        if [v for v in bm.verts if v.select] :
            if self.set_unset_center == 'set':
                bpy.ops.object.vertex_group_assign()
            elif self.set_unset_center == 'unset':
                bpy.ops.object.vertex_group_remove_from()
            elif self.set_unset_center == 'select':
                bpy.ops.mesh.select_all(action='DESELECT')

        if self.set_unset_center == 'set':
            for v in bm.verts :
                if v.select :
                    bpy.ops.object.speedretopo_align_center_edges()

        if self.set_unset_center == 'clear':
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_remove_from(use_all_verts=True)

        if self.set_unset_center == 'select':
            bpy.ops.object.vertex_group_select()

        return {"FINISHED"}

class SPEEDRETOPO_OT_remove_double(bpy.types.Operator):
    bl_idname = 'object.speedretopo_remove_double'
    bl_label = "Remove double"
    bl_description= "Remove Double"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    threshold : FloatProperty(name="", default=0.001, min=0.0001, max=100, precision=3)
    use_unselected : BoolProperty(name="Unselected", default=False, description="Merge Selected To Other Unselected Vertices")
    use_sharp_edge_from_normals : BoolProperty(name="Sharp Edge", default=False, description="Calculate Sharp Edges Using Custom Normal Data (When Available)")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'threshold', text='Threshold')
        layout.prop(self, 'use_unselected', text='Unselected')
        layout.prop(self, 'use_sharp_edge_from_normals', text='Sharp Edge')

    def execute(self, context):
        actual_mode = context.object.mode

        if context.object.mode!='EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.mesh.remove_doubles(threshold=self.threshold, use_unselected=self.use_unselected, use_sharp_edge_from_normals=self.use_sharp_edge_from_normals)

        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.mode_set(mode=actual_mode)
        return {'FINISHED'}

class SPEEDRETOPO_OT_smooth_flat(bpy.types.Operator):
    bl_idname = 'object.speedretopo_smooth_flat'
    bl_label = "Smooth Shading or Flat Shading"
    bl_description = "Smooth or Flat the Shading of the Mesh"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 1, 0):
            return True

    def execute(self, context):

        mode = context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        if context.object.data.use_auto_smooth == False:
            bpy.ops.object.shade_smooth(use_auto_smooth=True)
            context.object.data.auto_smooth_angle = 1.0472
        else:
            bpy.ops.object.shade_smooth(use_auto_smooth=False)
            bpy.ops.object.shade_flat()

        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}

# BLENDER 4.1
class SPEEDRETOPO_OT_set_smooth(bpy.types.Operator):
    bl_idname = 'object.speedretopo_set_smooth'
    bl_label = "Set Smooth"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 1, 0):
            return True

    def execute(self, context):
        obj = context.active_object
        current_mode = obj.mode

        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.shade_smooth()

        #Restore Mode
        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

        return {'FINISHED'}

class SPEEDRETOPO_OT_set_flat(bpy.types.Operator):
    bl_idname = 'object.speedretopo_set_flat'
    bl_label = "Set Flat"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (4, 1, 0):
            return True

    def execute(self, context):
        obj = context.active_object
        current_mode = obj.mode

        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.shade_flat()

        #Restore Mode
        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

        return {'FINISHED'}

CLASSES =  [SPEEDRETOPO_OT_create_speedretopo,
            SPEEDRETOPO_OT_align_center_edges,
            SPEEDRETOPO_OT_add_subsurf,
            SPEEDRETOPO_OT_remove_subsurf,
            SPEEDRETOPO_OT_apply_subsurf,
            SPEEDRETOPO_OT_add_mirror,
            SPEEDRETOPO_OT_apply_mirror,
            SPEEDRETOPO_OT_remove_mirror,
            SPEEDRETOPO_OT_remove_shrinkwrap,
            SPEEDRETOPO_OT_add_and_apply_shrinkwrap,
            SPEEDRETOPO_OT_apply_shrinkwrap,
            SPEEDRETOPO_OT_add_shrinkwrap,
            SPEEDRETOPO_OT_update_shrinkwrap,
            SPEEDRETOPO_OT_recalculate_normals_outside,
            SPEEDRETOPO_OT_recalculate_normals_inside,
            SPEEDRETOPO_OT_srrelax,
            SPEEDRETOPO_OT_space_relax,
            SPEEDRETOPO_OT_double_threshold_plus,
            SPEEDRETOPO_OT_double_threshold_minus,
            SPEEDRETOPO_OT_add_color,
            SPEEDRETOPO_OT_remove_color,
            SPEEDRETOPO_OT_symmetrize,
            SPEEDRETOPO_OT_gstretch,
            SPEEDRETOPO_OT_decimate,
            SPEEDRETOPO_OT_apply_decimate,
            SPEEDRETOPO_OT_remove_decimate,
            SPEEDRETOPO_OT_freeze_unfreeze,
            SPEEDRETOPO_OT_set_unset_center,
            SPEEDRETOPO_OT_set_bsurface,
            SPEEDRETOPO_OT_remove_double,
            SPEEDRETOPO_OT_smooth_flat,
            SPEEDRETOPO_OT_set_flat,
            SPEEDRETOPO_OT_set_smooth
            ]

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
    # for cls in CLASSES :
    #     if hasattr(bpy.types, cls.__name__):
    #         bpy.utils.unregister_class(cls)