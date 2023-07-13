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


def Test_uv_zenuv_update_addon(context):
    ''' Update Zen UV add-on '''
    bpy.ops.uv.zenuv_update_addon(filepath="", filter_glob="*ZenUV*.zip", files=[], filename="", directory="")


def Test_zenuv_reset_preferences(context):
    ''' Reset preferences to the Default state '''
    bpy.ops.zenuv.reset_preferences()


def Test_view3d_zenuv_check_library(context):
    ''' Check Zen UV Dynamic Library '''
    bpy.ops.view3d.zenuv_check_library()


def Test_uv_zenuv_unregister_library(context):
    ''' Unregister Zen UV Core Library '''
    bpy.ops.uv.zenuv_unregister_library()


def Test_uv_switch_stretch_map(context):
    ''' Display an angle-based stretching map '''
    bpy.ops.uv.switch_stretch_map()


def Test_ops_zenuv_show_prefs(context):
    ''' Set Shortcuts for Zen UV Menus '''
    bpy.ops.ops.zenuv_show_prefs(tabs='KEYMAP')


def Test_view3d_zenuv_draw_tagged(context):
    ''' Draw tagged elements. Inner system Operator '''
    bpy.ops.view3d.zenuv_draw_tagged()


def Test_view3d_zenuv_install_library(context):
    ''' Install Zen UV Dynamic Library '''
    bpy.ops.view3d.zenuv_install_library(filepath="", filter_glob="*.dll", files=[], filename="", directory="")


def Test_zenuv_call_popup(context):
    ''' Call Zen UV Popup menu. You can setup custom hotkey: RMB on the button > Change Shortcut '''
    bpy.ops.zenuv.call_popup()


def Test_zuv_pie_menu(context):
    ''' Call Zen UV - Pie menu. You can setup custom hotkey: RMB on the button > Change Shortcut '''
    bpy.ops.zuv.pie_menu()


def Test_uv_zenuv_debug(context):
    bpy.ops.uv.zenuv_debug()


def Test_zenuv_test_addon_test(context):
    bpy.ops.zenuv_test.addon_test(stop_on_fail=False, report_undefined=True, write_functions=False, write_skipped=False)


def Test_zenuv_check_sel_in_sync_states(context):
    pass


tests_misc = [
    Test_uv_zenuv_update_addon,
    Test_zenuv_reset_preferences,
    Test_view3d_zenuv_check_library,
    Test_uv_zenuv_unregister_library,
    Test_uv_switch_stretch_map,
    Test_ops_zenuv_show_prefs,
    Test_view3d_zenuv_draw_tagged,
    Test_view3d_zenuv_install_library,
    Test_zenuv_call_popup,
    Test_zuv_pie_menu,
    Test_uv_zenuv_debug,
    Test_zenuv_test_addon_test,
    Test_zenuv_check_sel_in_sync_states
]


if __name__ == "__main__":
    pass
