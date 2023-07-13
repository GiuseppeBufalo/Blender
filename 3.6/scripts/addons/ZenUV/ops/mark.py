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

""" # Zen UV Mark System """
from math import radians, pi
import bpy
import bmesh
from ZenUV.utils.generic import (
    get_mesh_data,
    collect_selected_objects_data,
)
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.constants import UiConstants as uc
from ZenUV.utils.mark_utils import (
    MarkStateManager,
    zuv_mark_seams,
    unmark_all_seams_sharp,
    sharp_by_uv_border,
    seams_by_uv_border,
    seams_by_sharp,
    sharp_by_seam,
    seams_by_open_edges
)
from ZenUV.ui.pie import ZsPieFactory


class MarkOpTemplate(bpy.types.Operator):
    bl_idname = ""
    bl_label = ""
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    # markSharpEdges: bpy.props.BoolProperty(
    #     name=ZuvLabels.PREF_MARK_SHARP_EDGES_LABEL,
    #     description=ZuvLabels.PREF_MARK_SHARP_EDGES_DESC,
    #     default=True,
    # )

    # markSeamEdges: bpy.props.BoolProperty(
    #     name=ZuvLabels.PREF_MARK_SEAM_EDGES_LABEL,
    #     description=ZuvLabels.PREF_MARK_SEAM_EDGES_DESC,
    #     default=True,
    # )

    def draw(self, context):
        props = context.scene.zen_uv
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout = self.layout
        box = layout.box()
        if not addon_prefs.useGlobalMarkSettings:
            box.prop(props, 'op_markSeamEdges')
            box.prop(props, 'op_markSharpEdges')
        else:
            box.label(text="Settings in Global mode.")

    def execute(self, context):
        pass


class ZUV_OT_Mark_Seams(bpy.types.Operator):
    """Mark selected edges or face borders as Seams and/or Sharp edges"""
    bl_idname = "uv.zenuv_mark_seams"
    bl_label = ZuvLabels.OT_MARK_LABEL
    bl_description = ZuvLabels.OT_MARK_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        context.scene.zen_uv.draw_mark_unmark(self.layout, context, 'MARK')

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()
        scene = context.scene

        mSeam, mSharp = MarkStateManager(context).get_state()
        if not mSeam and not mSharp:
            return {'FINISHED'}

        for obj in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(obj.data)
            zuv_mark_seams(context, bm, mSeam, mSharp, assign=True, switch=False)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        if scene.tool_settings.use_edge_path_live_unwrap:
            bpy.ops.uv.zenuv_unwrap("INVOKE_DEFAULT", action="LIVE_UWRP")

        return {'FINISHED'}


class ZUV_OT_Unmark_Seams(bpy.types.Operator):
    bl_idname = "uv.zenuv_unmark_seams"
    bl_label = ZuvLabels.OT_UNMARK_LABEL
    bl_description = ZuvLabels.OT_UNMARK_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        context.scene.zen_uv.draw_mark_unmark(self.layout, context, state="UNMARK")

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()
        scene = context.scene

        mSeam, mSharp = MarkStateManager(context).get_state()
        if not mSeam and not mSharp:
            return {'FINISHED'}

        for obj in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(obj.data)
            zuv_mark_seams(context, bm, mSeam, mSharp, assign=False, switch=False)
            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        if scene.tool_settings.use_edge_path_live_unwrap:
            bpy.ops.uv.zenuv_unwrap("INVOKE_DEFAULT", action="LIVE_UWRP")

        return {'FINISHED'}


class ZUV_OT_Unmark_All(bpy.types.Operator):
    bl_idname = "uv.zenuv_unmark_all"
    bl_label = ZuvLabels.UNMARK_ALL_LABEL
    bl_description = ZuvLabels.UNMARK_ALL_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # markPinned: bpy.props.BoolProperty(
    #     name=ZuvLabels.PREF_MARK_PINNED_LABEL,
    #     description=ZuvLabels.PREF_MARK_PINNED_DESC,
    #     default=False,
    # )

    def draw(self, context):
        props = context.scene.zen_uv
        props.draw_unmark_all(self.layout, context)
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        # layout = self.layout
        # layout.prop(self, "markPinned")
        # box = layout.box()
        # if not addon_prefs.useGlobalMarkSettings:
        #     box.prop(self, 'markSeamEdges')
        #     box.prop(self, 'markSharpEdges')
        # else:
        #     box.label(text="Settings in Global mode.")

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        props = context.scene.zen_uv
        mSeam, mSharp = MarkStateManager(context).get_state()

        if not mSeam and not mSharp:
            return {'FINISHED'}

        for obj in context.objects_in_mode:
            me, bm = get_mesh_data(obj)

            """ Clear Pinned Data """
            uv_layer = bm.loops.layers.uv.verify()

            edges = [edge for edge in bm.edges if not edge.hide]

            if props.op_markPinned:
                for loop in [loop for face in bm.faces for loop in face.loops]:
                    loop[uv_layer].pin_uv = False

            if mSeam:
                for edge in edges:
                    edge.seam = False

            if mSharp:
                for edge in edges:
                    edge.smooth = True

            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


class ZUV_OT_UnifiedMark(bpy.types.Operator):
    bl_idname = "uv.zenuv_unified_mark"
    bl_label = ZuvLabels.UNIFIED_MARK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.UNIFIED_MARK_DESC

    convert: bpy.props.EnumProperty(
        items=uc.unified_mark_enum,
        default="SEAM_BY_OPEN_EDGES",
        # options={'HIDDEN'}
    )
    unmark_seams: bpy.props.BoolProperty(name="Unmark Seams", default=False)
    unmark_sharp: bpy.props.BoolProperty(name="Unmark Sharp", default=False)

    def invoke(self, context, event):
        self.convert = context.scene.zen_uv.sl_convert
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "convert", text="Operation")
        box = layout.box()
        if self.convert in {"SEAM_BY_UV_BORDER", "SHARP_BY_UV_BORDER"}:
            box.prop(self, "unmark_seams")
            box.prop(self, "unmark_sharp")
        else:
            box.label(text="No options.")

    def execute(self, context):
        bms = collect_selected_objects_data(context)
        if self.convert == "SHARP_BY_UV_BORDER":
            if self.unmark_seams or self.unmark_sharp:
                unmark_all_seams_sharp(bms, self.unmark_seams, self.unmark_sharp)
            sharp_by_uv_border(bms)
        if self.convert == "SEAM_BY_UV_BORDER":
            if self.unmark_seams or self.unmark_sharp:
                unmark_all_seams_sharp(bms, self.unmark_seams, self.unmark_sharp)
            seams_by_uv_border(bms)
        elif self.convert == "SEAM_BY_SHARP":
            seams_by_sharp(context)
        elif self.convert == "SHARP_BY_SEAM":
            sharp_by_seam(context)
        elif self.convert == "SEAM_BY_OPEN_EDGES":
            seams_by_open_edges(bms)
        return {'FINISHED'}


class ZUV_OT_Seams_By_UV_Borders(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_uv_islands"
    bl_label = ZuvLabels.MARK_BY_BORDER_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.MARK_BY_BORDER_DESC

    unmark_seams: bpy.props.BoolProperty(name="Unmark Seams", default=False)
    unmark_sharp: bpy.props.BoolProperty(name="Unmark Sharp", default=False)

    def execute(self, context):
        bms = collect_selected_objects_data(context)
        if self.unmark_seams or self.unmark_sharp:
            unmark_all_seams_sharp(bms, self.unmark_seams, self.unmark_sharp)
        seams_by_uv_border(bms)
        return {'FINISHED'}


class ZUV_OT_Sharp_By_UV_Borders(bpy.types.Operator):
    bl_idname = "uv.zenuv_sharp_by_uv_islands"
    bl_label = ZuvLabels.MARK_SHARP_BY_BORDER_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.MARK_SHARP_BY_BORDER_DESC

    unmark_seams: bpy.props.BoolProperty(name="Unmark Seams", default=False)
    unmark_sharp: bpy.props.BoolProperty(name="Unmark Sharp", default=False)

    def execute(self, context):
        bms = collect_selected_objects_data(context)
        if self.unmark_seams or self.unmark_sharp:
            unmark_all_seams_sharp(bms, self.unmark_seams, self.unmark_sharp)
        sharp_by_uv_border(bms)
        return {'FINISHED'}


class ZUV_OT_Seams_By_Open_Edges(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_open_edges"
    bl_label = ZuvLabels.SEAM_BY_OPEN_EDGES_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SEAM_BY_OPEN_EDGES_DESC

    def execute(self, context):
        bms = collect_selected_objects_data(context)

        seams_by_open_edges(bms)
        return {'FINISHED'}


class ZUV_OT_Seam_By_Sharp(bpy.types.Operator):
    bl_idname = "uv.zenuv_seams_by_sharp"
    bl_label = ZuvLabels.SEAM_BY_SHARP_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SEAM_BY_SHARP_DESC

    def execute(self, context):
        seams_by_sharp(context)
        return {'FINISHED'}


class ZUV_OT_Sharp_By_Seam(bpy.types.Operator):
    bl_idname = "uv.zenuv_sharp_by_seams"
    bl_label = ZuvLabels.SHARP_BY_SEAM_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SHARP_BY_SEAM_DESC

    def execute(self, context):
        sharp_by_seam(context)
        return {'FINISHED'}


class ZUV_OT_Auto_Mark(bpy.types.Operator):
    bl_idname = "uv.zenuv_auto_mark"
    bl_label = ZuvLabels.AUTO_MARK_LABEL
    bl_description = ZuvLabels.AUTO_MARK_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # angle: bpy.props.FloatProperty(
    #     name=ZuvLabels.AUTO_MARK_ANGLE_NAME,
    #     description=ZuvLabels.AUTO_MARK_ANGLE_DESC,
    #     min=0.0,
    #     max=180.0,
    #     default=30.03
    # )

    # action: bpy.props.EnumProperty(
    #     items=[
    #         ("NONE", "Auto Seams", "Default Auto Seams Mode."),
    #         ("RESET", "Reset Auto Seams", "Perform Reset Values of Operator")],
    #     default="NONE"
    # )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        context.scene.zen_uv.draw_auto_mark(self.layout, context)
        # props = context.scene.zen_uv
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        # layout = self.layout
        # layout.prop(props, "op_mark_angle_angle")
        # # layout.prop(context.scene.zen_uv, "op_mark_angle_action")
        # box = layout.box()
        # if not addon_prefs.useGlobalMarkSettings:
        #     box.prop(props, 'op_markSeamEdges')
        #     box.prop(props, 'op_markSharpEdges')
        # else:
        #     box.label(text="Settings in Global mode.")

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        mSeam, mSharp = MarkStateManager(context).get_state()
        if not mSeam and not mSharp:
            return {'FINISHED'}
        for obj in context.objects_in_mode:
            bm = bmesh.from_edit_mesh(obj.data)

            edges = [edge for edge in bm.edges if not edge.hide]
            sharp = [edge for edge in edges if edge.calc_face_angle(pi) > radians(context.scene.zen_uv.op_mark_angle_angle)]

            if mSeam and mSharp:
                self.mark_both(edges, state=False)
                self.mark_both(sharp, state=True)
            elif mSeam and not mSharp:
                self.mark_seam(edges, state=False)
                self.mark_seam(sharp, state=True)
            elif not mSeam and mSharp:
                self.mark_sharp(edges, state=False)
                self.mark_sharp(sharp, state=True)
            else:
                return {'CANCELLED'}

            bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        return {'FINISHED'}

    def mark_both(self, edges, state=True):
        for edge in edges:
            edge.seam = state
            edge.smooth = not state

    def mark_sharp(self, edges, state=True):
        for edge in edges:
            edge.smooth = not state

    def mark_seam(self, edges, state=True):
        for edge in edges:
            edge.seam = state
