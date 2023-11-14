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
import bmesh
from mathutils import Vector

from .addon_test_utils import (
    AddonTestError,
    AddonTestManual,
    _prepare_test,
    _select_edges_by_id_active_obj,
    _select_faces_by_id_active_obj,
    _get_objs,
    _move_uv
    )
from ZenUV.ops.pack_exclusion import PackExcludedFactory


def _get_selected_edges_idxs(context):
    objs = _get_objs(context)
    edges = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        edges.extend([e.index for e in bm.edges if e.select])
        bm.free()
    return edges


def _get_selected_faces_idxs(context):
    objs = _get_objs(context)
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        faces.extend([f.index for f in bm.faces if f.select])
        bm.free()
    return faces


def _get_not_hided_faces_idxs(context):
    objs = _get_objs(context)
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        faces.extend([f.index for f in bm.faces if not f.hide])
        bm.free()
    return faces


def _scale_uv(context, scale=(1, 1), all_objs=False):
    if all_objs:
        objs = _get_objs(context)
    else:
        objs = [context.object, ]
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = [loop for face in bm.faces for loop in face.loops]
        for loop in loops:
            loop[uv_layer].uv *= Vector(scale)
        bmesh.update_edit_mesh(obj.data)

    return faces


def Test_uv_zenuv_select_by_direction(context):
    ''' Select edges by direction '''
    # bpy.ops.mesh.select_all(action='DESELECT')
    e_count = 16
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.uv.zenuv_select_by_direction(direction='U', clear_sel=True, angle=30, desc="Select edges by direction")
    edges = _get_selected_edges_idxs(context)
    if len(edges) != e_count:
        raise AddonTestError(f"TEST> Selected edges must be {e_count} instead of {len(edges)}")


def Test_uv_zenuv_show_sim_index(context):
    ''' Show Sim Index of the selected island '''
    # bpy.ops.uv.zenuv_show_sim_index()
    raise AddonTestManual


def Test_uv_zenuv_select_similar(context):
    ''' Select Islands similar to selected '''
    bpy.ops.mesh.select_all(action='DESELECT')
    f_count = 12
    _select_faces_by_id_active_obj(context, [0, ])

    bpy.ops.uv.zenuv_select_similar()

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_select_island(context):
    ''' Select Islands by selected edge/face of the Islands '''
    bpy.ops.mesh.select_all(action='DESELECT')
    f_count = 6
    _select_faces_by_id_active_obj(context, [0, ])

    bpy.ops.uv.zenuv_select_island()

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_select_stretched_islands(context):
    ''' Select Stretched Islands '''
    # bpy.ops.uv.zenuv_select_stretched_islands(Filter=0.1)
    raise AddonTestManual


def Test_uv_zenuv_select_uv_borders(context):
    ''' Select existing UV Borders '''
    bpy.ops.mesh.select_all(action='DESELECT')
    e_count = 14
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    bpy.ops.uv.zenuv_select_uv_borders(clear_selection=True)

    edges = _get_selected_edges_idxs(context)
    if len(edges) != e_count:
        raise AddonTestError(f"TEST> Selected edges must be {e_count} instead of {len(edges)}")


def Test_uv_zenuv_select_uv_overlap(context):
    ''' Select Overlapped Islands '''
    f_count = 7
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    _move_uv(context, offset=(0.5, 0))
    bpy.ops.uv.zenuv_select_uv_overlap()

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_select_flipped(context):
    ''' Select Flipped Islands '''
    f_count = 6
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    _scale_uv(context, scale=(-1, 1))

    bpy.ops.uv.zenuv_select_flipped()

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_select_pack_excluded(context):
    ''' Select Islands tagged as Excluded from Packing '''
    f_count = 6
    bpy.ops.mesh.select_all(action='DESELECT')
    objs = _get_objs(context)

    _select_faces_by_id_active_obj(context, [0, ])

    PackExcludedFactory.tag_pack_excluded(context, objs, action="TAG")

    bpy.ops.uv.zenuv_select_pack_excluded(clear_sel=True)

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_select_loop(context):
    ''' Select Edge Loop with Seams respect '''
    test_edge_id = 219
    test_edges_sel_count = 8
    _prepare_test(context, model='CYLINDER')
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_edges_by_id_active_obj(context, [test_edge_id, ])

    bpy.ops.uv.zenuv_select_loop()

    edges = _get_selected_edges_idxs(context)
    if len(edges) != test_edges_sel_count:
        raise AddonTestError(f"TEST> Selected edges count must be {test_edges_sel_count} instead of {len(edges)}")


def Test_uv_zenuv_isolate_island(context):
    ''' Isolate Islands (Toggle) by selected edge/face of the Islands '''
    test_face_id = 4
    visible_result = 32
    _prepare_test(context, model='CYLINDER')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    _select_faces_by_id_active_obj(context, [test_face_id, ])

    bpy.ops.uv.zenuv_isolate_island()

    faces = _get_not_hided_faces_idxs(context)
    if len(faces) != visible_result:
        raise AddonTestError(f"TEST> Selected faces count must be {visible_result} instead of {len(faces)}")


def Test_mesh_zenuv_mirror_seams(context):
    ''' Mirror Seams by axes '''
    seam_total_result = 148
    _prepare_test(context, model='CYLINDER')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.zenuv_mirror_seams(use_mirror_x=True, use_mirror_y=False, use_mirror_z=False)

    edges = _get_selected_edges_idxs(context)

    if len(edges) != seam_total_result:
        raise AddonTestError(f"TEST> Seam Edges count must be {seam_total_result} instead of {len(edges)}")


def Test_uv_zenuv_select_by_uv_area(context):
    "Select by UV Area"
    f_count = 6
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_faces_by_id_active_obj(context, [*range(0, 6)])
    _scale_uv(context, (0, 0))
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.uv.zenuv_select_by_uv_area(clear_selection=True, condition='ZERO', treshold=0.5)

    faces = _get_selected_faces_idxs(context)
    if len(faces) != f_count:
        raise AddonTestError(f"TEST> Selected faces count must be {f_count} instead of {len(faces)}")


def Test_uv_zenuv_grab_sel_area(context):
    "Get Selected Area"
    prop = context.scene.zen_uv
    s_init = 123456
    # prop.range_value_start = s_init
    # prop.range_value_end = e_init
    prop.area_value_for_sel = s_init

    bpy.ops.uv.zenuv_grab_sel_area(mode='FACE', average=True)

    test_value = 6250
    res_value = round(prop.area_value_for_sel, 0)

    if res_value != test_value:
        raise AddonTestError(f"TEST> The value was not changed. Must be: {test_value}. Instead of {res_value}")


tests_select_sys = (
    Test_uv_zenuv_select_by_direction,
    Test_uv_zenuv_show_sim_index,
    Test_uv_zenuv_select_similar,
    Test_uv_zenuv_select_island,
    Test_uv_zenuv_select_stretched_islands,
    Test_uv_zenuv_select_uv_borders,
    Test_uv_zenuv_select_uv_overlap,
    Test_uv_zenuv_select_flipped,
    Test_uv_zenuv_select_pack_excluded,
    Test_uv_zenuv_select_loop,
    Test_uv_zenuv_isolate_island,
    Test_mesh_zenuv_mirror_seams,
    Test_uv_zenuv_select_by_uv_area,
    Test_uv_zenuv_grab_sel_area

)


if __name__ == "__main__":
    pass
