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

# blender
import bpy

from ZenUV.utils.blender_zen_utils import get_command_props


def _get_caller_enum_items(self, template_items):
    items = []
    for op_id in template_items.values():
        op_props = get_command_props(op_id)
        items.append((op_id, op_props.bl_label, op_props.bl_desc))
    return items


def _get_caller_description(template_items, properties):
    if properties.is_menu:
        for op_id in template_items.values():
            if op_id == properties.cmd_enum:
                op_props = get_command_props(op_id)
                desc = op_id
                if op_props.bl_desc:
                    desc = op_props.bl_desc
                elif op_props.bl_label:
                    desc = op_props.bl_label
                return desc
    else:
        items = []
        for op_key, op_id in template_items.items():
            op_props = get_command_props(op_id)

            desc = op_id
            if op_props.bl_desc:
                desc = op_props.bl_desc
            elif op_props.bl_label:
                desc = op_props.bl_label
            items.append(f'{op_key} - {desc}')
        return '\n'.join(items)
    return ''


class ZsBasicPieCaller(bpy.types.Operator):
    """ Zen UV Caller Operator """

    bl_description = 'Click to open Popup'

    def _get_cmd_enum(self, context):
        return []

    def _exec_cmd(self):
        p_cmd = get_command_props(self.cmd_enum)
        return eval(p_cmd.cmd) if (p_cmd.bl_op_cls and p_cmd.bl_op_cls.poll()) else {'CANCELLED'}

    @classmethod
    def poll(cls, context):
        res = False
        for op_id in cls.template_items.values():
            op_props = get_command_props(op_id)
            if (op_props.bl_op_cls and op_props.bl_op_cls.poll()):
                res = True
        return res

    @classmethod
    def description(cls, context, properties):
        return _get_caller_description(cls.template_items, properties)

    def invoke(self, context, event):
        if self.is_menu:
            return self.execute(context)
        else:
            if event.type == 'LEFTMOUSE' or event.value != 'RELEASE':
                # sequencies (Ctrl+Shift etc.) have priority
                for op_key, op_id in self.template_items.items():
                    if '+' in op_key:
                        keys = op_key.lower().split('+')

                        has_seq = False
                        for key in keys:
                            if getattr(event, key, False):
                                has_seq = True
                            else:
                                has_seq = False
                                break

                        if has_seq:
                            self.cmd_enum = op_id
                            return self.execute(context)

                # alt, ctrl, shift
                for op_key, op_id in self.template_items.items():
                    key = op_key.lower()
                    if getattr(event, key, False):
                        self.cmd_enum = op_id
                        return self.execute(context)
        self.cmd_enum = self.template_items['Default']
        return self.execute(context)

    def execute(self, context):
        return self._exec_cmd()
