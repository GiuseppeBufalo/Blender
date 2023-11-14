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
from ZenUV.utils.constants import ADV_UV_MAP_NAME_PATTERN, ZUV_COPIED, TEST_OBJ_NAME_CUBE
from .addon_test_utils import (
    AddonTestError,
    AddonTestManual,
    _select_faces_by_id_active_obj,
    _set_object_mode,
    _set_edit_mode,
    _move_uv,
    _get_bounding_box
    )
from ZenUV.utils.vlog import Log


def _get_uv_layers_active_obj(context):
    return [layer for layer in context.object.data.uv_layers]


def Test_mesh_rename_uvs(context):
    ''' - Rename all UV Maps using UVChannel_* pattern.
- Hold * (Zen Modifier Key) to apply on all selected objects '''

    bpy.ops.mesh.rename_uvs(name_pattern=ADV_UV_MAP_NAME_PATTERN, use_numbering=True, use_default_name=False, active_only=False, desc="- Rename all UV Maps using UVChannel_* pattern.\n- Hold * (Zen Modifier Key) to apply on all selected objects")
    uv_layers = _get_uv_layers_active_obj(context)
    if ADV_UV_MAP_NAME_PATTERN not in uv_layers[0].name:
        raise AddonTestError(f"UV Map name was not changed. Must be {ADV_UV_MAP_NAME_PATTERN} instead of {uv_layers[0].name}")


def Test_mesh_remove_inactive_uvs(context):
    ''' - Remove all inactive UV Maps.
- Hold * (Zen Modifier Key) to apply on all selected objects '''
    Log.info('Testing Phase --> 01')
    test_count = 3
    bpy.ops.mesh.add_uvs(desc="- Duplicate active UV Map.\n- Hold * (Zen Modifier Key) to apply on all selected objects", mode='DEFAULT')
    bpy.ops.mesh.add_uvs(desc="- Duplicate active UV Map.\n- Hold * (Zen Modifier Key) to apply on all selected objects", mode='DEFAULT')
    uv_layers = _get_uv_layers_active_obj(context)
    Log.info(f"Phase 01. UV Maps: {uv_layers}")
    if len(uv_layers) != test_count:
        raise AddonTestError(f"UV Maps count in Testing Phase 01 must be {test_count} instead of {len(uv_layers)}")
    else:
        Log.info('Testing Phase 01 --> Done')
    bpy.ops.mesh.remove_inactive_uvs('INVOKE_DEFAULT', desc="- Remove all inactive UV Maps.\n- Hold * (Zen Modifier Key) to apply on all selected objects")
    test_count = 1
    uv_layers = _get_uv_layers_active_obj(context)
    Log.info(f"Phase 01. UV Maps: {uv_layers}")
    if len(uv_layers) != test_count:
        raise AddonTestError(f"UV Maps count in Testing Phase 02 must be {test_count} instead of {len(uv_layers)}")
    else:
        Log.info('Testing Phase 02 --> Done')


def Test_mesh_sync_uv_ids(context):
    ''' - Set the same active UV Map index for all selected objects.
- Hold * (Zen Modifier Key) to enable/disable automatic synchronization.
- Blue background - UV Maps are synchronized.
- Red background - UV Maps are desynchronized '''
    # bpy.ops.mesh.sync_uv_ids(desc="- Set the same active UV Map index for all selected objects.\n- Hold * (Zen Modifier Key) to enable/disable automatic synchronization.\n- Blue background - UV Maps are synchronized.\n- Red background - UV Maps are desynchronized")
    raise AddonTestManual


def Test_mesh_remove_uvs(context):
    ''' - Remove active UV Map.
- Hold * (Zen Modifier Key) to apply on all selected objects '''
    test_count = 0

    bpy.ops.mesh.remove_uvs('INVOKE_DEFAULT', desc="- Remove active UV Map.\n- Hold * (Zen Modifier Key) to apply on all selected objects")
    uv_layers = _get_uv_layers_active_obj(context)
    if len(uv_layers) != test_count:
        raise AddonTestError(f"UV Maps count must be {test_count} instead of {len(uv_layers)}")


def Test_mesh_show_uvs(context):
    ''' Display selected UV Map '''
    # bpy.ops.mesh.show_uvs(desc="Display selected UV Map")
    raise AddonTestManual


def Test_mesh_add_uvs(context):
    ''' - Duplicate active UV Map.
- Hold * (Zen Modifier Key) to apply on all selected objects '''
    test_count = 2
    bpy.ops.mesh.add_uvs('INVOKE_DEFAULT', desc="- Duplicate active UV Map.\n- Hold * (Zen Modifier Key) to apply on all selected objects", mode='DEFAULT')
    uv_layers = _get_uv_layers_active_obj(context)
    if len(uv_layers) != test_count:
        raise AddonTestError(f"UV Maps count must be {test_count} instead of {len(uv_layers)}")


# Copy / Paste UV Sys

def Test_uv_zenuv_copy_uv(context):
    ''' Copy the UV coordinates of the selection '''
    scene = context.scene
    del scene.zen_uv[ZUV_COPIED]
    Log.info("The Init Data is cleared.")
    data = scene.zen_uv.get(ZUV_COPIED, None)
    if data is not None:
        raise AddonTestError(f"Scene ZenUV Copied Data is Not Cleared --> {data}")
    else:
        Log.info('Scene ZenUV Copied Data is Cleared')

    bpy.ops.uv.zenuv_copy_uv(desc="Copy the UV coordinates of the selection")

    data = scene.zen_uv.get(ZUV_COPIED, None)

    if data is None:
        raise AddonTestError("Scene ZenUV Copied Data is None.")
    else:
        Log.info(f'Test Passed. Scene ZenUV Copied Data is {data}')


def Test_uv_zenuv_paste_uv(context):
    ''' Paste the parameters saved earlier to selected Islands/Faces '''

    context.scene.tool_settings.use_uv_select_sync = True
    _set_object_mode(context)
    obj = bpy.context.scene.objects[TEST_OBJ_NAME_CUBE]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    _set_edit_mode(context)
    _select_faces_by_id_active_obj(context, [*range(0, 6)])

    bpy.ops.uv.zenuv_copy_uv(desc="Copy the UV coordinates of the selection")
    bpy.ops.mesh.add_uvs('INVOKE_DEFAULT', desc="- Duplicate active UV Map.\n- Hold * (Zen Modifier Key) to apply on all selected objects", mode='DEFAULT')
    _move_uv(context, offset=(0, 1))
    init_bbox = _get_bounding_box(context)
    bpy.ops.uv.zenuv_paste_uv(desc="Paste the UV coordinates")
    res_bbox = _get_bounding_box(context)

    if init_bbox.center == res_bbox.center:
        raise AddonTestError("UV Island position was not changed. Paste UV does not work as expected.")


def Test_wm_auto_sync_uv_ids(context):
    ''' Automatically set the same active UV Map
index for all selected objects '''
    # bpy.ops.wm.auto_sync_uv_ids()
    raise AddonTestManual


tests_adv_uv_maps_sys = (
    Test_mesh_rename_uvs,
    Test_mesh_remove_inactive_uvs,
    Test_mesh_sync_uv_ids,
    Test_mesh_remove_uvs,
    Test_mesh_show_uvs,
    Test_mesh_add_uvs,
    Test_uv_zenuv_copy_uv,
    Test_uv_zenuv_paste_uv,
    Test_wm_auto_sync_uv_ids,
)


if __name__ == "__main__":
    pass
