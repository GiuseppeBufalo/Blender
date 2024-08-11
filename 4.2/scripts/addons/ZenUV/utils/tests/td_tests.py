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
    _set_object_mode,
    _set_edit_mode,
    get_prefs_within_tests,
    AddonTestError,
    AddonTestManual
    )
from ZenUV.utils.vlog import Log


def _reset_td_state(context):
    addon_prefs = get_prefs_within_tests()
    addon_prefs.TD_TextureSizeX = 1024
    addon_prefs.TD_TextureSizeY = 1024
    addon_prefs.td_unit = 'm'

# ---------------------------------------------------------------------------------------
# Texel Density System Object Mode --> Start


def Test_uv_zenuv_set_texel_density_obj(context):
    ''' Set Texel Density to selected Objects '''
    addon_prefs = get_prefs_within_tests()
    # _prepare_test(context)
    _set_object_mode(context)
    _reset_td_state(context)

    # 1-st
    bpy.ops.uv.zenuv_set_texel_density_obj(td=1024, u=1024, v=1024, units='m', mode='overall')
    bpy.ops.uv.zenuv_get_texel_density_obj('INVOKE_DEFAULT')
    Log.info(f"TEST 01> Texel Density is {addon_prefs.TexelDensity}")

    if addon_prefs.TexelDensity != 1024:
        raise AddonTestError(f"TEST 01> Resulted TD must be 1024 instead of {addon_prefs.TexelDensity}")

    # 2-nd
    bpy.ops.uv.zenuv_set_texel_density_obj(td=50, u=1024, v=1024, units='m', mode='overall')
    bpy.ops.uv.zenuv_get_texel_density_obj('INVOKE_DEFAULT')
    Log.info(f"TEST 02> Texel Density is {addon_prefs.TexelDensity}")

    if addon_prefs.TexelDensity != 50:
        raise AddonTestError(f"TEST 02> Resulted TD must be 50 instead of {addon_prefs.TexelDensity}")


def Test_uv_zenuv_get_texel_density_obj(context):
    ''' Get Texel Density from selected Islands '''
    _reset_td_state(context)
    addon_prefs = get_prefs_within_tests()
    Log.info("Testing --> Get Texel Density from selected Objects")

    _set_object_mode(context)

    temp_value = 16.4
    test_value = 128

    addon_prefs.TexelDensity = temp_value

    Log.info(f"Current TD is set to temporary value: {temp_value}")

    bpy.ops.uv.zenuv_get_texel_density_obj('INVOKE_DEFAULT')

    res_value = addon_prefs.TexelDensity
    Log.info(f"Test performed. Result TD is {res_value}")

    if res_value != test_value:
        raise AddonTestError(f"TEST> OBJECT Mode. Result TD must be {test_value} instead of {res_value}")


# Texel Density System. Object Mode --> End
# ---------------------------------------------------------------------------------------


# Texel Density System. Mesh Mode --> Start

def Test_uv_zenuv_hide_texel_density(context):
    ''' Disable displaying Texel Density in Viewport by chosen TD Checker value and colors '''
    # bpy.ops.uv.zenuv_hide_texel_density(map_type='BALANCED')
    raise AddonTestManual


def Test_uv_zenuv_display_td_balanced(context):
    ''' Display Balanced Texel Density in Viewport by chosen TD Checker value and colors '''
    # bpy.ops.uv.zenuv_display_td_balanced(face_mode=False)
    raise AddonTestManual


def Test_zenuv_set_current_td_to_checker_td(context):
    ''' Set Current TD value to Checker TD value '''
    _reset_td_state(context)
    addon_prefs = get_prefs_within_tests()
    tested_value = 12.0
    addon_prefs.TexelDensity = tested_value
    Log.info(f"Current TD is {addon_prefs.TexelDensity}")
    Log.info(f"Current Checker TD is {addon_prefs.td_checker}")

    bpy.ops.zenuv.set_current_td_to_checker_td()

    Log.info(f"Test performed. Current Checker TD is {addon_prefs.td_checker}")

    if addon_prefs.td_checker != tested_value:
        raise AddonTestError(f"TEST> Checker TD must be {tested_value} instead of {addon_prefs.td_checker}")


def Test_uv_zenuv_get_texel_density(context):
    ''' Get Texel Density from selected Islands '''
    _reset_td_state(context)
    bpy.ops.mesh.select_all(action='SELECT')
    # _set_object_mode(context)
    _set_edit_mode(context)
    temp_value = 12.5
    res_value = 128
    addon_prefs = get_prefs_within_tests()
    addon_prefs.TexelDensity = temp_value

    Log.info(f"Current TD is set to temporary value: {temp_value}")

    bpy.ops.uv.zenuv_get_texel_density()

    Log.info(f"Test performed. Result TD is {addon_prefs.TexelDensity}")

    if addon_prefs.TexelDensity != res_value:
        raise AddonTestError(f"TEST> EDIT Mode. Result TD must be {res_value} instead of {temp_value}")


def Test_uv_zenuv_set_texel_density(context):
    ''' Set Texel Density to selected Islands '''
    _reset_td_state(context)
    res_value = 12.0
    addon_prefs = get_prefs_within_tests()

    addon_prefs.TexelDensity = 2.0
    bpy.ops.uv.zenuv_get_texel_density()
    Log.info(f"Current TD is {addon_prefs.TexelDensity}")

    addon_prefs.TexelDensity = res_value
    Log.info(f"Current TD is set to value: {res_value}")
    bpy.ops.uv.zenuv_set_texel_density()
    bpy.ops.uv.zenuv_get_texel_density()
    Log.info(f"Test performed. Current TD is {addon_prefs.TexelDensity}")

    if addon_prefs.TexelDensity != res_value:
        raise AddonTestError(f"TEST> Result TD must be {res_value} instead of {addon_prefs.TexelDensity}")


def Test_uv_zenuv_get_uv_coverage(context):
    ''' Recalculate UV Coverage '''
    _reset_td_state(context)
    addon_prefs = get_prefs_within_tests()
    addon_prefs.UVCoverage = 0
    tested_coverage = 75.0
    _set_object_mode(context)
    Log.info(f"UV Coverage is reset. Current UV Coverage: {addon_prefs.UVCoverage}")
    Log.info("Testing in OBJECT Mode...")
    bpy.ops.uv.zenuv_get_uv_coverage()

    res_value = round(addon_prefs.UVCoverage, 0)

    Log.info(f"Test performed. Current UV Coverage: {res_value}")

    if res_value != tested_coverage:
        raise AddonTestError(f"TEST> UV Coverage in the OBJECT Mode must be {tested_coverage} instead of {res_value}")

    Log.info("Testing in EDIT Mode...")
    _set_edit_mode(context)
    addon_prefs.UVCoverage = 0
    Log.info(f"UV Coverage is reset. Current UV Coverage: {addon_prefs.UVCoverage}")

    bpy.ops.uv.zenuv_get_uv_coverage()

    res_value = round(addon_prefs.UVCoverage, 0)

    Log.info(f"Test performed. Current UV Coverage: {res_value}")

    if res_value != tested_coverage:
        raise AddonTestError(f"TEST> UV Coverage in the EDIT mode must be {tested_coverage} instead of {res_value}")


def Test_uv_zenuv_get_image_size_uv_layout(context):
    ''' Get image size from the image displayed in UV Editor '''
    _reset_td_state(context)
    addon_prefs = get_prefs_within_tests()
    image_name = "Zen UV Test Image"
    Log.info(f"Init Image Size X is: {addon_prefs.TD_TextureSizeX}")

    bpy.ops.image.new(name=image_name, width=122, height=123, color=(0, 0, 0, 1), alpha=True, generated_type='COLOR_GRID', float=False, use_stereo_3d=False, tiled=False)
    test_image = bpy.data.images[image_name]

    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.spaces.active.image = test_image

    bpy.ops.uv.zenuv_get_image_size_uv_layout()
    Log.info(f"Result Image Size X is: {addon_prefs.TD_TextureSizeX}")
    if addon_prefs.TD_TextureSizeX != 122:
        raise AddonTestError(f"TEST> Image Size X is {addon_prefs.TexelDensity} instead of 122. Possible UV Editor not in the UI. Recommended Manual Testing.")

# Texel Density System Mesh Mode --> End
# ---------------------------------------------------------------------------------------


# Texel Density System Presets Testing --> Start

def Test_zen_tdpr_generate_presets(context):
    '''Generate Presets'''
    _reset_td_state(context)
    scene = context.scene
    Log.info(f"Current Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.clear_presets()
    Log.info(f"List cleared. Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.generate_presets()
    Log.info(f"Preset Generated. Items In the List: {len(scene.zen_tdpr_list)}")


def Test_zen_tdpr_set_td_from_preset(context):
    ''' Set TD from active preset to selected Islands '''
    _reset_td_state(context)
    bpy.ops.zen_tdpr.generate_presets()
    bpy.ops.zen_tdpr.set_td_from_preset()
    bpy.ops.uv.zenuv_get_texel_density()
    Log.debug()


def Test_zen_tdpr_move_item(context):
    ''' Move an item in the list '''
    _reset_td_state(context)
    bpy.ops.zen_tdpr.clear_presets()
    bpy.ops.zen_tdpr.generate_presets()
    bpy.ops.zen_tdpr.move_item(direction='UP')
    bpy.ops.zen_tdpr.move_item(direction='DOWN')


def Test_zen_tdpr_new_item(context):
    '''Add a new item to the list'''
    _reset_td_state(context)
    scene = context.scene
    Log.info(f"Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.clear_presets()
    Log.info(f"Clear List performed. Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.new_item()
    Log.info(f"New Item created. Items In the List: {len(scene.zen_tdpr_list)}")
    if len(scene.zen_tdpr_list) != 1:
        raise AddonTestError(f"TEST> Items in the List must be 1 instead of {len(scene.zen_tdpr_list)}")


def Test_zen_tdpr_delete_item(context):
    ''' Delete the selected item from the list '''
    _reset_td_state(context)
    scene = context.scene
    # scene.zen_tdpr_list_index
    Log.info(f"Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.clear_presets()
    Log.info(f"Presets Cleared. Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.new_item()
    Log.info(f"New Item Created Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.delete_item()
    Log.info(f"The Item deleted. Items In the List: {len(scene.zen_tdpr_list)}")


def Test_zen_tdpr_clear_presets(context):
    ''' Clear '''
    _reset_td_state(context)
    scene = context.scene
    Log.info(f"Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.generate_presets()
    Log.info(f"Presets generated. Items In the List: {len(scene.zen_tdpr_list)}")
    bpy.ops.zen_tdpr.clear_presets()
    Log.info(f"List Cleared. Items In the List: {len(scene.zen_tdpr_list)}")


def Test_uv_zenuv_display_td_preset(context):
    ''' Display Presets '''
    # bpy.ops.uv.zenuv_display_td_preset(face_mode=False, presets_only=False)
    raise AddonTestManual


def Test_zen_tdpr_select_by_texel_density(context):
    ''' Select Islands By Texel Density '''
    _reset_td_state(context)
    import bmesh
    tested_value = 128.0
    prefs = get_prefs_within_tests()
    prefs.TexelDensity = tested_value
    bpy.ops.mesh.select_all(action='DESELECT')
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data).copy()
    s_faces = [f.index for f in bm.faces if f.select]
    bm.free()
    Log.info(f'Current object: {obj.name}. Selected faces: {len(s_faces)}')

    bpy.ops.zen_tdpr.select_by_texel_density(texel_density=tested_value, treshold=0.01, clear_selection=True, sel_underrated=False, sel_overrated=False, by_value=True)

    bm = bmesh.from_edit_mesh(obj.data).copy()
    s_faces = [f.index for f in bm.faces if f.select]
    bm.free()
    Log.info(f'Test performed. Current object: {obj.name}. Selected faces: {len(s_faces)}')
    if len(s_faces) != 6:
        raise AddonTestError(f"TEST> Selected faces with TD {tested_value} must be 6 instead of {len(s_faces)}")


def Test_zen_tdpr_get_td_from_preset(context):
    '''Get TD from selected Islands to active preset'''
    _reset_td_state(context)
    bpy.ops.zen_tdpr.clear_presets()
    bpy.ops.zen_tdpr.new_item()
    from ZenUV.ops.texel_presets import PRESET_NEW
    default_new_value = PRESET_NEW["value"]
    Log.info(f"New List Item Created. Current Value: {default_new_value}")
    bpy.ops.zen_tdpr.get_td_from_preset()
    scene = context.scene
    list_index = scene.zen_tdpr_list_index
    if list_index in range(len(scene.zen_tdpr_list)):
        new_value = scene.zen_tdpr_list[list_index].value
    Log.info(f"Operator test performed. Current Value: {new_value}")
    if new_value != 128.0:
        raise AddonTestError(f"TEST> Resulted TD must be 128.0 instead of {new_value}")

# Texel Density System Presets Testing --> End
# ---------------------------------------------------------------------------------------


tests_texel_density = (
    Test_zen_tdpr_move_item,
    Test_uv_zenuv_set_texel_density_obj,
    Test_zen_tdpr_set_td_from_preset,
    Test_zen_tdpr_clear_presets,
    Test_uv_zenuv_display_td_preset,
    Test_zen_tdpr_delete_item,
    Test_uv_zenuv_hide_texel_density,
    Test_zen_tdpr_select_by_texel_density,
    Test_uv_zenuv_display_td_balanced,
    Test_zenuv_set_current_td_to_checker_td,
    Test_zen_tdpr_new_item,
    Test_zen_tdpr_generate_presets,
    Test_zen_tdpr_get_td_from_preset,
    Test_uv_zenuv_get_texel_density_obj,
    Test_uv_zenuv_get_texel_density,
    Test_uv_zenuv_set_texel_density,
    Test_uv_zenuv_get_uv_coverage,
    Test_uv_zenuv_get_image_size_uv_layout
)


if __name__ == "__main__":
    pass
