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
from .addon_test_utils import (
    AddonTestError,
    AddonTestManual,
    _select_faces_by_id_active_obj,
    _set_object_mode,
    _set_edit_mode,
    _move_uv,
    _get_bounding_box,
    _select_objs_by_names,
    _get_selected_faces_ids
    )
from ZenUV.utils.vlog import Log
from ZenUV.utils.constants import ZUV_STORED


# Automatic Stack Tests

def Test_uv_zenuv_select_stack(context):
    ''' Select Stack Parts '''
    # Tested only in the SINGLES mode
    context.scene.zen_display.stack_display_mode = 'SINGLES'
    test_count = 6
    bpy.ops.mesh.select_all(action='DESELECT')
    _set_object_mode(context)
    bpy.ops.object.select_all(action='DESELECT')
    obj = context.scene.objects["ZenUvTestCube"]
    obj.select_set(True)
    context.view_layer.objects.active = obj
    _set_edit_mode(context)

    bpy.ops.uv.zenuv_select_stack('INVOKE_DEFAULT', select_master=True, select_stack=True, select_singles=True, desc="Select Stack Parts")

    count = len(_get_selected_faces_ids(context))

    if count != test_count:
        raise AddonTestError(f"Stacked Selection incorrect. Must be {test_count} instead of {count}")


def Test_uv_zenuv_select_stacked(context):
    ''' Clear Selection and Select Stacked Islands
* (Zen Modifier Key) - Append to existing Selection '''
    test_count = 12

    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.uv.zenuv_stack_similar(silent=True, selected=False)

    bpy.ops.uv.zenuv_select_stacked('INVOKE_DEFAULT')

    count = len(_get_selected_faces_ids(context))

    if count != test_count:
        raise AddonTestError(f"Stacked Selection incorrect. Must be {test_count} instead of {count}")


def Test_uv_zenuv_unstack(context):
    ''' Shift Islands from Stacks in the given direction '''
    init_bbox = _get_bounding_box(context)
    bpy.ops.uv.zenuv_stack_similar(silent=True, selected=False)
    stacked_bbox = _get_bounding_box(context)
    if init_bbox.center == stacked_bbox.center:
        raise AddonTestError("Phase 01. Stack Similar was not performed.")

    bpy.ops.uv.zenuv_unstack('INVOKE_DEFAULT', RelativeToPrimary=False, UnstackMode='STACKED', breakStack=False, increment=1, selected=False)

    unstacked_bbox = _get_bounding_box(context)
    if stacked_bbox.center == unstacked_bbox.center:
        raise AddonTestError(f"Phase 02. Unstack Similar was not performed. Stacked BBOX: {stacked_bbox.center} Unstacked BBOX: {unstacked_bbox.center}")


def Test_uv_zenuv_stack_similar(context):
    ''' Collect Similar Islands on Stacks '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_stack_similar('INVOKE_DEFAULT', silent=True, selected=False)

    stacked_bbox = _get_bounding_box(context)
    if init_bbox.center == stacked_bbox.center:
        raise AddonTestError(f"Phase 02. Unstack Similar was not performed. Stacked BBOX: {init_bbox.center} Unstacked BBOX: {stacked_bbox.center}")

# Automatic Stack Tests END


# Copy / Paste System Tests

def Test_uv_zenuv_copy_param(context):
    ''' Copy parameters of selected Islands/Faces and save them '''
    scene = context.scene
    scene.zen_uv[ZUV_STORED] = None

    Log.info(f"copy/paste data cleared. Data --> {(context.scene.zen_uv[ZUV_STORED])}")

    bpy.ops.mesh.select_all(action='SELECT')

    # _select_faces_by_id_active_obj(context, [*range(0, 6)])
    bpy.ops.uv.zenuv_copy_param('INVOKE_DEFAULT', st_store_mode='ISLAND', desc="Copy parameters of selected Islands/Faces and save them")

    Log.info(f"Stored Data: {context.scene.zen_uv[ZUV_STORED]}")
    if not scene.zen_uv.get(ZUV_STORED, None):
        raise AddonTestError('TEST> There is no stored data')


def Test_uv_zenuv_paste_param(context):
    ''' Paste the parameters saved earlier to selected Islands/Faces '''
    init_bbox = _get_bounding_box(context)
    _set_object_mode(context)
    obj_master = bpy.context.scene.objects["ZenUvTestCube"]
    obj_replica = bpy.context.scene.objects["ZenUvTestCube.001"]
    obj_master.data.polygons[0].select = True
    _set_edit_mode(context)
    bpy.ops.uv.zenuv_copy_param(st_store_mode='ISLAND', desc="Copy parameters of selected Islands/Faces and save them")
    _set_object_mode(context)
    obj_master.data.polygons[0].select = False
    obj_replica.data.polygons[0].select = True
    _set_edit_mode(context)

    bpy.ops.uv.zenuv_paste_param('INVOKE_DEFAULT', use_stack_offset=False, fit_proportional=True, st_fit_mode='tc', st_store_mode='ISLAND', MatchMode='TD', silent=False, TransferMode='STACK', AreaMatch=True, move=False)

    res_bbox = _get_bounding_box(context)

    if init_bbox.center == res_bbox.center:
        raise AddonTestError("UV Island position was not changed. Paste Params does not work as expected.")


# Copy / Paste System Tests END


# Simple Stack System Tests

def Test_uv_zenuv_simple_stack(context):
    ''' Places the islands in the stack, with no respect for their topology '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_simple_stack(position='UVCENTER', custom_position=(0, 0))

    res_bbox = _get_bounding_box(context)

    if init_bbox.center == res_bbox.center:
        raise AddonTestError("UV Island position was not changed. Paste Params does not work as expected.")


def Test_uv_zenuv_simple_unstack(context):
    ''' Shifting the islands in a given direction '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_simple_unstack(direction=(1, 0))

    res_bbox = _get_bounding_box(context)

    if init_bbox.center == res_bbox.center:
        raise AddonTestError("UV Island position was not changed. Paste Params does not work as expected.")

# Simple Stack System Tests END


# Manual Stack Tests

def Test_zen_stack_list_remove_all_m_stacks(context):
    ''' Remove all Manual Stacks from selected Objects '''
    test_count = len(context.object.zen_stack_list)
    bpy.ops.zen_stack_list.new_item()
    bpy.ops.zen_stack_list.new_item()
    test_count += 2
    if test_count == 0:
        raise AddonTestError("TEST> Manual Stacks was not created")

    bpy.ops.zen_stack_list.remove_all_m_stacks()
    count = len(context.object.zen_stack_list)

    if count != 0:
        raise AddonTestError(f"Manual Stack Remove All Manual Stacks was not be performed. Count must be zero instead of {count}")


def Test_uv_zenuv_unstack_manual_stack(context):
    ''' Shift Islands from Manual Stacks in the given direction '''
    init_bbox = _get_bounding_box(context)
    bpy.ops.zen_stack_list.new_item()
    bpy.ops.uv.zenuv_collect_manual_stacks(selected=False)
    stacked_bbox = _get_bounding_box(context)
    if init_bbox.center == stacked_bbox.center:
        raise AddonTestError("Phase 01. Stacking was not performed.")

    bpy.ops.uv.zenuv_unstack_manual_stack('INVOKE_DEFAULT', breakStack=False, increment=1, selected=False)

    unstacked_bbox = _get_bounding_box(context)

    if stacked_bbox.center == unstacked_bbox.center:
        raise AddonTestError(f"Phase 02. Unstack Manual Stack was not performed. Stacked BBOX: {stacked_bbox.center} Unstacked BBOX: {unstacked_bbox.center}")


def Test_zen_stack_list_new_item(context):
    ''' Add new Stack '''
    test_count = len(context.object.zen_stack_list)

    bpy.ops.zen_stack_list.new_item()

    count = len(context.object.zen_stack_list)

    if count == test_count:
        raise AddonTestError(f"Manual Stack New item was not be performed. Count must be {test_count + 1} instead of {count}")


def Test_uv_zenuv_assign_manual_stack(context):
    ''' Append selected Islands to the active Stack '''
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_faces_by_id_active_obj(context, [0, ])
    bpy.ops.zen_stack_list.new_item()

    test_count = 6
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.uv.zenuv_select_m_stack()
    count = len(_get_selected_faces_ids(context))

    if count != test_count:
        raise AddonTestError(f"Phase 01. Manual Stack with count {test_count} must be created instead of {count}")

    # Phase 02
    test_count = 12
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.uv.zenuv_assign_manual_stack()

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.uv.zenuv_select_m_stack()

    count = len(_get_selected_faces_ids(context))

    if count != test_count:
        raise AddonTestError(f"Phase 02. Manual Stack with count {test_count} must be created instead of {count}")


def Test_uv_zenuv_collect_manual_stacks(context):
    ''' Collect Islands on Manual Stacks '''
    init_bbox = _get_bounding_box(context)
    bpy.ops.zen_stack_list.new_item()

    bpy.ops.uv.zenuv_collect_manual_stacks(selected=False)

    res_bbox = _get_bounding_box(context)

    if init_bbox.center == res_bbox.center:
        raise AddonTestError("UV Island position was not changed. Collect Manual Stack does not work as expected.")


def Test_zen_stack_list_delete_item(context):
    ''' Delete selected Stack '''
    bpy.ops.zen_stack_list.new_item()
    bpy.ops.zen_stack_list.new_item()
    test_count = len(context.object.zen_stack_list)

    bpy.ops.zen_stack_list.delete_item()

    count = len(context.object.zen_stack_list)

    if count == test_count:
        raise AddonTestError(f"Manual Stack New item was not be performed. Count must be {test_count - 1} instead of {count}")


def Test_uv_zenuv_analyze_stack(context):
    ''' Analyze Islands Similarities in the Stack. You can find details in the Zen UV Manual Stack Analyze document in the Text Editor '''
    # bpy.ops.uv.zenuv_analyze_stack()
    raise AddonTestManual


def Test_uv_zenuv_select_m_stack(context):
    ''' Select Islands in the Stack '''
    bpy.ops.zen_stack_list.new_item()
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.uv.zenuv_select_m_stack()

    count = len(_get_selected_faces_ids(context))

    if not count:
        raise AddonTestError("Manual Stack Select M Stack was not performed.")


# Manual Stack Tests END


tests_stacks_sys = (
    Test_zen_stack_list_remove_all_m_stacks,
    Test_uv_zenuv_simple_stack,
    Test_uv_zenuv_unstack_manual_stack,
    Test_zen_stack_list_new_item,
    Test_uv_zenuv_select_stack,
    Test_uv_zenuv_select_stacked,
    Test_uv_zenuv_assign_manual_stack,
    Test_uv_zenuv_collect_manual_stacks,
    Test_uv_zenuv_paste_param,
    Test_uv_zenuv_select_m_stack,
    Test_uv_zenuv_simple_unstack,
    Test_uv_zenuv_unstack,
    Test_zen_stack_list_delete_item,
    Test_uv_zenuv_analyze_stack,
    Test_uv_zenuv_stack_similar,
    Test_uv_zenuv_copy_param
)


if __name__ == "__main__":
    pass
