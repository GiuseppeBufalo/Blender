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

from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import select_by_context
from ZenUV.utils.vlog import Log

from .addon_test_utils import (
    _get_selected_faces_ids,
    AddonTestError,
    AddonTestManual,
    _select_faces_by_id_active_obj,
    _get_objs,
    _get_bounding_box,
    _ensure_facemap
    )

from ZenUV.utils.finishing_util import FINISHED_FACEMAP_NAME


def _prepare_finished_testing(context):
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_faces_by_id_active_obj(context, [*range(0, 6)])
    bpy.ops.uv.zenuv_tag_finished()


def _get_finished_islands(context):
    islands_finished = []
    for obj in _get_objs(context):
        bm = bmesh.from_edit_mesh(obj.data).copy()
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        finished_facemap = _ensure_facemap(bm, FINISHED_FACEMAP_NAME)
        islands = island_util.get_islands(context, bm)
        islands_finished.extend([island for island in islands if True in [f[finished_facemap] for f in island]])
        bm.free()
    return islands_finished


def select_finished(context, bm, _finished_facemap):
    islands = island_util.get_islands(context, bm)
    islands_for_select = [island for island in islands if True in [f[_finished_facemap] for f in island]]
    if not islands_for_select:
        False
    select_by_context(context, bm, islands_for_select, state=True)
    return True


def Test_uv_zenuv_untag_finished(context):
    ''' Tag Islands as Unfinished '''
    test_count = 0
    _prepare_finished_testing(context)

    bpy.ops.uv.zenuv_untag_finished()

    islands_finished = _get_finished_islands(context)

    if len(islands_finished) != test_count:
        raise AddonTestError(f"Total Finished Islands must be {test_count} instead of {len(islands_finished)}")


def Test_uv_zenuv_islands_sorting(context):
    ''' Sort Islands by Tags. Finished Islands move to the right side from Main UV Tile, Unfinished - to the left '''
    _prepare_finished_testing(context)
    init_bbox = _get_bounding_box(context)
    bpy.ops.uv.zenuv_islands_sorting()
    result_bbox = _get_bounding_box(context)
    # init_bbox.show_bbox(name="Init bbox")
    # result_bbox.show_bbox(name="Result bbox")
    if init_bbox.center == result_bbox.center:
        raise AddonTestError(f"Init Bounding box center is equal to result. Init: {init_bbox.center}, Result: {result_bbox.center}. So Sorting was not completed.")
    else:
        Log.info(f"Init BBOX center is not equal to BBOX result. Init: {init_bbox.center}, Result: {result_bbox.center}.")


def Test_uv_zenuv_display_finished(context):
    ''' Display Finished/Unfinished Islands in the viewport '''
    # bpy.ops.uv.zenuv_display_finished()
    raise AddonTestManual


def Test_uv_zenuv_tag_finished(context):
    ''' Tag Islands as Finished '''
    test_count = 1
    _prepare_finished_testing(context)

    islands_finished = _get_finished_islands(context)

    if len(islands_finished) != test_count:
        raise AddonTestError(f"Total Finished Islands must be {test_count} instead of {len(islands_finished)}")


def Test_uv_zenuv_select_finished(context):
    ''' Select Islands tagged as Finished '''
    test_count = 6
    _prepare_finished_testing(context)

    bpy.ops.uv.zenuv_select_finished(clear_sel=True)

    faces = _get_selected_faces_ids(context)

    if len(faces) != test_count:
        raise AddonTestError(f"Selected faces must be {test_count} instead of {len(faces)}")


tests_texel_density = (
    Test_uv_zenuv_untag_finished,
    Test_uv_zenuv_islands_sorting,
    Test_uv_zenuv_display_finished,
    Test_uv_zenuv_tag_finished,
    Test_uv_zenuv_select_finished,

)


if __name__ == "__main__":
    pass
