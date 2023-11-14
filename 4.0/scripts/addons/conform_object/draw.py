"""
    Contains UI reference function for the addon.
"""
import bpy
import blf
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import bmesh

import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
import colorsys

_draw_handle = None
_is_running = False




def _draw_callback_3d(context):
    """Draw in 3D a representaion of the mesh"""

    if not context.space_data.overlay.show_overlays or not context.object.mode == 'OBJECT':
        return

    if not hasattr(context, 'visible_objects') or not context.visible_objects:
        return

    enable_viewer = context.window_manager.conform_object_ui.enable_viewer
    if not enable_viewer:
        return

    try:
        
        rv3d = context.space_data.region_3d

        if rv3d.is_perspective:
            view_position = rv3d.view_matrix.inverted().translation
        else:
            region = context.region
            view_position = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))

        view_direction = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))

        show_xray = context.space_data.shading.show_xray

        zero_weights_opts = context.window_manager.conform_object_ui.zero_weights_opts

        vertex_group_selection_opts = context.window_manager.conform_object_ui.vertex_group_selection_opts

        objs = []
        if vertex_group_selection_opts == 'ACTIVE' and context.active_object.type == 'MESH':
            objs.append(context.active_object)
        elif vertex_group_selection_opts == 'SELECTED':
            objs.extend([o for o in context.selected_objects if o.type == 'MESH' and o.select_get()])
        elif vertex_group_selection_opts == 'ALL':
            objs.extend([o for o in context.visible_objects if o.type == 'MESH'])

        all_coords = []
        all_vertex_colors = []
        # Draw gradient vertex weights
        for obj in objs:

            obj_eval = obj.evaluated_get(context.evaluated_depsgraph_get())
            if not obj_eval.vertex_groups.active:
                continue

            bvh_tree = BVHTree.FromObject(obj_eval, context.evaluated_depsgraph_get())

            coords = []
            vertex_colors = []

            
            bm = bmesh.new()
            bm.from_mesh(obj_eval.data)

            deform_layer = bm.verts.layers.deform.verify()

            group_index = obj_eval.vertex_groups.active.index

            for v in bm.verts:

                vertex_color = None

                if group_index in v[deform_layer]:
                    weight = v[deform_layer][group_index]

                    if weight > 0:
                        color_vec = colorsys.hsv_to_rgb((1- weight) * .667, 1, 1)
                        vertex_color = Vector((color_vec[0], color_vec[1], color_vec[2], 1))

                if not vertex_color and zero_weights_opts == 'ALL':
                    vertex_color = Vector((0, 0, 1, 1))

                if not vertex_color:
                    continue

                if not show_xray:
                    world_normal = v.normal.to_4d()
                    world_normal.w = 0
                    world_normal = (obj_eval.matrix_world @ world_normal).to_3d()

                    world_position = obj_eval.matrix_world @ v.co

                    vec_to_cam = (world_position - view_position)
                    
                    if world_normal.dot(vec_to_cam) >= 0:
                        continue
                        
                    local_pos = obj_eval.matrix_world.inverted() @ view_position
                    local_ray = obj_eval.matrix_world.inverted().to_3x3() @ vec_to_cam
                    hit_location, normal, index, distance = bvh_tree.ray_cast(local_pos, local_ray)

                    if hit_location:
                        if normal.dot(local_ray) >= 0:
                            continue

                        if index not in [f.index for f in v.link_faces]:
                            continue

                    else:
                        continue

                if vertex_color:
                    vertex_colors.append(vertex_color)
                    coords.append(obj_eval.matrix_world @ v.co)

            all_coords.extend(coords)
            all_vertex_colors.extend(vertex_colors)

        # Draw vertices
        gpu.state.blend_set("ALPHA")
        gpu.state.point_size_set(context.window_manager.conform_object_ui.vertex_group_view_size)
        shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        batch = batch_for_shader(shader, 'POINTS', {"pos": all_coords, "color": all_vertex_colors   })
        shader.bind()
        batch.draw(shader)

        gpu.state.blend_set("NONE")

    except Exception:
        pass
    
def register(context):
    global _is_running
    if not _is_running:
        global _draw_handle
        global _draw_callback_3d
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_callback_3d, (context,), 'WINDOW', 'POST_VIEW')
        _is_running = True


def unregister():
    global _is_running
    if _is_running:
        global _draw_handle
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _is_running = False
