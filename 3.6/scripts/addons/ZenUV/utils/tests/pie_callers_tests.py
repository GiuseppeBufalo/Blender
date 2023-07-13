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


def Test_zenuv_pie_caller_top_right(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_top_right(cmd_enum='uv.zenuv_auto_mark', is_menu=True)


def Test_zenuv_pie_caller_bottom(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_bottom(cmd_enum='bpy.ops.uv.zenuv_unwrap("INVOKE_DEFAULT")', is_menu=True)


def Test_zenuv_pie_caller_top(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_top(cmd_enum='bpy.ops.uv.zenuv_isolate_island("INVOKE_DEFAULT")', is_menu=True)


def Test_zenuv_pie_caller_bottom_left(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_bottom_left(cmd_enum='uv.zenuv_quadrify', is_menu=True)


def Test_zenuv_pie_caller_bottom_right(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_bottom_right(cmd_enum='view3d.zenuv_checker_toggle', is_menu=True)


def Test_zenuv_pie_caller_right(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_right(cmd_enum='uv.zenuv_mark_seams', is_menu=True)


def Test_zenuv_pie_caller_left(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_left(cmd_enum='uv.zenuv_unmark_seams', is_menu=True)


def Test_zenuv_pie_caller_top_left(context):
    ''' Click to open Popup '''
    bpy.ops.zenuv.pie_caller_top_left(cmd_enum='uv.zenuv_select_island', is_menu=True)


tests_pie_callers = [
    Test_zenuv_pie_caller_top_right,
    Test_zenuv_pie_caller_bottom,
    Test_zenuv_pie_caller_top,
    Test_zenuv_pie_caller_bottom_left,
    Test_zenuv_pie_caller_bottom_right,
    Test_zenuv_pie_caller_right,
    Test_zenuv_pie_caller_left,
    Test_zenuv_pie_caller_top_left,
]


if __name__ == "__main__":
    pass
