from math import radians, degrees, isclose

import bmesh
import bpy
import numpy as np
from bpy.props import *
from bpy.utils import register_class, unregister_class
from mathutils import Vector, Quaternion, Matrix, geometry
from mathutils.bvhtree import BVHTree as BVH
from collections import defaultdict

_conform_obj_group_name = "Conform Object Gradient Group"
_blend_obj_group_name = "Conform Object Blend Group"
_deform_mod_name = 'Conform Deformation'
_deform_shrinkwrap_mod_name = 'Conform Shrinkwrap'
_transfer_mod_name = "Conform Object Normal Transfer"
_subd_mod_name = "Conform Object Subdivisions"
_lattice_mod_name = "Conform Lattice"


def map_range(value, leftMin, leftMax, rightMin, rightMax):
    
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    if leftSpan > 0:
        valueScaled = float(value - leftMin) / float(leftSpan)
    else:
        valueScaled = rightMin

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def rotate_local(obj, euler_rot, source_object_projection_point, bbox_center):
    # separate the object's world matrix into a translation matrix and a combined scale rotation matrix
    loc, rot, sca = obj.matrix_world.decompose()

    scale_matrix_x2 = Matrix.Scale(sca[0], 4, (1.0, 0.0, 0.0))
    scale_matrix_y2 = Matrix.Scale(sca[1], 4, (0.0, 1.0, 0.0))
    scale_matrix_z2 = Matrix.Scale(sca[2], 4, (0.0, 0.0, 1.0))
    scale_matrix_xall = scale_matrix_x2 @ scale_matrix_y2 @ scale_matrix_z2

    if source_object_projection_point == 'CENTER':

        # We need to do a local rotation but then offset it back to its original location.
        # We do this by decomposing the matrix and then inserting a custom rotation using
        # a conjugated (inverted) set of rotation quaternions that will return us to the center
        # bounding box position after rotations have been applied.
        rot_conjugated = rot.conjugated()

        loc_conj = loc.copy()
        loc_conj.rotate(rot_conjugated)

        bbox_center_conj = bbox_center.copy()
        bbox_center_conj.rotate(rot_conjugated)

        obj.matrix_world = Matrix.Translation(bbox_center) @ \
                                    rot.to_matrix().to_4x4() @ \
                                    euler_rot.to_matrix().to_4x4() @ \
                                    Matrix.Translation(loc_conj - bbox_center_conj) @ \
                                        scale_matrix_xall
    else:
        # this is ok we can rotate around the origin fine
        obj.matrix_world = Matrix.Translation(loc) @ \
                                    rot.to_matrix().to_4x4() @ \
                                    euler_rot.to_matrix().to_4x4() @\
                                        scale_matrix_xall
        

def create_vertex_group(source_obj, group_name, gradient_type, gradient_start, gradient_end, closest_point, projection_vec):

    bm = bmesh.new()
    mesh = source_obj.data
    bm.from_mesh(mesh)

    if group_name not in source_obj.vertex_groups:
        group = source_obj.vertex_groups.new(name=group_name)
    else:
        group = source_obj.vertex_groups.get(group_name)

    distances = {}
    for v in bm.verts:
        distances[v.index] = (closest_point - geometry.intersect_point_line(source_obj.matrix_world @ v.co, closest_point, closest_point + -projection_vec)[0]).magnitude

    index_weight_map = {}
    max_vert_pos = distances[max(distances, key=distances.get)]
    min_vert_pos = distances[min(distances, key=distances.get)]

    min_vert_pos_trans = map_range(gradient_start, 0, 1, min_vert_pos, max_vert_pos)
    max_vert_pos_trans = map_range(gradient_end, 0, 1, min_vert_pos, max_vert_pos)
    
    for v in bm.verts:
        if gradient_type == 'LINEAR' and min_vert_pos_trans != max_vert_pos_trans:
            index_weight_map[v.index] =  map_range(distances[v.index], min_vert_pos_trans, max_vert_pos_trans, 1,0)
        else:
            gradient_point = map_range(distances[v.index], min_vert_pos, max_vert_pos, 0, 1)
            if gradient_point < gradient_end:
                index_weight_map[v.index] = 1
            else:
                index_weight_map[v.index] = 0

    # go through each vert and lerp in terms of vertex position
    group_index = source_obj.vertex_groups[group.name].index
    for v in mesh.vertices:
        group.add([v.index], index_weight_map[v.index], 'REPLACE' )
    
    mesh.update()

    bm.free()

    return group
    

def create_vertex_radial_group(context, source_obj, target_obj, group_name, gradient_type, gradient_start, gradient_end):

    bm = bmesh.new()
    mesh = source_obj.data
    bm.from_mesh(mesh)
    bvh = BVH.FromObject(target_obj, context.evaluated_depsgraph_get())

    if group_name not in source_obj.vertex_groups:
        group = source_obj.vertex_groups.new(name=group_name)
    else:
        group = source_obj.vertex_groups.get(group_name)

    distances = {}
    for v in bm.verts:
        # for each world coord find closest point on Target Object
        ray_origin = target_obj.matrix_world.inverted() @ (source_obj.matrix_world @ v.co)

        location, normal, face_index, distance = bvh.find_nearest(ray_origin)

        if location:
            world_vertex_location = source_obj.matrix_world @ v.co
            closest_point_on_target = target_obj.matrix_world @ location
            distance = (closest_point_on_target - world_vertex_location).magnitude
            distances[v.index] = distance

    index_weight_map = {}
    max_vert_pos = distances[max(distances, key=distances.get)]
    min_vert_pos = distances[min(distances, key=distances.get)]

    min_vert_pos_trans = map_range(gradient_start, 0, 1, min_vert_pos, max_vert_pos)
    max_vert_pos_trans = map_range(gradient_end, 0, 1, min_vert_pos, max_vert_pos)
    
    for v in bm.verts:
        if v.index not in distances:
            continue

        if gradient_type == 'LINEAR' and min_vert_pos_trans != max_vert_pos_trans:
            index_weight_map[v.index] =  map_range(distances[v.index], min_vert_pos_trans, max_vert_pos_trans, 1,0)
        else:
            gradient_point = map_range(distances[v.index], min_vert_pos, max_vert_pos, 0, 1)
            if gradient_point < gradient_end:
                index_weight_map[v.index] = 1
            else:
                index_weight_map[v.index] = 0

    # go through each vert and lerp in terms of vertex position
    group_index = source_obj.vertex_groups[group.name].index
    for v in mesh.vertices:
        group.add([v.index], index_weight_map[v.index], 'REPLACE' )
    
    mesh.update()

    bm.free()

    return group

def get_target_obj(source_obj):
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        deform_mod = source_obj.modifiers[_deform_shrinkwrap_mod_name]
        target_obj = deform_mod.target
        return target_obj
    grid_object = get_grid_obj(source_obj)
    if grid_object:
        for mod in grid_object.modifiers:
            if mod.type == 'SHRINKWRAP':
                target_obj = mod.target
                return target_obj
    return None

def get_grid_obj(source_obj):
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        grid_object = mod.target
        return grid_object
    return None

def get_lattice_obj(conform_grid_obj):
    if _lattice_mod_name in conform_grid_obj.modifiers:
        mod = conform_grid_obj.modifiers[_lattice_mod_name]
        lat_object = mod.object
        return lat_object
    return None


def get_world_projection_vectors(obj, location, normal):
    world_location = obj.matrix_world @ location

    normal_local = normal.to_4d()
    normal_local.w = 0
    world_normal = (obj.matrix_world @ normal_local).to_3d()
    
    return world_location, world_normal



class CONFORMOBJECT_OT_ToggleGridSnap(bpy.types.Operator):
    """Toggle Surface Blender's Snapping settings when moving an object"""
    bl_idname = "conform_object.toggle_snapping"
    bl_label = "Toggle Surface Snapping"

    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        context.scene.tool_settings.use_snap = not context.scene.tool_settings.use_snap
        if context.scene.tool_settings.use_snap:
            context.scene.tool_settings.snap_elements = {'FACE'}
        else:
            context.scene.tool_settings.snap_elements = {'INCREMENT'}
        context.scene.tool_settings.use_snap_align_rotation = context.scene.tool_settings.use_snap
        context.scene.tool_settings.use_snap_project = context.scene.tool_settings.use_snap
        return {'FINISHED'}

class CONFORMOBJECT_OT_Dig(bpy.types.Operator):
    """Dig Object"""
    bl_idname = "conform_object.dig"
    bl_label = "Dig Object"

    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    
    thickness : FloatVectorProperty(
            name="Thickness X/Y/Z",
            description="Thickness of dug object",
            default=[0.1, 0.1, 0],
            step=1,
            precision=4
            )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and len(context.selected_objects) > 1 \
                and len([o for o in context.selected_objects if o.type == 'MESH']) == len(context.selected_objects)


    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'thickness')

    def execute(self, context):

        target_obj = context.active_object
        source_objs = [obj for obj in context.selected_objects if obj != context.active_object]

        for source_obj in source_objs:
            # make a copy of the object

            new_obj = source_obj.copy()
            new_obj.data = source_obj.data.copy()
            new_obj.animation_data_clear()
            context.collection.objects.link(new_obj)

            bm = bmesh.new()
            bm.from_mesh(new_obj.data)

            for v in bm.verts:
                v.co = v.co + (Vector((v.normal.x * self.thickness[0], v.normal.y * self.thickness[1], v.normal.z * self.thickness[2])))
            bm.to_mesh(new_obj.data)

            bm.free()

            new_obj.display_type = 'WIRE'

            mod = target_obj.modifiers.new(name="Dig Boolean", type="BOOLEAN")

            mod.object = new_obj
            mod.operation = 'DIFFERENCE'




        return {'FINISHED'}

mod_items = []

class CONFORMOBJECT_OT_Conform(bpy.types.Operator):
    """Project an Object onto another Object's surface"""
    bl_idname = "mesh.conform_object"
    bl_label = "Conform Object"

    bl_options = {'REGISTER', 'UNDO', 'PRESET'}


    conform_type : EnumProperty(items= (('GRID', 'Grid', 'Use a hidden deformation grid.'),
                                        ('SHRINKWRAP', 'Shrinkwrap', 'Use a Shrink Wrap Modifier.')),
                                        name = "Wrap Method", default='GRID', description='Method used to wrap the object onto the surface')



    make_copy :  BoolProperty (
            name="Make Copy",
            description="Make a Copy of the Source Object)",
            default=False
            )

    collapse_modifiers :  BoolProperty (
            name="Collapse Modifiers",
            description="Collapse the modifiers on the Source Object (Useful for when complex modifiers are involved)",
            default=False
            )

    deform_modifier_pos : EnumProperty(items= (('START', 'Start', ''),
                                        ('BEFORE', 'Before', ''),
                                        ('END', 'End', '')),
                                        name = "Deform Modifier Postion", default='END')

    def get_modifiers(self, context):
        global mod_items
        mod_items = []
        mod_items.append(('NONE', 'Choose Modifier', ''))
        mods = [m for m in context.active_object.modifiers if m.name not in [_deform_shrinkwrap_mod_name, _deform_mod_name]]
        for mod in mods:
            mod_items.append((mod.name, mod.name, ''))
        return mod_items



    deform_before_mod : EnumProperty(items=get_modifiers,
                                        name = "Modifier")

    falloff : FloatProperty(
            name="Interpolation Falloff",
            description="Controls how much nearby polygons influence deformation",
            default=4.000,
            step=1,
            precision=4,
            min = 2,
            max = 16
            )

    vertical_subdivisions : IntProperty(
            name="Grid Vertical Subdivisions",
            description="Number of vertical subdivisions for grid",
            default=20,
            min = 0
        )
    
    horizontal_subdivisions : IntProperty(
            name="Grid Horizontal Subdivisions",
            description="Number of vertical subdivisions for grid",
            default=20,
            min = 0
        )

    grid_subsurf : IntProperty(
            name="Grid Smoothing",
            description="Subdivision Surface Smoothing for grid",
            default=0,
            min = 0,
            max=6
        )

    source_object_offset : FloatProperty(
            name="Offset",
            description="Amount of offset from the surface of the Target Object",
            default=0,
            step=1,
            precision=4,
            options={'SKIP_SAVE'}
            )

    source_object_location : FloatVectorProperty(
            name="Location",
            description="Relative location of Target Object once it has been projected onto the surface",
            subtype='TRANSLATION',
            default=[0,0,0],
            options={'SKIP_SAVE'}
            )

    hide_grid : BoolProperty (
            name="Hide Grid",
            description="Hide or show the deformation grid",
            default=True
            )

    enable_grid : BoolProperty (
            name="Enable Grid",
            description="Enable or Disable the deformation grid (parameters will still be editable)",
            default=True
            )

    grid_transform_x : FloatProperty(
            name="Grid X",
            description="Relative X location of Deformation Grid",
            default=0,
            step=1,
            precision=4
            )


    grid_transform_y : FloatProperty(
            name="Grid Y",
            description="Relative Y location of Deformation Grid",
            default=0,
            step=1,
            precision=4
            )

    grid_transform_z : FloatProperty(
            name="Grid Z",
            description="Relative Z location of Deformation Grid",
            default=0,
            step=1,
            precision=4,
            min=0
            )

    grid_size_x : FloatProperty(
            name="Grid Scale X",
            description="Width of Deformation Grid",
            default=1,
            step=1,
            precision=4,
            min=0
            )

    grid_rotation : FloatProperty(
            name="Grid Rotation",
            description="Z Rotation of Deformation Grid",
            default=0,
            precision=4
            )


    grid_size_y : FloatProperty(
            name="Grid Scale Y",
            description="Height of Deformation Grid",
            default=1,
            step=1,
            precision=4
            )

    parent_grid_to_source :  BoolProperty (
            name="Parent Deform Grid to Source",
            description="Parent the deformation grid to the original Source Object, useful if you wish to move the object later.",
            default=True
            )


    create_lattice : BoolProperty (
            name="Create Lattice",
            description="Create a Lattice to deform the grid",
            default=False
            )

    lattice_u : IntProperty (
            name="Lattice U",
            description="Number of lattice subdivisions in U direction",
            default=3,
            min=2
        )

    lattice_v : IntProperty (
            name="Lattice V",
            description="Number of lattice subdivisions in V direction",
            default=3,
            min=2
        )
    
    interpolation_type : EnumProperty(items=(('KEY_LINEAR', 'Linear interpolation', ''),
                                            ('KEY_CARDINAL', 'Cardinal interpolation', ''),
                                            ('KEY_CATMULL_ROM', 'Catmull-Rom interpolation', ''),
                                            ('KEY_BSPLINE', 'BSpline interpolation', '')),
                                        name = "Interpolation Type", default='KEY_BSPLINE')

    place_mod_at_start : BoolProperty (
            name="Deform Modifier at Start",
            description="Place the Surface Deform Modifier at the start of the start of the modifier stack",
            default=False
        )

    is_graduated : BoolProperty (
            name = "Gradient Effect",
            description = "Restrict the effect from the bottom to the top",
            default = True
    )

    gradient_type : EnumProperty(items= (('LINEAR', 'Linear', 'This will produce a smooth transition.'),
                                        ('CONSTANT', 'Constant', 'The will produce a full weighting which drops off at the end'),),
                                        name = "Gradient Type", default='LINEAR', description="Type of gradient to apply.")


    gradient_method : EnumProperty(items= (
                                        ('GRADIENT', 'Standard', 'Use the standard gradient effect from the closest part of the Source Object the furthest part.'),
                                        ('PROXIMITY', 'Proximity', 'This will weight the closest vertices and then taper off ')),                               
                                        name = "Gradient Method", default='GRADIENT', description='Method used to add vertex weights of the the Source Object onto the surface')



    def check_grad_start(self, context):
        if self.gradient_start > self.gradient_end:
            self.gradient_end = self.gradient_start

    gradient_start : FloatProperty(
            name = "Start",
            description = "This is the lower end point of the effect (0=bottom of object)",
            default = 0,
            min=0,
            step=1,
            precision=4,
            update=check_grad_start
    )

    def check_grad_end(self, context):
        if self.gradient_end < self.gradient_start:
            self.gradient_start = self.gradient_end

    gradient_end : FloatProperty(
            name = "End",
            description = "This is the upper end point of the effect (1=top of object)",
            default = 1,
            min=0,
            step=1,
            precision=4,
            update=check_grad_end
    )

    is_gradient_mode_active : BoolProperty (
            name = "Gradient Mode Active",
            description = "Whether or not the Vertex Group for the Gradient Effect is active or not.",
            default = True
    )

    is_blend_normals : BoolProperty (
            name = "Blend normals",
            description = "Blend the normals of the target surface",
            default = False
    )

    blend_gradient_type : EnumProperty(items= (('LINEAR', 'Linear', 'This will produce a smooth transition.'),
                                        ('CONSTANT', 'Constant', 'The will produce a full weighting which drops off at the end'),),
                                        name = "Blend Gradient Type", default='LINEAR', description="Type of gradient to apply.")

    blend_gradient_method : EnumProperty(items= (
                                        ('GRADIENT', 'Standard', 'Use the standard gradient effect from the closest part of the Source Object the furthest part.'),
                                        ('PROXIMITY', 'Proximity', 'This will weight the closest vertices and then taper off ')),                               
                                        name = "Gradient Method", default='GRADIENT', description='Method used to add vertex weights of the the Source Object onto the surface')

    def check_blend_grad_start(self, context):
        if self.blend_gradient_start > self.blend_gradient_end:
            self.blend_gradient_end = self.blend_gradient_start

    blend_gradient_start : FloatProperty(
            name = "Start",
            description = "This is the lower end point of the effect (0=bottom of object)",
            default = 0.0,
            min=0,
            step=1,
            precision=4,
            update=check_blend_grad_start

    )

    def check_blend_grad_end(self, context):
        if self.blend_gradient_end < self.blend_gradient_start:
            self.blend_gradient_start = self.blend_gradient_end

    blend_gradient_end : FloatProperty(
            name = "End",
            description = "This is the upper end point of the effect (1=top of object)",
            default = 0.2,
            min=0,
            step=1,
            precision=4,
            update=check_blend_grad_end
    )

    is_blend_whole_obj : BoolProperty (
            name = "Blend whole object",
            description = "Blend the normals of the entire object",
            default = False
    )

    add_subsurf_simple : BoolProperty (
        name="Add Simple Subdivisions",
        description="Add a simple Subdivision Surface modifier to automatically subdivide the mesh",
        default=False
    )

    subsurf_divisions : IntProperty (
        name="Subdivisions",
        description="Number of Subdivisions",
        default=1,
        min=1,
        soft_max=6
    )

    source_object_position : EnumProperty(items= (('LOWEST', 'Closest Point', 'The closest point on the Source Object to the Target Object'),
                                        ('CENTER', 'Center', 'The middle of the Source Object')),
                                        name = "Source Object Point", default='LOWEST', description="Which point on the Source Object is used for placement.")


    projection_orientation : FloatVectorProperty(
            name="Conform Orientation",
            description="Orientation of Projection from the Source Object",
            subtype='EULER',
            default=[0,0,0]
            )

    enable_source_obj_projection : BoolProperty (
        name="Enable Projection",
        description="Enable or Disable Source Object Projection (parameters will still be editable)",
        default=True
    )

    source_object_projection_point : EnumProperty(items= (('CENTER', 'Median Point', 'The calculated center of the object'),
                                        ('ORIGIN', 'Origin', 'The object\s origin point in 3D space'),
                                        ),
                                        name = "Source Object Reference Point", default='CENTER', description="Which point on the Source Object is used to project it onto the Source Object.")

    source_object_orientation : FloatVectorProperty(
            name="Source Object Orientation",
            description="Rotation of Source Object once it has been projected onto the surface of the Target Object",
            subtype='EULER',
            options={'SKIP_SAVE'}
            )

    projection_method : EnumProperty(items= (
                                        ('AUTO', 'Auto', 'Try to project the Source Object using its local -Z axis line, otherwise project it onto the nearest point on the Targt Object.'),
                                        ('LOCAL_AXIS', 'Axis Line', 'Use a local axis line on the Source Object to project onto the target surface.'),
                                        ('NEAREST', 'Nearest', 'The Source Object will be projected onto the nearest point on the Target Object.'),
                                        ('CUSTOM', 'Custom', 'Specify a custom direction to the Target Object.'),
                                        ),
                                        name = "Direction", default='AUTO', description="Method used to project the Source Object onto the Target Object.")

    local_axis : EnumProperty(items= (('X', 'X', ''),
                                        ('Y', 'Y', ''),
                                        ('Z', 'Z', ''),
                                        ('-X', '-X', ''),
                                        ('-Y', '-Y', ''),
                                        ('-Z', '-Z', ''),
                                        ),
                                            name = "Local Axis", default='-Z', description="Which local axis line of the Source Object is used to project onto the Target Object.")




    axis_mat = {
                    'X' :  Quaternion((0.7071068, 0.0, 0.7071068, 0.0)).to_matrix(),
                    'Y' :  Quaternion((0.7071068, -0.7071068, 0.0, 0.0)).to_matrix(),
                    'Z' :  Quaternion((1.0, 0.0, 0.0, 0.0)).to_matrix(),
                    '-X' : Quaternion((0.7071068, 0.0, -0.7071068, 0.0)).to_matrix(),
                    '-Y' : Quaternion((0.7071068, 0.7071068, 0.0, 0.0)).to_matrix(),
                    '-Z' : Quaternion((0.0, 0.0, 1.0, 0.0)).to_matrix(),
            }

    parent_source_obj : BoolProperty (
        name="Parent Source Object to Target Object",
        description="Assign the Target Object as the Parent of the Source Object",
        default=False
    )


    def get_axis_mat(self):
        if self.local_axis in self.axis_mat:
            return self.axis_mat[self.local_axis].copy()
        else:
            return None
    def draw(self, context):


        conform_ui_props = context.window_manager.conform_object_ui


        layout = self.layout
        col = layout.column()

        box = col.box()
        row = box.row()
        row.alignment = 'LEFT'
        props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_projection_panel else "TRIA_RIGHT",
            emboss=False, text='Projection')
        props.section_to_expand = 'show_projection_panel'
        props.description = "Expand/Collapse Projection Parameters"

        if conform_ui_props.show_projection_panel:

            col_props = box.column(align=True)

            col_props.label(text="Direction: ")
            col_proj_method = col_props.column(align=True)
            col_proj_method.row(align=True).prop(self, 'projection_method', expand=True)
            if self.projection_method in {'LOCAL_AXIS'}:
                col_proj_method.row(align=True).prop(self, 'local_axis', expand=True)
            if self.projection_method in {'CUSTOM'}:
                col_proj_method.prop(self, 'projection_orientation', text="")

            col_props.separator()

            col_props.label(text="Method: ")
            col_props.row(align=True).prop(self, 'conform_type', expand=True)
            if self.conform_type == 'GRID':

                box = col_props.box()
                splits = box.split(factor=0.8)
                row = splits.row(align=True)
                row.alignment = 'LEFT'
                props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_grid_panel else "TRIA_RIGHT",
                    emboss=False, text='Deformation Grid')
                props.section_to_expand = 'show_grid_panel'
                props.description = "Expand/Collapse Deformation Grid Parameters"

                selected_lattices = [l for l in context.selected_objects if l.type == 'LATTICE']
                if not selected_lattices:
                    row.prop(self, 'create_lattice', text="", emboss = False,
                                            icon="OUTLINER_OB_LATTICE" if self.create_lattice else "MOD_LATTICE")
                else:
                    row.label(text='', icon="OUTLINER_OB_LATTICE")
                    row.label(text='', icon="CHECKMARK")

                row = splits.row(align=True)
                row.alignment = 'RIGHT'
            
                row.separator()
                row.prop(self, 'hide_grid', text="", emboss = False,
                                        icon="HIDE_ON" if self.hide_grid else "HIDE_OFF")
                row.separator()
                row.prop(self, 'enable_grid', text="", emboss = False,
                                        icon="CHECKBOX_HLT" if self.enable_grid else "CHECKBOX_DEHLT")                          

                if conform_ui_props.show_grid_panel:
                    
                    col_trim = box.column(align=True)
                    col_props = col_trim.column(align=True)
                    col_props.prop(self, 'hide_grid', text="Show Grid" if self.hide_grid else "Hide Grid", toggle=True)
                    col_props.prop(self, 'vertical_subdivisions', text="Grid Subdivisions X")
                    col_props.prop(self, 'horizontal_subdivisions', text="Grid Subdivisions Y")
                    col_props.prop(self, 'grid_subsurf') 
                    col_props.prop(self, 'grid_transform_x') 
                    col_props.prop(self, 'grid_transform_y') 
                    col_props.prop(self, 'grid_transform_z') 
                    col_props.prop(self, 'grid_size_x') 
                    col_props.prop(self, 'grid_size_y')
                    col_props.prop(self, 'grid_rotation')
                    col_props.prop(self, 'falloff')
                    col_props.separator()
                    if not selected_lattices:
                        col_props.prop(self, 'create_lattice', text="Lattice Created" if self.create_lattice else "Create Lattice", toggle=True)
                        col_lat_props = col_props.column(align=True)
                        col_lat_props.enabled = self.create_lattice
                        col_lat_props.prop(self, 'lattice_u') 
                        col_lat_props.prop(self, 'lattice_v') 
                        col_lat_props.prop(self, 'interpolation_type', text="")
                    else:
                        col_lat_props = col_props.column(align=True).row()
                        col_lat_props.alignment="CENTER"
                        col_lat_props.label(text='', icon="CHECKMARK")
                        col_lat_props.label(text="Lattice object already selected.")

                
            col_props.separator()

            col_props.label(text="Projection Starting Point:")
            col_props.row().prop(self, 'source_object_projection_point', expand=True)

            col_props.separator()

        source_objs = [obj for obj in context.selected_objects if obj != context.active_object]
        box = col.box()
        row = box.row()
        row.alignment = 'LEFT'

        props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_orientation_panel else "TRIA_RIGHT",
            emboss=False, text="Object Transform")
        props.section_to_expand = 'show_orientation_panel'
        props.description = "Expand/Collapse Orientation Parameters"

        if conform_ui_props.show_orientation_panel:

            col_props = box.column(align=True)

            col_props.prop(self, 'source_object_offset', text="Surface Offset")
            col_props.prop(self, 'source_object_location', text="Local Position")
            col_props.prop(self, 'source_object_orientation', text="Local Rotation")

            col_props.label(text="Object Projection:")
            col_props.prop(self, 'enable_source_obj_projection', text="Disable Projection" if self.enable_source_obj_projection else "Enable Projection", toggle=True)
            pos_col_props = col_props.column(align=True)
            pos_col_props.enabled = self.enable_source_obj_projection
            pos_col_props.row(align=True).prop(self, 'source_object_position', expand=True)

            col_props.separator()

        box = col.box()
        splits = box.split(factor=0.8)
        row = splits.row(align=True)
        row.alignment = 'LEFT'
        props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_gradient_panel else "TRIA_RIGHT",
            emboss=False, text='Gradient Effect')
        props.section_to_expand = 'show_gradient_panel'
        props.description = "Expand/Collapse Gradient Effect Vertex Weight Parameters"
        row = splits.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(self, 'is_graduated', text="", emboss = False,
                                icon="CHECKBOX_HLT" if self.is_graduated else "CHECKBOX_DEHLT")

        if conform_ui_props.show_gradient_panel:

            col_grad_props = box.column(align=True)
            col_grad_props.enabled = self.is_graduated
            
            col_grad_props.label(text="Gradient Type:")
            col_grad_props.row(align=True).prop(self, "gradient_type", expand=True)

            col_grad_props.label(text="Gradient Method:")
            col_grad_props.row(align=True).prop(self, "gradient_method", expand=True)

            col_grad_props.separator()

            row_grad_props = col_grad_props.row(align=True)
            if self.gradient_type == 'LINEAR':
                row_grad_props.prop(self, "gradient_start", text="Start")


            row_grad_props.prop(self, "gradient_end", text="End")

            col_grad_props.separator()

            col_grad_props.prop(self, 'is_gradient_mode_active', toggle=True, text="Select Group")

            col_grad_props.separator()

        box = col.box()
        splits = box.split(factor=0.8)
        row = splits.row(align=True)
        row.alignment = 'LEFT'
        props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_blend_panel else "TRIA_RIGHT",
            emboss=False, text='Blend Normals')
        props.section_to_expand = 'show_blend_panel'
        props.description = "Expand/Collapse Normal Blending Parameters"
        row = splits.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(self, 'is_blend_normals', text="", emboss = False,
                                icon="CHECKBOX_HLT" if self.is_blend_normals else "CHECKBOX_DEHLT")

        if conform_ui_props.show_blend_panel:

            col_blend_props = box.column(align=True)
            col_blend_props.enabled = self.is_blend_normals

            col_blend_props.label(text="Blend Gradient Type:")
            col_blend_props.row(align=True).prop(self, "blend_gradient_type", expand=True)

            col_blend_props.label(text="Blend Gradient Method:")
            col_blend_props.row(align=True).prop(self, "blend_gradient_method", expand=True)
            
            col_blend_grad_end = col_blend_props.column()
            col_blend_grad_end.enabled = not self.is_blend_whole_obj

            col_blend_props.separator()
            row_blend_grad_end = col_blend_grad_end.row(align=True)
            if self.blend_gradient_type == 'LINEAR':
                row_blend_grad_end.prop(self, "blend_gradient_start")
            row_blend_grad_end.prop(self, "blend_gradient_end")

            col_is_blend_whole_obj = col_blend_props.column()
            col_is_blend_whole_obj.prop(self, "is_blend_whole_obj", expand=True)

            col_blend_props.separator()

            col_blend_props.prop(self, 'is_gradient_mode_active', toggle=True, text="Select Group", invert_checkbox=True)

            col_blend_props.separator()

        box = col.box()
        row = box.row(align=True)
        row.alignment = 'LEFT'
        props = row.operator(CONFORMOBJECT_OT_ExpandCollapseUI.bl_idname, icon="TRIA_DOWN" if conform_ui_props.show_other_panel else "TRIA_RIGHT",
            emboss=False, text='Other Options')
        props.section_to_expand = 'show_other_panel'
        props.description = "Expand/Collapse All other Parameters"

        if conform_ui_props.show_other_panel:

            other_opts_col = box.column(align=True)

            subsurf_box = other_opts_col.box()
            subsurf_box.prop(self, 'add_subsurf_simple')
            col_props_subd = subsurf_box.column()
            col_props_subd.enabled = self.add_subsurf_simple
            col_props_subd.prop(self, 'subsurf_divisions')

            other_opts_col.separator()
            other_opts_col.separator()


            other_opts_col.box().prop(self, 'collapse_modifiers')
            
            other_opts_col.separator()
            other_opts_col.separator()

            deform_pos_box = other_opts_col.box()
            deform_pos_box.label(text="Deform Modifier Position: ")
            row_mod_pos_props = deform_pos_box.row()
            row_mod_pos_props.prop(self, 'deform_modifier_pos', text="")
            if self.deform_modifier_pos == 'BEFORE':
                row_mod_pos_props.prop(self, 'deform_before_mod', text="")

            other_opts_col.separator()
            
            other_opts_col.box().prop(self, 'parent_source_obj')

            other_opts_col.separator()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and\
            len([o for o in context.selected_objects if o.type in {'MESH', 'LATTICE'}]) == len(context.selected_objects) and\
            len([o for o in context.selected_objects if o.type == 'MESH']) > 1 and\
            len([o for o in context.selected_objects if o.type == 'LATTICE'])  <= 1


    def invoke(self, context, event):


        return self.execute(context)


    def execute(self, context):
        if context.window_manager.conform_object_ui.update_draw_only:
            context.window_manager.conform_object_ui.update_draw_only = False
            return {'PASS_THROUGH'}

        target_obj = context.active_object
        target_obj_evaluated = target_obj.evaluated_get(context.evaluated_depsgraph_get())

        # find the nearest point on the target mesh.
        target_matrix_evaluated = target_obj_evaluated.matrix_world

        source_objs = [obj for obj in context.selected_objects if obj != context.active_object and obj.type == 'MESH']
        
        # Parent source objects to target object if needed.
        if self.parent_source_obj:
            old_active = context.view_layer.objects.active
            context.view_layer.objects.active = target_obj
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            if old_active:
                context.view_layer.objects.active = old_active
            

        for source_obj in source_objs:

            enable_source_obj_projection = self.enable_source_obj_projection
        
            context.view_layer.objects.active = target_obj

            collection = source_obj.users_collection[0] if len(source_obj.users_collection) else context.collection

            # create a copy of this Source Object for processing
            if self.make_copy:
                source_obj_name = source_obj.name + " Conformed"
                source_obj = source_obj.copy()
                source_obj.name = source_obj_name
                source_obj.data = source_obj.data.copy()
                source_obj.animation_data_clear()
                collection.objects.link(source_obj)
            
            conform_undo(source_obj, context, reset_matrix=False)
            source_obj.conform_object.is_conform_obj = False
            source_obj.conform_object.is_conform_shrinkwrap = False


            if self.collapse_modifiers:
                old_data = source_obj.data
                source_object_data = bpy.data.meshes.new_from_object(source_obj.evaluated_get(context.evaluated_depsgraph_get()))
                source_obj.modifiers.clear()
                source_obj.data = source_object_data
                bpy.data.meshes.remove(old_data)

            # Move source to nearest point on target
            bvh = BVH.FromObject(target_obj_evaluated, context.evaluated_depsgraph_get())

            # get the nearest point on the Target Object to the Source Object (including modifiers).
            if self.source_object_projection_point == 'CENTER':
                _, world_source_obj_bbox_center = self.calc_bbox(source_obj, context)
            else: 
                world_source_obj_bbox_center = source_obj.location

            context.view_layer.update()

            force_closest = False
            projection_vec = None
            projection_mat = None
            grid_rotation = None
            projection_success = False
            if self.projection_method in {'AUTO', 'LOCAL_AXIS', 'CUSTOM'}:

                # Set up the right local orientation first.
                up_vec = Vector((0,0,1))
                if self.projection_method == 'AUTO':
                    projection_mat = source_obj.matrix_world.copy()
                    projection_vec = -up_vec
                elif self.projection_method == 'LOCAL_AXIS':
                    projection_mat = source_obj.matrix_world @ self.get_axis_mat().to_4x4()
                    projection_vec = up_vec
                elif self.projection_method == 'CUSTOM':
                    projection_mat = source_obj.matrix_world @ self.projection_orientation.to_matrix().to_4x4()
                    projection_vec = -up_vec
                # Align projection vector to the projection matrix.
                projection_vec = projection_mat.to_3x3() @ projection_vec

                # Now attempt to cast the right rays
                highest_source_obj_point = self.find_furthest_point_on_object(context, source_obj, world_source_obj_bbox_center, -projection_vec)
                ray_direction = target_matrix_evaluated.inverted().to_3x3() @ projection_vec
                ray_origin = target_matrix_evaluated.inverted() @ highest_source_obj_point
                location, normal, face_index, distance = bvh.ray_cast(ray_origin, ray_direction)

                if location:
                    world_closest_point_on_target_obj, _ = get_world_projection_vectors(target_obj_evaluated, location, normal)
                    projection_success = True
                elif self.projection_method == 'AUTO':
                    # We could not find a point from the Source Object to the Target Object using this method.
                    # fallback to using the nearest method.
                    force_closest = True
                elif self.projection_method == 'LOCAL_AXIS':
                    self.report({'WARNING'}, "Could not project using local " + self.local_axis + " axis of Source Object.")
                    enable_source_obj_projection = False
                    world_closest_point_on_target_obj = self.find_furthest_point_on_object(context, source_obj, world_source_obj_bbox_center, projection_vec)
                elif self.projection_method == 'CUSTOM':
                    self.report({'WARNING'}, "Could not project Source Object to Target Object using custom direction.")
                    enable_source_obj_projection = False
                    world_closest_point_on_target_obj = self.find_furthest_point_on_object(context, source_obj, world_source_obj_bbox_center, projection_vec)

            
            if self.projection_method == 'NEAREST' or force_closest:

                ray_origin = target_matrix_evaluated.inverted() @ world_source_obj_bbox_center
                location, normal, face_index, distance = bvh.find_nearest(ray_origin)

                if location:
                    world_closest_point_on_target_obj, world_normal = get_world_projection_vectors(target_obj_evaluated, location, normal)
                    projection_vec = world_closest_point_on_target_obj - world_source_obj_bbox_center
                    # Do some checks if this projection vector is too small to be accurate.
                    if isclose(projection_vec.magnitude,0, abs_tol=0.00001):
                        projection_vec = -world_normal
                    if projection_vec.dot(world_normal) > 0:
                        projection_vec = -projection_vec
                    projection_vec.normalize()
                    projection_mat = -projection_vec.to_track_quat('Z', 'Y')
                    projection_mat = projection_mat.to_matrix().to_4x4()
                    projection_success = True
                else:
                    self.report({'ERROR'}, "Cannot find path from Source Object to Target Object. \n See 'Tips and Troubleshooting' at conform-object-docs.readthedocs.io or email info@configurate.net")
                    return {'CANCELLED'}

            def flatten(mat):
                dim = len(mat)
                return [mat[j][i] for i in range(dim) 
                                for j in range(dim)]
                                
            # offset the location by the height of the Source Object.
            original_matrix = source_obj.matrix_world.copy()

            source_obj.conform_object.original_matrix = flatten(original_matrix)

            context.view_layer.update()

            # make the Source Object the active object.
            context.view_layer.objects.active = source_obj

            # Add a subdivision modifier if necessay
            if self.add_subsurf_simple:
                if _subd_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_subd_mod_name, 'SUBSURF')
                else:
                    mod = source_obj.modifiers.get(_subd_mod_name)
                mod.subdivision_type = 'SIMPLE'
                mod.levels = self.subsurf_divisions

            # offset the Source Object from the surface.
            rotate_local(source_obj, self.source_object_orientation, self.source_object_projection_point, world_source_obj_bbox_center)
            context.view_layer.update()

            if enable_source_obj_projection:
                if self.source_object_position == 'LOWEST':
                    world_closest_point_on_source_obj = self.find_furthest_point_on_object(context, source_obj, world_source_obj_bbox_center, projection_vec)
                    source_obj.location = source_obj.location + world_closest_point_on_target_obj - world_closest_point_on_source_obj
                else:
                    source_obj.location = source_obj.location + world_closest_point_on_target_obj - world_source_obj_bbox_center

                source_obj.location = source_obj.location + (-projection_vec * self.source_object_offset) 

            
            source_obj.location = source_obj.location + (self.source_object_location @ source_obj.matrix_world.inverted())
            
            context.view_layer.update()

            if self.conform_type == 'GRID':
                conform_grid_obj, lattice_obj = self.create_grid(source_obj, context, projection_vec, projection_mat, world_closest_point_on_target_obj, collection)

                # Add a Surface Deform modifier to the Source Object and set the grid as the deform object and bind it.
                if _deform_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_deform_mod_name, 'SURFACE_DEFORM')
                else:
                    mod = source_obj.modifiers.get(_deform_mod_name)

                mod.show_viewport = projection_success
                mod.show_render = projection_success
                mod.target = conform_grid_obj
                mod.falloff = self.falloff

               
                if self.place_mod_at_start:
                    bpy.ops.object.modifier_move_to_index(modifier=_deform_mod_name, index=0)

            # if graduated, create the graduated vertex group and assign it to the modifier.
                if self.is_graduated and not lattice_obj:
                    old_active_group = source_obj.vertex_groups.active
                    if self.gradient_method == 'GRADIENT':
                        group = create_vertex_group(source_obj, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end, world_closest_point_on_target_obj, projection_vec)
                    else:
                        group = create_vertex_radial_group(context, source_obj, target_obj_evaluated, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end)
                    
                    if self.is_gradient_mode_active:
                        source_obj.vertex_groups.active = group
                    elif old_active_group:
                        source_obj.vertex_groups.active = old_active_group
                        
                    mod = source_obj.modifiers.get(_deform_mod_name)
                    mod.vertex_group = group.name

            elif self.conform_type == "SHRINKWRAP":

                # add the shrinkwrap modifier and set it to the Target Object
                if _deform_shrinkwrap_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_deform_shrinkwrap_mod_name, 'SHRINKWRAP')
                else:
                    mod = source_obj.modifiers.get(_deform_shrinkwrap_mod_name)
                
                mod.show_viewport = projection_success
                mod.show_render = projection_success
                mod.target = target_obj
                mod.offset = self.source_object_offset

                # if graduated, create the graduated vertex group and assign it to the modifier.
                if self.is_graduated:
                    old_active_group = source_obj.vertex_groups.active
                    if self.gradient_method == 'GRADIENT':
                        group = create_vertex_group(source_obj, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end, world_closest_point_on_target_obj, projection_vec)
                    else:
                        group = create_vertex_radial_group(context, source_obj, target_obj_evaluated, _conform_obj_group_name, self.gradient_type, self.gradient_start, self.gradient_end)
                    
                    if self.is_gradient_mode_active:
                        source_obj.vertex_groups.active = group
                    elif old_active_group:
                        source_obj.vertex_groups.active = old_active_group

                    mod = source_obj.modifiers.get(_deform_shrinkwrap_mod_name)
                    mod.vertex_group = group.name

            
            # position the modifier if needed.
            if self.deform_modifier_pos == 'START':
                while source_obj.modifiers.find(mod.name) != 0:
                    bpy.ops.object.modifier_move_up(modifier=mod.name)
            elif self.deform_modifier_pos == 'BEFORE':
                if self.deform_before_mod and self.deform_before_mod != 'NONE':
                    target_mod_name = self.deform_before_mod
                    while source_obj.modifiers.find(target_mod_name) < source_obj.modifiers.find(mod.name):
                        bpy.ops.object.modifier_move_up(modifier=mod.name)


            if self.is_blend_normals:

                source_obj.data.use_auto_smooth = True

                if _transfer_mod_name not in source_obj.modifiers:
                    mod = source_obj.modifiers.new(_transfer_mod_name, 'DATA_TRANSFER')
                else:
                    mod = source_obj.modifiers.get(_transfer_mod_name)
                mod.object = None
                mod.object = target_obj
                mod.use_loop_data = True
                mod.data_types_loops = {'CUSTOM_NORMAL'}

                if not self.is_blend_whole_obj:
                    old_active_group = source_obj.vertex_groups.active
                    if self.blend_gradient_method == 'GRADIENT':
                        group = create_vertex_group(source_obj, _blend_obj_group_name, self.blend_gradient_type, self.blend_gradient_start, self.blend_gradient_end, world_closest_point_on_target_obj, projection_vec)
                    else:
                        group = create_vertex_radial_group(context, source_obj, target_obj_evaluated, _blend_obj_group_name, self.blend_gradient_type, self.blend_gradient_start, self.blend_gradient_end)
                    
                    if not self.is_gradient_mode_active:
                        source_obj.vertex_groups.active = group
                    elif old_active_group:
                        source_obj.vertex_groups.active = old_active_group

                    
                    mod.vertex_group = group.name

                source_obj.data.update()

            if self.conform_type == 'GRID':

                # Add the Lattice modifier if it was created.
                if lattice_obj:
                    lattice_mod = conform_grid_obj.modifiers.new(name=_lattice_mod_name, type='LATTICE')

                # Now add a shrinkwrap modifer to the grid object.
                shrink_mod_name = 'Conformation Shrink Wrap'
                if shrink_mod_name not in conform_grid_obj.modifiers:
                    grid_shrinkwrap_mod = conform_grid_obj.modifiers.new(shrink_mod_name, 'SHRINKWRAP')
                else:
                    grid_shrinkwrap_mod = conform_grid_obj.modifiers.get(shrink_mod_name)
                    grid_shrinkwrap_mod.target = None
                    bpy.ops.object.surfacedeform_bind(modifier=_deform_mod_name)

                if self.grid_subsurf > 0:
                    subsurf_mod_name = 'Conformation Subdivision'
                    if subsurf_mod_name not in conform_grid_obj.modifiers:
                        grid_subsurf_mod = conform_grid_obj.modifiers.new(subsurf_mod_name, 'SUBSURF')
                    else:
                        grid_subsurf_mod = conform_grid_obj.modifiers.get(subsurf_mod_name)
                    
                    grid_subsurf_mod.levels = self.grid_subsurf
                    grid_subsurf_mod.subdivision_type = 'CATMULL_CLARK'
                    grid_subsurf_mod.render_levels = self.grid_subsurf
                    grid_subsurf_mod.show_expanded = False
                    grid_subsurf_mod.show_only_control_edges = False


                grid_shrinkwrap_mod.show_viewport = self.enable_grid and projection_success
                grid_shrinkwrap_mod.show_render = self.enable_grid and projection_success
                
                grid_shrinkwrap_mod.wrap_method = 'PROJECT'
                grid_shrinkwrap_mod.use_negative_direction = True
                grid_shrinkwrap_mod.use_positive_direction = True
                grid_shrinkwrap_mod.cull_face = 'OFF'

                # hide the grid (optionally)
                conform_grid_obj.hide_set(self.hide_grid) # EYE icon
                conform_grid_obj.hide_viewport = self.hide_grid # MONITOR icon
                conform_grid_obj.hide_render = self.hide_grid # RENDER icon

                # bind the grid object to the Source Object before it gets shrinkwrapped to the Target Object
                bpy.ops.object.surfacedeform_bind(modifier=_deform_mod_name)

                # Now apply the lattice if it was created.
                if lattice_obj:
                    lattice_mod.object = lattice_obj

                # Now shrink to target object once it has been binded.
                grid_shrinkwrap_mod.target = target_obj
            
                context.view_layer.update() 
                # make grid child of Source Object
                if self.parent_grid_to_source:
                    conform_grid_obj.parent = source_obj
                    conform_grid_obj.matrix_parent_inverse = source_obj.matrix_world.inverted()

                conform_grid_obj.conform_object.is_grid_obj = True
                source_obj.conform_object.is_conform_shrinkwrap = False
                
            elif self.conform_type == 'SHRINKWRAP':
                source_obj.conform_object.is_conform_shrinkwrap = True

            source_obj.conform_object.is_conform_obj = True
                
            


        return {'FINISHED'}

    def find_furthest_point_on_object(self, context, obj, pt, vec):
        '''Find the furthest world point of an object given a point and directional vector'''

        # get the farthest point on the Source Object pointing away from Target Object.
        def point_on_line(co):
            point, _ = geometry.intersect_point_line(co, pt, pt + vec)
            return point

        def dist_func(co):
            return (co - pt).magnitude

        # get all coordinates of Source Object with modfiers.
        object_cos = []

        bm_tmp = self.calc_from_object(obj, context)

        object_cos.extend([point_on_line(obj.matrix_world @ v.co) for v in bm_tmp.verts])
        bm_tmp.free()

        filtered_cos = []

        for co in object_cos:
            if vec.dot(co - pt) >= 0:
                filtered_cos.append(co)

        if filtered_cos:
            # get farthest point on the Source Object from the Target Object point and the middle of the Source Object.
            furthest_point = max(filtered_cos, key=dist_func)
            
            return furthest_point
        elif object_cos:
            return object_cos[0]
        else:
            return obj.matrix_world @ Vector((0,0,0))

    def create_grid(self, source_obj, context, projection_vec, projection_mat, world_closest_point_on_target_obj, collection):
        # create a grid object directly below.
        grid_obj = get_grid_obj(source_obj)
        if grid_obj and grid_obj in source_obj.children:
            conform_grid_obj = grid_obj
            mesh = conform_grid_obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.clear()
        else:
            mesh = bpy.data.meshes.new("Conform Grid Mesh")
            conform_grid_obj = bpy.data.objects.new(source_obj.name + " Conform Grid", mesh)
            collection.objects.link(conform_grid_obj)
            conform_grid_obj.conform_object.source_obj = source_obj
            bm = bmesh.new()
            bm.from_mesh(mesh)

        lattice_obj = None

        conform_grid_obj.conform_object.is_grid_obj = False
        conform_grid_obj.matrix_world = projection_mat.copy()

        # get the bounding box aligned to the projection matrix.
        (lower_point1, lower_point2, lower_point4, lower_point3, upper_point1, upper_point2, upper_point4, upper_point3), grid_center = self.calc_bbox(source_obj, context, projection_mat)
        grid_up_vec = grid_center + projection_vec
        point, percentage = geometry.intersect_point_line(world_closest_point_on_target_obj, grid_center, grid_up_vec)
        conform_grid_obj.location = point

        context.view_layer.update()

        # take the points of the bounding box and find the 'middle' slice.
        point1 = (lower_point1 + upper_point1) / 2
        point2 = (lower_point2 + upper_point2) / 2
        point3 = (lower_point3 + upper_point3) / 2
        point4 = (lower_point4 + upper_point4) / 2

        # offset by the recalculated grid position.
        point1 = point1 + (point - grid_center)
        point2 = point2 + (point - grid_center)
        point3 = point3 + (point - grid_center)
        point4 = point4 + (point - grid_center)

        # apply these points as the intial points for the grid.
        vert0 = bm.verts.new(conform_grid_obj.matrix_world.inverted() @ point1)
        vert1 = bm.verts.new(conform_grid_obj.matrix_world.inverted() @ point2)
        vert2 = bm.verts.new(conform_grid_obj.matrix_world.inverted() @ point3)
        vert3 = bm.verts.new(conform_grid_obj.matrix_world.inverted() @ point4)
        
        face = bm.faces.new([vert3, vert2, vert1, vert0])

        crease_layer = bm.edges.layers.crease.verify()
        for e in bm.edges:
            e[crease_layer] = 1.0


        # edge split horizontal and vertical.
        first_loop = face.loops[0]
        horizontal_edges = [first_loop.edge, first_loop.link_loop_next.link_loop_next.edge]
        result = bmesh.ops.subdivide_edges(bm, edges=list(set(horizontal_edges)), cuts=self.vertical_subdivisions, use_grid_fill=True, use_only_quads=True)

        vertical_edges = []
        for f in bm.faces:
            second_loop = f.loops[0].link_loop_next
            vertical_edges.append(second_loop.edge)
            vertical_edges.append(second_loop.link_loop_next.link_loop_next.edge)

        result = bmesh.ops.subdivide_edges(bm, edges=list(set(vertical_edges)), cuts=self.horizontal_subdivisions, use_grid_fill=True, use_only_quads=False)


        bm.to_mesh(mesh)
        bm.free()            

        conform_grid_obj.location.x += self.grid_transform_x
        conform_grid_obj.location.y += self.grid_transform_y
        conform_grid_obj.location.z += self.grid_transform_z
        
        conform_grid_obj.scale.x *= self.grid_size_x
        conform_grid_obj.scale.y *= self.grid_size_y

        conform_grid_obj.show_wire = True
        conform_grid_obj.show_all_edges = True
        conform_grid_obj.show_in_front = True
        conform_grid_obj.display_type = 'WIRE'

        # Create a lattice object to support grid deformation

        selected_lattice = None
        selected_lattices = [l for l in context.selected_objects if l.type =='LATTICE']
        if selected_lattices:
            selected_lattice = selected_lattices[0]
        if selected_lattice:
            context.view_layer.update()
            lattice_obj = selected_lattice
            lattice_obj.parent = conform_grid_obj
            lattice_obj.matrix_parent_inverse = conform_grid_obj.matrix_world.inverted()
            lattice_obj.show_in_front = True
        elif self.create_lattice:
            context.view_layer.update()

            lattice_obj = get_lattice_obj(conform_grid_obj)

            if lattice_obj and lattice_obj in conform_grid_obj.children:
                lattice_data = lattice_obj.data
            else:
                lattice_data = bpy.data.lattices.new('Conform Grid Lattice')
                lattice_obj = bpy.data.objects.new(source_obj.name + ' Conform Lattice', lattice_data)
                lattice_obj.conform_object.is_conform_lattice = True
                lattice_obj.conform_object.source_obj = source_obj
                collection.objects.link(lattice_obj)

            lattice_obj.matrix_world = projection_mat.copy()
            lattice_obj.location = point
            dimensions = []
            dimensions.append(conform_grid_obj.dimensions[0] if conform_grid_obj.dimensions[0] else 0.001)
            dimensions.append(conform_grid_obj.dimensions[1] if conform_grid_obj.dimensions[1] else 0.001)
            dimensions.append(conform_grid_obj.dimensions[2] if conform_grid_obj.dimensions[2] else 0.001)
            lattice_obj.dimensions=Vector(dimensions)

            # Set lattice resolution
            lattice_data.points_u = self.lattice_u
            lattice_data.points_v = self.lattice_v
            lattice_data.points_w = 1  # for a flat plane, 1  point is enough in the W axis

            lattice_data.interpolation_type_u = self.interpolation_type
            lattice_data.interpolation_type_v = self.interpolation_type
            lattice_data.interpolation_type_w = self.interpolation_type

            lattice_obj.location.x += self.grid_transform_x
            lattice_obj.location.y += self.grid_transform_y
            lattice_obj.location.z += self.grid_transform_z
            
            lattice_obj.scale.x *= self.grid_size_x
            lattice_obj.scale.y *= self.grid_size_y

            lattice_obj.show_in_front = True

            lattice_obj.parent = conform_grid_obj
            lattice_obj.matrix_parent_inverse = conform_grid_obj.matrix_world.inverted()

        return conform_grid_obj, lattice_obj

    def calc_bbox(self, obj, context, mat=None):


        source_object_cos = []

        bm = self.calc_from_object(obj, context)

        source_object_cos.extend([obj.matrix_world @ v.co for v in bm.verts])
        bm.free()

        x_coords = [co.x for co in source_object_cos]
        y_coords = [co.y for co in source_object_cos]
        z_coords = [co.z for co in source_object_cos]

        center = ((max(x_coords) + min(x_coords)) / 2,
                                (max(y_coords) + min(y_coords)) / 2,
                                (max(z_coords) + min(z_coords)) / 2)


        up = Vector((0,0,1))
        down = Vector((0,0,-1))
        left = Vector((1,0,0))
        right = Vector((-1,0,0))
        front = Vector((0,1,0))
        back = Vector((0,-1,0))

        if mat != None:
            up = (mat.to_3x3() @ up).normalized()
            down = (mat.to_3x3() @ down).normalized()
            left = (mat.to_3x3() @ left).normalized()
            right = (mat.to_3x3() @ right).normalized()
            front = (mat.to_3x3() @ front).normalized()
            back = (mat.to_3x3() @ back).normalized()

        def max_dist(co):
            return geometry.distance_point_to_plane(co, Vector(center), norm)
        
        norm = up
        up_co = max(source_object_cos, key=max_dist)
        up_dist = max_dist(up_co)
        up_co = Vector(center)  + (norm * up_dist)

        norm = down
        down_co = max(source_object_cos, key=max_dist)
        down_dist = max_dist(down_co)
        down_co = Vector(center)  + (norm * down_dist)

        norm = left
        left_co = max(source_object_cos, key=max_dist)
        left_dist = max_dist(left_co)
        left_co = Vector(center)  + (norm * left_dist)

        norm = right
        right_co = max(source_object_cos, key=max_dist)
        right_dist = max_dist(right_co)
        right_co = Vector(center)  + (norm * right_dist)

        norm = front
        front_co = max(source_object_cos, key=max_dist)
        front_dist = max_dist(front_co)
        front_co = Vector(center)  + (norm * front_dist)

        norm = back
        back_co = max(source_object_cos, key=max_dist)
        back_dist = max_dist(back_co)
        back_co = Vector(center)  + (norm * back_dist)

        # find the center by first finding intersecting with the top plan, facing down, and then the same with the down plane.......

        pt1, vec1 = geometry.intersect_plane_plane(up_co, down, left_co, right)
        pt2, vec2 = geometry.intersect_plane_plane(up_co, down, right_co, left)
        pt3, vec3 = geometry.intersect_plane_plane(up_co, down, front_co, back)
        pt4, vec4 = geometry.intersect_plane_plane(up_co, down, back_co, front)

        point1, _ = geometry.intersect_line_line(pt1, pt1 + vec1, pt3, pt3 + vec3)
        point2, _ = geometry.intersect_line_line(pt1, pt1 + vec1, pt4, pt4 + vec4)
        point3, _ = geometry.intersect_line_line(pt2, pt2 + vec2, pt3, pt3 + vec3)
        point4, _ = geometry.intersect_line_line(pt2, pt2 + vec2, pt4, pt4 + vec4)


        pt5, vec5 = geometry.intersect_plane_plane(down_co, up, left_co, right)
        pt6, vec6 = geometry.intersect_plane_plane(down_co, up, right_co, left)
        pt7, vec7 = geometry.intersect_plane_plane(down_co, up, front_co, back)
        pt8, vec8 = geometry.intersect_plane_plane(down_co, up, back_co, front)

        point5, _ = geometry.intersect_line_line(pt5, pt5 + vec5, pt7, pt7 + vec7)
        point6, _ = geometry.intersect_line_line(pt5, pt5 + vec5, pt8, pt8 + vec8)
        point7, _ = geometry.intersect_line_line(pt6, pt6 + vec6, pt7, pt7 + vec7)
        point8, _ = geometry.intersect_line_line(pt6, pt6 + vec6, pt8, pt8 + vec8)

        all_coords = [point1, point2, point3, point4, point5, point6, point7, point8]

        center = sum(all_coords, Vector()) / len(all_coords)

        return (point1, point2, point3, point4, point5, point6, point7, point8), center

    def calc_from_object(self, obj, context):

        # disable the modifiers if we need the object in a certain state.
        modifier_states = {}
        if self.deform_modifier_pos == 'START':
            for mod in obj.modifiers:
                modifier_states[mod.name] = (mod.show_viewport, mod.show_render)
                mod.show_viewport=False
                mod.show_render=False
        elif self.deform_modifier_pos == 'BEFORE':
            if self.deform_before_mod and self.deform_before_mod != 'NONE':
                target_mod_name = self.deform_before_mod
                disable = False
                for mod in obj.modifiers:
                    if mod.name == target_mod_name:
                        disable = True
                    if disable:
                        modifier_states[mod.name] = (mod.show_viewport, mod.show_render)
                        mod.show_viewport=False
                        mod.show_render=False

        context.view_layer.update()

        
        obj_eval = obj.evaluated_get(context.evaluated_depsgraph_get())
        
        bm = bmesh.new()
        bm.from_mesh(obj_eval.data)

        for mod_name in modifier_states:
            mod = obj.modifiers[mod_name]
            mod.show_viewport = modifier_states[mod_name][0]
            mod.show_render = modifier_states[mod_name][0]

        context.view_layer.update()

        return bm


def apply_modifiers(obj):
    ctx = bpy.context.copy()
    ctx['object'] = obj
    for _, m in enumerate(obj.modifiers):
        try:
            ctx['modifier'] = m
            bpy.ops.object.modifier_apply(ctx, modifier=m.name)
        except RuntimeError:
            print(f"Error applying {m.name} to {obj.name}, removing it instead.")
            obj.modifiers.remove(m)

    for m in obj.modifiers:
        obj.modifiers.remove(m)

def apply_modifier(obj, m):
    ctx = bpy.context.copy()
    ctx['object'] = obj
    try:
        ctx['modifier'] = m
        bpy.ops.object.modifier_apply(ctx, modifier=m.name)
    except RuntimeError:
        print(f"Error applying {m.name} to {obj.name}, removing it instead.")
        obj.modifiers.remove(m)



def conform_undo(source_obj, context, remove_grid=True, set_active=True, reset_matrix=True):
    if not source_obj.conform_object.is_conform_obj:
        return

    target_obj = get_target_obj(source_obj)

    #remove subdivision modifier.
    if _subd_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_subd_mod_name])

    #remove the deform modifier.
    grid_object = None
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        grid_object = mod.target
        source_obj.modifiers.remove(mod)

    #remove the transfer modifier.
    if _transfer_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_transfer_mod_name])

    # remove shrinkwrap modifier if preset. 
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        source_obj.modifiers.remove(source_obj.modifiers[_deform_shrinkwrap_mod_name])


    # # remove any related vertex groups.
    if _conform_obj_group_name in source_obj.vertex_groups:
        # only perform this is the object has not other data instances.
        result = defaultdict(list)
        for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
            result[obj.data].append(obj)
        if len(result[source_obj.data]) <= 1:
            source_obj.vertex_groups.remove(source_obj.vertex_groups[_conform_obj_group_name])


    # # remove any related vertex groups.
    if _blend_obj_group_name in source_obj.vertex_groups:
        # only perform this is the object has not other data instances.
        result = defaultdict(list)
        for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
            result[obj.data].append(obj)
        if len(result[source_obj.data]) <= 1:
            source_obj.vertex_groups.remove(source_obj.vertex_groups[_blend_obj_group_name])


    #remove grid object.
    if grid_object and remove_grid:
        # check all other objects in the scene to see if this is being used elsewhere.
        found_other_grid = False
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if mod.name == _deform_mod_name and mod.target == grid_object:
                    found_other_grid = True
                    break

        if not found_other_grid:
            lattice_obj = get_lattice_obj(grid_object)
            if lattice_obj:
                if not lattice_obj.select_get():
                    data_to_remove = lattice_obj.data
                    bpy.data.objects.remove(lattice_obj)
                    bpy.data.lattices.remove(data_to_remove) 
                else:
                    old_lat_matrix = lattice_obj.matrix_world.copy()
                    lattice_obj.parent = None
                    lattice_obj.matrix_world = old_lat_matrix

            data_to_remove = grid_object.data
            bpy.data.objects.remove(grid_object)
            bpy.data.meshes.remove(data_to_remove)

    if reset_matrix:
        all_zeros = not np.any(source_obj.conform_object.original_matrix)

        if not all_zeros:    
            source_obj.matrix_world = source_obj.conform_object.original_matrix
    

    if set_active and target_obj and target_obj.name in bpy.data.objects:
        try:
            context.view_layer.objects.active = target_obj
        except RuntimeError:
            pass

    source_obj.conform_object.is_conform_obj = False

def conform_apply(source_obj, context):
    if not source_obj.conform_object.is_conform_obj:
        return

    source_obj.conform_object.is_conform_obj = False

    #apply subdivision modifier.
    if _subd_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_subd_mod_name])

    #apply the deform modifier.
    if _deform_mod_name in source_obj.modifiers:
        mod = source_obj.modifiers[_deform_mod_name]
        apply_modifier(source_obj, mod)

    #apply the transfer modifier.
    if _transfer_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_transfer_mod_name])

    # apply shrinkwrap modifier if preset. 
    if _deform_shrinkwrap_mod_name in source_obj.modifiers:
        apply_modifier(source_obj, source_obj.modifiers[_deform_shrinkwrap_mod_name])

    # remove any related vertex groups.
    if _conform_obj_group_name in source_obj.vertex_groups:
        source_obj.vertex_groups.remove(source_obj.vertex_groups[_conform_obj_group_name])

    # remove any related vertex groups.
    if _blend_obj_group_name in source_obj.vertex_groups:
        source_obj.vertex_groups.remove(source_obj.vertex_groups[_blend_obj_group_name])

    

    #remove grid object.
    grid_object = get_grid_obj(source_obj)
    if grid_object:
        # check all other objects in the scene to see if this is being used elsewhere.
        try:
            lattice_obj = get_lattice_obj(grid_object)
            if lattice_obj:
                data_to_remove = lattice_obj.data
                bpy.data.objects.remove(lattice_obj)
                bpy.data.lattices.remove(data_to_remove) 

            data_to_remove = grid_object.data
            bpy.data.objects.remove(grid_object)
            bpy.data.meshes.remove(data_to_remove)
        except ReferenceError:
            pass




class CONFORMOBJECT_OT_ConformUndo(bpy.types.Operator):
    """Conform Object"""
    bl_idname = "mesh.conform_object_undo"
    bl_label = "Undo Conform Object"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len([o for o in context.selected_objects if o.conform_object.is_conform_obj])


    def execute(self, context):
        source_objs = [o for o in context.selected_objects if o.conform_object.is_conform_obj]
        for source_obj in source_objs:
            conform_undo(source_obj, context)
            

        return {'FINISHED'}

class CONFORMOBJECT_OT_ConformApply(bpy.types.Operator):
    """Conform Object"""
    bl_idname = "mesh.conform_object_apply"
    bl_label = "Apply Conform Object"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and len([o for o in context.selected_objects if o.conform_object.is_conform_obj])


    def execute(self, context):
        source_objs = [o for o in context.selected_objects if o.conform_object.is_conform_obj]
        for source_obj in source_objs:
            conform_apply(source_obj, context)
            
        self.report({'INFO'}, "Conform modifiers have been applied to the object.")
        return {'FINISHED'}



class OBJECT_MT_conform_object(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_conform_object'
    bl_label = 'Conform Object'

    def draw(self, context):
        layout = self.layout
        layout.operator(CONFORMOBJECT_OT_Conform.bl_idname, icon='GP_MULTIFRAME_EDITING')
        layout.operator(CONFORMOBJECT_OT_ConformUndo.bl_idname, icon='MOD_INSTANCE')
        layout.operator(CONFORMOBJECT_OT_ConformApply.bl_idname, icon='MOD_THICKNESS')
        layout.separator()
        layout.operator(CONFORMOBJECT_OT_ToggleGridSnap.bl_idname, icon='SNAP_FACE')
        
        # layout.operator(CONFORMOBJECT_OT_Dig.bl_idname)


class CONFORMOBJECT_OT_ExpandCollapseUI(bpy.types.Operator):
    bl_idname = "conform_object.conform_expand_collapse"
    bl_label = "Expand and Collapse"

    bl_options = {'INTERNAL'}

    section_to_expand : StringProperty()

    description : StringProperty()


    @classmethod
    def description(self, context, properties):
        return properties.description

    def execute(self, context):
        setattr(context.window_manager.conform_object_ui, self.section_to_expand, not getattr(context.window_manager.conform_object_ui, self.section_to_expand))
        return {'FINISHED'}


class CONFORMOBJECT_OT_toggle_source_object_unselectable(bpy.types.Operator):
    bl_idname = "conform_object.toggle_active_unselectable"
    bl_label = "Toggle Source Object Unselectable"
    bl_description = "Make source object selectable or unselectable"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.lattice is not None and context.view_layer.objects.active and context.view_layer.objects.active.conform_object.source_obj

    def execute(self, context):

        # set outliner display.
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'OUTLINER':
                    for space in area.spaces:
                        if space.type == 'OUTLINER':
                            # now you can access space.show_restrict_column_select
                            space.show_restrict_column_select = True
                            break


        # Set active object unselectable
        hide_select = context.view_layer.objects.active.conform_object.source_obj.hide_select
        context.view_layer.objects.active.conform_object.source_obj.hide_select = not hide_select

        return {'FINISHED'}
    
class CONFORMOBJECT_OT_toggle_grid_visibility_from_source_object(bpy.types.Operator):
    bl_idname = "conform_object.toggle_grid_visibility_from_source_object"
    bl_label = "Toggle Grid Visibility"
    bl_description = "Make the grid object visible/invisible"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.conform_object.is_conform_obj

    def execute(self, context):

        for child in context.view_layer.objects.active.children:

            if child.conform_object.is_grid_obj:
                conform_grid_obj = child
                visible = not conform_grid_obj.hide_viewport
                conform_grid_obj.hide_set(visible) # EYE icon
                conform_grid_obj.hide_viewport = visible # MONITOR icon
                conform_grid_obj.hide_render = visible # RENDER icon

                return {'FINISHED'}
        return {'CANCELLED'}
    
class CONFORMOBJECT_OT_toggle_lattice_visibility_from_source_object(bpy.types.Operator):
    bl_idname = "conform_object.toggle_lattice_visibility_from_source_object"
    bl_label = "Toggle Grid Visibility"
    bl_description = "Make the lattice object visible/invisible"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.conform_object.is_conform_obj

    def execute(self, context):

        for child in context.view_layer.objects.active.children:
            if child.conform_object.is_grid_obj:
                for child2 in child.children:
                    if child2.type == 'LATTICE' and child2.conform_object.is_conform_lattice:
                        conform_lattice = child2
                        visible = not conform_lattice.hide_viewport
                        conform_lattice.hide_set(visible) # EYE icon
                        conform_lattice.hide_viewport = visible # MONITOR icon
                        conform_lattice.hide_render = visible # RENDER icon

                    return {'FINISHED'}
        return {'CANCELLED'}
        

class CONFORMOBJECT_OT_toggle_grid_visibility_from_lattice(bpy.types.Operator):
    bl_idname = "conform_object.toggle_grid_visibility_from_lattice"
    bl_label = "Toggle Grid Visibility"
    bl_description = "Make the grid object visible/invisible"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.lattice is not None and context.view_layer.objects.active and context.view_layer.objects.active.conform_object.source_obj

    def execute(self, context):

        if context.view_layer.objects.active.parent and context.view_layer.objects.active.parent.conform_object.is_grid_obj:
            conform_grid_obj = context.view_layer.objects.active.parent
            visible = not conform_grid_obj.hide_viewport
            conform_grid_obj.hide_set(visible) # EYE icon
            conform_grid_obj.hide_viewport = visible # MONITOR icon
            conform_grid_obj.hide_render = visible # RENDER icon


            return {'FINISHED'}
        return {'CANCELLED'}
        


def menu_func(self, context):
    self.layout.menu(OBJECT_MT_conform_object.bl_idname)

def menu_quick_func(self, context):
    self.layout.menu(OBJECT_MT_conform_object.bl_idname,icon='GP_MULTIFRAME_EDITING', text="" )

def conform_func(self, context):
    if hasattr(context, 'active_object') and context.active_object is not None and context.active_object.mode == 'OBJECT':
        col = self.layout.column()
        col.operator(CONFORMOBJECT_OT_Conform.bl_idname, icon='GP_MULTIFRAME_EDITING', text="")

def snap_func(self, context):
    col = self.layout.column()
    col.label(text="Conform Object")
    depressed = context.scene.tool_settings.use_snap and context.scene.tool_settings.snap_elements == {'FACE'} and \
                    context.scene.tool_settings.use_snap_align_rotation and context.scene.tool_settings.use_snap_project
    col.operator(CONFORMOBJECT_OT_ToggleGridSnap.bl_idname, icon='SNAP_FACE', depress=depressed)

classes = [
    CONFORMOBJECT_OT_Conform,
    CONFORMOBJECT_OT_ConformUndo,
    CONFORMOBJECT_OT_ConformApply,
    CONFORMOBJECT_OT_ToggleGridSnap,
    CONFORMOBJECT_OT_Dig,
    OBJECT_MT_conform_object,
    CONFORMOBJECT_OT_ExpandCollapseUI,
    CONFORMOBJECT_OT_toggle_source_object_unselectable,
    CONFORMOBJECT_OT_toggle_grid_visibility_from_source_object,
    CONFORMOBJECT_OT_toggle_grid_visibility_from_lattice,
    CONFORMOBJECT_OT_toggle_lattice_visibility_from_source_object]

def register():
    global classes
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)

    bpy.types.VIEW3D_PT_snapping.prepend(snap_func)
    bpy.types.VIEW3D_MT_editor_menus.append(menu_quick_func)

def unregister():
    global classes

    bpy.types.VIEW3D_MT_editor_menus.remove(menu_quick_func)
    bpy.types.VIEW3D_PT_snapping.remove(snap_func)

    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

    for cls in classes:
        unregister_class(cls)
