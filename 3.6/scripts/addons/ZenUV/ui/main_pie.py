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

""" Zen UV Main Pie Menu """
import bpy
from bpy.types import Menu
from ZenUV.ico import icon_get
from ZenUV.ui.labels import ZuvLabels

bl_info = {
    "name": "Zen UV Pie Menu",
    "version": (0, 1),
    "description": "Zen UV Main Pie Menu",
    "blender": (2, 80, 0),
    "category": "UV"
}


def get_command_props(op):
    if isinstance(op, str):
        if "bpy.ops." in op:
            op = op.split("(")[0]
            op = op[8:]
        try:
            op = eval("bpy.ops.%s" % op)
        except:
            return None

        try:
            if hasattr(op, "get_rna"):
                rna = op.get_rna().rna_type
                return rna.name, rna.description
            else:
                rna = op.get_rna_type()
                return rna.name, rna.description
        except:
            return None


def operator_text(context, input_text):
    """ Detect mode for Pie Menu 4 and 6 sector """
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    if addon_prefs.markSeamEdges:
        input_text += ' Seams'
        if addon_prefs.markSharpEdges:
            input_text += ' /'
    if addon_prefs.markSharpEdges:
        input_text += ' Sharp Edges'
    return input_text


class ZUV_OT_StretchMapSwitch(bpy.types.Operator):
    bl_idname = "uv.switch_stretch_map"
    bl_label = ZuvLabels.OT_STRETCH_DISPLAY_LABEL
    bl_description = ZuvLabels.OT_STRETCH_DISPLAY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context):
    #     return context.area.type == 'VIEW_3D'

    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            context.scene.zen_display.stretch = not context.scene.zen_display.stretch
        elif context.area.type == 'IMAGE_EDITOR':
            context.space_data.uv_editor.show_stretch = not context.space_data.uv_editor.show_stretch
        else:
            return {'CANCELLED'}

        return {'FINISHED'}


class ZUV_OT_Pie_Caller(bpy.types.Operator):
    """ Zen UV Caller Operator """
    bl_idname = "zenuv.pie_caller"
    bl_label = "Pie Caller"
    bl_options = {'REGISTER', 'UNDO'}

    alt: bpy.props.StringProperty(name="alt", default="", options={'HIDDEN'})
    ctrl: bpy.props.StringProperty(name="ctrl", default="", options={'HIDDEN'})
    shift: bpy.props.StringProperty(name="shift", default="", options={'HIDDEN'})
    command: bpy.props.StringProperty(name="command", default="", options={'HIDDEN'})
    desc: bpy.props.StringProperty(name="Caller Description", default="", options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        desc = properties.desc
        if not desc:
            desc = get_command_props(properties.command)[1]
            if not desc:
                desc = desc[0]
        p_alt = get_command_props(properties.alt)
        p_ctrl = get_command_props(properties.ctrl)
        p_shift = get_command_props(properties.shift)
        if p_alt:
            desc += ("\nALT - %s - %s" % (p_alt[0], p_alt[1]))
        if p_ctrl:
            desc += ("\nCTRL - %s - %s" % (p_ctrl[0], p_ctrl[1]))
        if p_shift:
            desc += ("\nSHIFT - %s - %s" % (p_shift[0], p_shift[1]))
        return desc

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        lb_event = event.type == "LEFTMOUSE"
        if self.alt and event.alt and lb_event:
            if get_command_props(self.alt) and eval(self.alt.split("(")[0]).poll():
                exec(self.alt)
        elif get_command_props(self.ctrl) and self.ctrl and event.ctrl and lb_event:
            if eval(self.ctrl.split("(")[0]).poll():
                exec(self.ctrl)
        elif get_command_props(self.shift) and self.shift and event.shift and lb_event:
            if eval(self.shift.split("(")[0]).poll():
                exec(self.shift)
        else:
            if get_command_props(self.command) and eval(self.command.split("(")[0]).poll():
                exec(self.command)

        return self.execute(context)

    def execute(self, context):
        return {'FINISHED'}


class ZUV_MT_Main_Pie(Menu):
    bl_label = 'Zen UV'
    bl_idname = "ZUV_MT_Main_Pie"

    def draw(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout = self.layout
        pie = layout.menu_pie()

        # Sector 4 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_4",
        #     text=operator_text(context, input_text=ZuvLabels.OT_UNMARK_LABEL),
        #     icon_value=icon_get(ZuvLabels.OT_UNMARK_ICO))
        alt = "bpy.ops.uv.zenuv_unmark_all()"
        ctrl = "bpy.ops.uv.zenuv_untag_finished()"
        shift = addon_prefs.s4
        command = "bpy.ops.uv.zenuv_unmark_seams()"
        desc = ""
        op = pie.operator(
            "zenuv.pie_caller",
            text=operator_text(context, input_text=ZuvLabels.OT_UNMARK_LABEL),
            icon_value=icon_get(ZuvLabels.OT_UNMARK_ICO)
        )
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 6 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_6",
        #     text=operator_text(context, input_text=ZuvLabels.OT_MARK_LABEL),
        #     icon_value=icon_get(ZuvLabels.OT_MARK_ICO))
        alt = ""
        ctrl = "bpy.ops.uv.zenuv_tag_finished()"
        shift = addon_prefs.s6
        command = "bpy.ops.uv.zenuv_mark_seams()"
        desc = ""
        op = pie.operator(
            "zenuv.pie_caller",
            text=operator_text(context, input_text=ZuvLabels.OT_MARK_LABEL),
            icon_value=icon_get(ZuvLabels.OT_MARK_ICO)
        )
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 2 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_2",
        #     text=ZuvLabels.ZEN_UNWRAP_LABEL,
        #     icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO))
        alt = "bpy.ops.uv.zenuv_pack(display_uv = True)"
        ctrl = ""
        shift = addon_prefs.s2
        command = "bpy.ops.uv.zenuv_unwrap('INVOKE_DEFAULT', action='NONE')"
        desc = ""
        op = pie.operator(
            "zenuv.pie_caller",
            text=ZuvLabels.ZEN_UNWRAP_LABEL,
            icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO)
        )
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 8 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_8",
        #     text=ZuvLabels.ISOLATE_ISLAND_LABEL)
        alt = ""
        ctrl = ""
        shift = addon_prefs.s8
        command = "bpy.ops.uv.zenuv_isolate_island('INVOKE_DEFAULT')"
        desc = ""
        op = pie.operator(
            "zenuv.pie_caller",
            text=ZuvLabels.ISOLATE_ISLAND_LABEL
        )
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 7 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_7",
        #     text=ZuvLabels.SELECT_ISLAND_LABEL)
        alt = "bpy.ops.uv.zenuv_select_uv_overlap()"
        ctrl = "bpy.ops.uv.zenuv_select_flipped()"
        shift = addon_prefs.s7
        command = "bpy.ops.uv.zenuv_select_island()"
        desc = ""
        op = pie.operator("zenuv.pie_caller", text=ZuvLabels.SELECT_ISLAND_LABEL)
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 9 ###########################################################
        pie.operator(
            "uv.zenuv_auto_mark",
            text=ZuvLabels.AUTO_MARK_LABEL)

        # Sector 1 ###########################################################
        # pie.operator(
        #     "uv.zenuv_quadrify",
        #     text=ZuvLabels.QUADRIFY_LABEL,
        #     icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))
        # pie.operator(
        #     "zenuv.caller_sector_1",
        #     text=ZuvLabels.QUADRIFY_LABEL)
        #     icon_value=icon_get(ZuvLabels.ZEN_CHECKER_ICO))
        # ZUV_OT_Pie_Caller.alt = ""
        # ZUV_OT_Pie_Caller.ctrl = "bpy.ops.uv.zenuv_unwrap('INVOKE_DEFAULT', action='NONE')"
        if context.area.type == "IMAGE_EDITOR":
            alt = "bpy.ops.uv.zenuv_distribute(relax_linked=True)"
        else:
            alt = ""
        ctrl = ""
        shift = addon_prefs.s1
        command = "bpy.ops.uv.zenuv_quadrify()"
        desc = ZuvLabels.QUADRIFY_DESC
        op = pie.operator(
            "zenuv.pie_caller",
            text=ZuvLabels.QUADRIFY_LABEL,
            icon_value=icon_get(ZuvLabels.ZEN_QUADRIFY_ICO))
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc

        # Sector 3 ###########################################################
        # pie.operator(
        #     "zenuv.caller_sector_3",
        #     text=ZuvLabels.OT_CHECKER_TOGGLE_LABEL,
        #     icon_value=icon_get(ZuvLabels.ZEN_CHECKER_ICO))
        alt = "bpy.ops.uv.switch_stretch_map()"
        ctrl = "bpy.ops.uv.zenuv_display_finished()"
        shift = addon_prefs.s3
        command = "bpy.ops.view3d.zenuv_checker_toggle()"
        desc = ""
        op = pie.operator(
            "zenuv.pie_caller",
            text=ZuvLabels.OT_CHECKER_TOGGLE_LABEL,
            icon_value=icon_get(ZuvLabels.ZEN_CHECKER_ICO)
        )
        op.alt = alt
        op.ctrl = ctrl
        op.shift = shift
        op.command = command
        op.desc = desc
