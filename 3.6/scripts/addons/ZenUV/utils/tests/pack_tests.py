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
from .addon_test_utils import (
    AddonTestError,
    AddonTestManual,
    _prepare_test,
    _get_bounding_box,
    get_prefs_within_tests,
    _select_faces_by_id_active_obj,
    _get_objs,
    _ensure_facemap,
    _get_selected_faces_ids,
    _get_hided_faces_ids,
    _hide_faces_by_id_active_obj
    )
from ZenUV.utils.vlog import Log
from ZenUV.ops.pack import UVPMmanager, UVPackerManager
from ZenUV.utils.constants import PACK_EXCLUDED_FACEMAP_NAME
from ZenUV.utils import get_uv_islands as island_util


def _prepare_taged_excluded_testing(context):
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_faces_by_id_active_obj(context, [*range(0, 6)])
    bpy.ops.uv.zenuv_tag_pack_excluded()


def _get_tagged_excluded_islands(context):
    islands_finished = []
    for obj in _get_objs(context):
        bm = bmesh.from_edit_mesh(obj.data).copy()
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        finished_facemap = _ensure_facemap(bm, PACK_EXCLUDED_FACEMAP_NAME)
        islands = island_util.get_islands(context, bm)
        islands_finished.extend([island for island in islands if True in [f[finished_facemap] for f in island]])
        bm.free()
    return islands_finished


def Test_uv_zenuv_pack(context):
    ''' Pack all Islands '''
    raise AddonTestManual
    prefs = get_prefs_within_tests()

    # Phase 01. Blender Pack Engine ========================================

    Log.info("Pack Testing.\nPhase 01. Pack Engine --> Blender")
    prefs.packEngine = "BLDR"

    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_pack(display_uv=False)

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center:
        raise AddonTestError(f"Phase 01. 'Blender' Pack was not completed. Init bbox center is equal to result bbox center. Init: {init_bbox.center}, Result: {test_bbox.center}.")
    else:
        Log.info('TEST> Blender Engine --> Passed')

    # Phase 02. UVPackmaster Pack Engine  ==================================

    _prepare_test(context, model='CUBE')

    Log.info("Pack Testing.\nPhase 02. Pack Engine --> UVPackmaster")
    PM = UVPMmanager(context, prefs)
    if PM.get_engine_version() is not None:

        prefs.packEngine = "UVP"

        init_bbox = _get_bounding_box(context)
        Log.info(f"Init BBOX --> {init_bbox.center}")

        bpy.ops.uv.zenuv_pack(display_uv=False)

        test_bbox = _get_bounding_box(context)
        Log.info(f"Test BBOX --> {init_bbox.center}")

        if init_bbox.center == test_bbox.center:
            raise AddonTestError(f"Phase 02. 'UVPackmaster' Pack was not completed. Init bbox center is equal to result bbox center. Init: {init_bbox.center}, Result: {test_bbox.center}.")
        else:
            Log.info("TEST> 'UVPackmaster' --> Passed")
    else:
        Log.info("TEST> Was not completed. UV Packmaster Engine is not present in the Blender.")

    # Phase 03. UVPacker Pack Engine  ==================================

    _prepare_test(context)
    Log.info("Pack Testing.\nPhase 03. Pack Engine --> UVPacker")
    PM = UVPackerManager(context, prefs)
    if PM._engine_is_present():

        prefs.packEngine = "UVPACKER"

        init_bbox = _get_bounding_box(context)

        bpy.ops.uv.zenuv_pack(display_uv=False)

        # Pause Here

        test_bbox = _get_bounding_box(context)

        if init_bbox.center == test_bbox.center:
            raise AddonTestError(f"Phase 03. 'UVPacker' Pack was not completed. Init bbox center is equal to result bbox center. Init: {init_bbox.center}, Result: {test_bbox.center}.")
        else:
            Log.info("TEST> 'UVPacker' --> Passed")
    else:
        Log.info("TEST> Was not completed. 'UVPacker' Engine is not present in the Blender.")


def Test_uv_zenuv_sync_to_uvp(context):
    ''' Transfer Pack settings from Zen UV to UVPackmaster '''
    # bpy.ops.uv.zenuv_sync_to_uvp()
    raise AddonTestManual


def Test_uv_zenuv_offset_pack_excluded(context):
    ''' Move Islands tagged as Excluded from Packing out of UV Area '''
    bpy.ops.uv.zenuv_tag_pack_excluded()
    init_bbox = _get_bounding_box(context)
    bpy.ops.uv.zenuv_offset_pack_excluded(offset=(1, 0))
    test_bbox = _get_bounding_box(context)
    if init_bbox.center == test_bbox.center:
        raise AddonTestError(f"Offset is not completed. Init bbox center is equal to result bbox center. Init: {init_bbox.center}, Result: {test_bbox.center}.")


def Test_uv_zenuv_untag_pack_excluded(context):
    ''' Untag Islands tagged as Excluded from Packing '''
    test_count = 0
    _prepare_taged_excluded_testing(context)
    Log.info(f'Islands tagged as Excluded --> {len(_get_tagged_excluded_islands(context))}')
    bpy.ops.uv.zenuv_untag_pack_excluded()
    count = len(_get_tagged_excluded_islands(context))
    Log.info(f'Untag Performed. Islands tagged as Excluded --> {count}')
    if count != test_count:
        raise AddonTestError(f"Total Tagged as Excluded Islands must be {test_count} instead of {count}")


def Test_uv_zenuv_unhide_pack_excluded(context):
    ''' Unhide Islands tagged as Excluded from Packing '''
    test_count = 6
    _prepare_taged_excluded_testing(context)

    _hide_faces_by_id_active_obj(context, [*range(0, 6)])
    count = len(_get_hided_faces_ids(context))
    if count != test_count:
        raise AddonTestError(f"Phase 01. Hidden faces must be {test_count} instead of {count}")

    test_count = 0

    bpy.ops.uv.zenuv_unhide_pack_excluded()

    count = len(_get_hided_faces_ids(context))
    if count != test_count:
        raise AddonTestError(f"Phase 02. Hidden faces must be {test_count} instead of {count}")


def Test_uv_zenuv_tag_pack_excluded(context):
    ''' Tag Islands as Excluded from Packing '''
    test_count = 1
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_faces_by_id_active_obj(context, [*range(0, 6)])

    bpy.ops.uv.zenuv_tag_pack_excluded()

    count = len(_get_tagged_excluded_islands(context))
    Log.info(f'Tag Performed. Islands tagged as Excluded --> {count}')
    if count != test_count:
        raise AddonTestError(f"Total Tagged as Excluded Islands must be {test_count} instead of {count}")


def Test_uv_zenuv_select_pack_excluded(context):
    ''' Select Islands tagged as Excluded from Packing '''
    test_count = 6
    bpy.ops.mesh.select_all(action='DESELECT')

    if len(_get_selected_faces_ids(context)) != 0:
        raise AddonTestError('bpy.ops DESELECT was not completed')

    _prepare_taged_excluded_testing(context)

    bpy.ops.uv.zenuv_select_pack_excluded(clear_sel=True)
    count = len(_get_selected_faces_ids(context))
    if count != test_count:
        raise AddonTestError(f"Total Selected faces must be {test_count} instead of {count}")


def Test_uv_zenuv_hide_pack_excluded(context):
    ''' Hide Islands tagged as Excluded from Packing '''
    test_count = 6
    _prepare_taged_excluded_testing(context)

    bpy.ops.uv.zenuv_hide_pack_excluded()

    count = len(_get_hided_faces_ids(context))
    if count != test_count:
        raise AddonTestError(f"Total Hidden faces must be {test_count} instead of {count}")


tests_pack_sys = (
    Test_uv_zenuv_sync_to_uvp,
    Test_uv_zenuv_pack,
    Test_uv_zenuv_offset_pack_excluded,
    Test_uv_zenuv_untag_pack_excluded,
    Test_uv_zenuv_unhide_pack_excluded,
    Test_uv_zenuv_tag_pack_excluded,
    Test_uv_zenuv_select_pack_excluded,
    Test_uv_zenuv_hide_pack_excluded,

)


if __name__ == "__main__":
    pass
