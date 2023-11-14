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
from . addon_test_utils import (
    AddonTestError,
    _prepare_test,
    _get_seam_edges_ids,
    _set_seams,
    _set_sharp,
    _select_edges_by_id_active_obj,
    _select_faces_by_id_active_obj,
    _get_selected_edges_ids,
    _get_sharp_edges_ids,
    _hide_faces_by_id_active_obj
)
from ZenUV.utils.vlog import Log


def seam_by_open_edges(context):
    Log.info("Current Mode: 'SEAM_BY_OPEN_EDGES'")
    test_count = 4
    _prepare_test(context, model='CUBE')

    _set_seams(context, [*range(0, 12)], state=False)

    _hide_faces_by_id_active_obj(context, [1, ])

    bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_OPEN_EDGES', unmark_seams=False, unmark_sharp=False)

    seams = len(_get_seam_edges_ids(context))

    if seams != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} instead of Seam: {seams}")


def sharp_by_seam(context):
    Log.info("Current Mode: 'SHARP_BY_SEAM'")
    test_count = 8
    _prepare_test(context, model='CUBE')

    _set_sharp(context, [*range(0, 12)], state=False)
    _set_seams(context, [*range(0, 12)], state=False)

    _set_seams(context, [*range(0, 4)], state=True)

    Log.info(f"Sharp was cleared. Current Sharp count is: {len(_get_sharp_edges_ids(context))}")

    bpy.ops.uv.zenuv_unified_mark(convert='SHARP_BY_SEAM', unmark_seams=False, unmark_sharp=False)

    sharp = len(_get_sharp_edges_ids(context))
    Log.info(f"Test Performed. Current Sharp count is: {sharp}")
    if sharp != test_count:
        raise AddonTestError(f"TEST> The Results must be Sharp: {test_count} instead of Sharp: {sharp}")


def seam_by_sharp(context):
    _prepare_test(context, model='CUBE')
    Log.info("Current Mode: 'SEAM_BY_SHARP'")

    test_count = 8
    _set_seams(context, [*range(0, 12)], state=False)
    _set_sharp(context, [*range(0, 4)], state=True)

    Log.info(f"Seams was cleared. Current Seams count is: {len(_get_seam_edges_ids(context))}")

    bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_SHARP', unmark_seams=False, unmark_sharp=False)

    seams = len(_get_seam_edges_ids(context))

    Log.info(f"Test Performed. Current Seams count is: {seams}")

    if seams != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} instead of Seam: {seams}")


def seam_by_uv_sharp_by_uv(context):
    Log.info("Current Modes: 'SEAM_BY_UV_BORDER', 'SHARP_BY_UV_BORDER'")
    _set_seams(context, [*range(0, 12)], state=False)
    _set_sharp(context, [*range(0, 12)], state=False)

    test_count = 14

    bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_UV_BORDER', unmark_seams=False, unmark_sharp=False)
    bpy.ops.uv.zenuv_unified_mark(convert='SHARP_BY_UV_BORDER', unmark_seams=False, unmark_sharp=False)

    seams = _get_seam_edges_ids(context)
    sharps = _get_sharp_edges_ids(context)

    if len(seams) != test_count or len(sharps) != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} and Sharp: {test_count} instead of Seam: {len(seams)}, Sharp: {len(sharps)}")


def Test_uv_zenuv_seams_by_sharp(context):
    ''' Mark Seams by existing Sharp edges '''

    test_count = 8
    _set_seams(context, [*range(0, 12)], state=False)
    _set_sharp(context, [*range(0, 4)], state=True)

    Log.info(f"Seams was cleared. Current Seams count is: {len(_get_seam_edges_ids(context))}")

    bpy.ops.uv.zenuv_seams_by_sharp()

    seams = len(_get_seam_edges_ids(context))

    Log.info(f"Test Performed. Current Seams count is: {seams}")

    if seams != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} instead of Seam: {seams}")


def Test_uv_zenuv_seams_by_uv_islands(context):
    ''' Mark Seams by existing UV Borders '''

    _set_seams(context, [*range(0, 12)], state=False)

    test_count = 14

    bpy.ops.uv.zenuv_seams_by_uv_islands(unmark_seams=False, unmark_sharp=False)

    seams = _get_seam_edges_ids(context)

    if len(seams) != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} instead of Seam: {len(seams)}.")


def Test_uv_zenuv_seams_by_open_edges(context):
    ''' Mark Seams by Open Edges. The way that looks in the viewport '''

    test_count = 4

    _set_seams(context, [*range(0, 12)], state=False)

    _hide_faces_by_id_active_obj(context, [1, ])

    bpy.ops.uv.zenuv_seams_by_open_edges()

    seams = len(_get_seam_edges_ids(context))

    if seams != test_count:
        raise AddonTestError(f"TEST> The Results must be Seam: {test_count} instead of Seam: {seams}")


def Test_uv_zenuv_sharp_by_seams(context):
    ''' Mark Sharp edges by existing Seams '''

    test_count = 8
    _prepare_test(context, model='CUBE')

    _set_sharp(context, [*range(0, 12)], state=False)
    _set_seams(context, [*range(0, 12)], state=False)

    _set_seams(context, [*range(0, 4)], state=True)

    Log.info(f"Sharp was cleared. Current Sharp count is: {len(_get_sharp_edges_ids(context))}")

    bpy.ops.uv.zenuv_sharp_by_seams()

    sharp = len(_get_sharp_edges_ids(context))
    Log.info(f"Test Performed. Current Sharp count is: {sharp}")
    if sharp != test_count:
        raise AddonTestError(f"TEST> The Results must be Sharp: {test_count} instead of Sharp: {sharp}")


def Test_mesh_zenuv_select_sharp(context):
    ''' Select Edges Marked as Sharp '''
    test_count = 4
    _set_sharp(context, [*range(0, 2)], state=True)

    bpy.ops.mesh.zenuv_select_sharp()

    sharp = len(_get_sharp_edges_ids(context))

    if sharp != test_count:
        raise AddonTestError(f"TEST> The Results must be Sharp: {test_count} instead of Sharp: {sharp}")


def Test_uv_zenuv_unified_mark(context):
    ''' Mark and Convert Seams and Sharp '''
    from ZenUV.utils.constants import UiConstants
    modes = [i[0] for i in UiConstants.unified_mark_enum]
    Log.info(f"Modes for testing: {modes}")
    # ['SEAM_BY_UV_BORDER', 'SHARP_BY_UV_BORDER', 'SEAM_BY_SHARP', 'SHARP_BY_SEAM', 'SEAM_BY_OPEN_EDGES']

    seam_by_uv_sharp_by_uv(context)

    seam_by_sharp(context)

    sharp_by_seam(context)

    seam_by_open_edges(context)


def Test_uv_zenuv_mark_seams(context):
    ''' Mark selected edges or face borders as Seams and/or Sharp edges '''
    Log.info("Testing in the EDGE Mode")
    test_count = 5
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    bpy.ops.mesh.select_all(action='DESELECT')
    _set_seams(context, [*range(0, 12)], state=False)

    _select_edges_by_id_active_obj(context, [*range(0, 5)])

    bpy.ops.uv.zenuv_mark_seams()

    seams = _get_seam_edges_ids(context)

    if len(seams) != test_count:
        raise AddonTestError(f"TEST> Seams edges must be {test_count} instead of {len(seams)}")

    Log.info("Testing in the FACE Mode")
    test_count = 4
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    _set_seams(context, [*range(0, 12)], state=False)

    _select_faces_by_id_active_obj(context, [1, ])

    bpy.ops.uv.zenuv_mark_seams()

    seams = _get_seam_edges_ids(context)

    if len(seams) != test_count:
        raise AddonTestError(f"TEST> Seams edges must be {test_count} instead of {len(seams)}")


def Test_mesh_zenuv_select_seams(context):
    ''' Select Edges Marked as Seams '''
    test_seams = 14
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.mesh.zenuv_select_seams()

    seams = _get_selected_edges_ids(context)

    if len(seams) != test_seams:
        raise AddonTestError(f"TEST> Seams edges must be {test_seams} instead of {len(seams)}")


def Test_uv_zenuv_auto_mark(context):
    ''' Mark edges as Seams and/or Sharp edges by Angle '''
    test_seams = 24
    bpy.ops.uv.zenuv_auto_mark()

    seams = _get_seam_edges_ids(context)

    if len(seams) != test_seams:
        raise AddonTestError(f"TEST> Seams edges must be {test_seams} instead of {len(seams)}")


def Test_uv_zenuv_unmark_all(context):
    ''' Remove all the Seams and/or Sharp edges from the mesh '''
    bpy.ops.uv.zenuv_unmark_all()

    seams = _get_seam_edges_ids(context)

    if len(seams) != 0:
        raise AddonTestError(f"TEST> Seams edges must be 0 (zero) instead of {len(seams)}")


def Test_uv_zenuv_sharp_by_uv_islands(context):
    ''' Mark Sharp by existing UV Borders '''
    test_sharp = 14

    _set_sharp(context, [*range(0, 12)], state=False)

    Log.info(f"Sharp Edges cleared. Current sharp edges count --> {len(_get_sharp_edges_ids(context))}")

    bpy.ops.uv.zenuv_sharp_by_uv_islands(unmark_seams=False, unmark_sharp=False)

    sharp = _get_sharp_edges_ids(context)

    Log.info(f"Test performed. Current sharp edges count --> {len(sharp)}")

    if len(sharp) != test_sharp:
        raise AddonTestError(f"TEST> Sharp edges count must be {test_sharp} instead of {len(sharp)}")


def Test_uv_zenuv_unmark_seams(context):
    ''' Unmark selected edges or face borders as Seams and/or Sharp edges '''
    Log.info("Testing in the EDGE Mode")
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    unmark_edge_id = 7
    test_seams = 13
    bpy.ops.mesh.select_all(action='DESELECT')
    seams = _get_seam_edges_ids(context)
    Log.info(f"Current Seams count {len(seams)}")

    _select_edges_by_id_active_obj(context, [unmark_edge_id, ])

    bpy.ops.uv.zenuv_unmark_seams()

    seams = _get_seam_edges_ids(context)
    Log.info(f"Test Performed. Current Seams count {len(seams)}")

    if len(seams) != test_seams:
        raise AddonTestError(f"TEST> Sharp edges count must be {test_seams} instead of {len(seams)}")

    Log.info("Testing in the FACE Mode")
    _prepare_test(context)
    test_count = 11
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')

    _select_faces_by_id_active_obj(context, [1, ])

    bpy.ops.uv.zenuv_unmark_seams()

    seams = _get_seam_edges_ids(context)

    if len(seams) != test_count:
        raise AddonTestError(f"TEST> Seams edges must be {test_count} instead of {len(seams)}")


tests_mark_sys = (
    Test_uv_zenuv_seams_by_sharp,
    Test_uv_zenuv_seams_by_uv_islands,
    Test_uv_zenuv_seams_by_open_edges,
    Test_uv_zenuv_sharp_by_seams,
    Test_mesh_zenuv_select_sharp,
    Test_uv_zenuv_unified_mark,
    Test_uv_zenuv_mark_seams,
    Test_mesh_zenuv_select_seams,
    Test_uv_zenuv_auto_mark,
    Test_uv_zenuv_unmark_all,
    Test_uv_zenuv_sharp_by_uv_islands,
    Test_uv_zenuv_unmark_seams,
)


if __name__ == "__main__":
    pass
