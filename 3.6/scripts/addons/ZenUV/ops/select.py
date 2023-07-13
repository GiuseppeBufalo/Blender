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
import bmesh
from itertools import chain
from math import radians
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from ZenUV.ui.labels import ZuvLabels

from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.base_clusters.zen_cluster import ZenCluster
from ZenUV.utils.constants import u_axis, v_axis

from ZenUV.utils.generic import (
    get_mesh_data,
    resort_objects,
    resort_by_type_mesh_in_edit_mode_and_sel,
    face_indexes_by_sel_mode,
    select_by_context
)
from ZenUV.utils.mark_utils import select_uv_border
from ZenUV.utils.blender_zen_utils import ZenPolls
from ZenUV.utils.texel_density import UV_faces_area
from ZenUV.utils.constants import FACE_UV_AREA_MULT


class ZUV_OT_SelectByDirection(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_by_direction"
    bl_label = ZuvLabels.OT_SEL_BY_DIRECTION_LABEL
    bl_description = ZuvLabels.OT_SEL_BY_DIRECTION_DESC
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="Edge direction",
        items=[
            ("U", "U", "U Axis"),
            ("V", "V", "V Axis"),
        ],
        default="U"
    )
    clear_sel: BoolProperty(
        name="Clear",
        description="Clear previous selection",
        default=True
    )
    angle: FloatProperty(
        name="Angle",
        min=0,
        max=45,
        default=30,
    )

    desc: bpy.props.StringProperty(name="Description", default=ZuvLabels.OT_SEL_BY_DIRECTION_DESC, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "direction")
        layout.prop(self, "angle")
        layout.prop(self, "clear_sel")

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            self.report({'INFO'}, "Select something.")
            return {"CANCELLED"}

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            islands = island_util.get_island(context, bm, uv_layer)
            if not islands:
                self.report({'WARNING'}, "Select some Island.")
                return {"CANCELLED"}

            for island in islands:
                cl = ZenCluster(context, obj, island, bm)
                if self.clear_sel:
                    cl.deselect_all_edges()
                if self.direction == 'U':
                    axis = u_axis
                elif self.direction == 'V':
                    axis = v_axis
                edges = cl.get_edges_by_angle_to_axis(radians(self.angle), axis)
                for edge in edges:
                    edge.select(context)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


class ZUV_OT_Select_UV_Borders(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_uv_borders"
    bl_label = ZuvLabels.SELECT_UV_BORDER_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.SELECT_UV_BORDER_DESC

    clear_selection: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_SEL_BY_TD_CLEAR_SEL_LABEL, default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "There are no selected objects")
            return {'CANCELLED'}
        area = context.area.type
        uv_sync = context.scene.tool_settings.use_uv_select_sync
        if context.area.type == 'IMAGE_EDITOR' and not uv_sync:
            context.scene.tool_settings.uv_select_mode = "EDGE"
        else:
            bpy.ops.mesh.select_mode(type="EDGE")
        if ZenPolls.version_greater_3_2_0 and area == 'IMAGE_EDITOR':
            for obj in objs:
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()
                # uv_layer = bm.loops.layers.uv.verify()
                for island in island_util.get_islands(context, bm):
                    cl = ZenCluster(context, obj, island, bm)
                    if self.clear_selection:
                        for edge in cl.uv_edges:
                            edge.select(context, False)
                    bound_uv_edges = cl.get_bound_edges()
                    for edge in bound_uv_edges:
                        edge.select(context, True)
                bm.select_flush_mode()
                bmesh.update_edit_mesh(obj.data, loop_triangles=False)

        else:
            select_uv_border(context, objs, self.clear_selection)

        return {'FINISHED'}


class AreaIsland:

    def __init__(self, faces, uv_layer) -> None:
        self.faces = faces
        self.area = UV_faces_area(faces, uv_layer) * FACE_UV_AREA_MULT


class ZUV_OT_SelectByUvArea(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_by_uv_area"
    bl_label = ZuvLabels.OT_SEL_BY_UV_AREA_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_SEL_BY_UV_AREA_DESC

    clear_selection: bpy.props.BoolProperty(
        name=ZuvLabels.OT_TDPR_SEL_BY_TD_CLEAR_SEL_LABEL,
        description=ZuvLabels.OT_TDPR_SEL_BY_TD_CLEAR_SEL_DESC,
        default=True
        )

    condition: EnumProperty(
        name=ZuvLabels.PROP_SEL_BY_UV_AREA_CONDITION_LABEL,
        description=ZuvLabels.PROP_SEL_BY_UV_AREA_CONDITION_DESC,
        items=[
            ("LESS", "Less than", ""),
            ("EQU", "Equal to", ""),
            ("MORE", "More than", ""),
            ("WITHIN", "Within range", ""),
            ("ZERO", "Zero Area", "")
        ],
        default="ZERO"
    )
    treshold: bpy.props.FloatProperty(
        name=ZuvLabels.PROP_SEL_BY_UV_AREA_TRESHOLD_LABEL,
        description=ZuvLabels.PROP_SEL_BY_UV_AREA_TRESHOLD_DESC,
        precision=2,
        default=0.5,
        min=0.0
    )
    mode: EnumProperty(
        name="Mode",
        description="Mode for getting area",
        items=[
            ('ISLAND', 'Island', 'Get Area from selected island'),
            ('FACE', 'Face', 'Get area from selected faces'),
        ],
        default="ISLAND"
    )

    def draw(self, context):
        sc_lv_prop = context.scene.zen_uv
        layout = self.layout
        layout.prop(self, 'mode')
        layout.prop(self, "clear_selection")
        box = layout.box()
        box.label(text=ZuvLabels.LABEL_SEL_BY_UV_AREA_DRAW if self.mode == 'FACE' else ZuvLabels.LABEL_SEL_BY_UV_AREA_DRAW.replace('Faces', 'Islands'))
        box.prop(self, "condition")
        if self.condition == "WITHIN":
            row = box.row(align=True)
            row.prop(sc_lv_prop, "range_value_start")
            row.prop(sc_lv_prop, "range_value_end")
        elif self.condition == "ZERO":
            pass
        else:
            box.prop(sc_lv_prop, "area_value_for_sel")
        box.prop(self, "treshold")

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "There are no selected objects")
            return {'CANCELLED'}

        for obj in objs:
            if len(obj.data.uv_layers) == 0:
                self.report({'WARNING'}, f"Cancelled. Object {obj.name} have no active UV Map.")
                return {'CANCELLED'}

        uv_sync = context.scene.tool_settings.use_uv_select_sync
        self.sc_lv_prop = context.scene.zen_uv

        condition = {"LESS": self.less, "EQU": self.equ, "MORE": self.more, "WITHIN": self.within, "ZERO": self.zero}

        if self.clear_selection:
            bpy.ops.uv.select_all(action='DESELECT')

        if context.area.type == 'IMAGE_EDITOR' and not uv_sync:

            context.scene.tool_settings.uv_select_mode = "FACE"

            for obj in objs:
                bm, me, uv_layer = self.get_bmesh_from_obj(obj)
                if self.mode == 'FACE':
                    for_sel_faces = [f for f in bm.faces if condition[self.condition](UV_faces_area([f, ], uv_layer) * FACE_UV_AREA_MULT, self.sc_lv_prop.area_value_for_sel)]
                else:
                    for_sel_faces = self.get_faces_for_select(context, condition, bm, uv_layer)
                select_by_context(context, bm, [for_sel_faces, ], state=True)
                self.update_edit_bmesh(bm, me)
        else:

            bpy.ops.mesh.select_mode(type="FACE")

            for obj in objs:
                bm, me, uv_layer = self.get_bmesh_from_obj(obj)
                init_selection = [f.index for f in bm.faces if f.select]
                if self.mode == 'FACE':
                    for face in bm.faces:
                        face.select = condition[self.condition](UV_faces_area([face, ], uv_layer) * FACE_UV_AREA_MULT, self.sc_lv_prop.area_value_for_sel)
                else:
                    for face in self.get_faces_for_select(context, condition, bm, uv_layer):
                        face.select = True

                if not self.clear_selection:
                    self.restore_selection(bm, init_selection)

                self.update_edit_bmesh(bm, me)

        return {'FINISHED'}

    def get_faces_for_select(self, context, condition, bm, uv_layer):
        islands = island_util.get_islands(context, bm)
        ar_islands = [AreaIsland(island, uv_layer) for island in islands]
        return chain.from_iterable([i.faces for i in ar_islands if condition[self.condition](i.area, self.sc_lv_prop.area_value_for_sel)])

    def update_edit_bmesh(self, bm, me):
        bm.select_flush_mode()
        bmesh.update_edit_mesh(me, loop_triangles=False)

    def get_bmesh_from_obj(self, obj):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        return bm, obj.data, uv_layer

    def restore_selection(self, bm, init_selection):
        for i in init_selection:
            bm.faces[i].select = True

    def less(self, area, value):
        return area < value + self.treshold

    def equ(self, area, value):
        return value - self.treshold < area <= value + self.treshold

    def more(self, area, value):
        return area > value - self.treshold

    def within(self, area, value):
        return self.sc_lv_prop.range_value_start - self.treshold <= area <= self.sc_lv_prop.range_value_end + self.treshold

    def zero(self, area, value):
        return area <= 0.0 + self.treshold


class ZUV_OT_GrabSelectedArea(bpy.types.Operator):
    bl_idname = "uv.zenuv_grab_sel_area"
    bl_label = ZuvLabels.OT_GET_UV_AREA_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.OT_GET_UV_AREA_DESC

    real_area: FloatProperty(
        name=ZuvLabels.PROP_GET_UV_REAL_LABEL,
        description=ZuvLabels.PROP_GET_UV_REAL_DESC,
        default=0.0,
        options={'HIDDEN'}
    )
    multiplied_area: FloatProperty(
        name=ZuvLabels.PROP_GET_UV_MULT_LABEL,
        description=ZuvLabels.PROP_GET_UV_REAL_DESC,
        default=2.0,
        options={'HIDDEN'},
    )
    mode: EnumProperty(
        name="Mode",
        description="Mode for getting area",
        items=[
            ('ISLAND', 'Island', 'Get Area from selected island'),
            ('FACE', 'Face', 'Get area from selected faces'),
        ],
        default="ISLAND"
    )
    average: bpy.props.BoolProperty(
        name='Average',
        description='Get the average value from the selected',
        default=False
        )

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mode')
        layout.prop(self, 'average')
        box = layout.box()
        box.prop(self, "real_area")
        box.label(text="Real UV Area" + ": " + str(self.real_area))
        box.prop(self, "multiplied_area")

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "There are no selected objects")
            return {'CANCELLED'}
        self.sc_lv_prop = context.scene.zen_uv
        sel_faces_count = []
        part_area = []
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data).copy()
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            if self.mode == 'FACE':
                faces = [bm.faces[i] for i in face_indexes_by_sel_mode(context, bm)]
                sel_faces_count.append(len(faces))
                part_area.append(sum([UV_faces_area([face, ], uv_layer) for face in faces]))
            else:
                islands = island_util.get_island(context, bm, uv_layer)
                sel_faces_count.append(len(islands))
                faces = [f for island in islands for f in island]
                part_area.append(sum([UV_faces_area([face, ], uv_layer) for face in faces]))
        sel_faces_count = sum(sel_faces_count)
        if sel_faces_count != 0:
            self.real_area = sum(part_area)
            if self.average:
                self.real_area /= sel_faces_count
            self.multiplied_area = self.real_area * FACE_UV_AREA_MULT
            self.sc_lv_prop.area_value_for_sel = self.multiplied_area
            self.update_range_values()
        else:
            self.report({'WARNING'}, "There are no selected faces")
        return {'FINISHED'}

    def update_range_values(self):
        self.sc_lv_prop.range_value_start = self.multiplied_area - 2
        self.sc_lv_prop.range_value_end = self.multiplied_area + 2


select_classes = (
    ZUV_OT_Select_UV_Borders,
    ZUV_OT_SelectByUvArea,
    ZUV_OT_GrabSelectedArea,
)


poll_3_2_select_classes = (
    ZUV_OT_SelectByDirection,

)

if __name__ == '__main__':
    pass
