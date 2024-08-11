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
import random
from mathutils import Vector
from ZenUV.utils.vlog import Log
from .addon_test_utils import (
    AddonTestError,
    _select_edges_by_id_active_obj,
    _get_bounding_box,
    _prepare_test,
    _rotate_uv
    )


def is_same_vectors(vec01, vec02):
    if round(vec01[0], 4) == round(vec02[0], 4) and round(vec01[1], 4) == round(vec02[1], 4):
        return True
    return False


def _get_2d_cursor_pos(context):
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            return area.spaces.active.cursor_location
    return None


def _set_2d_cursor_pos(context, position):
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.spaces.active.cursor_location = position
            return True
    return False


# Unified Transform Operator

def Test_uv_zenuv_unified_transform(context):
    ''' Move Islands '''
    transform_modes = (
        "MOVE",
        "SCALE",
        "ROTATE",
        "FLIP",
        "FIT",
        "ALIGN"
    )
    pp_pos = (
        "tl",
        "tc",
        "tr",
        "lc",
        "cen",
        "rc",
        "bl",
        "bc",
        "br"
    )
    prop = context.scene.zen_uv
    skip_values_combination = (("MOVE", "cen"), ("FLIP", "cen"))
    prop.tr_pivot_mode = 'CENTER'
    prop.tr_type = 'ISLAND'
    prop.tr_scale.x = 2.0
    prop.tr_scale.y = 2.0
    for c_mode in transform_modes:
        Log.info(f"Current mode --> {c_mode}")
        for pp in pp_pos:
            _prepare_test(context)
            _rotate_uv(context)
            init_bbox = _get_bounding_box(context)
            combination = (c_mode, pp)
            if combination in skip_values_combination:
                Log.info(f"Tested Combination: {combination}. Skipped.")
                continue
            Log.info(f"Tested Combination: {c_mode, pp}")
            bpy.ops.uv.zenuv_unified_transform(transform_mode=c_mode, orient_by_selected=False, pp_pos=pp, fit_keep_proportion=True, desc="Transform")

            test_bbox = _get_bounding_box(context)
            if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
                raise AddonTestError(f"TEST> Mode: {c_mode, pp}. The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")
            else:
                Log.info("Passed.\n")

    # Testing Mode --> 2DCURSOR:
    pos = (1 + random.random(), 1 + random.random())
    _set_2d_cursor_pos(context, pos)
    init_pos = _get_2d_cursor_pos(context).copy().freeze()
    if init_pos is None:
        raise AddonTestError('TEST> Mode --> 2DCURSOR. There is no 2D Cursor position. Possible UV Editior not in UI.')
    _rotate_uv(context, angle=15)
    bpy.ops.uv.zenuv_unified_transform(transform_mode="2DCURSOR", orient_by_selected=False, pp_pos='tr', fit_keep_proportion=True, desc="Transform")

    test_pos = _get_2d_cursor_pos(context)
    if test_pos == init_pos:
        raise AddonTestError(f"TEST> Mode --> 2DCURSOR. The position of 2D Cursor was not changed. Init: {init_pos}. Test: {test_pos}")
    else:
        Log.info("TEST> Mode --> 2DCURSOR. PASSED.")

# Unified Transform Operator END


# Independent Operators

def Test_uv_zenuv_align_grab_position(context):
    "Grab Position"
    prop = context.scene.zen_uv
    temp_value = Vector((10.0, 10.0))
    test_value = Vector((0.0, 0.5))
    prop.tr_align_position = temp_value

    bpy.ops.uv.zenuv_align_grab_position()

    res_value = prop.tr_align_position

    if res_value != test_value:
        raise AddonTestError(f"TEST> scene.zen_uv.tr_align_position was not changed. Test Value: {test_value}. Result: {res_value}.")


def Test_uv_zenuv_unwrap(context):
    ''' Unwrap by Marked edges. If you have selected edges or faces they will be Marked as Seams and/or Sharp edges and Unwrapped after '''
    bpy.ops.mesh.select_all(action='DESELECT')
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_unwrap(action='DEFAULT')

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_distribute_verts(context):
    ''' Distribute vertices along the line '''
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    _select_edges_by_id_active_obj(context, [5, 6, 7, 10])
    context.view_layer.objects.active = context.scene.objects["ZenUvTestCube"]
    _select_edges_by_id_active_obj(context, [5, 6, 7, 10])
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_distribute_verts(desc="Distribute vertices along the line", lock_pos=True, sorting='TOP_LEFT', orient_along='INPLACE', sources='SELECTED', starts_pos='ASIS', ends_pos='ASIS', spacing='GEOMETRY', reverse_start=False, reverse_dir=False, relax_linked=False, relax_mode='ANGLE_BASED', angle=15, offset=(0, 0), offset_u=0, offset_v=0, select_border=True, border_offset=1, border_proportion='SHORT', detect_corners='CORNER_AND_PINS')

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_distribute_islands(context):
    ''' Distributes and sorts the selected islands. '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_distribute_islands(axis='U', from_where=(0, 0), sort_to='NONE', reverse=False, margin=0.005, inplace=False)

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_world_orient(context):
    ''' Rotate Islands the way they are oriented on the Models.
Each method (Organic/Hard Surface) uses a heuristic approach
and correctly orients most of the Islands in its area '''
    _rotate_uv(context)
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_world_orient(method='HARD', rev_x=False, rev_y=False, rev_z=False, rev_neg_x=False, rev_neg_y=False, rev_neg_z=False, further_orient=True, flip_by_axis=False)

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_relax(context):
    ''' Relax selected islands '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_relax()

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_quadrify(context):
    ''' Straighten rectangular shaped Island '''
    _rotate_uv(context)
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_quadrify()

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_reshape_island(context):
    ''' Changes the form of the island in accordance with the input parameters '''
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    _select_edges_by_id_active_obj(context, [5, 6, 7, 10])
    context.view_layer.objects.active = context.scene.objects["ZenUvTestCube"]
    _select_edges_by_id_active_obj(context, [5, 6, 7, 10])
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_reshape_island(lock_pos=True, sorting='TOP_LEFT', orient_along='AUTO', sources='SELECTED', starts_pos='ASIS', ends_pos='ASIS', spacing='GEOMETRY', reverse_start=False, reverse_dir=False, relax_linked=True, relax_mode='ANGLE_BASED', angle=15, offset=(0, 0), offset_u=0, offset_v=0, select_border=True, border_offset=1, border_proportion='SHORT', detect_corners='CORNER_AND_PINS')

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_arrange_transform(context):
    ''' Arrange selected islands '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_arrange_transform('INVOKE_DEFAULT', quant=(0, 0), quant_u=0, quant_v=0, count_u=0, count_v=0, reposition=(0, 0), limit=(1, 1), input_mode='SIMPLIFIED', start_from='INPLACE', randomize=False, seed=132, scale=1)

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_randomize_transform(context):
    ''' Randomize Transformation '''
    init_bbox = _get_bounding_box(context)

    bpy.ops.uv.zenuv_randomize_transform(transform_islands='ISLAND', move_u=1.0, move_v=0, uniform_move=True, scale_u=0, scale_v=0, uniform_scale=True, rotate=0, shaker=132)

    test_bbox = _get_bounding_box(context)

    if init_bbox.center == test_bbox.center and init_bbox.len_x == test_bbox.len_x:
        raise AddonTestError(f"TEST>The transformation was not completed. Init BBOX: {init_bbox.center}. Test BBOX: {test_bbox.center}")


def Test_uv_zenuv_tr_scale_tuner(context):
    ''' Tune Scale parameters '''
    prop = context.scene.zen_uv
    # Set Default values
    prop.tr_scale.x = 2.0
    prop.tr_scale.y = 2.0

    test_value = Vector((8.0, 8.0))

    bpy.ops.uv.zenuv_tr_scale_tuner(mode='DOUBLE', axis='XY')
    bpy.ops.uv.zenuv_tr_scale_tuner(mode='DOUBLE', axis='XY')

    res_value = prop.tr_scale
    if res_value != test_value:
        raise AddonTestError(f"TEST> Mode DOUBLE. scene.zen_uv.prop.tr_scale was not changed. Test Value: {test_value}. Result: {res_value}.")

    test_value = Vector((4.0, 4.0))

    bpy.ops.uv.zenuv_tr_scale_tuner(mode='HALF', axis='XY')
    res_value = prop.tr_scale
    if res_value != test_value:
        raise AddonTestError(f"TEST> Mode HALF. scene.zen_uv.prop.tr_scale was not changed. Test Value: {test_value}. Result: {res_value}.")

    test_value = Vector((1.0, 1.0))

    bpy.ops.uv.zenuv_tr_scale_tuner(mode='RESET', axis='XY')

    res_value = prop.tr_scale
    if res_value != test_value:
        raise AddonTestError(f"TEST> Mode RESET. scene.zen_uv.prop.tr_scale was not changed. Test Value: {test_value}. Result: {res_value}.")


# Fit Region

def Test_uv_zenuv_scale_grab_size(context):
    ''' Grab size from the selection '''
    init_value = 0.0
    test_value = 2.0
    scene = context.scene
    scene.zen_uv.unts_desired_size = init_value
    bpy.ops.mesh.select_all(action='DESELECT')
    _select_edges_by_id_active_obj(context, [0, ])

    bpy.ops.uv.zenuv_scale_grab_size(multiplier=1, units='m')

    resulting_value = scene.zen_uv.unts_desired_size
    if resulting_value != test_value:
        raise AddonTestError(f"scene.zen_uv.unts_desired_size was not changed. Init: {init_value}. Test: {test_value}. Result: {resulting_value}")


def Test_uv_zenuv_fit_region(context):
    ''' Fit into Region '''
    prop = context.scene.zen_uv
    init_region = (Vector((0.1, 0.1)), Vector((0.8, 0.8)))

    prop.tr_fit_region_bl = Vector((0.0, 0.0))
    prop.tr_fit_region_tr = Vector((1.0, 1.0))

    Log.info(f"The Region is filled with default values. bl: {prop.tr_fit_region_bl}. tr: {prop.tr_fit_region_tr}")

    prop.tr_fit_region_bl = init_region[0]
    prop.tr_fit_region_tr = init_region[1]

    Log.info(f"The Region is filled with init values. bl: {prop.tr_fit_region_bl}. tr: {prop.tr_fit_region_tr}")

    bpy.ops.uv.zenuv_fit_region(fit_keep_proportion=False, st_fit_mode='cen')

    test_bbox = _get_bounding_box(context)

    if not is_same_vectors(test_bbox.bot_left, init_region[0]) or not is_same_vectors(test_bbox.top_right, init_region[1]):
        raise AddonTestError(f"test_bbox is wrong. Must be bl: {init_region[0]}. tr: {init_region[1]} instead of bl: {test_bbox.bot_left}. tr: {test_bbox.top_right}")


def Test_uv_zenuv_fit_grab_region(context):
    ''' Grab Region '''

    init_region = (Vector((-0.8750, 0.0000)), Vector((0.8750, 1.0000)))

    bpy.ops.uv.zenuv_fit_grab_region(selected_only=True, desc="Grab Region coordinates form Selection")

    test_bbox = _get_bounding_box(context)

    if not is_same_vectors(test_bbox.bot_left, init_region[0]) or not is_same_vectors(test_bbox.top_right, init_region[1]):
        raise AddonTestError(f"test_bbox is wrong. Must be bl: {init_region[0]}. tr: {init_region[1]} instead of bl: {test_bbox.bot_left}. tr: {test_bbox.top_right}")

# Fit Region END


tests_transform_sys = (
    Test_uv_zenuv_unified_transform,
    Test_uv_zenuv_arrange_transform,
    Test_uv_zenuv_randomize_transform,
    Test_uv_zenuv_tr_scale_tuner,
    Test_uv_zenuv_fit_region,
    Test_uv_zenuv_fit_grab_region,
    Test_uv_zenuv_quadrify,
    Test_uv_zenuv_reshape_island,
    Test_uv_zenuv_scale_grab_size,
    Test_uv_zenuv_relax,
    Test_uv_zenuv_unwrap,
    Test_uv_zenuv_distribute_verts,
    Test_uv_zenuv_distribute_islands,
    Test_uv_zenuv_world_orient,
    Test_uv_zenuv_align_grab_position

)


if __name__ == "__main__":
    pass
