import bpy
import bmesh
import mathutils
import math
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_line_plane
from mathutils.bvhtree import BVHTree
from . import maths

def make_single_user(obj):
    if obj.data.users > 0:
        bpy.ops.object.select_linked(type="OBDATA")
        bpy.ops.object.make_single_user(
            object=True,
            obdata=True,
            material=False,
            animation=False,
        )

def coord_on_plane(reg, rv3d, coord, location, normal):
    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)
    vec = intersect_line_plane(ray_origin, ray_origin + view_vector, location, mathutils.mathutils.Vector((normal)))
    return vec

def ray_cast(reg, rv3d, coord, context):
    view_vector = view3d_utils.region_2d_to_vector_3d(reg, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(reg, rv3d, coord)

    hitresult, location, normal, index, object, matrix = context.scene.ray_cast(
        context.view_layer.depsgraph, ray_origin, view_vector
    )

    if object:
        x = object.visible_get(view_layer=context.view_layer)
        if x:
            return location, normal, index, object

    else:
        objects = [
            (obj)
            for obj in bpy.context.visible_objects
            if obj.type in ["META", "CURVE"]
        ]
        if objects is not None:
            deg = context.evaluated_depsgraph_get()

            for obj in objects:

                mw = obj.matrix_world
                mwi = mw.inverted()
                ray_origin = mwi @ ray_origin
                view_vector = mwi.to_3x3() @ view_vector

                bm = bmesh.new()
                mesh = obj.evaluated_get(deg).to_mesh()
                bm.from_mesh(mesh)
                bvh = BVHTree.FromBMesh(bm)

                location, normal, index, distance = bvh.ray_cast(
                    ray_origin, view_vector
                )

                bm.free()

                if location is not None:
                    return mw @ location, mw.to_3x3() @ normal, index, obj

    return None, None, None, None

def window_info(context, event, buffer, area):
    regX = 0
    regY = 0
    active = 0
    zoomlevel = 0
    window = []
    if context.area == area:

        r3d = area.spaces[0].region_3d

        div = maths.remap(bpy.context.space_data.lens, 1, 250, 0, 1)

        zoomlevel = (r3d.view_distance * 0.1) / (div * 5)

        for r in area.regions:
            if r.type == "UI":
                uiWidth = r.width
            if r.type == "HEADER":
                headerHeight = r.height

        windowWidth = area.width
        windowHeight = area.height

        regX = windowWidth - uiWidth
        regY = windowHeight - headerHeight*2

        magic = maths.calc_percent(windowWidth, buffer)

        window = [
            int(area.x + magic),
            int(windowWidth - uiWidth - magic),
            int(windowHeight - headerHeight*2 + area.y - magic),
            int(area.y + magic)
        ]

        if (
            event.mouse_region_x > int(0 + magic)
            and event.mouse_region_x < window[1]
            and event.mouse_region_y < int(windowHeight - magic - headerHeight*2)
            and event.mouse_region_y > int(0 + magic)
        ):
            active = 1
            return regX, regY, active, zoomlevel, window

    return regX, regY, active, zoomlevel, window

def cursor_warp(shift, ctrl, event, window, context):
    buffer = 20
    if event.mouse_x > window[1] - buffer:
        context.window.cursor_warp(window[0] + buffer*4, event.mouse_y)
    elif event.mouse_x < window[0] + buffer:
        context.window.cursor_warp(window[1] - buffer*4, event.mouse_y)
    elif event.mouse_y > window[2] - buffer:
        context.window.cursor_warp(event.mouse_x, window[3] + buffer*4)
    elif event.mouse_y < window[3] + buffer:
        context.window.cursor_warp(event.mouse_x, window[2] - buffer*4)
    delta = (event.mouse_prev_x - event.mouse_x) * -0.004
    delta *= bpy.context.preferences.addons[__package__].preferences.mouse_mult
    if shift == 1:
        delta *= 0.1
    if ctrl == 1:
        delta *= 10
    return delta

def update_dirt_radius(self, context):
    ob = bpy.context.active_object
    if ob:
        mat = ob.data.materials[0]
        dirt = mat.node_tree.nodes.get("QT_Dirt_Preview")
        dirt.inputs[0].default_value = bpy.context.window_manager.my_toolqt.dirt_radius_preview

def update_edges_radius(self, context):
    ob = bpy.context.active_object
    if ob:
        mat = ob.data.materials[0]
        edges = mat.node_tree.nodes.get("QT_Edge_Preview")
        edges.inputs[0].default_value = bpy.context.window_manager.my_toolqt.edges_radius_preview

def get_nodes(ob):
    if len(ob.material_slots) == 0:
        return None
        
    # material
    mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material

    if not mat:
        return None
    if not mat.node_tree:
        return None

    out = mat.node_tree.nodes.get("QT_Output")
    layer = mat.node_tree.nodes.get("QT_Layer_" + (str(bpy.context.window_manager.my_toolqt.active_layer)))
    
    if not layer:
        return None
    
    nodes = layer.node_tree.nodes
    node_tree = layer.node_tree
        
    if not nodes:
        return None
            
    layer_out = nodes.get("OUT")
    shader = nodes.get("QT_Shader")
    mix = nodes.get("QT_Mix")

    # coord
    tex_coord = nodes.get("QT_Coord")
    # mapping
    diffuse_mapping = nodes.get("QT_Diffuse_Mapping")
    rough_mapping = nodes.get("QT_Rough_Mapping")
    bump_mapping = nodes.get("QT_Bump_Mapping")
    alpha_mapping = nodes.get("QT_Alpha_Mapping")
    disp_mapping = nodes.get("QT_Disp_Mapping")
    metal_mapping = nodes.get("QT_Metal_Mapping")
    normal_mapping = nodes.get("QT_Normal_Mapping")
    # textures
    diffuse_tex = nodes.get("QT_Diffuse_Tex")
    rough_tex = nodes.get("QT_Rough_Tex")
    bump_tex = nodes.get("QT_Bump_Tex")
    normal_tex = nodes.get("QT_Normal_Tex")
    alpha_tex = nodes.get("QT_Alpha_Tex")
    disp_tex = nodes.get("QT_Disp_Tex")
    ao_tex = nodes.get("QT_AO_Tex")
    metal_tex = nodes.get("QT_Metal_Tex")
    # clamps
    roughness_clamp = nodes.get("QT_Roughness_Clamp")
    bump_clamp = nodes.get("QT_Bump_Clamp")
    alpha_clamp = nodes.get("QT_Alpha_Clamp")
    # hue
    diffuse_hue_sat = nodes.get("QT_Diffuse_Hue_Sat")
    rough_hue_sat = nodes.get("QT_Rough_Hue_Sat")
    bump_hue_sat = nodes.get("QT_Bump_Hue_Sat")
    alpha_hue_sat = nodes.get("QT_Alpha_Hue_Sat")
    # contrast
    diffuse_bright_contrast = nodes.get("QT_Diffuse_Bright_Contrast")
    rough_bright_contrast = nodes.get("QT_Rough_Bright_Contrast")
    bump_bright_contrast = nodes.get("QT_Bump_Bright_Contrast")
    alpha_bright_contrast = nodes.get("QT_Alpha_Bright_Contrast")
    # invert
    rough_invert = nodes.get("QT_Rough_Invert")
    bump_invert = nodes.get("QT_Bump_Invert")
    alpha_invert = nodes.get("QT_Alpha_Invert")
    metal_invert = nodes.get("QT_Metal_Invert")
    # bump
    bump = nodes.get("QT_Bump")
    # disp
    disp = nodes.get("QT_Disp")
    # strength
    bump_strength = nodes.get("QT_Bump_Strength")
    normal_strength = nodes.get("QT_Normal_Strength")
    ao_strength = nodes.get("QT_AO_Strength")
    # mask
    texture_mask = nodes.get("QT_Texture_Mask")
    edge_mask = nodes.get("QT_Edge_Mask")
    dirt_mask = nodes.get("QT_Dirt_Mask")
    depth_mask = nodes.get("QT_Depth_Mask")
    height_mask = nodes.get("QT_Height_Mask")
    normal_mask = nodes.get("QT_Normal_Mask")
    smudge = nodes.get("QT_Smudge")
    randcolor = nodes.get("QT_RandColor")
    randrough = nodes.get("QT_RandRough")
    variation = nodes.get("QT_Variation")
    detiling = nodes.get("QT_Detiling")
    edge = nodes.get("QT_Edge")
    dirt = nodes.get("QT_Dirt")
    # emission
    emission_contrast = nodes.get("QT_Emission_Bright_Contrast")

    return (
        mat, out, layer, nodes, node_tree, layer_out, shader, mix, tex_coord, diffuse_mapping, 
        rough_mapping, bump_mapping, alpha_mapping, disp_mapping, diffuse_tex, rough_tex, bump_tex,
        normal_tex, alpha_tex, disp_tex, ao_tex, roughness_clamp, bump_clamp, alpha_clamp,
        diffuse_hue_sat, rough_hue_sat, bump_hue_sat, alpha_hue_sat, diffuse_bright_contrast,
        rough_bright_contrast, bump_bright_contrast, alpha_bright_contrast, rough_invert,
        bump_invert, alpha_invert, bump, disp, bump_strength, normal_strength,
        ao_strength, texture_mask, edge_mask, dirt_mask, depth_mask, height_mask, normal_mask,
        smudge, randcolor, randrough, variation, detiling, edge, dirt, metal_mapping, metal_tex, metal_invert, normal_mapping,
        emission_contrast
    )
        
def get_input_nodes(node, links):
    input_links = {lnk for lnk in links if lnk.to_node == node}
    sorted_nodes = []
    done_nodes = set()
    for socket in node.inputs:
        done_links = set()
        for link in input_links:
            nd = link.from_node
            if nd in done_nodes:
                done_links.add(link)
            elif link.to_socket == socket:
                sorted_nodes.append(nd)
                done_links.add(link)
                done_nodes.add(nd)
        input_links -= done_links
    return sorted_nodes

def auto_align_nodes(node_tree):
    x_gap = 400
    y_gap = 400
    nodes = node_tree.nodes
    links = node_tree.links
    output_node = None
    for node in nodes:
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
            break
    else:
        return
    def align(to_node):
        from_nodes = get_input_nodes(to_node, links)
        for i, node in enumerate(from_nodes):
            node.location.x = min(node.location.x, to_node.location.x - x_gap)
            node.location.y = to_node.location.y
            node.location.y -= i * y_gap
            node.location.y += (len(from_nodes) - 1) * y_gap / (len(from_nodes))
            align(node)
    align(output_node)

def find_closest_bounding_point(sel, co):
    min_x, min_y, min_z = (999999.0,)*3
    max_x, max_y, max_z = (-999999.0,)*3
    
    for obj in sel:
        world_matrix = obj.matrix_world
        for corner in obj.bound_box:
            world_corner = world_matrix @ mathutils.Vector((corner[0], corner[1], corner[2], 1))
            
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)
                
    combined_bbox_corners = [
        (min_x, min_y, min_z),
        (min_x, min_y, max_z),
        (min_x, max_y, min_z),
        (min_x, max_y, max_z),
        (max_x, min_y, min_z),
        (max_x, min_y, max_z),
        (max_x, max_y, min_z),
        (max_x, max_y, max_z),
    ]
    
    closest_point = min(combined_bbox_corners, key=lambda point: (mathutils.Vector(point) - co).length)
    
    return mathutils.Vector((closest_point)), combined_bbox_corners