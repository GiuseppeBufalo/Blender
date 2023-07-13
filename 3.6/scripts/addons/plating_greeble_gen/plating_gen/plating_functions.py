import bpy
import bmesh
import numpy as np
import mathutils
from mathutils import Vector
from random import uniform, choice
import functools
from math import ceil, radians, degrees

def getMaterialId(materials, material_name):
    if material_name is None or material_name == "":
        return -1
    material_id = 0
    for material in materials:
        if material.name == material_name:
            return material_id
        material_id+=1
    #if we got this far we need to either assign or create the material.
    found_material = False
    for material in bpy.data.materials:
        if material.name == material_name:
            # assign the material.
            materials.append(material)
            found_material = True
            break
    if not found_material:
        material = bpy.data.materials.new(name=material_name)
        
    return material_id

def deal_with_materials(self, obj):
    plating_mat_ids = []
    for plating_material in self.plating_materials:
        if plating_material.name != "":
            plating_material_id = getMaterialId(obj.data.materials, plating_material.name)
            plating_mat_ids.append(plating_material_id)

    groove_material_id = -1
    if self.groove_material != "":
        groove_material_id = getMaterialId(obj.data.materials, self.groove_material)

    return plating_mat_ids, groove_material_id

def plating_gen_exec(self, obj, bm, context, seed=0):
    # deal with materials.
    plating_mat_ids, groove_material_id = deal_with_materials(self, obj)

    #call the plate pattern generator.
    create_plates(bm,
                            pattern_type=self.pattern_type,
                            random_seed = self.random_seed + seed,
                            amount = self.amount,
                            pre_subdivisions = self.pre_subdivisions,
                            triangle_random_seed = self.triangle_random_seed + seed,
                            triangle_percentage= self.triangle_percentage,
                            ruby_dragon_random_seed = self.ruby_dragon_random_seed + seed,
                            ruby_dragon_percentage= self.ruby_dragon_percentage,
                            edge_selection_only = self.edge_selection_only,
                            cut_at_faces=self.cut_at_faces,
                            face_angle_limit=self.face_angle_limit,
                            face_angle_dev=self.face_angle_dev,
                            groove_width = self.groove_width,
                            clamp_grooves = self.clamp_grooves,
                            plate_taper = self.plate_taper,
                            groove_depth = self.groove_depth,
                            plate_min_height = self.plate_min_height,
                            plate_max_height = self.plate_max_height,
                            bevel_amount = self.bevel_amount,
                            plate_height_random_seed = self.plate_height_random_seed + seed,
                            groove_bevel_amount = self.groove_bevel_amount,
                            bevel_segments = self.bevel_segments,
                            bevel_outer_bevel_type = self.bevel_outer_bevel_type,
                            groove_bevel_segments = self.groove_bevel_segments,
                            groove_bevel_outer_bevel_type = self.groove_bevel_outer_bevel_type,
                            side_segments = self.side_segments,
                            groove_segments = self.groove_segments,
                            corner_width=self.corner_width,
                            minor_corner_width=self.minor_corner_width,
                            corner_bevel_segments=self.corner_bevel_segments,
                            corner_outer_bevel_type=self.corner_outer_bevel_type,
                            minor_corner_bevel_segments=self.minor_corner_bevel_segments,
                            minor_corner_outer_bevel_type=self.corner_outer_bevel_type,
                            remove_grooves=self.remove_grooves,
                            edge_split=self.edge_split,
                            mark_seams=self.mark_seams,
                            use_rivets=self.use_rivets,
                            rivet_corner_distance=self.rivet_corner_distance,
                            rivet_subdivisions=self.rivet_subdivisions,
                            rivet_diameter=self.rivet_diameter,
                            rivet_material_index=self.rivet_material_index,
                            select_grooves=self.select_grooves,
                            select_plates=self.select_plates,
                            plating_material_ids=plating_mat_ids,
                            plating_materials_random_seed = self.plating_materials_random_seed + seed,
                            groove_material_id=groove_material_id,
                            add_vertex_colors_to_plates=self.add_vertex_colors_to_plates,
                            vertex_colors_random_seed=self.vertex_colors_random_seed,
                            vertex_colors_layer_name=self.vertex_colors_layer_name,
                            remove_inner_grooves=self.remove_inner_grooves,
                            rectangle_random_seed=self.rectangle_random_seed + seed,
                            rectangle_amount=self.rectangle_amount,
                            rectangle_width_min=self.rectangle_width_min,
                            rectangle_width_max=self.rectangle_width_max,
                            rectangle_height_min=self.rectangle_height_min,
                            rectangle_height_max=self.rectangle_height_max,
                            context=context
                            )            



def plating_gen_execute(self, context):
    if self.update_draw_only:
        self.update_draw_only = False
        return {'PASS_THROUGH'}

    if bpy.ops.object.mode_set.poll():
        #capture previous edit mode
        previous_mode = context.active_object.mode
        previous_edit_mode = list(context.tool_settings.mesh_select_mode)

        # Switching to EDIT edge mode
        bpy.ops.object.mode_set(mode = 'EDIT')

        # read mesh data
        obj = context.edit_object
        me = obj.data

        bm = bmesh.from_edit_mesh(me)

        plating_gen_exec(self, obj, bm, context)
        
        # update the bmmesh
        bmesh.update_edit_mesh(obj.data)
        # NOTE: bm does not need to be freed, see https://developer.blender.org/T39121


        #reset to previous mode
        if not self.edge_selection_only:
            context.tool_settings.mesh_select_mode = previous_edit_mode
        else:
            context.tool_settings.mesh_select_mode = (False, True, False)

        bpy.ops.object.mode_set(mode = previous_mode)
        return {'FINISHED'}
    return {'CANCELLED'}


def generate_plate_selection_pattern(bm, 
                                        faces, 
                                        random_seed, 
                                        amount, 
                                        face_selected_prop, 
                                        groove_edge_marked_prop, 
                                        use_tris=False,
                                        triangle_random_seed=1234567,
                                        triangle_percentage=0):
    """Generate a plating pattern over existing edge geometry."""
    #create a list of edges to return
    edges_to_return = []

	#mark the boundary edges as in the grooves.
    for f in faces:
        for e in f.edges:
            for f1 in e.link_faces:
                if not f1[face_selected_prop]:
                    e[groove_edge_marked_prop] = 1
                    edges_to_return.append(e)
                    edges_to_return.append(e.verts[0])
                    edges_to_return.append(e.verts[1])

    #seed this randomly
    rng_pattern = np.random.RandomState(random_seed)

    #iteratively split up the mesh by selecting an edge loop at random,
    #split it, and then randomly selecting another to be split, and so on.
    if use_tris:
        rng_tri_pattern = np.random.RandomState(triangle_random_seed)
    for x in range(0, amount):
        #select random edge
        bm.edges.ensure_lookup_table()
        current_edge = rng_pattern.choice(rng_pattern.choice(faces).edges)

        if not use_tris:
            edges_to_return.extend(__mark_groove_edges(bm, current_edge, groove_edge_marked_prop))
        else: 
            edges_to_return.extend(__mark_groove_edges_tris(bm, current_edge, groove_edge_marked_prop, triangle_random_seed, triangle_percentage, rng_tri_pattern))

    return edges_to_return


def generate_plate_selection_pattern_rectangular(bm, 
                                        faces, 
                                        random_seed, 
                                        amount, 
                                        face_selected_prop, 
                                        groove_edge_marked_prop,
                                        use_tris=False,
                                        triangle_random_seed=1234567,
                                        triangle_percentage=0,
                                        rectangle_random_seed=12345,
                                        rectangle_amount=50,
                                        rectangle_width_min=5,
                                        rectangle_width_max=15,
                                        rectangle_height_min=5,
                                        rectangle_height_max=15):
    """Generate a plating pattern over existing edge geometry."""
    #create a list of edges to return
    edges_to_return = []

	#mark the boundary edges as in the grooves.
    for f in faces:
        for e in f.edges:
            for f1 in e.link_faces:
                if not f1[face_selected_prop]:
                    e[groove_edge_marked_prop] = 1
                    edges_to_return.append(e)
                    edges_to_return.append(e.verts[0])
                    edges_to_return.append(e.verts[1])

    #seed this randomly
    rng_pattern = np.random.RandomState(rectangle_random_seed)

    if use_tris:
        rng_tri_pattern = np.random.RandomState(triangle_random_seed)

    #iteratively create rectangles around the mesh
    for x in range(0, rectangle_amount):
        #select random edge
        bm.edges.ensure_lookup_table()
        current_edge = rng_pattern.choice(rng_pattern.choice(faces).edges)
        edges_to_return.extend(__mark_groove_edges_rectangular(bm, current_edge, groove_edge_marked_prop, face_selected_prop, rng_pattern, rectangle_width_min, rectangle_width_max, rectangle_height_min, rectangle_height_max))

    rng_pattern = np.random.RandomState(random_seed)
    
    #iteratively create rectangles around the mesh
    for x in range(0, amount):
        #select random edge
        bm.edges.ensure_lookup_table()
        current_edge = rng_pattern.choice(rng_pattern.choice(faces).edges)

        if not use_tris:
            edges_to_return.extend(__mark_groove_edges(bm, current_edge, groove_edge_marked_prop))
        else: 
            edges_to_return.extend(__mark_groove_edges_tris(bm, current_edge, groove_edge_marked_prop, triangle_random_seed, triangle_percentage, rng_tri_pattern))
        
    return edges_to_return

zero_bevel_temp_width = 0.0001
zero_bevel_temp_remove_dist = zero_bevel_temp_width * 10

def create_plates(bm,
                        pattern_type='0',
                        random_seed = 12345,
                        triangle_random_seed = 12345,
                        triangle_percentage= 0.0,
                        ruby_dragon_random_seed = 12345,
                        ruby_dragon_percentage= 50,
                        amount = 50,
                        pre_subdivisions = 0,
                        edge_selection_only = False,
                        cut_at_faces = True,
                        face_angle_limit = 90,
                        face_angle_dev=0.1,
                        groove_width = 0.01,
                        clamp_grooves = False,
                        plate_taper = 0.000,
                        groove_depth = 0.01,
                        plate_min_height = 0.000,
                        plate_max_height = 0.000,
                        bevel_amount = 0.000,
                        plate_height_random_seed = 12345,
                        groove_bevel_amount = 0.000,
                        bevel_segments = 1,
                        bevel_outer_bevel_type = 'OFFSET',
                        groove_bevel_segments = 1,
                        groove_bevel_outer_bevel_type = 'OFFSET',
                        side_segments = 1,
                        groove_segments = 1,
                        corner_width=0.0,
                        minor_corner_width=0.0,
                        corner_bevel_segments=1,
                        corner_outer_bevel_type='OFFSET',
                        minor_corner_bevel_segments=1,
                        minor_corner_outer_bevel_type='OFFSET',
                        remove_grooves=False,
                        edge_split=False,
                        mark_seams=False,
                        use_rivets=False,
                        rivet_corner_distance=0.05,
                        rivet_subdivisions=1,
                        rivet_diameter=0.01,
                        rivet_material_index=-1,
                        select_grooves=False,
                        select_plates=True,
                        plating_material_ids=[],
                        plating_materials_random_seed = 12345,
                        groove_material_id=-1,
                        add_vertex_colors_to_plates=False,
                        vertex_colors_random_seed=12345,
                        vertex_colors_layer_name="plating_color",
                        remove_inner_grooves = False,
                        rectangle_random_seed=12345,
                        rectangle_amount=50,
                        rectangle_width_min=5,
                        rectangle_width_max=15,
                        rectangle_height_min=5,
                        rectangle_height_max=15,
                        context=bpy.context,
                            sourceMesh=None,
                            greeble_func=None,
                            op=None,
                            greeble_random_seed=123456,
                            greeble_plates=True,
                            greeble_sides=False,
                            greeble_grooves=False,
                            greeble_amount=25,
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
    """Create the 3d plates on the mesh topology"""

    #set up custom data layer for tracking the edge groove pattern
    face_selected_prop = bm.faces.layers.int.new('face_selected')
    groove_face_prop = bm.faces.layers.int.new('groove_face')
    groove_inner_face_prop = bm.faces.layers.int.new('groove_inner_face')
    plate_face_prop = bm.faces.layers.int.new('plate_face')
    plate_face_group_prop = bm.faces.layers.int.new('plate_face_group')
    plate_inner_face_prop = bm.faces.layers.int.new('plate_inner_face')
    plate_side_face_prop = bm.faces.layers.int.new('plate_side_face')
    groove_edge_marked_prop = bm.edges.layers.int.new('groove_edge_marked')
    groove_and_side_face_prop = bm.faces.layers.int.new('groove_and_side_face')
    corner_vert_prop = bm.verts.layers.int.new('corner_vert')
    main_corner_vert_prop = bm.verts.layers.int.new('main_corner_vert')
    subd_vert_prop = bm.verts.layers.int.new('subd_vert')
    

    bm.faces.ensure_lookup_table()

    #capture the selected faces
    selected_faces = []
    is_face_selection_present = False

    def sort_f_func(f):
        summed = f.calc_center_median()
        return (summed[0], summed[1], summed[2])

    edges_pattern = []
    if pattern_type == '0':

        #capture any faces already selected
        for f in bm.faces:
            if f.select:
                is_face_selection_present = True
                f[face_selected_prop] = 1
                selected_faces.append(f)
                f.select = False

        if not is_face_selection_present:
            for f in bm.faces:
                f[face_selected_prop] = 1
            selected_faces = bm.faces[:]

        if len(selected_faces) == 0:
            return

        edges = []
        for f in selected_faces:
            edges.extend(f.edges)
        edges = list(set(edges))
        result = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=pre_subdivisions, use_grid_fill=True, use_only_quads=False, smooth=0.0)

        for v in result['geom_inner']:
            if isinstance(v, bmesh.types.BMVert):
                v[subd_vert_prop] = 1
        
        selected_faces = []
        #capture any faces already selected
        for f in bm.faces:
            if f[face_selected_prop]:
                selected_faces.append(f)
        selected_faces.sort(key=sort_f_func)

        selected_edges = []
        for f in selected_faces:
            for e in f.edges:
                selected_edges.append(e)
        selected_edges = list(set(selected_edges))

        amount_edges = int((amount / 100) * len(selected_edges))

        #generate the plate selection pattern.
        edges_pattern = generate_plate_selection_pattern(bm, selected_faces, random_seed, amount_edges, face_selected_prop, groove_edge_marked_prop)
    elif pattern_type == '1':
        for e in bm.edges:
            if e.select:
                e[groove_edge_marked_prop] = 1
                edges_pattern.append(e)
                edges_pattern.append(e.verts[0])
                edges_pattern.append(e.verts[1])
                e.select = False
        
    elif pattern_type == '5':
        for e in bm.edges:
            if e.seam:
                e[groove_edge_marked_prop] = 1
                edges_pattern.append(e)
                edges_pattern.append(e.verts[0])
                edges_pattern.append(e.verts[1])
    elif pattern_type == '6':
        # Ruby Dragon
        #capture any faces already selected
        for f in bm.faces:
            if f.select:
                is_face_selection_present = True
                f[face_selected_prop] = 1
                selected_faces.append(f)
                f.select = False

        if not is_face_selection_present:
            for f in bm.faces:
                f[face_selected_prop] = 1
            selected_faces = bm.faces[:]

        if len(selected_faces) == 0:
            return

        edges = []
        for f in selected_faces:
            edges.extend(f.edges)
        edges = list(set(edges))
        result = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=pre_subdivisions, use_grid_fill=True, use_only_quads=False, smooth=0.0)

        for v in result['geom_inner']:
            if isinstance(v, bmesh.types.BMVert):
                v[subd_vert_prop] = 1

        selected_faces = []
        #capture any faces already selected
        for f in bm.faces:
            if f[face_selected_prop]:
                selected_faces.append(f)
        selected_faces.sort(key=sort_f_func)


        edges_pattern = ruby_dragon(bm, selected_faces, ruby_dragon_percentage, ruby_dragon_random_seed)
        
    elif pattern_type == '2':
        #Standard pattern with triangles
        #capture any faces already selected
        for f in bm.faces:
            if f.select:
                is_face_selection_present = True
                f[face_selected_prop] = 1
                selected_faces.append(f)
                f.select = False

        if not is_face_selection_present:
            for f in bm.faces:
                f[face_selected_prop] = 1
            selected_faces = bm.faces[:]

        if len(selected_faces) == 0:
            return

        edges = []
        for f in selected_faces:
            edges.extend(f.edges)
        edges = list(set(edges))
        selected_faces.sort(key=sort_f_func)
        result = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=pre_subdivisions, use_grid_fill=True, use_only_quads=False, smooth=0.0)

        for v in result['geom_inner']:
            if isinstance(v, bmesh.types.BMVert):
                v[subd_vert_prop] = 1

        selected_faces = []
        #capture any faces already selected
        for f in bm.faces:
            if f[face_selected_prop]:
                selected_faces.append(f)
        selected_faces.sort(key=sort_f_func)

        selected_edges = []
        for f in selected_faces:
            for e in f.edges:
                selected_edges.append(e)
        selected_edges = list(set(selected_edges))

        amount_edges = int((amount / 100) * len(selected_edges))

        #generate the plate selection pattern.
        edges_pattern = generate_plate_selection_pattern(bm, selected_faces, random_seed, amount_edges, face_selected_prop, groove_edge_marked_prop, True, triangle_random_seed, triangle_percentage)
    elif pattern_type == '3' or pattern_type == '4':
        #capture any faces already selected
        for f in bm.faces:
            if f.select:
                is_face_selection_present = True
                f[face_selected_prop] = 1
                selected_faces.append(f)
                f.select = False

        if not is_face_selection_present:
            for f in bm.faces:
                f[face_selected_prop] = 1
            selected_faces = bm.faces[:]

        if len(selected_faces) == 0:
            return

        edges = []
        for f in selected_faces:
            edges.extend(f.edges)
        edges = list(set(edges))
        result = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=pre_subdivisions, use_grid_fill=True, use_only_quads=False, smooth=0.0)

        for v in result['geom_inner']:
            if isinstance(v, bmesh.types.BMVert):
                v[subd_vert_prop] = 1

        selected_faces = []
        #capture any faces already selected
        for f in bm.faces:
            if f[face_selected_prop]:
                selected_faces.append(f)

        selected_faces.sort(key=sort_f_func)
        
        #generate the plate selection pattern.
        if pattern_type == '3':
            edges_pattern = generate_plate_selection_pattern_rectangular(bm, 
                                                                        selected_faces, 
                                                                        random_seed, 
                                                                        0, 
                                                                        face_selected_prop,
                                                                        groove_edge_marked_prop,
                                                                        False, 
                                                                        0, 
                                                                        0,
                                                                        rectangle_random_seed,
                                                                        rectangle_amount,
                                                                        rectangle_width_min,
                                                                        rectangle_width_max,
                                                                        rectangle_height_min,
                                                                        rectangle_height_max)
        elif pattern_type == '4':
            selected_edges = []
            for f in selected_faces:
                for e in f.edges:
                    selected_edges.append(e)
            selected_edges = list(set(selected_edges))

            amount_edges = int((amount / 100) * len(selected_edges))
            edges_pattern = generate_plate_selection_pattern_rectangular(bm, 
                                                                        selected_faces, 
                                                                        random_seed, 
                                                                        amount_edges, 
                                                                        face_selected_prop,
                                                                        groove_edge_marked_prop,
                                                                        True, 
                                                                        triangle_random_seed, 
                                                                        triangle_percentage,
                                                                        rectangle_random_seed,
                                                                        rectangle_amount,
                                                                        rectangle_width_min,
                                                                        rectangle_width_max,
                                                                        rectangle_height_min,
                                                                        rectangle_height_max)

    # also add any edges that give off an angle.
    if cut_at_faces and pattern_type not in {'1','5'}:
        edged_edges = []
        for e in bm.edges:
            found = False
            for f in e.link_faces:
                if f[face_selected_prop]:
                    found=True
                    break
            if not found:
                continue
            angle = e.calc_face_angle(None)
            if angle:
                lower_limit = face_angle_limit * (1-face_angle_dev)
                upper_limit = face_angle_limit * (1+face_angle_dev)
                if angle > radians(lower_limit) and  angle < radians(upper_limit):
                    edged_edges.append(e)

        edges_pattern.extend(edged_edges)


    #if we are only to output the edge selection, we are finished.
    if edge_selection_only:
        for e in edges_pattern:
            if isinstance(e, bmesh.types.BMEdge):
                e.select = True
    else:
        #determine main corners in the selection
        main_corner_vert_id = 0
        for v in edges_pattern:
            # Only check for corners on non-subdivided edges, as they can only be on ones that aren't subdivided.
            if isinstance(v, bmesh.types.BMVert) and not v[subd_vert_prop]:
                #is this a main corner? ie a vertex with two edges that share a face
                edge_count = 0
                face_indexes = []
                for e in v.link_edges:
                    if e[groove_edge_marked_prop] == 1:
                        edge_count+=1
                        for f in e.link_faces:
                            face_indexes.append(f.index)
                if len(face_indexes) > len(list(set(face_indexes))):
                    #if there are only two edges, mark this as a main corner
                    if edge_count == 2:
                        main_corner_vert_id += 1
                        v[main_corner_vert_prop] = main_corner_vert_id


        #nasty hack if the width is zero.  This will then be resolved by remove_doubles at end of method.
        groove_width_to_bevel = groove_width
        #bevel the edges to form the grooves.
        if groove_width == 0:
            groove_width_to_bevel = zero_bevel_temp_width

        if bpy.app.version < (2, 90, 0):
            bevelled_edges = bmesh.ops.bevel(bm,
                                            geom=list(set(edges_pattern)),
                                            offset=groove_width_to_bevel,
                                            segments=1,
                                            offset_type='OFFSET',
                                            vertex_only=False,
                                            clamp_overlap=clamp_grooves,
                                            profile=0.5,
                                            loop_slide=True,
                                            material=-1)
        else:
            bevelled_edges = bmesh.ops.bevel(bm,
                                            geom=list(set(edges_pattern)),
                                            offset=groove_width_to_bevel,
                                            segments=1,
                                            offset_type='OFFSET',
                                            affect='EDGES',
                                            clamp_overlap=clamp_grooves,
                                            profile=0.5,    
                                            loop_slide=True,
                                            material=-1)


        

        #now the grooves are created, create a list of all the faces to inset for the plates.
        faces_to_inset = []
        for f in bevelled_edges['faces']:
            faces_to_inset.append(f)        
            f[groove_face_prop] = 1
            f[groove_inner_face_prop] = 1
            for e in f.edges:
                e[groove_edge_marked_prop] = 0
        groove_verts = []
        #now everything is marked, determine grooves by determining adjacent faces.  More efficient than
        #checking the faces are contained in the whole selection.
        for f in bevelled_edges['faces']:
            for loop in f.loops:
                adjacent_f = loop.link_loop_radial_next.face
                if not adjacent_f[groove_face_prop]:
                    loop.edge[groove_edge_marked_prop] = 1
                    groove_verts.append(loop.edge.verts[0])
                    groove_verts.append(loop.edge.verts[1])

        bm.verts.ensure_lookup_table()
        corner_vert_id = main_corner_vert_id + 1
        #mark minor corners
        for v in groove_verts:
            #is this a corner? ie a vertex with two edges that share a face

            # only do the minor corner if it is healthily surrounded by quads or tris,
            # suggesting it is safely within the bounds of the selection.
            valid = True
            for f in v.link_faces:
                if len(f.edges) > 4:
                    valid = False
                    break
            if not valid:
                continue

            edge_count = 0
            face_indexes = []
            for e in v.link_edges:
                if e[groove_edge_marked_prop] == 1:
                    edge_count+=1
                    for f in e.link_faces:
                        face_indexes.append(f.index)
            if len(face_indexes) > len(list(set(face_indexes))):
                #mark the general corners
                corner_vert_id += 1
                v[corner_vert_prop] = corner_vert_id

        #inset to create the grooves.
        bm.faces.ensure_lookup_table()
        result = bmesh.ops.inset_region(bm, faces=faces_to_inset, thickness=plate_taper, depth=0, use_even_offset=True, use_outset=True, use_boundary=True )


        #the inset operation will have created the sides of the plates. Mark them as so.
        for f in result['faces']:
            f[groove_face_prop] = 0
            f[groove_inner_face_prop] = 0
            f[plate_side_face_prop] = 1

        #we can now determine which edges are around the outside of the plates.
        bm.faces.ensure_lookup_table()
        plate_tops = []

        groove_faces = []
        plate_verts = []
        for f in bm.faces:
            #mark the faces if they are not grooves or side plates, depending on whether
            #there was a selection in the first place. if there was, it depends if it was marked.
            #if there wasn't, just mark the plate as selected.
            if ((not is_face_selection_present) or f[face_selected_prop]) and \
                (not (f[groove_face_prop] or f[plate_side_face_prop])):
                f[plate_face_prop] = 1
                f[plate_inner_face_prop] = 1
                plate_tops.append(f)
            elif f[groove_face_prop]:
                groove_faces.append(f)

        #__shrink_fatten the faces using a custom function (inset operation produces bad geometry).
        __shrink_fatten(bm, groove_faces, -groove_depth)

        # Group faces.
        face_groups = []


        #if the min and max height values are other than zero, randomly adjust the heights of the plates
        if (plate_min_height != 0 or plate_max_height != 0):

            rng_plate_heights = np.random.RandomState(plate_height_random_seed)

             
            #traverse around each plate face and assemble them into groups
            __find_face_groups(plate_tops, face_groups, plate_face_prop, plate_face_group_prop)
            plates = []
            # order face groups by their total area.
            def sort_func(fg):
                summed = sum([f.calc_center_median() for f in fg], Vector()) / len(fg)
                return (summed[0], summed[1], summed[2])

            # face_groups.sort(key=lambda fg: sum([f.calc_area() for f in fg]))
            face_groups.sort(key=sort_func)

            for face_group in face_groups:
                height = rng_plate_heights.uniform(plate_min_height, plate_max_height)

                __shrink_fatten(bm, face_group, height)
                
                
        # add vertex colors
        if add_vertex_colors_to_plates:
            if vertex_colors_layer_name not in bm.loops.layers.color:
                color_layer = bm.loops.layers.color.new(vertex_colors_layer_name)
            else:
                color_layer = bm.loops.layers.color.get(vertex_colors_layer_name)
            rng_vertex_color = np.random.RandomState(vertex_colors_random_seed)
            def random_color(alpha=1):
                return [rng_vertex_color.uniform(0, 1) for c in "rgb"] + [alpha]

            __find_face_groups(plate_tops, face_groups, plate_face_prop, plate_face_group_prop)
            for face_group in face_groups:
                side_faces = bmesh.ops.region_extend(bm, geom=face_group, use_faces=True)['geom']
                face_group_sides = []
                face_group_sides.extend(face_group)
                face_group_sides.extend(side_faces)
                

                random_col = random_color()
                for f in face_group_sides:
                    for loop in f.loops:
                        loop[color_layer] = random_col
        
        # Add plate materials
        if len(plating_material_ids) > 0:
            rng_pattern_plate_mats = np.random.RandomState(plating_materials_random_seed)
            __find_face_groups(plate_tops, face_groups, plate_face_prop, plate_face_group_prop)
            for face_group in face_groups:
                side_faces = bmesh.ops.region_extend(bm, geom=face_group, use_faces=True)['geom']
                face_group_sides = []
                face_group_sides.extend(face_group)
                face_group_sides.extend(side_faces)

                material_id = rng_pattern_plate_mats.choice(plating_material_ids)
                for f in face_group_sides:
                    f.material_index = material_id
        
        # Add groove materials
        if groove_material_id > -1:
            for f in groove_faces:
                f.material_index = groove_material_id


        #perform a bevel on the outer plates and/or grooves if necessary
        # find the grooves and select one more.
        plate_edges_to_bevel = []
        groove_edges_to_bevel = []
        if bevel_amount > 0.000 or groove_bevel_amount > 0.000:
            bm.faces.ensure_lookup_table()
            faces_to_extend = []
            for f in bm.faces:
                if f[groove_face_prop] == 1:
                    faces_to_extend.append(f)

            result = bmesh.ops.region_extend(bm, geom=faces_to_extend, use_faces=True)['geom']
            faces_to_extend.extend(result)

            #identify the edges to bevel.
            for f in result:
                for loop in f.loops:
                    adjacent_f = loop.link_loop_radial_next.face
                    if not (adjacent_f[groove_face_prop] or adjacent_f[plate_side_face_prop]):
                        plate_edges_to_bevel.append(loop.edge)
                        plate_edges_to_bevel.append(loop.edge.verts[0])
                        plate_edges_to_bevel.append(loop.edge.verts[1])



            #bevel the outside of the plates.
            if bpy.app.version < (2, 90, 0):
                bevelled_plate_edges = bmesh.ops.bevel(bm,
                                                geom=list(set(plate_edges_to_bevel)),
                                                offset=bevel_amount,
                                                segments=bevel_segments,
                                                offset_type=bevel_outer_bevel_type,
                                                vertex_only=False,
                                                clamp_overlap=False,
                                                profile=0.5,
                                                loop_slide=True,
                                                material=-1)
            else:
                bevelled_plate_edges = bmesh.ops.bevel(bm,
                                                geom=list(set(plate_edges_to_bevel)),
                                                offset=bevel_amount,
                                                segments=bevel_segments,
                                                offset_type=bevel_outer_bevel_type,
                                                affect='EDGES',
                                                clamp_overlap=False,
                                                profile=0.5,
                                                loop_slide=True,
                                                material=-1)

            #mark the resulted bevel as plates, not sides.
            for f in bevelled_plate_edges['faces']:
                f[plate_face_prop] = 1
                f[plate_inner_face_prop] = 0
                f[plate_side_face_prop] = 0

            for f in bm.faces:
                if f[groove_face_prop] == 1:
                    for loop in f.loops:
                        adjacent_f = loop.link_loop_radial_next.face
                        if adjacent_f[plate_side_face_prop] == 1:
                            groove_edges_to_bevel.append(loop.edge)
                            groove_edges_to_bevel.append(loop.edge.verts[0])
                            groove_edges_to_bevel.append(loop.edge.verts[1])

            #bevel the outside of the plates.
            if bpy.app.version < (2, 90, 0):
                bevelled_plate_edges = bmesh.ops.bevel(bm,
                                                geom=list(set(groove_edges_to_bevel)),
                                                offset=groove_bevel_amount,
                                                segments=groove_bevel_segments,
                                                offset_type=groove_bevel_outer_bevel_type,
                                                vertex_only=False,
                                                clamp_overlap=False,
                                                profile=0.5,
                                                loop_slide=True,
                                                material=-1)
            else:
                bevelled_plate_edges = bmesh.ops.bevel(bm,
                                                geom=list(set(groove_edges_to_bevel)),
                                                offset=groove_bevel_amount,
                                                segments=groove_bevel_segments,
                                                offset_type=groove_bevel_outer_bevel_type,
                                                affect='EDGES',
                                                clamp_overlap=False,
                                                profile=0.5,
                                                loop_slide=True,
                                                material=-1)

            #mark the resulted bevel as grooves, not sides.
            for f in bevelled_plate_edges['faces']:
                f[groove_face_prop] = 1
                f[groove_inner_face_prop] = 0
                f[plate_side_face_prop] = 0

        #segment the sides and/or grooves of the plates if necessary.
        if side_segments > 1 or groove_segments > 1:
            bm.faces.ensure_lookup_table()
            side_edges_to_subdivide = []
            groove_edges_to_subdivide = []
            #find the edges that need to be sibdivided.
            for f in bm.faces:
                if f[plate_side_face_prop]:
                    for loop in f.loops:
                        if loop.link_loop_radial_next.face[plate_side_face_prop]:
                            side_edges_to_subdivide.append(loop.edge)
                if f[groove_inner_face_prop]:
                    for loop in f.loops:
                        if loop.link_loop_radial_next.face[groove_inner_face_prop]:
                            groove_edges_to_subdivide.append(loop.edge)
            #subdivide sides.
            bmesh.ops.subdivide_edges(bm, edges=list(set(side_edges_to_subdivide)), cuts=side_segments-1, use_grid_fill=True, use_only_quads=False, smooth=0.0)
            #subbdivide grooves.
            result = bmesh.ops.subdivide_edges(bm, edges=list(set(groove_edges_to_subdivide)), cuts=groove_segments-1, use_grid_fill=True, use_only_quads=False, smooth=0.0)
            for v in result['geom']:
                if isinstance(v, bmesh.types.BMVert):
                    v[corner_vert_prop] = 0

        #apply a greeble function if needed...
        if greeble_func != None:
            greeble_faces = []
            for f in bm.faces:
                if greeble_plates and f[plate_inner_face_prop]:
                    greeble_faces.append(f)
                if greeble_sides and f[plate_side_face_prop]:
                    greeble_faces.append(f)
                if greeble_grooves and f[groove_inner_face_prop]:
                    greeble_faces.append(f)
            greeble_func(bm,
                                        context=context,
                                        op=op,
                                        sourceMesh=sourceMesh,
                                        faces=greeble_faces,
                                        no_of_greebles=greeble_amount,
                                        greeble_random_seed=greeble_random_seed,
                                        library_greebles=library_greebles,
                                        custom_object_args=custom_object_args,
                                        greeble_min_width=greeble_min_width,
                                        greeble_max_width=greeble_max_width,
                                        greeble_min_length=greeble_min_length,
                                        greeble_max_length=greeble_max_length,
                                        greeble_min_height=greeble_min_height,
                                        greeble_max_height=greeble_max_height,
                                        greeble_deviation=kwargs['greeble_deviation'],
                                        greeble_subd_levels=kwargs['greeble_subd_levels'],
                                        greeble_pattern_type=kwargs['greeble_pattern_type'],
                                        coverage_amount=kwargs['coverage_amount'],
                                        is_custom_normal_direction=kwargs['is_custom_normal_direction'],
                                        custom_normal_direction=kwargs['custom_normal_direction'],
                                        is_custom_rotation=kwargs['is_custom_rotation'],
                                        custom_rotate_amount=kwargs['custom_rotate_amount'],
                                        greeble_rotation_seed=kwargs['greeble_rotation_seed'])

        #bevel the main corners of the plates if necessary.
        if corner_width > 0 or minor_corner_width > 0:
            #find all the corners and bevel them if needed
            #find the grooves and select one more.
            bm.edges.ensure_lookup_table()

            major_corners_to_bevel = {}
            minor_corners_to_bevel = {}

            #find the main corners that are not connected to one another and share a uniquie id.
            for e in bm.edges:

                if corner_width > 0 and \
                    ((e.verts[0][main_corner_vert_prop] and e.verts[1][main_corner_vert_prop]) and \
                    (e.verts[0][main_corner_vert_prop] == e.verts[1][main_corner_vert_prop])):
                    prop_id = e.verts[0][main_corner_vert_prop]
                    #group the corners to bevel by the id of the main corner.
                    if not prop_id in major_corners_to_bevel:
                        major_corners_to_bevel[prop_id] = []
                    major_corners_to_bevel[prop_id].append(e)
                    major_corners_to_bevel[prop_id].append(e.verts[0])
                    major_corners_to_bevel[prop_id].append(e.verts[1])
                if minor_corner_width > 0 and \
                    ((not (e.verts[0][main_corner_vert_prop] and e.verts[1][main_corner_vert_prop])) and \
                    (e.verts[0][corner_vert_prop] and e.verts[1][corner_vert_prop]) and \
                    (e.verts[0][corner_vert_prop] == e.verts[1][corner_vert_prop])):
                    prop_id = e.verts[0][corner_vert_prop]
                    if not prop_id in minor_corners_to_bevel:
                        minor_corners_to_bevel[prop_id] = []
                    minor_corners_to_bevel[prop_id].append(e)
                    minor_corners_to_bevel[prop_id].append(e.verts[0])
                    minor_corners_to_bevel[prop_id].append(e.verts[1])


            #if there are any major corners to bevel, do this.
            for key, corner_edges in major_corners_to_bevel.items():
                if len(corner_edges) > 0:
                    if bpy.app.version < (2, 90, 0):
                        result = bevelled_corner_edges = bmesh.ops.bevel(bm,
                                                        geom=list(set(corner_edges)),
                                                        offset=corner_width,
                                                        segments=corner_bevel_segments,
                                                        offset_type=corner_outer_bevel_type,
                                                        vertex_only=False,
                                                        clamp_overlap=False,
                                                        profile=0.5,
                                                        loop_slide=True,
                                                        material=-1)
                    else:
                        result = bevelled_corner_edges = bmesh.ops.bevel(bm,
                                                        geom=list(set(corner_edges)),
                                                        offset=corner_width,
                                                        segments=corner_bevel_segments,
                                                        offset_type=corner_outer_bevel_type,
                                                        affect='EDGES',
                                                        clamp_overlap=False,
                                                        profile=0.5,
                                                        loop_slide=True,
                                                        material=-1)

                    for f in result['faces']:
                        adjacent_groove_count = 0
                        for loop in f.loops:
                            if not (loop.link_loop_radial_next.face[groove_face_prop] or \
                                loop.link_loop_radial_next.face[plate_side_face_prop]):
                                adjacent_groove_count += 1
                        if adjacent_groove_count == 3:
                            f[groove_face_prop] = 0
                            f[groove_inner_face_prop] = 0
                            f[plate_side_face_prop] = 0

            #if there are any minor corners to bevel, do this.
            for key, corner_edges in minor_corners_to_bevel.items():
                if len(corner_edges) > 0:
                    if bpy.app.version < (2, 90, 0):
                        result = bevelled_corner_edges = bmesh.ops.bevel(bm,
                                                        geom=list(set(corner_edges)),
                                                        offset=minor_corner_width,
                                                        segments=minor_corner_bevel_segments,
                                                        offset_type=minor_corner_outer_bevel_type,
                                                        vertex_only=False,
                                                        clamp_overlap=False,
                                                        profile=0.5,
                                                        loop_slide=True,
                                                        material=-1)
                    else:
                        result = bevelled_corner_edges = bmesh.ops.bevel(bm,
                                                        geom=list(set(corner_edges)),
                                                        offset=minor_corner_width,
                                                        segments=minor_corner_bevel_segments,
                                                        offset_type=minor_corner_outer_bevel_type,
                                                        affect='EDGES',
                                                        clamp_overlap=False,
                                                        profile=0.5,
                                                        loop_slide=True,
                                                        material=-1)
                    for f in result['faces']:
                        adjacent_groove_count = 0
                        for loop in f.loops:
                            if loop.link_loop_radial_next.face[groove_inner_face_prop]:
                                adjacent_groove_count += 1
                        if adjacent_groove_count == 3:
                            f[groove_face_prop] = 1
                            f[groove_inner_face_prop] = 1
                        if len(f.edges) == 3: #  hack but appears to remove inner grooves when corners are bevelled.
                            f[groove_face_prop] = 1
                            f[groove_inner_face_prop] = 1

        #delete grooves if required.
        if remove_grooves:
            bm.faces.ensure_lookup_table()
            #inner_grooves = [f for f in bm.faces if f[groove_inner_face_prop]]
            #result = inner_grooves + bmesh.ops.region_extend(bm, geom=inner_grooves, use_faces=True)['geom']
            result = [f for f in bm.faces if f[groove_face_prop] or f[plate_side_face_prop]]
            bmesh.ops.delete(bm, geom=result, context='FACES')

        #if groove width was actually zero, we need to try and make amends and remove doubles.
        if groove_width == 0:
            groove_verts_dedupe = []
            for f in bm.faces:
                if f[groove_face_prop]:
                    for v in f.verts:
                        groove_verts_dedupe.append(v)
            bmesh.ops.remove_doubles(bm, verts=list(set(groove_verts_dedupe)), dist=zero_bevel_temp_width*10)

        #perform split operations if required.
        if (edge_split or mark_seams):
            # find the grooves and select one more.
            bm.faces.ensure_lookup_table()
            edges_to_mark = []
            faces_to_extend = []
            for f in bm.faces:
                if f[groove_inner_face_prop] == 1:
                    for loop in f.loops:
                        if loop.link_loop_radial_next.face[groove_inner_face_prop] == 0:
                            loop.edge.seam=mark_seams
                            edges_to_mark.append(loop.edge)
                if f[groove_face_prop] == 1:
                    faces_to_extend.append(f)
                    for loop in f.loops:
                        if loop.link_loop_radial_next.face[groove_face_prop] == 0:
                            loop.edge.seam=mark_seams
                            edges_to_mark.append(loop.edge)

            for i in range(side_segments):
                result = bmesh.ops.region_extend(bm, geom=faces_to_extend, use_faces=True)['geom']
                for f in result:
                    f[groove_and_side_face_prop] = 1
                faces_to_extend.extend(result)

            #mark seams
            for f in result:
                for loop in f.loops:
                    if loop.link_loop_radial_next.face[groove_and_side_face_prop] == 0:
                        loop.edge.seam=mark_seams

            #split edges
            if edge_split:

                #split around the edges if necessary.
                for f in result:
                    for loop in f.loops:
                        if loop.link_loop_radial_next.face[groove_and_side_face_prop] == 0:
                            edges_to_mark.append(loop.edge)

                #if we have also bevelled the plates, extend to this region as well.
                if bevel_amount > 0:
                    for i in range(bevel_segments):
                        result = bmesh.ops.region_extend(bm, geom=faces_to_extend, use_faces=True)['geom']
                        for f in result:
                            f[groove_and_side_face_prop] = 1
                        faces_to_extend.extend(result)

                    for f in result:
                        for loop in f.loops:
                            if loop.link_loop_radial_next.face[groove_and_side_face_prop] == 0:
                                edges_to_mark.append(loop.edge)

                #if necessary also add any corners to split.
                bm.edges.ensure_lookup_table()
                for e in bm.edges:
                    if ((corner_width > 0) and \
                        (e.verts[0][main_corner_vert_prop] and e.verts[1][main_corner_vert_prop])) or \
                        ((minor_corner_width > 0) and \
                        (e.verts[0][corner_vert_prop] and e.verts[1][corner_vert_prop])):
                            #ignore corners as they are bevelled
                        continue
                    if minor_corner_width == 0 and \
                        (e.verts[0][corner_vert_prop] and e.verts[1][corner_vert_prop]) and \
                        (e.verts[0][corner_vert_prop] == e.verts[1][corner_vert_prop]):
                        edges_to_mark.append(e)

                bmesh.ops.split_edges(bm, edges = list(set(edges_to_mark)))

        if use_rivets:
            #add in rivets...
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            rivet_coords = {}
            for v in bm.verts:
                if v[corner_vert_prop] or v[main_corner_vert_prop]:
                    for f in v.link_faces:
                        if f[plate_inner_face_prop]:
                            av_edge_vec = Vector((0,0,0))
                            av_edge_count = 0
                            for e in f.edges:
                                if e.verts[0].index == v.index:
                                    av_edge_count += 1
                                    av_edge_vec += (e.verts[1].co - e.verts[0].co).normalized()
                                if e.verts[1].index == v.index:
                                    av_edge_count += 1
                                    av_edge_vec += (e.verts[0].co - e.verts[1].co).normalized()
                            av_edge_vec = (av_edge_vec / av_edge_count).normalized()
                            rivet_coord = v.co + (av_edge_vec * rivet_corner_distance)
                            mat_loc = mathutils.Matrix.Translation(rivet_coord)

                            corner_id = 0
                            #we are assuming the ids are unique
                            if v[corner_vert_prop]:
                                corner_id = v[corner_vert_prop]
                            if v[main_corner_vert_prop]:
                                corner_id = v[main_corner_vert_prop]

                            corner_id = str(f.index) + '-' + str(corner_id)

                            if not corner_id in rivet_coords:
                                rivet_coords[corner_id] = []

                            rivet_coords[corner_id].append(rivet_coord)

            #now we know all this, create the rivets
            for key, corner_coords in rivet_coords.items():
                rivet_coord = functools.reduce(lambda x, y: x + y, corner_coords) / len(corner_coords)
                mat_loc = mathutils.Matrix.Translation(rivet_coord)
                if bpy.app.version >= (3, 0, 0):
                    result = bmesh.ops.create_icosphere(bm, subdivisions=rivet_subdivisions, radius=rivet_diameter, matrix=mat_loc, calc_uvs = False)
                else:
                    result = bmesh.ops.create_icosphere(bm, subdivisions=rivet_subdivisions, diameter=rivet_diameter, matrix=mat_loc, calc_uvs = False)
                if rivet_material_index > -1:
                    for v in result['verts']:
                        for f in v.link_faces:
                            f.material_index = rivet_material_index


        #ensure all grooves are selected.
        bm.faces.ensure_lookup_table()
        groove_faces = []

        # Final cleanup
        for f in bm.faces:
            f.select = (select_grooves and f[groove_face_prop]) or (select_plates and f[plate_face_prop])
            # fix material assignment in grooves.
            if f[groove_face_prop] and groove_material_id > -1:
                f.material_index = groove_material_id

    # remove the very inside of the groove, ignoring bevels.
    if remove_inner_grooves:
        groove_faces = []
        for f in bm.faces:
            if f[groove_face_prop]:
                groove_faces.append(f)
        if groove_bevel_amount > 0:
            for i in range(0, groove_bevel_segments):
                region_reduced = bmesh.ops.region_extend(bm, geom=groove_faces, use_contract=True, use_faces=True)['geom']
                for f in region_reduced:
                    groove_faces.remove(f)

        bmesh.ops.delete(bm, geom=groove_faces, context='FACES')

    #tidy up for when creating a separate object. #TODO not ideal that the function knows about this property.
    if 'face_was_not_selected_prop' in bm.faces.layers.int:
        face_was_not_selected_prop = bm.faces.layers.int.get('face_was_not_selected_prop')
        for f in bm.faces:
            if f[groove_face_prop]:
                f[face_was_not_selected_prop] = 0

    #remove custom data layers for tracking the edge groove pattern TODO this code caused a dramatic shipwright crash, re-instate when safe to do so.
    # bm.faces.layers.int.remove(face_selected_prop)
    # bm.faces.layers.int.remove(groove_face_prop)
    # bm.faces.layers.int.remove(groove_inner_face_prop)
    # bm.faces.layers.int.remove(plate_face_prop)
    # bm.faces.layers.int.remove(plate_face_group_prop)
    # bm.faces.layers.int.remove(plate_inner_face_prop)
    # bm.faces.layers.int.remove(plate_side_face_prop)
    # bm.edges.layers.int.remove(groove_edge_marked_prop)
    # bm.faces.layers.int.remove(groove_and_side_face_prop)
    # bm.verts.layers.int.remove(corner_vert_prop)
    # bm.verts.layers.int.remove(main_corner_vert_prop)
    # bm.verts.layers.int.remove(subd_vert_prop)



                

def __shrink_fatten(bm, faces, amount):
    """Custom function to perform shrink and fatten operations"""

    
    verts = {}
    for f in faces:
        for v in f.verts:
            if v in verts:
                verts[v].append(f)
            else:
                verts[v] = [f]

    for v in verts:
        unique_faces = verts[v]
        normals = [f.normal for f in unique_faces]
        if len(normals) > 0:
            av_normal = normals[0]
            for normal in normals[1:]:
                av_normal = av_normal + normal
            av_normal = av_normal / len(normals)
            v.co += amount * av_normal.normalized()

    bm.normal_update()

def __find_face_groups(plate_tops, face_groups, plate_face_prop, plate_face_group_prop):

    if len(face_groups) > 0:
        return

    for f in plate_tops:
        face_group = []
        __find_face_group(f, face_group, plate_face_prop, plate_face_group_prop)
        if len(face_group) > 0:
            face_groups.append(face_group)


def __find_face_group(f, face_group, plate_face_prop, plate_face_group_prop):
    """Used to find a group of faces for the plates."""
    #just return if this face has already been marked.
    if f[plate_face_group_prop] == 1 or f[plate_face_prop] == 0:
        return
    #otherwise, add this to the following list.
    f[plate_face_group_prop] = 1
    faces_to_find = [f]

    while (len(faces_to_find) > 0):
        next_faces_to_find = []
        for new_face in faces_to_find:
            face_group.append(new_face)

            for v in new_face.verts:
                for link_face in v.link_faces:
                    if link_face[plate_face_group_prop] == 0 and link_face[plate_face_prop] == 1:
                        link_face[plate_face_group_prop] = 1
                        next_faces_to_find.append(link_face)

        faces_to_find = next_faces_to_find

def __mark_groove_edges(bm, e, groove_edge_marked_prop):
    """Go through and mark the edges around a groove."""
    edges_to_return = []

    if e[groove_edge_marked_prop] | e.is_boundary:
        return edges_to_return


    e[groove_edge_marked_prop] = 1
    edges_to_return.append(e)
    edges_to_return.append(e.verts[0])
    edges_to_return.append(e.verts[1])

    # get BMLoop that points to the right direction
    for loop in e.link_loops:
        if len(loop.vert.link_edges) == 4:
            next_loop = loop
            while len(next_loop.vert.link_edges) == 4:

                #are we about to cross a groove boundary? If so, break out of the loop.
                groove_count = 0
                for edge_to_check in next_loop.vert.link_edges:
                    if edge_to_check[groove_edge_marked_prop]:
                        groove_count+=1
                if groove_count > 1:
                    break

                #this is a direction we can go in
                next_loop = next_loop.link_loop_prev.link_loop_radial_prev.link_loop_prev

                edge_to_mark = next_loop.edge

                if edge_to_mark[groove_edge_marked_prop] | edge_to_mark.is_boundary:
                    break
                else:
                    edge_to_mark[groove_edge_marked_prop] = 1
                    edges_to_return.append(edge_to_mark)
                    edges_to_return.append(edge_to_mark.verts[0])
                    edges_to_return.append(edge_to_mark.verts[1])

    return edges_to_return


def __mark_groove_edges_tris(bm, e, groove_edge_marked_prop, triangle_random_seed, triangle_percentage, rng_pattern):
    """Go through and mark the edges around a groove as per usual, but add in some triangular edges."""
    edges_to_return = []

    if e[groove_edge_marked_prop] | e.is_boundary:
        return edges_to_return

    

    e[groove_edge_marked_prop] = 1
    edges_to_return.append(e)
    edges_to_return.append(e.verts[0])
    edges_to_return.append(e.verts[1])

    faces_to_be_cut = []
    face_edgenet = []

    precentage = triangle_percentage / 100
    p = [1 - precentage, precentage]

    # get BMLoop that points to the right direction
    e_link_loops = e.link_loops
    for loop in e_link_loops:
        if len(loop.vert.link_edges) == 4:
            next_loop = loop
            while len(next_loop.vert.link_edges) == 4:

                #are we about to cross a groove boundary? If so, break out of the loop.
                groove_count = 0
                for edge_to_check in next_loop.vert.link_edges:
                    if edge_to_check[groove_edge_marked_prop]:
                        groove_count+=1
                if groove_count > 1:
                    break
                                            
                #this is a direction we can go in
                default_loop = next_loop.link_loop_prev.link_loop_radial_prev.link_loop_prev
                if (rng_pattern.choice([True, False], p=p)):
                    # This just needs to be the standard criss cross pattern.
                    next_loop = default_loop
                else:
                    #triangles
                    #First, see if a triangle is feasible (ie does not bump into corners)
                    vertA, vertB, test_loop, face_to_cut = __can_make_tri(next_loop, groove_edge_marked_prop, rng_pattern)
                    # If we have a vert to create with...
                    if vertA is not None:
                        # ... create the triangle.
                        faces_to_be_cut.append(face_to_cut)
                        edge = bm.edges.new([vertA, vertB])
                        face_edgenet.append((face_to_cut, edge))
                        # sometimes the next loop ('test loop') will be reported as None to say the next loop is not viable.
                        # in cases like this, we have probably hit a boundary se we can exit out the loop.
                        if test_loop is not None:
                            next_loop = test_loop
                        else:
                            break
                    else:
                        # if we failed to find a feasible triangle, continue as per default criss-cross pattern
                        next_loop = default_loop
                    

                edge_to_mark = next_loop.edge

                if edge_to_mark[groove_edge_marked_prop] | edge_to_mark.is_boundary:
                    break
                else:
                    edge_to_mark[groove_edge_marked_prop] = 1
                    edges_to_return.append(edge_to_mark)
                    edges_to_return.append(edge_to_mark.verts[0])
                    edges_to_return.append(edge_to_mark.verts[1])

    for face_edge in face_edgenet:
        bmesh.utils.face_split_edgenet(face_edge[0], [face_edge[1]])
        face_edge[1][groove_edge_marked_prop] = 1
        edges_to_return.append(face_edge[1])
        edges_to_return.append(face_edge[1].verts[0])
        edges_to_return.append(face_edge[1].verts[1])
                
    return edges_to_return


def __can_make_tri(next_loop, groove_edge_marked_prop, rng_pattern):
    """Can we make a triangle?  If so, return relevant information"""
    can_make = False

    # First, go either 'left' or 'right' by traversing the loops.
    vertA = next_loop.vert
    if rng_pattern.choice([True, False]):
        test_loop = next_loop.link_loop_prev.link_loop_radial_prev.link_loop_next.link_loop_radial_prev
        face_to_cut = next_loop.link_loop_prev.link_loop_radial_prev.link_loop_next.face
    else:
        test_loop = next_loop.link_loop_radial_prev.link_loop_next.link_loop_radial_prev.link_loop_prev
        face_to_cut = next_loop.link_loop_radial_prev.link_loop_next.link_loop_radial_prev.face
    
    vertB = test_loop.vert

    # Sometimes if we have, say, hit an edge, we may be accidentally creating an existing edge.  Exit out and report back this is not feasible.
    for edge_test in vertA.link_edges:
        for edge_test2 in vertB.link_edges:
            if edge_test == edge_test2:
                return (None, None, None, None)

    #are we about to cross a groove boundary? If so, break out of the loop the next time round by indicating a None next_loop.
    groove_count = 0
    for edge_to_check in test_loop.vert.link_edges:
        if edge_to_check[groove_edge_marked_prop]:
            groove_count+=1
    if groove_count > 1:
        return (vertA, vertB, None, face_to_cut)

    # if we are all good, prepare the next loop for processing.
    test_loop = test_loop.link_loop_prev.link_loop_radial_prev.link_loop_prev

    return (vertA, vertB, test_loop, face_to_cut)

def __traverse_length(loop, length, groove_edge_marked_prop, edges_to_return, mark_edge):
    i = 0
    edges_to_return_tmp = []
    next_loop = loop
    
    # mark_edge = True
    while len(next_loop.vert.link_edges) == 4 and i < length:
        edge_to_mark = next_loop.edge

        if next_loop.link_loop_prev.edge.is_boundary or \
            next_loop.link_loop_next.edge.is_boundary:
            break
        else:
            if mark_edge:
                edges_to_return_tmp.append(edge_to_mark)
                edges_to_return_tmp.append(edge_to_mark.verts[0])
                edges_to_return_tmp.append(edge_to_mark.verts[1])
        i+=1

        if i < length:
            default_loop = next_loop.link_loop_next.link_loop_radial_next.link_loop_next
            next_loop = default_loop

    return next_loop, edges_to_return_tmp

def __mark_groove_edges_rectangular(bm, e, groove_edge_marked_prop, face_selected_prop, rng_pattern, rectangle_width_min, rectangle_width_max, rectangle_height_min, rectangle_height_max):
    """Go through and mark the edges in a rectangular pattern."""
    edges_to_return = []

    if e[groove_edge_marked_prop] | e.is_boundary:
        return edges_to_return


    # Go around things in a loop.
    e_link_loops = e.link_loops

    # get random height and width
    if rectangle_width_min == rectangle_width_max:
        max_width = rectangle_width_min
    else:
        if rectangle_width_min < rectangle_width_max:
            max_width = rng_pattern.randint(rectangle_width_min, rectangle_width_max)
        else:
            max_width = rng_pattern.randint(rectangle_width_max, rectangle_width_min)

    if rectangle_height_min == rectangle_height_max:
        max_height = rectangle_height_min
    else:
        if rectangle_height_min < rectangle_height_max:
            max_height = rng_pattern.randint(rectangle_height_min, rectangle_height_max)
        else:
            max_height = rng_pattern.randint(rectangle_height_max, rectangle_height_min)

    # get an edge on the loop.
    if len(e_link_loops):
        loop = e_link_loops[0]
        # attempt to take loop forward by width amount.
        if len(loop.vert.link_edges) == 4:
            mark_edge = True
            next_loop = loop
            next_loop, edges_to_return_tmp1 = __traverse_length(next_loop, max_width, groove_edge_marked_prop, edges_to_return, mark_edge)
            
            next_loop = next_loop.link_loop_next
            next_loop, edges_to_return_tmp2 = __traverse_length(next_loop, max_height , groove_edge_marked_prop, edges_to_return, mark_edge)

            
            next_loop = next_loop.link_loop_next
            next_loop, edges_to_return_tmp3 = __traverse_length(next_loop, max_width, groove_edge_marked_prop, edges_to_return, mark_edge)

            next_loop = next_loop.link_loop_next
            next_loop, edges_to_return_tmp4 = __traverse_length(next_loop, max_height, groove_edge_marked_prop, edges_to_return, mark_edge)
            

            if len(edges_to_return_tmp1) and len(edges_to_return_tmp2) and len(edges_to_return_tmp3) and len(edges_to_return_tmp4):
                edges_to_return_potential = []
                edges_to_return_potential.extend(edges_to_return_tmp1)
                edges_to_return_potential.extend(edges_to_return_tmp2)
                edges_to_return_potential.extend(edges_to_return_tmp3)
                edges_to_return_potential.extend(edges_to_return_tmp4)

                edges_to_return.extend(edges_to_return_potential)

            # if we got this far mark the edges up
            edges_to_remove = []
            for e in edges_to_return:
                to_mark = False
                for f in e.link_faces:
                    if f[face_selected_prop]:
                        to_mark = True
                        break
                if to_mark and isinstance(e, bmesh.types.BMEdge):
                    e[groove_edge_marked_prop] = 1
                else: 
                    edges_to_remove.append(e)
            for e in edges_to_remove:
                edges_to_return.remove(e)

    return edges_to_return



def ruby_dragon(bm, selected_faces, percentage, random_seed):

    # determine how many random selections we should make.
    steps = int(len(selected_faces) * ((100 - percentage)/100))
    face_indexes = set([f.index for f in selected_faces])
    rng = np.random.RandomState(random_seed)
    edges_pattern = []

    i = 0
    bm.faces.ensure_lookup_table()

    found_faces = []

    selected_faces_shuffled = selected_faces[:]
    rng.shuffle(selected_faces_shuffled)
        
    for f in selected_faces_shuffled:

        if f in found_faces:
            continue

        found_faces.append(f)

        
        current_faces = []
        current_faces.append(f)
        current_face = f
        current_edges = list(current_face.edges)
        
        
        step = 0
        while step < steps:
            # Go through neighbours and see if we can branch out.
            found = False
            faces_edges = current_face.edges[:]
            
            faces_edges = [e for e in current_face.edges]
            rng_step = np.random.RandomState(random_seed + i)
            rng_step.shuffle(faces_edges)

            for e in faces_edges:
                for f1 in e.link_faces:
                    if f1 not in found_faces and f1 in selected_faces:
                        found_faces.append(f1)
                        current_face = f1
                        current_faces.append(current_face)
                        current_edges.extend(list(current_face.edges))
                        found = True
                        break
                if found:
                    break

            # if we didn't find anything, randonly decide if we can go somewhere else.
            if not found:
                current_face = rng_step.choice(current_faces)
                found_route = False
                for e in current_face.edges:
                    for f1 in e.link_faces:
                        if f1 not in found_faces and f1 in selected_faces:
                            found_route = True
                            break
                    if found_route:
                        break
                if not found_route:
                    break
                else:
                    step = -1
            step+=1

        for e in current_edges:
            # check whether all the faces linked to this edge are a part of the faces.
            check = all(f in found_faces for f in e.link_faces)
            if not check and e not in edges_pattern: 
                # because they weren't all in, they are at a boundary
                edges_pattern.append(e)
                edges_pattern.append(e.verts[0])
                edges_pattern.append(e.verts[1])
        i+=1

    return list(set(edges_pattern))