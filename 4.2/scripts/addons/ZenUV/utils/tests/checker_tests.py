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
    get_prefs_within_tests,
)
from ZenUV.zen_checker.checker import ZEN_GENERIC_MAT_NAME
from ZenUV.utils.vlog import Log


def Test_view3d_zenuv_checker_toggle(context):
    ''' Add Checker Texture to the mesh (Toggle) '''
    Log.info('Phase 01')
    bpy.ops.view3d.zenuv_checker_remove()
    gen_mats = [m for m in bpy.data.materials if ZEN_GENERIC_MAT_NAME in m.name]
    if len(gen_mats) != 0:
        raise AddonTestError(f"Phase 01. The checker Materials is not cleared. {gen_mats}")
    else:
        Log.info("Checker Materials was cleared. Phase 01 --> Passed.")

    Log.info('Phase 02')
    bpy.ops.view3d.zenuv_checker_toggle()
    gen_mats = [m for m in bpy.data.materials if ZEN_GENERIC_MAT_NAME in m.name]
    if len(gen_mats) != 0:
        Log.info("Checker Materials exists. Phase 02 --> Passed.")
        Log.info("TEST> --> Passed.")
    else:
        raise AddonTestError(f"TEST> Failed. Phase 02. The checker Materials is not present in the scene. {gen_mats}")


def Test_view3d_zenuv_checker_remove(context):
    ''' Remove Zen UV Checker Nodes from the scene materials '''
    bpy.ops.view3d.zenuv_checker_toggle()
    bpy.ops.view3d.zenuv_checker_remove()
    gen_mats = [m for m in bpy.data.materials if ZEN_GENERIC_MAT_NAME in m.name]
    if len(gen_mats) != 0:
        raise AddonTestError(f"The checker Materials is not cleared. {gen_mats}")


def Test_view3d_zenuv_checker_collect_images(context):
    ''' Refresh Textures from Checker Library Folder '''
    addon_prefs = get_prefs_within_tests()
    addon_prefs.files_dict = ''
    bpy.ops.view3d.zenuv_checker_collect_images()
    # print(addon_prefs.files_dict)
    if addon_prefs.files_dict == '':
        raise AddonTestError('The addon_prefs.files_dict is empty. It must be filled with images.')


def Test_view3d_zenuv_checker_reset(context):
    ''' Reset Zen UV Checker to Default state  '''
    addon_prefs = get_prefs_within_tests()
    current_image_name = addon_prefs.ZenCheckerImages
    test_image_name = current_image_name
    if 'mono' in test_image_name:
        test_image_name.replace('mono', 'color')
    elif 'color' in test_image_name:
        test_image_name.replace('color', 'mono')
    else:
        raise AddonTestError(f'The image suitable for the current test was not found. Current Image is {current_image_name}')

    addon_prefs.ZenCheckerImages = test_image_name

    bpy.ops.view3d.zenuv_checker_reset()

    if addon_prefs.ZenCheckerImages != current_image_name:
        raise AddonTestError(f'TEST> Image name was not changed. {current_image_name}. Test Image Name: {test_image_name}')


def Test_view3d_zenuv_checker_open_editor(context):
    ''' Open Shader Editor with Zen UV Checker Node '''
    # bpy.ops.view3d.zenuv_checker_open_editor()
    raise AddonTestManual


def Test_view3d_zenuv_checker_append_checker_file(context):
    ''' Open File Browser and add
 the selected texture to the Checker Library '''
    # bpy.ops.view3d.zenuv_checker_append_checker_file(filepath="", filter_glob="*.jpg;*.png")
    raise AddonTestManual


def Test_ops_zenuv_checker_reset_path(context):
    ''' Reset Checker Library path to Default State '''
    addon_prefs = get_prefs_within_tests()
    current_path = addon_prefs.assetspath
    addon_prefs.assetspath = "c:\\"

    test_path = addon_prefs.assetspath
    bpy.ops.ops.zenuv_checker_reset_path()
    if current_path == test_path:
        raise AddonTestError(f'TEST> The path was not reset/ Current Path: {current_path}. Tested Path: {test_path}')
    else:
        Log.info('TEST> Passed')


tests_texture_checker_sys = (
    Test_view3d_zenuv_checker_toggle,
    Test_view3d_zenuv_checker_remove,
    Test_view3d_zenuv_checker_collect_images,
    Test_view3d_zenuv_checker_reset,
    Test_view3d_zenuv_checker_open_editor,
    Test_view3d_zenuv_checker_append_checker_file,
    Test_ops_zenuv_checker_reset_path,
)


if __name__ == "__main__":
    pass
