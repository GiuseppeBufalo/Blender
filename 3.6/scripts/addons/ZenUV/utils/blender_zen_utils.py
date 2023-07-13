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

# Copyright 2021, Alex Zhornyak

""" Zen Blender Utils """

import bpy

import platform

from .vlog import Log

class ZenPolls:

    version_greater_3_2_0 = False


class CallerCmdProps:
    bl_op_cls = None
    bl_label = None
    bl_desc = None
    cmd = None


class ZsDrawConstans:
    DEFAULT_VERT_ACTIVE_ALPHA = 80
    DEFAULT_VERT_INACTIVE_ALPHA = 60
    DEFAULT_VERT_ACTIVE_POINT_SIZE = 10
    DEFAULT_VERT_INACTIVE_POINT_SIZE = 6
    DEFAULT_VERT_USE_ZOOM_FACTOR = False

    DEFAULT_EDGE_ACTIVE_ALPHA = 60
    DEFAULT_EDGE_INACTIVE_ALPHA = 40
    DEFAULT_EDGE_ACTIVE_LINE_WIDTH = 3
    DEFAULT_EDGE_INACTIVE_LINE_WIDTH = 2

    DEFAULT_FACE_ACTIVE_ALPHA = 60
    DEFAULT_FACE_INACTIVE_ALPHA = 40

    DEFAULT_OBJECT_ACTIVE_ALPHA = 40
    DEFAULT_OBJECT_INACTIVE_ALPHA = 20
    DEFAULT_OBJECT_COLLECTION_BOUNDBOX_WIDTH = 2
    DEFAULT_OBJECT_COLLECTION_LABEL_SIZE = 12

    BGL_ACTIVE_FONT_COLOR = (0.855, 0.141, 0.07)  # Zen Red Color
    BGL_INACTIVE_FONT_COLOR = (0.8, 0.8, 0.8)


def get_zen_platform():
    s_system = platform.system()
    if s_system == 'Darwin':
        try:
            import sysconfig;
            if 'arch64-apple-darwin' in sysconfig.get_config_vars()['HOST_GNU_TYPE']:
                s_system = 'DarwinSilicon'

        except Exception as e:
            Log.error(e)
    return s_system


def get_command_props(cmd, context=bpy.context) -> CallerCmdProps:

    op_props = CallerCmdProps()

    if cmd:
        op_cmd = cmd
        op_args = '()'

        cmd_split = cmd.split("(", 1)
        if len(cmd_split) == 2:
            op_cmd = cmd_split[0]
            op_args = '(' + cmd_split[1]

        op_cmd_short = op_cmd.replace("bpy.ops.", "", 1)
        op_cmd = f"bpy.ops.{op_cmd_short}"

        try:
            if op_args == '()':
                wm = context.window_manager
                op_last = wm.operator_properties_last(op_cmd_short)
                if op_last:
                    props = op_last.bl_rna.properties
                    keys = set(props.keys()) - {'rna_type'}
                    args = [
                        k + '=' + repr(getattr(op_last, k))
                        for k in dir(op_last)
                        if k in keys and not props[k].is_readonly and not props[k].is_skip_save]

                    if len(args):
                        op_args = f'({",".join(args)})'

            op_props.bl_op_cls = eval(op_cmd)
            op_props.cmd = op_cmd + op_args

            try:
                rna = op_props.bl_op_cls.get_rna().rna_type \
                    if hasattr(op_props.bl_op_cls, "get_rna") \
                    else op_props.bl_op_cls.get_rna_type()

                op_props.bl_label = rna.name
                op_props.bl_desc = rna.description
            except Exception as ex:                
                Log.warn('Description error:', ex)

        except Exception as ex:
            op_props = CallerCmdProps()            
            Log.error('Eval error:', ex, 'cmd:', cmd)

    return op_props


class ZsOperatorAttrs:
    @classmethod
    def get_operator_attr(cls, op_name, attr_name, default=None):
        wm = bpy.context.window_manager
        op_last = wm.operator_properties_last(op_name)
        if op_last:
            return getattr(op_last, attr_name, default)
        return default

    @classmethod
    def set_operator_attr(cls, op_name, attr_name, value):
        wm = bpy.context.window_manager
        op_last = wm.operator_properties_last(op_name)
        if op_last:
            setattr(op_last, attr_name, value)

    @classmethod
    def get_operator_attr_int_enum(cls, op_name, attr_name, default, p_items):
        p_val = cls.get_operator_attr(op_name, attr_name, default)
        for i, item in enumerate(p_items):
            if item[0] == p_val:
                return i
        return 0

    @classmethod
    def set_operator_attr_int_enum(cls, op_name, attr_name, value, p_items):
        for i, item in enumerate(p_items):
            if i == value:
                cls.set_operator_attr(op_name, attr_name, item[0])
