import bpy
import math
import numpy as np
import mathutils
import bmesh
from mathutils import Vector
from . import standard_greeble_objects, greeble_factory

from .. import preferences

import os

def get_greeble_object_args(greeble_settings):
    custom_object_args = []
    for i in range(0, len(greeble_settings)):
        custom_greeble_setting = greeble_settings[i]
        custom_object_arg = {
            "object_name" : getattr(custom_greeble_setting, "name"),
            "scene_ref" : getattr(custom_greeble_setting, "scene_ref"),
            "coverage" : getattr(custom_greeble_setting, "coverage"),
            "override_materials" : getattr(custom_greeble_setting, "override_materials"),
            "material_index" : getattr(custom_greeble_setting, "material_index"),
            "override_height" : getattr(custom_greeble_setting, "override_height"),
            "height_override" : getattr(custom_greeble_setting, "height_override"),
            "keep_aspect_ratio" : getattr(custom_greeble_setting, "keep_aspect_ratio")
        }
        custom_object_args.append(custom_object_arg)
    return custom_object_args

def greeble_gen_exec(self,obj,bm,context, seed=0):

    selected_faces = []
    for f in bm.faces:
        if f.select:
            selected_faces.append(f)
    if len(selected_faces) == 0:
        selected_faces.extend(bm.faces)
        
    #call the plate pattern generator.
    add_greebles(bm,
                    op=self,
                    context=context,
                    sourceMesh=obj.data,
                    faces=selected_faces,
                    no_of_greebles=self.greeble_amount,
                    greeble_random_seed=self.greeble_random_seed + seed,
                    library_greebles=self.library_greebles,
                    default_greeble_args=[],
                    custom_object_args=get_greeble_object_args(self.custom_greebles),
                    greeble_min_width=self.greeble_min_width,
                    greeble_max_width=self.greeble_max_width,
                    greeble_min_length=self.greeble_min_length,
                    greeble_max_length=self.greeble_max_length,
                    greeble_min_height=self.greeble_min_height,
                    greeble_max_height=self.greeble_max_height,
                    greeble_deviation=self.greeble_deviation,
                    greeble_subd_levels=self.greeble_subd_levels,
                    greeble_pattern_type=self.greeble_pattern_type,
                    coverage_amount=self.coverage_amount,
                    is_custom_normal_direction=self.is_custom_normal_direction,
                    custom_normal_direction=self.custom_normal_direction,
                    is_custom_rotation=self.is_custom_rotation,
                    custom_rotate_amount=self.custom_rotate_amount,
                    greeble_rotation_seed=self.greeble_rotation_seed,
                    add_vertex_colors_to_greebles=self.add_vertex_colors_to_greebles,
                    vertex_colors_random_seed= self.vertex_colors_random_seed,
                    vertex_colors_layer_name= self.vertex_colors_layer_name)

def generate_materials_map(sourceMesh, targetMesh):
    materialsMap = {}

    # targetMesh = kwargs['sourceMesh']
    # sourceMesh = new_object.data

    # Link any materials to the target that are linked to the source (without duplicating links).
    # Then, when we bring over the faces we'll also bring over the material assignments.
    for sourceMaterialIndex in range( len( sourceMesh.materials ) ):

        sourceMaterial = sourceMesh.materials[ sourceMaterialIndex ]
        targetHasMaterial = False

        for targetMaterialIndex in range( len( targetMesh.materials ) ):

            targetMaterial = targetMesh.materials[ targetMaterialIndex ]
            if sourceMaterial.name == targetMaterial.name:
                targetHasMaterial = True
                materialsMap[ sourceMaterialIndex ] = targetMaterialIndex
                break

        if not targetHasMaterial:
            materialsMap[ sourceMaterialIndex ] = len( targetMesh.materials )
            targetMesh.materials.append( sourceMaterial )

    return materialsMap

def _remove_object_data(obj):
    try:
        if obj.data:
            if obj.type == 'MESH':
                bpy.data.meshes.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)
            elif obj.type not in {'FONT', 'META', 'SURFACE', 'CURVE'}:
                getattr(bpy.data, '{}s'.format(obj.type.lower())).remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)

            elif obj.type in {'FONT', 'SURFACE', 'CURVE'}:
                bpy.data.curves.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)

            else:
                bpy.data.metaballs.remove(obj.data, do_unlink=True, do_id_user=True, do_ui_user=True)
    except: pass

def add_greebles(bm,
                faces=[],
                op=None,
                context=bpy.context,
                no_of_greebles=25,
                greeble_random_seed=123456,
                library_greebles=[],
                default_greeble_args=[],
                custom_object_args=[],
                greeble_min_width=0.2,
                greeble_max_width=0.8,
                greeble_min_length=0.2,
                greeble_max_length=0.8,
                greeble_min_height=0,
                greeble_max_height=0.1,
                **kwargs
                ):
    """Add Greebles to faces"""


    add_vertex_colors = kwargs['add_vertex_colors_to_greebles'] if 'add_vertex_colors_to_greebles' in kwargs else False
    vertex_colors_random_seed = kwargs['vertex_colors_random_seed'] if 'vertex_colors_random_seed' in kwargs else 0
    vertex_colors_layer_name = kwargs['vertex_colors_layer_name'] if 'vertex_colors_layer_name' in kwargs else ''


    #put all the greeble object properties into a list we can reference later.
    greeble_object_props = []
    greeble_object_props.clear()

    for default_greeble_arg in default_greeble_args:
        greeble_object_props.append({"name_prop": default_greeble_arg['object_name'],
                                        "coverage_prop": default_greeble_arg['coverage'],
                                        "override_materials" : default_greeble_arg['override_materials'],
                                        "material_index": default_greeble_arg['material_index'],
                                        "keep_aspect_ratio" : default_greeble_arg['keep_aspect_ratio'],
                                        "override_height" : default_greeble_arg['override_height'],
                                        "height_override" : default_greeble_arg['height_override'],
                                        "is_custom": False})

    for custom_object_arg in custom_object_args:
        object_name = custom_object_arg["scene_ref"]
        if object_name in context.scene.objects:
            

            greeble_object_props.append({"name_prop": object_name,
                                            "coverage_prop": custom_object_arg["coverage"],
                                            "override_height": custom_object_arg["override_height"],
                                            "height_override": custom_object_arg["height_override"],
                                            "override_materials": custom_object_arg["override_materials"],
                                            "material_index": custom_object_arg["material_index"],
                                            "keep_aspect_ratio" : custom_object_arg["keep_aspect_ratio"],
                                            "is_custom": True})

    # Load the custom greeble objects if any are set
    total_coverage = 0
    greeble_objects = {}

    greeble_meshes_to_remove = []

    for greeble_object_prop in greeble_object_props:
        object_name = greeble_object_prop['name_prop']
        if object_name != '':
            coverage = greeble_object_prop['coverage_prop']
            total_coverage+=coverage
            is_custom = greeble_object_prop['is_custom']
            if is_custom:
                #convert the vertices into world locations to assess orientation later.
                new_mesh = bpy.data.meshes.new("Greeble")
                new_object = None
                if object_name in context.scene.objects:
                    new_object = context.scene.objects[object_name]

                    # We need maintain a map between our source and target materials as we'll be merging, not
                    # simply appending like we do with the vertices and faces.
                    materialsMap = {}

                    if not greeble_object_prop['override_materials']:
                        materialsMap = generate_materials_map(new_object.data, kwargs['sourceMesh'])


                    try:
                        obj_mesh = new_object.to_mesh(preserve_all_data_layers=True, depsgraph=context.view_layer.depsgraph)


                        new_bm = bmesh.new()
                        new_bm.from_mesh(obj_mesh)#, settings='PREVIEW'))


                        for f in new_bm.faces:
                            f.select = False
                        new_bm.transform(new_object.matrix_world)
                        new_bm.to_mesh(new_mesh)
                        new_bm.free()
                        greeble_object_prop['object'] = new_object
                        greeble_object_prop['materialsMap'] = materialsMap
                        greeble_object_prop['object_data'] = new_mesh
                        greeble_object_prop['matrix_world'] = new_object.matrix_world
                    finally:
                        new_object.to_mesh_clear()

                greeble_meshes_to_remove.append(new_mesh)
            else:
                if object_name == 'Square':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_square_1_shape_greeble()
                elif object_name == 'Double Square':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_square_2_shape_greeble()
                elif object_name == 'Triple Square':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_square_3_shape_greeble()
                elif object_name == 'L Shape':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_L_shape_greeble()
                elif object_name == 'T Shape':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_T_shape_greeble()
                elif object_name == 'Cylinder':
                    greeble_object_prop['object_data'] = standard_greeble_objects.get_cylinder_greeble()

    p = []
    greeble_objects = []
    greeble_objects_to_remove = []

    try:
        pref = preferences.preference()
        catalogue = pref.catalogue

        
        for library_greeble in library_greebles:
            if getattr(library_greeble, 'category', None) is None or library_greeble.category == '':
                continue

            greeble_obj = greeble_factory.get_greeble_obj(library_greeble)
            if greeble_obj is None:
                new_greeble = greeble_factory.get_greebles_metadata_from_name_and_category(catalogue, library_greeble.thumbnail, library_greeble.category)
                if new_greeble is not None:
                    library_greeble.file_path = new_greeble.file_path
                    greeble_obj = greeble_factory.get_greeble_obj(library_greeble)

            greeble_objects_to_remove.append(greeble_obj)
            if greeble_obj is not None:
                materialsMap = {}
                if not library_greeble.override_materials:
                    materialsMap = generate_materials_map(greeble_obj.data, kwargs['sourceMesh'])
                
                greeble_objects.append(GreebleObject(None,
                                                None,
                                                greeble_obj.data,
                                                library_greeble.keep_aspect_ratio,
                                                materialsMap,
                                                None,
                                                library_greeble.override_height,
                                                library_greeble.height_override,
                                                library_greeble.override_materials,
                                                library_greeble.material_index,
                                                library_greeble.coverage,
                                                add_vertex_colors=add_vertex_colors,
                                                vertex_colors_random_seed= vertex_colors_random_seed,
                                                vertex_colors_layer_name= vertex_colors_layer_name
                                                ))
                total_coverage+=library_greeble.coverage
            else:
                if hasattr(op, 'report'):
                    op.report({'ERROR'}, 'Greeble object not loaded.')

        if total_coverage != 0:

            for greeble_object in greeble_objects:
                p.append(greeble_object.coverage / total_coverage)

            for greeble_object_prop in greeble_object_props:
                object_name = greeble_object_prop['name_prop']
                if object_name != '':
                    greeble_added = False
                    if 'object' in greeble_object_prop:
                        greeble_objects.append(GreebleObject(context.evaluated_depsgraph_get(),
                                                greeble_object_prop['object'],
                                                greeble_object_prop['object_data'],
                                                greeble_object_prop['keep_aspect_ratio'],
                                                greeble_object_prop['materialsMap'],
                                                greeble_object_prop['matrix_world'],
                                                greeble_object_prop['override_height'],
                                                greeble_object_prop['height_override'],
                                                greeble_object_prop['override_materials'],
                                                greeble_object_prop['material_index'],
                                                add_vertex_colors=add_vertex_colors,
                                                vertex_colors_random_seed= vertex_colors_random_seed,
                                                vertex_colors_layer_name= vertex_colors_layer_name
                                                ))

                    elif 'object_data' in greeble_object_prop:
                        greeble_objects.append(GreebleObject(None,
                                                                None,
                                                                greeble_object_prop['object_data'],
                                                                greeble_object_prop['keep_aspect_ratio'],
                                                                None,
                                                                None,
                                                                greeble_object_prop['override_height'],
                                                                greeble_object_prop['height_override'],
                                                                greeble_object_prop['override_materials'],
                                                                greeble_object_prop['material_index'],
                                                                add_vertex_colors=add_vertex_colors,
                                                                vertex_colors_random_seed= vertex_colors_random_seed,
                                                                vertex_colors_layer_name= vertex_colors_layer_name

                                                                ))


                    p.append(greeble_object_prop['coverage_prop'] / total_coverage)

            if len(greeble_objects) > 0:
                rng_pattern = np.random.RandomState(greeble_random_seed)
                rng_rotate = np.random.RandomState(kwargs['greeble_rotation_seed'])
                if (kwargs['greeble_pattern_type'] == '0'):
                    add_greebles_to_mesh(bm,
                                            faces=faces,
                                            greeble_objects=greeble_objects,
                                            p=p,
                                            no_of_greebles=no_of_greebles,
                                            rng_pattern=rng_pattern,
                                            greeble_min_width=greeble_min_width,
                                            greeble_max_width=greeble_max_width,
                                            greeble_min_length=greeble_min_length,
                                            greeble_max_length=greeble_max_length,
                                            greeble_min_height=greeble_min_height,
                                            greeble_max_height=greeble_max_height,
                                            is_custom_normal_direction=kwargs['is_custom_normal_direction'],
                                            custom_normal_direction=kwargs['custom_normal_direction'],
                                            is_custom_rotation=kwargs['is_custom_rotation'],
                                            custom_rotate_amount=kwargs['custom_rotate_amount'],
                                            rng_rotate=rng_rotate)
                elif (kwargs['greeble_pattern_type'] == '1'):
                    add_non_overlapping_greebles_to_mesh(bm,
                                                faces=faces,
                                                greeble_objects=greeble_objects,
                                                p=p,
                                                greeble_subd_levels=kwargs['greeble_subd_levels'],
                                                rng_pattern=rng_pattern,
                                                greeble_deviation=kwargs['greeble_deviation'],
                                                greeble_min_width=greeble_min_width,
                                                greeble_max_width=greeble_max_width,
                                                greeble_min_length=greeble_min_length,
                                                greeble_max_length=greeble_max_length,
                                                greeble_min_height=greeble_min_height,
                                                greeble_max_height=greeble_max_height,
                                                coverage_amount=kwargs['coverage_amount'],
                                                is_custom_normal_direction=kwargs['is_custom_normal_direction'],
                                                custom_normal_direction=kwargs['custom_normal_direction'],
                                                is_custom_rotation=kwargs['is_custom_rotation'],
                                                custom_rotate_amount=kwargs['custom_rotate_amount'],
                                                rng_rotate=rng_rotate)

    finally:
        for greeble_object_to_remove in greeble_objects_to_remove:
            _remove_object_data(greeble_object_to_remove)
            try:
                bpy.data.objects.remove(greeble_object_to_remove, do_unlink=True, do_id_user=True, do_ui_user=True)
            except: pass
        for greeble_mesh_to_remove in greeble_meshes_to_remove:
            bpy.data.meshes.remove(greeble_mesh_to_remove, do_unlink=True, do_id_user=True, do_ui_user=True)



def add_non_overlapping_greebles_to_mesh(bm,
                            faces=[],
                            greeble_objects=[],
                            p=[],
                            greeble_subd_levels=1,
                            rng_pattern=np.random.RandomState(12345),
                            greeble_deviation=0.5,
                            greeble_min_width=0.2,
                            greeble_max_width=0.8,
                            greeble_min_length=0.2,
                            greeble_max_length=0.8,
                            greeble_min_height=0,
                            greeble_max_height=0.1,
                            coverage_amount=50,
                            is_custom_normal_direction=False,
                            custom_normal_direction=Vector((0,0,1)),
                            is_custom_rotation=False,
                            custom_rotate_amount=0,
                            rng_rotate=np.random.RandomState(12345)):
    "Add greebles in a non overlapping pattern"
    if len(faces) == 0:
        return

    if greeble_subd_levels == 0:
        greeble_subd_amount = 0
    elif greeble_subd_levels >= 1:
        greeble_subd_amount = 4 ** (greeble_subd_levels - 1)
    else:
        return

    temp_bm = bmesh.new()

    all_rects = []

    for f in faces:
        if f.is_valid and len(f.loops) == 4:
            loop_a = f.loops[0]
            loop_b = loop_a.link_loop_next
            loop_c = loop_b.link_loop_next
            loop_d = loop_c.link_loop_next

            p0 = loop_a.vert.co
            p1 = loop_b.vert.co
            p2 = loop_c.vert.co
            p3 = loop_d.vert.co

            f_rect =  Rectangle3D(p0, p1, p2, p3, f.normal)

            rects = [f_rect]   # seed output list
            while len(rects) <= greeble_subd_amount:
                rects = [subrect for rect in rects
                                    for subrect in __quadsect(temp_bm,
                                                                rect,
                                                                rng_pattern,
                                                                greeble_deviation
                                                                )]
            all_rects.extend(rects)

    new_meshes = []
    i=0
    for rect in all_rects:

        if len(greeble_objects) != len(p):
            continue

        greeble_obj = rng_pattern.choice(greeble_objects, p=p)

        check_coverage = rng_pattern.random_sample() * 100

        width = rng_pattern.uniform(greeble_min_width, greeble_max_width)
        length = rng_pattern.uniform(greeble_min_length, greeble_max_length)

        new_height = rng_pattern.uniform(greeble_min_height, greeble_max_height)

        n = rng_rotate.randint(0,4)
        if is_custom_rotation:
            n = custom_rotate_amount % 4


        if check_coverage <= coverage_amount:

            loop_a = f.loops[0]
            loop_b = loop_a.link_loop_next
            loop_c = loop_b.link_loop_next
            loop_d = loop_c.link_loop_next

            p0 = rect.p0
            p1 = rect.p1
            p2 = rect.p2
            p3 = rect.p3

            x_lerp = (1 - width) / 2
            y_lerp = (1 - length) / 2

            center0_tmp = p0.lerp(p1, x_lerp)
            center1_tmp = p1.lerp(p0, x_lerp)
            center2_tmp = p2.lerp(p3, x_lerp)
            center3_tmp = p3.lerp(p2, x_lerp)

            center0 = center0_tmp.lerp(center3_tmp, y_lerp)
            center1 = center1_tmp.lerp(center2_tmp, y_lerp)
            center2 = center2_tmp.lerp(center1_tmp, y_lerp)
            center3 = center3_tmp.lerp(center0_tmp, y_lerp)

            transform_points = [center0, center1, center2, center3]

            normal = rect.normal
            if is_custom_normal_direction:
                normal = custom_normal_direction

            new_mesh = __graft_object(greeble_obj, normal, transform_points, new_height, n, i)
            new_meshes.append(new_mesh)
        i+=1

    for new_mesh in new_meshes:
        bm.from_mesh(new_mesh)
        bpy.data.meshes.remove(new_mesh)


    temp_bm.free()

def __quadsect(bm,
                rect,
                rng_pattern=np.random.RandomState(12345),
                greeble_deviation=0.5):
    """ Subdivide given rectangle into four non-overlapping rectangles.
        'greeble_deviation' is an integer representing the proportion of the width or
        height the deviatation from the center of the rectangle allowed.
    """
    deviation_start = 0.5 - (0.5 * greeble_deviation)
    deviation_end = 0.5 + (0.5 * greeble_deviation)

    slice_1_lerp = rng_pattern.uniform(deviation_start, deviation_end)
    slice_2_lerp = rng_pattern.uniform(deviation_start, deviation_end)

    p0 = rect.p0
    p1 = rect.p1
    p2 = rect.p2
    p3 = rect.p3

    point0 = p0.lerp(p1, slice_1_lerp)
    point1 = p1.lerp(p2, slice_2_lerp)
    point2 = p3.lerp(p2, slice_1_lerp)
    point3 = p0.lerp(p3, slice_2_lerp)

    # We are finding th emid point in the cross hairs of the face...
    #     |
    #     |
    # ----|-----
    #     |
    #     |

    intersection_tuple = mathutils.geometry.intersect_line_line(point0, point2, point3, point1)

    center = (intersection_tuple[0] + intersection_tuple[1]) / 2

    vert0 = p0
    vert_0_1_mid = point0
    vert1 = p1
    vert_1_2_mid = point1
    vert2 = p2
    vert_2_3_mid = point2
    vert3 = p3
    vert_3_0_mid = point3

    rect0 = Rectangle3D(vert0, vert_0_1_mid, center, vert_3_0_mid, rect.normal)
    rect1 = Rectangle3D(vert_0_1_mid, vert1, vert_1_2_mid, center, rect.normal)
    rect2 = Rectangle3D(center, vert_1_2_mid, vert2, vert_2_3_mid, rect.normal)
    rect3 = Rectangle3D(vert_3_0_mid, center, vert_2_3_mid, vert3, rect.normal)

    return [rect0,rect1,rect2,rect3]

def add_greebles_to_mesh(bm,
                            faces=[],
                            greeble_objects=[],
                            p=[],
                            no_of_greebles=1,
                            rng_pattern=np.random.RandomState(12345),
                            greeble_min_width=0.2,
                            greeble_max_width=0.8,
                            greeble_min_length=0.2,
                            greeble_max_length=0.8,
                            greeble_min_height=0,
                            greeble_max_height=0.1,
                            is_custom_normal_direction=False,
                            custom_normal_direction=Vector((0,0,1)),
                            is_custom_rotation=False,
                            custom_rotate_amount=0,
                            rng_rotate=np.random.RandomState(12345)):
    """Add Greeble object to a mesh"""
    if len(faces) == 0:
        return

    new_meshes = []
    for i in range(0, no_of_greebles):
        f = rng_pattern.choice(faces)
        greeble_obj = rng_pattern.choice(greeble_objects, p=p)


        if f.is_valid and len(f.loops) == 4:

            width = rng_pattern.uniform(greeble_min_width, greeble_max_width)
            length = rng_pattern.uniform(greeble_min_length, greeble_max_length)

            slice_1_lerp = rng_pattern.uniform(0, 1 - width)
            slice_2_lerp = slice_1_lerp + width
            slice_3_lerp = rng_pattern.uniform(0, 1 - length)
            slice_4_lerp = slice_3_lerp + length
            #loops
            # v3---a---v0
            # |       |
            # d       b
            # |       |
            # v2---c---v1

            loop_a = f.loops[0]
            loop_b = loop_a.link_loop_next
            loop_c = loop_b.link_loop_next
            loop_d = loop_c.link_loop_next

            v0 = loop_a.vert
            v1 = loop_b.vert
            v2 = loop_c.vert
            v3 = loop_d.vert

            slice1_a = v3.co.lerp(v0.co, slice_1_lerp)
            slice1_b = v2.co.lerp(v1.co, slice_1_lerp)
            slice2_a = v3.co.lerp(v0.co, slice_2_lerp)
            slice2_b = v2.co.lerp(v1.co, slice_2_lerp)

            # the following will make:
            # a-------b
            # |       |
            # |       |
            # |       |
            # d-------c
            point_a = slice1_a.lerp(slice1_b, slice_3_lerp)
            point_b = slice2_a.lerp(slice2_b, slice_3_lerp)
            point_c = slice2_a.lerp(slice2_b, slice_4_lerp)
            point_d = slice1_a.lerp(slice1_b, slice_4_lerp)


            transform_points = [point_a, point_b, point_c, point_d]

            new_height = rng_pattern.uniform(greeble_min_height, greeble_max_height)

            n = rng_rotate.randint(0,len(transform_points))
            if is_custom_rotation:
                n = custom_rotate_amount % len(transform_points)


            normal = f.normal
            if is_custom_normal_direction:
                normal = custom_normal_direction

            new_mesh = __graft_object(greeble_obj, normal, transform_points, new_height, n, i)
            new_meshes.append(new_mesh)

    for new_mesh in new_meshes:
        bm.from_mesh(new_mesh)
        bpy.data.meshes.remove(new_mesh)

    bm.normal_update()

def __graft_object(greeble_object, normal, transform_points, height, n, i):
    """align a given object to a cube shape defined by four transform points defining a square and a height"""
    transform_points = __shift(transform_points, n=n)

    new_mesh = bpy.data.meshes.new("Greeble")

    new_bm = greeble_object.new_bm()

    # todo could there be a cache of min max verts if we have done this already...?
    if len(new_bm.verts) > 0:
        new_bm.verts.ensure_lookup_table()
        verts = new_bm.verts

        #find origin point, which is bottom corner of object.
        # first_vert_co = verts[0].co
        x_min = greeble_object.x_min
        x_max = greeble_object.x_max
        y_min = greeble_object.y_min
        y_max = greeble_object.y_max
        z_min = greeble_object.z_min
        z_max = greeble_object.z_max

        # a-------b
        # |       |
        # |       |
        # |       |
        # d-------c

        #go through and for each vert, interpolate its location in the brave new world.
        x_diff = abs(x_max - x_min)
        y_diff = abs(y_max - y_min)
        z_diff = abs(z_max - z_min)

        point_a = Vector(transform_points[0])
        point_b = Vector(transform_points[1])
        point_c = Vector(transform_points[2])
        point_d = Vector(transform_points[3])

        if greeble_object.preserveAspectRatio:


            # adjust the transform points so they are in proportion...
            #first, find center of transform points
            findCenter = lambda l: ( max(l) + min(l) ) / 2

            x,y,z  = [ [ v[i] for v in transform_points ] for i in range(3) ]

            mid_transform_point = [ findCenter(axis) for axis in [x,y,z] ]
            mid_transform_point = Vector((mid_transform_point[0], mid_transform_point[1], mid_transform_point[2]))

            #get the closest point on the transform point square to that mid point...
            #Get longest diameter of transform points
            trans_diag_1_length = (point_a - point_c).length
            trans_diag_2_length = (point_b - point_d).length

            longest_diameter = max(trans_diag_1_length, trans_diag_2_length)

            top_edge_point_distance = mathutils.geometry.intersect_point_line(mid_transform_point, point_a, point_b)
            top_edge_point = top_edge_point_distance[0]
            vector_from_edge = (top_edge_point - mid_transform_point)
            vector_from_edge.normalize()
            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(45), 4, normal))
            diff = (vector_from_edge * (longest_diameter / 2))
            vector_from_edge_p1 = mid_transform_point + diff
            vector_from_edge_p2 = mid_transform_point - diff

            shortest_length = None
            transform_point_edges = [(point_a, point_b), (point_b, point_c), (point_c, point_d), (point_d, point_a)]
            for transform_point in transform_point_edges:
                closest_tuple = mathutils.geometry.intersect_line_line(vector_from_edge_p1, vector_from_edge_p2, transform_point[0], transform_point[1])
                try:
                    distance = (closest_tuple[0] - mid_transform_point).length
                except TypeError:
                    distance = 0
                if shortest_length is None or distance < shortest_length:
                    shortest_length = distance
            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(90), 4, normal))
            diff = (vector_from_edge * (longest_diameter / 2))
            vector_from_edge_p1 = mid_transform_point + diff
            vector_from_edge_p2 = mid_transform_point - diff

            for transform_point in transform_point_edges:
                closest_tuple = mathutils.geometry.intersect_line_line(vector_from_edge_p1, vector_from_edge_p2, transform_point[0], transform_point[1])
                try:
                    distance = (closest_tuple[0] - mid_transform_point).length
                except TypeError:
                    distance = 0
                if shortest_length is None or distance < shortest_length:
                    shortest_length = distance
            top_edge_point = top_edge_point_distance[0]
            vector_from_edge = (top_edge_point - mid_transform_point)

            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(-45), 4, normal))
            vector_from_edge.normalize()
            point_a = mid_transform_point + (vector_from_edge * shortest_length)
            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(90), 4, normal))
            point_b = mid_transform_point + (vector_from_edge * shortest_length)
            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(90), 4, normal))
            point_c = mid_transform_point + (vector_from_edge * shortest_length)
            vector_from_edge.rotate(mathutils.Matrix.Rotation(math.radians(90), 4, normal))
            point_d = mid_transform_point + (vector_from_edge * shortest_length)

            # check aspect ratio of original object and adjust accordingly.
            if x_diff < y_diff:
                ratio = (1 - (x_diff / y_diff)) / 2
                new_point_a = point_a.lerp(point_b, ratio)
                new_point_b = point_b.lerp(point_a, ratio)
                new_point_c = point_c.lerp(point_d, ratio)
                new_point_d = point_d.lerp(point_c, ratio)
            else:
                ratio = (1 - (y_diff / x_diff)) / 2
                new_point_a = point_a.lerp(point_d, ratio)
                new_point_d = point_d.lerp(point_a, ratio)
                new_point_b = point_b.lerp(point_c, ratio)
                new_point_c = point_c.lerp(point_b, ratio)
            point_a = new_point_a
            point_b = new_point_b
            point_c = new_point_c
            point_d = new_point_d

            # sort out heights.
            length1 = (point_a - point_b).length
            length2 = (point_b - point_c).length
            total_diffs = x_diff + y_diff + z_diff
            proportion_square = (x_diff + y_diff) / total_diffs
            some_length = (length1 + length2) / ((x_diff + y_diff) / total_diffs)
            height = some_length - length1 - length2

        if greeble_object.override_height:
            height = greeble_object.height_override

        for v in verts:
            co = v.co

            if x_diff > 0:
                x_lerp = (co.x - x_min) / x_diff
            else:
                x_lerp = 0
            if y_diff > 0:
                y_lerp = (co.y - y_min) / y_diff
            else:
                y_lerp = 0
            if z_diff > 0:
                z_lerp = (co.z - z_min) / z_diff
            else:
                z_lerp = 0

            #now work out where the point will be in the new world.
            line_start = point_a.lerp(point_b, x_lerp)
            line_end = point_d.lerp(point_c, x_lerp)
            base_point = line_start.lerp(line_end, y_lerp)
            new_coord = base_point.lerp(base_point + (normal*height), z_lerp)

            v.co = new_coord

        for f in new_bm.faces:
            f.select_set(False)




    if greeble_object.add_vertex_colors:
        vertex_colors_random_seed = greeble_object.vertex_colors_random_seed
        vertex_colors_layer_name = greeble_object.vertex_colors_layer_name

        # add vertex colors
        if vertex_colors_layer_name not in new_bm.loops.layers.color:
            color_layer = new_bm.loops.layers.color.new(vertex_colors_layer_name)
        else:
            color_layer = new_bm.loops.layers.color.get(vertex_colors_layer_name)
        rng_vertex_color = np.random.RandomState(vertex_colors_random_seed + i)
        def random_color(alpha=1):
            return [rng_vertex_color.uniform(0, 1) for c in "rgb"] + [alpha]

        random_col = random_color()
        for f in new_bm.faces:
            for loop in f.loops:
                loop[color_layer] = random_col


    new_bm.to_mesh(new_mesh)
    new_bm.free()

    return new_mesh


def __shift(seq, n=0):
    """shift a list a given amount"""
    a = n % len(seq)
    return seq[-a:] + seq[:-a]


class GreebleObject:

    def __init__(self, 
                    depsgraph, 
                    object, 
                    meshObject, 
                    preserveAspectRatio, 
                    materialsMap, 
                    matrix_world, 
                    override_height, 
                    height_override, 
                    override_materials, 
                    material_index, 
                    coverage=100, 
                    add_vertex_colors=False,
                    vertex_colors_random_seed=123456,
                    vertex_colors_layer_name=''
                    ):
        self.meshObject = meshObject    # instance variable unique to each instance
        self.preserveAspectRatio = preserveAspectRatio
        #find origin point, which is bottom corner of object.
        first_vert_co = meshObject.vertices[0].co
        self.x_min = first_vert_co[0]
        self.x_max = first_vert_co[0]
        self.y_min = first_vert_co[1]
        self.y_max = first_vert_co[1]
        self.z_min = first_vert_co[2]
        self.z_max = first_vert_co[2]
        # for v in verts:
        for i in range(1, len(meshObject.vertices)):
            co = meshObject.vertices[i].co
            if co[0] < self.x_min:
                self.x_min = co[0]
            if co[0] > self.x_max:
                self.x_max = co[0]
            if co[1] < self.y_min:
                self.y_min = co[1]
            if co[1] > self.y_max:
                self.y_max = co[1]
            if co[2] < self.z_min:
                self.z_min = co[2]
            if co[2] > self.z_max:
                self.z_max = co[2]

        self.__bm = bmesh.new()
        if depsgraph is None and object is None:
            self.__bm.from_mesh(meshObject)
        else:
            self.__bm.from_object(object, depsgraph)

        if override_materials or (materialsMap is not None and len(materialsMap) > 0):
            for f in self.__bm.faces:
                if override_materials:
                    f.material_index = material_index
                elif (materialsMap is not None and len(materialsMap) > 0):
                    f.material_index = materialsMap[ f.material_index ]

        if matrix_world is not None:
            for v in self.__bm.verts:
                v.co = matrix_world @ v.co

        self.override_materials = override_materials
        self.override_height = override_height
        self.height_override = height_override
        self.coverage = coverage

        self.add_vertex_colors = add_vertex_colors
        self.vertex_colors_random_seed= vertex_colors_random_seed
        self.vertex_colors_layer_name= vertex_colors_layer_name

    def new_bm(self):
        return self.__bm.copy()

    def __del__(self):
        if self.__bm is not None:
            self.__bm.free()
      # body of destructor

class Rectangle3D:


    def __init__(self, p0, p1, p2, p3, normal):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.normal = normal
