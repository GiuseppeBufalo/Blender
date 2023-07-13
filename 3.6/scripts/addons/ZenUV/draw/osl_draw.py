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

import bpy
import bgl
import blf
import gpu
import bmesh
import numpy as np
from bpy.app.handlers import persistent
from mathutils import Color
from gpu_extras.batch import batch_for_shader
import ZenUV.utils.get_uv_islands as island_util
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.zen_checker.stretch_map import StretchMap
from ZenUV.utils.generic import ensure_facemap
from ZenUV.stacks.utils import (
    StacksSystem,
    enshure_stack_layer,
    STACK_LAYER_NAME,
    M_STACK_LAYER_NAME,
    write_sim_data_to_layer
)
from ZenUV.utils.finishing_util import FINISHED_FACEMAP_NAME
from ZenUV.ops.pack_exclusion import PACK_EXCLUDED_FACEMAP_NAME

handle_SpaceView3D_stacked = None
handle_SpaceView2D_stacked = None
handle_SpaceView3D_m_stacked = None
handle_SpaceView2D_m_stacked = None
handle_SpaceView3D_s_stacked = None
handle_SpaceView2D_s_stacked = None
handle_SpaceView3D_ast_stacked = None
handle_SpaceView2D_ast_stacked = None

handle_SpaceView2D_finished = None
handle_SpaceView3D_finished = None

handle_SpaceView2D_p_excluded = None
handle_SpaceView3D_p_excluded = None

handle_SpaceView3D_stretch = None
handle_SpaceView2D_stretch = None

FONT_SIZE = (20, 40)


def draw_edges(verts, edges_colors, edge_indices):
    shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    batch2 = batch_for_shader(
        shader, 'LINES',
        {"pos": verts, "color": edges_colors},
        indices=edge_indices)
    shader.bind()
    batch2.draw(shader)


def draw_typo_2d(position, color, text):
    font_id = 0
    blf.position(font_id, position[0], position[1], 0)
    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.size(font_id, FONT_SIZE[0], FONT_SIZE[1])
    blf.draw(font_id, text)


def draw_faces(verts, face_colors, face_tri_indices):
    shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    batch1 = batch_for_shader(
        shader, 'TRIS',
        {"pos": verts, "color": face_colors},
        indices=face_tri_indices)
    shader.bind()
    batch1.draw(shader)


def draw_finished_callback_3d(operator, context):
    addon_prefs = get_prefs()
    ob = context.active_object
    objs = context.objects_in_mode
    for ob in objs:
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        fmap = bm.faces.layers.int.get("ZenUV_Finished")
        if fmap:
            bm = bm.copy()
            fmap = bm.faces.layers.int.get("ZenUV_Finished")
            verts = [(ob.matrix_world @ v.co) for v in bm.verts]
            face_colors = [addon_prefs.FinishedColor, ] * len(verts)
            face_colors_r = [addon_prefs.UnFinishedColor, ] * len(verts)

            p_loops = bm.calc_loop_triangles()
            face_tri_indices = [[loop.vert.index for loop in looptris]
                                for looptris in p_loops
                                if not looptris[0].face.hide and looptris[0].face[fmap] == 1]
            face_tri_indices_r = [[loop.vert.index for loop in looptris]
                                  for looptris in p_loops
                                  if not looptris[0].face.hide and looptris[0].face[fmap] == 0]
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)

            draw_faces(verts, face_colors, face_tri_indices)
            draw_faces(verts, face_colors_r, face_tri_indices_r)

            # restore opengl defaults
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bm.free()


def draw_p_excluded_callback_3d(operator, context):
    addon_prefs = get_prefs()
    ob = context.active_object
    objs = context.objects_in_mode
    for ob in objs:
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        fmap = bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME)
        if fmap:
            bm = bm.copy()
            fmap = bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME)
            verts = [(ob.matrix_world @ v.co) for v in bm.verts]
            face_colors = [addon_prefs.ExcludedColor, ] * len(verts)
            # face_colors_r = [addon_prefs.UnFinishedColor, ] * len(verts)

            p_loops = bm.calc_loop_triangles()
            face_tri_indices = [[loop.vert.index for loop in looptris]
                                for looptris in p_loops
                                if not looptris[0].face.hide and looptris[0].face[fmap] == 1]
            # face_tri_indices_r = [[loop.vert.index for loop in looptris]
            #                       for looptris in p_loops
            #                       if not looptris[0].face.hide and looptris[0].face[fmap] == 0]
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)

            draw_faces(verts, face_colors, face_tri_indices)
            # draw_faces(verts, face_colors_r, face_tri_indices_r)

            # restore opengl defaults
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bm.free()


def draw_tagged_callback_3d(operator, context):
    ob = context.active_object
    if ob.mode == 'EDIT':

        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        verts = [(ob.matrix_world @ v.co) for v in bm.verts]

        face_colors = ((0.505, 0.8, 0.175, 0.2),) * len(verts)

        face_tri_indices = [[loop.vert.index for loop in looptris]
                            for looptris in bm.calc_loop_triangles()
                            if looptris[0].face.tag]

        edges_colors = ((0.0, 1.0, 0.25, 1),) * len(verts)
        edge_indices = [(v.index for v in e.verts) for e in bm.edges if e.tag]

        # 80% alpha, 2 pixel width line
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_DEPTH_TEST)

        draw_faces(verts, face_colors, face_tri_indices)

        draw_edges(verts, edges_colors, edge_indices)

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_DEPTH_TEST)


def draw_finished_callback_2d(self, context):
    text = "Zen UV: Finished Displayed"
    position = (int(context.area.width / 4), int(context.area.height - 80))
    bgl.glEnable(bgl.GL_BLEND)
    # draw_typo_2d(position, (0.093, 0.216, 0.539, 1.0), text)
    draw_typo_2d(position, (1.0, 1.0, 1.0, 1.0), text)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)


def draw_p_excluded_callback_2d(self, context):
    text = "Zen UV: Excluded from Pack Displayed"
    position = (int(context.area.width / 4), int(context.area.height - 80))
    bgl.glEnable(bgl.GL_BLEND)
    # draw_typo_2d(position, (0.093, 0.216, 0.539, 1.0), text)
    draw_typo_2d(position, (1.0, 1.0, 1.0, 1.0), text)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)


def draw_tagged_callback_2d(self, context):
    position = (int(context.area.width / 3), int(context.area.height - 80))
    bgl.glEnable(bgl.GL_BLEND)
    draw_typo_2d(position, (1.0, 1.0, 1.0, 1.0), "Zen UV: Tagged Displayed")
    # bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)


def color_by_layer_sim_index(bm, v_idx, s_layer):
    # solver returns order alpha, color.value, color.saturation
    solver = {0: (0.95, 0.0, 0.7)}
    face = bm.verts[v_idx].link_faces[0]
    s_index = 0.001 + face[s_layer] * 1000 * (not face.hide)
    color = [int(d)/10 for d in str(s_index) if d != '.']
    color = Color((color[0], color[1], color[2]))
    alpha, color.v, color.s = solver.get(sum(color), (0.5, 0.7, 0.7))
    return (color[0], color[1], color[2], alpha)


def color_by_sim_index(sim_index):
    # solver returns order alpha, color.value, color.saturation
    solver = {0: (0.95, 0.0, 0.7)}
    s_index = 0.001 + sim_index * 1000
    color = [int(d)/10 for d in str(s_index) if d != '.']
    color = Color((color[0], color[1], color[2]))
    alpha, color.v, color.s = solver.get(sum(color), (0.5, 0.7, 0.7))
    return (color[0], color[1], color[2], alpha)


class StackAstCache:
    all_loops = None

    osl_items = {}


_ast_cashe = StackAstCache()


def draw_ast_stack_callback_3d(operator, context):

    if context.mode != 'EDIT_MESH':
        print('MODE NOT SUPPORTED!')
        return

    all_bms = set(bmesh.from_edit_mesh(obj.data) for obj in context.objects_in_mode_unique_data if obj.type == 'MESH')
    all_data = {}
    for bm in all_bms:
        uv_layer = bm.loops.layers.uv.active
        if uv_layer:
            all_data[bm] = uv_layer

    all_loops = np.array([
        (loop[uv_layer].uv.to_tuple(5) if not f.hide else (0, 0))
        for bm, uv_layer in all_data.items()
        for f in bm.faces for loop in f.loops], 'f2')

    if (_ast_cashe.all_loops is None or
            not np.array_equal(_ast_cashe.all_loops, all_loops)):

        _ast_cashe.all_loops = all_loops

        _ast_cashe.osl_items = {}
        if len(all_loops):
            AstSolver = StacksSystem(context)
            AstSolver.get_stacked()
            _ast_cashe.osl_items = AstSolver.ASD_for_OSL().copy()

    if len(_ast_cashe.osl_items):
        # draw_data = init(context)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        # for obj_name, data in draw_data.items():
        for obj_name, data in _ast_cashe.osl_items.items():
            draw_faces(data["verts"], data["colors"], data["faces"])

        bgl.glDisable(bgl.GL_DEPTH_TEST)


def draw_stretch_callback_3d(operator, context):

    StMap = StretchMap(context)
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    for obj_name, data in StMap.create_osl_buffer().items():
        draw_faces(data["verts"], data["colors"], data["faces"])
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_DEPTH_TEST)


def draw_stretch_callback_2d(self, context):
    position = (int(context.area.width / 3), int(context.area.height - 80))
    bgl.glEnable(bgl.GL_BLEND)
    draw_typo_2d(position, (1.0, 1.0, 1.0, 1.0), "Zen UV: Stretch Map Displayed")
    # bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)


class StackSelectedCache:
    all_selected = None
    verts = []
    face_colors = []
    face_tri_indices = []


_selected_cache = StackSelectedCache


def draw_s_stack_callback_3d(operator, context: bpy.types.Context):

    if context.mode != 'EDIT_MESH':
        print('MODE NOT SUPPORTED!')
        return

    s_index = 0.0

    all_bms = set(bmesh.from_edit_mesh(obj.data) for obj in context.objects_in_mode_unique_data if obj.type == 'MESH')
    for bm in all_bms:
        bm.faces.ensure_lookup_table()

    arr_selected = np.fromiter([(int(f.hide) + int(f.select)) for bm in all_bms for f in bm.faces], 'i')

    if (_selected_cache.all_selected is None or
            not np.array_equal(_selected_cache.all_selected, arr_selected)):

        stacks = StacksSystem(context)
        sim_data = stacks.forecast_selected()

        _selected_cache.all_selected = arr_selected
        _selected_cache.verts = []
        _selected_cache.face_tri_indices = []
        _selected_cache.face_colors = []

        for sim_index, data in sim_data.items():
            s_index = sim_index
            for obj_name, islands in data["objs"].items():
                obj = context.scene.objects[obj_name]

                bms = bmesh.from_edit_mesh(obj.data).copy()
                bms.faces.ensure_lookup_table()
                bms.verts.ensure_lookup_table()

                s_faces = [bms.faces[i] for island, indices in islands.items() for i in indices]

                for face in s_faces:
                    face.tag = True

                faces_to_del = [f for f in bms.faces if not f.tag]

                bmesh.ops.delete(bms, geom=faces_to_del, context='FACES')
                bms.verts.ensure_lookup_table()
                bms.faces.ensure_lookup_table()

                was_index = len(_selected_cache.verts)
                _selected_cache.verts.extend([obj.matrix_world @ v.co for v in bms.verts])
                loops = bms.calc_loop_triangles()
                _selected_cache.face_tri_indices.extend([[
                    loop.vert.index + was_index for loop in looptris]
                    for looptris in loops
                    if not looptris[0].face.hide])
                _selected_cache.face_colors.extend(
                    (color_by_sim_index(s_index),) * len(bms.verts)
                )

    if len(_selected_cache.face_tri_indices):

        bgl.glEnable(bgl.GL_DEPTH_TEST)

        draw_faces(_selected_cache.verts, _selected_cache.face_colors, _selected_cache.face_tri_indices)

        bgl.glDisable(bgl.GL_DEPTH_TEST)


def draw_stack_callback_3d(operator, context, verts, face_colors, face_tri_indices):
    # verts, face_colors, face_tri_indices = prepare_geometry(context.objects_in_mode)
    # StackSolver = StacksSystem(context)
    # StackSolver.forecast()
    # StackSolver.SimData_for_OSL()
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    # for obj_name, data in StackSolver.SimData_for_OSL().items():
    #     print(len(data["verts"]), len(data["colors"]), len(data["faces"]))
    #     draw_faces(data["verts"], data["colors"], data["faces"])
    draw_faces(verts, face_colors, face_tri_indices)

    bgl.glDisable(bgl.GL_DEPTH_TEST)


def check_obj_updated():
    pass


def disable_all_draws(context):
    draw_prop = context.scene.zen_display
    props = draw_prop.items()
    for pref in props:
        draw_prop.pref = False


@persistent
def zenuv_scene_update(scene):
    # print(f"Scene Updated {scene}")
    if not bpy.context.objects_in_mode:
        bpy.context.scene.zen_display.stacked = False
        bpy.context.scene.zen_display.m_stacked = False
        bpy.context.scene.zen_display.s_stacked = False
        bpy.context.scene.zen_display.finished = False
        bpy.context.scene.zen_display.stretch = False
        bpy.context.scene.zen_display.ast_stacked = False
        bpy.context.scene.zen_display.stack_display_solver = False


def prepare_geometry(objs, manual):
    s_layer_name = {True: M_STACK_LAYER_NAME, False: STACK_LAYER_NAME}
    if objs:

        verts = []
        face_colors = []
        face_tri_indices = []

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data).copy()
            bm.verts.index_update()
            bm.edges.index_update()
            bm.edges.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            bound_edges = [bm.edges[index] for index in island_util.uv_bound_edges_indexes(bm.faces, uv_layer)]
            bmesh.ops.split_edges(bm, edges=bound_edges)
            bm.verts.ensure_lookup_table()
            no_actual_verts = [v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm, geom=no_actual_verts, context='VERTS')
            bm.verts.ensure_lookup_table()
            stacks_layer = enshure_stack_layer(bm, stack_layer_name=s_layer_name[manual])
            face_colors.extend([color_by_layer_sim_index(bm, v_idx, stacks_layer) for v_idx in range(len(bm.verts))])
            loops = bm.calc_loop_triangles()
            was_last_idx = len(verts)
            verts.extend([obj.matrix_world @ v.co for v in bm.verts])
            face_tri_indices.extend(
                [[loop.vert.index + was_last_idx for loop in looptris]
                 for looptris in loops
                 if not looptris[0].face.hide])
            bm.free()
    else:
        return [], [], []
    return verts, face_colors, face_tri_indices


def callback_solver(self, context, manual=False):

    global handle_SpaceView3D_stacked
    global handle_SpaceView2D_stacked
    global handle_SpaceView3D_m_stacked
    global handle_SpaceView2D_m_stacked
    global handle_SpaceView3D_s_stacked
    global handle_SpaceView2D_s_stacked
    global handle_SpaceView3D_ast_stacked
    global handle_SpaceView2D_ast_stacked
    global handle_SpaceView3D_finished
    global handle_SpaceView2D_finished
    global handle_SpaceView3D_p_excluded
    global handle_SpaceView2D_p_excluded
    global handle_SpaceView3D_stretch
    global handle_SpaceView2D_stretch

    zen_draw_props = context.scene.zen_display

    if zen_draw_props.stacked:  # Stacked
        handle_SpaceView3D_stacked, handle_SpaceView2D_stacked = register_stack_callback(
            self,
            context,
            handle_SpaceView3D_stacked,
            handle_SpaceView2D_stacked,
            manual
        )
    else:
        handle_SpaceView3D_stacked, handle_SpaceView2D_stacked = unregister_calback(handle_SpaceView3D_stacked, handle_SpaceView2D_stacked)

    if zen_draw_props.m_stacked:  # Manual Stacks
        handle_SpaceView3D_m_stacked, handle_SpaceView2D_m_stacked = register_stack_callback(
            self,
            context,
            handle_SpaceView3D_m_stacked,
            handle_SpaceView2D_m_stacked,
            manual
        )
    else:
        handle_SpaceView3D_m_stacked, handle_SpaceView2D_m_stacked = unregister_calback(handle_SpaceView3D_m_stacked, handle_SpaceView2D_m_stacked)

    if zen_draw_props.s_stacked:  # Stacks by selection
        handle_SpaceView3D_s_stacked, handle_SpaceView2D_s_stacked = register_s_stack_callback(
            self,
            context,
            handle_SpaceView3D_s_stacked,
            handle_SpaceView2D_s_stacked,
            manual
        )
    else:
        handle_SpaceView3D_s_stacked, handle_SpaceView2D_s_stacked = unregister_calback(handle_SpaceView3D_s_stacked, handle_SpaceView2D_s_stacked)

    if zen_draw_props.ast_stacked:  # Already Stacked Islands AST
        handle_SpaceView3D_ast_stacked, handle_SpaceView2D_ast_stacked = register_ast_stack_callback(
            self,
            context,
            handle_SpaceView3D_ast_stacked,
            handle_SpaceView2D_ast_stacked,
            manual
        )
    else:
        handle_SpaceView3D_ast_stacked, handle_SpaceView2D_ast_stacked = unregister_calback(handle_SpaceView3D_ast_stacked, handle_SpaceView2D_ast_stacked)

    if zen_draw_props.finished:
        handle_SpaceView3D_finished, handle_SpaceView2D_finished = register_finished_callback(
            self,
            context,
            handle_SpaceView3D_finished,
            handle_SpaceView2D_finished
        )
    else:
        handle_SpaceView3D_finished, handle_SpaceView2D_finished = unregister_calback(handle_SpaceView3D_finished, handle_SpaceView2D_finished)

    if zen_draw_props.p_excluded:
        handle_SpaceView3D_p_excluded, handle_SpaceView2D_p_excluded = register_p_excluded_callback(
            self,
            context,
            handle_SpaceView3D_p_excluded,
            handle_SpaceView2D_p_excluded
        )
    else:
        handle_SpaceView3D_p_excluded, handle_SpaceView2D_p_excluded = unregister_calback(handle_SpaceView3D_p_excluded, handle_SpaceView2D_p_excluded)

    if zen_draw_props.stretch:
        handle_SpaceView3D_stretch, handle_SpaceView2D_stretch = register_stretch_callback(
            self,
            context,
            handle_SpaceView3D_stretch,
            handle_SpaceView2D_stretch
        )
    else:
        handle_SpaceView3D_stretch, handle_SpaceView2D_stretch = unregister_calback(handle_SpaceView3D_stretch, handle_SpaceView2D_stretch)

    # Registering update callbacks
    if handle_SpaceView3D_stacked \
            or handle_SpaceView3D_m_stacked\
            or handle_SpaceView3D_s_stacked\
            or handle_SpaceView3D_finished\
            or handle_SpaceView3D_stretch\
            or handle_SpaceView3D_ast_stacked:
        register_update_callback()

    if handle_SpaceView3D_stacked is None \
            and handle_SpaceView3D_m_stacked is None \
            and handle_SpaceView3D_s_stacked is None \
            and handle_SpaceView3D_finished is None \
            and handle_SpaceView3D_stretch is None \
            and handle_SpaceView3D_ast_stacked is None:
        unregister_update_callback()


def unregister_calback(handle_3d, handle_2d):
    if handle_3d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(handle_3d, 'WINDOW')
        handle_3d = None
    if handle_2d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(handle_2d, 'WINDOW')
        handle_2d = None
    return handle_3d, handle_2d


def register_stack_callback(self, context, handle_3d, handle_2d, manual):
    text = ""
    if handle_3d is None:
        objs = context.objects_in_mode
        stacks = StacksSystem(context)
        sim_data = stacks.forecast_stacks()
        write_sim_data_to_layer(context, sim_data)
        verts, face_colors, face_tri_indices = prepare_geometry(objs, manual)
        args_3d = (self, context, verts, face_colors, face_tri_indices)
        if manual:
            text = "Manual "
        args_2d = (self, context, text)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_stack_callback_3d, args_3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_stack_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def register_finished_callback(self, context, handle_3d, handle_2d):
    if handle_3d is None:
        args_3d = (self, context)
        args_2d = (self, context)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_finished_callback_3d, args_3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_finished_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def register_p_excluded_callback(self, context, handle_3d, handle_2d):
    if handle_3d is None:
        args_3d = (self, context)
        args_2d = (self, context)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_p_excluded_callback_3d, args_3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_p_excluded_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def register_stretch_callback(self, context, handle_3d, handle_2d):
    if handle_3d is None:
        args_3d = (self, context)
        args_2d = (self, context)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_stretch_callback_3d, args_3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_stretch_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def register_s_stack_callback(self, context, handle_3d, handle_2d, manual):
    text = ""
    if handle_3d is None:
        args3d = (self, context)
        if manual:
            text = "Selected "
        args_2d = (self, context, text)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_s_stack_callback_3d, args3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_stack_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def register_ast_stack_callback(self, context, handle_3d, handle_2d, manual):
    text = ""
    if handle_3d is None:
        args3d = (self, context)
        if manual:
            text = "Stacked "
        args_2d = (self, context, text)
        handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_ast_stack_callback_3d, args3d, 'WINDOW', 'POST_VIEW')
        handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_stack_callback_2d, args_2d, 'WINDOW', 'POST_PIXEL')
    return handle_3d, handle_2d


def unregister_update_callback():
    if zenuv_scene_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(zenuv_scene_update)


def register_update_callback():
    if zenuv_scene_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(zenuv_scene_update)


def draw_stack_callback_2d(self, context, manual=""):
    text = "Zen UV: {}Stacks Displayed".format(manual)
    position = (int(context.area.width / 4), int(context.area.height - 80))
    bgl.glEnable(bgl.GL_BLEND)
    draw_typo_2d(position, (1.0, 1.0, 1.0, 1.0), text)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)


def draw_switch(context, primary):
    vizers = context.scene.zen_display
    for vizer, value in vizers.items():
        if vizer == primary:
            continue
        vizers[vizer] = False


class ZUV_OT_DrawFinished(bpy.types.Operator):
    bl_idname = "view3d.zenuv_draw_finished"
    bl_label = "Display Finished"

    def modal(self, context, event):
        context.area.tag_redraw()

        if not context.scene.zen_display.finished:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')

            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_finished_callback_3d, args, 'WINDOW', 'POST_VIEW')
            self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_finished_callback_2d, args, 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class ZUV_OT_DrawTagged(bpy.types.Operator):
    bl_idname = "view3d.zenuv_draw_tagged"
    bl_label = "Display Tagged"
    bl_description = "Draw tagged elements. Inner system Operator"

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'RIGHTMOUSE', 'ESC'}:  # or not context.scene.zen_display.tagged:
            # if not context.scene.zen_display.tagged:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
            # context.area.tag_redraw()
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_tagged_callback_3d, args, 'WINDOW', 'POST_VIEW')
            self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_tagged_callback_2d, args, 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


if __name__ == "__main__":
    pass
