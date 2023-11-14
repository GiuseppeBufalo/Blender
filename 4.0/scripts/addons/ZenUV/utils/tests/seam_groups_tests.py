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
from ZenUV.utils.generic import (
    resort_by_type_mesh
)
from .addon_test_utils import (
    _get_seam_edges_ids,
    _set_seams,
    AddonTestError,
    AddonTestManual
    )
from ZenUV.utils.vlog import Log


def _clear_seam_list(context):
    objs = resort_by_type_mesh(context)
    for obj in objs:
        obj.zen_sg_list.clear()
        obj.zsg_list_index = -1


def _get_list_count_all_objects(context):
    return len([i for obj in resort_by_type_mesh(context) for i in obj.zen_sg_list])


def _get_list_count_active_object(context):
    return len([i for i in context.object.zen_sg_list])


def Test_zen_sg_list_delete_item(context):
    ''' Delete the selected item from the list '''
    begin_count = _get_list_count_active_object(context)
    Log.info(f"Items in the Seam List: {begin_count}")

    bpy.ops.zen_sg_list.new_item()
    Log.info(f"New Item Added. Items in the Seam List: {_get_list_count_active_object(context)}")

    bpy.ops.zen_sg_list.delete_item()

    res_count = _get_list_count_active_object(context)

    if res_count != begin_count:
        raise AddonTestError(f"Active Object Test> List Items count must be {begin_count} instead of {res_count}")

    else:
        Log.info("Active Object Test --> Passed")


def Test_zen_sg_list_move_item(context):
    ''' Move an item in the list '''
    # bpy.ops.zen_sg_list.move_item(direction='UP')
    raise AddonTestManual


def Test_zen_sg_list_new_item(context):
    ''' Add a new item to the list '''
    Log.info(f"Items in the Seam List: {_get_list_count_active_object(context)}")
    _clear_seam_list(context)
    Log.info(f"Clear List performed. Items in the Seam List: {_get_list_count_active_object(context)}")

    bpy.ops.zen_sg_list.new_item()

    res_count = _get_list_count_active_object(context)

    if res_count != 1:
        raise AddonTestError(f"Active Object Test> List Items count must be 1 instead of {res_count}")
    else:
        Log.info("Active Object Test --> Passed")

    res_count = _get_list_count_all_objects(context)

    if res_count != 2:
        raise AddonTestError(f"All Object Test> List Items count must be 2 instead of {res_count}")
    else:
        Log.info("All Objects Test --> Passed")


def Test_uv_zenuv_activate_seam_group(context):
    ''' Set Seams from selected Seam Group '''
    test_count = 14
    bpy.ops.zen_sg_list.new_item()

    _set_seams(context, [*range(0, 11)], state=False)

    bpy.ops.uv.zenuv_activate_seam_group()

    seam_count = len(_get_seam_edges_ids(context))

    if seam_count != test_count:
        raise AddonTestError(f"TEST> Activated Seam count is {seam_count} instead of {test_count}")


def Test_uv_zenuv_assign_seam_to_group(context):
    ''' Assign Seams to selected Seam Group '''
    test_count = 16
    bpy.ops.zen_sg_list.new_item()

    _set_seams(context, [6, ], state=True)

    bpy.ops.uv.zenuv_assign_seam_to_group()

    _set_seams(context, [*range(0, 11)], state=False)

    bpy.ops.uv.zenuv_activate_seam_group()

    seam_count = len(_get_seam_edges_ids(context))

    if seam_count != test_count:
        raise AddonTestError(f"TEST> Activated Seam count is {seam_count} instead of {test_count}")


def Test_view3d_zenuv_set_smooth_by_sharp(context):
    ''' Toggle between Auto Smooth 180° (with sharp edges) and regular smooth modes '''
    init_state = context.object.data.use_auto_smooth

    bpy.ops.view3d.zenuv_set_smooth_by_sharp()

    res_state = context.object.data.use_auto_smooth

    if res_state == init_state:
        raise AddonTestError("TEST> Satate of Object.use_auto_smooth not changed.")


tests_seam_groups_sys = (
    Test_zen_sg_list_delete_item,
    Test_zen_sg_list_move_item,
    Test_zen_sg_list_new_item,
    Test_uv_zenuv_assign_seam_to_group,
    Test_view3d_zenuv_set_smooth_by_sharp,
    Test_uv_zenuv_activate_seam_group,

)


if __name__ == "__main__":
    pass
