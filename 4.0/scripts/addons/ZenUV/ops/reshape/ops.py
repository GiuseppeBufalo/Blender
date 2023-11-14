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
from math import radians
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatVectorProperty,
    FloatProperty
)
from mathutils import Vector
from ZenUV.utils.generic import (
    resort_objects,
    get_mesh_data,

)
from ZenUV.utils import get_uv_islands as island_util
# from ZenUV.ui.labels import Rlabels
from ZenUV.ops.reshape.labels import ReshapeLabels as Rlabels
from ZenUV.utils.base_clusters.zen_cluster import ZenCluster
from ZenUV.utils.base_clusters.stripes import UvStripes, StripesLimits
from ZenUV.ops.reshape.utils import DistributeUtils
from ZenUV.utils.constants import u_axis, v_axis
from ZenUV.ops.reshape.props import ReshapeProperties
from ZenUV.utils.blender_zen_utils import ZenPolls


class ZUV_OT_DistributeGeneric(bpy.types.Operator):
    bl_idname = ""
    bl_label = ""
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}

    desc: bpy.props.StringProperty(name="Description", default="", options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}

        uv_sync = context.scene.tool_settings.use_uv_select_sync
        if self.lock_pos:
            self.ends_pos = self.starts_pos

        # props.base_position = v_axis
        # props.end_position = Vector((0.5, 0.0))
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            props = ReshapeProperties(
                self.sources,
                self.orient_along,
                self.spacing,
                # self.length_axis,
                # self.orient_along,  # Duplicate value
                self.sorting,
                self.reverse_dir,
                self.starts_pos,
                self.ends_pos,
                # self.offset + Vector - Compensation zero values in the UI of operator properties
                Vector((self.offset_u, self.offset_v)) + Vector((1, 1)),
                self.border_offset,
                self.border_proportion,
                self.detect_corners
            )

            islands = island_util.get_island(context, bm, uv_layer)
            # clusters = []
            scope = []
            z_stripes = None
            for island in islands:
                cl = ZenCluster(context, obj, island, bm)
                if self.sources == "SELECTED":
                    # self.orient_along = props.orient_along = "INPLACE"
                    edges = cl.get_selected_edges()
                    z_stripes = UvStripes(edges, cl.uv_layer).get_stripes_from_selection()
                elif self.sources in {"UAXIS", "VAXIS"}:
                    self.orient_along = props.orient_along = "AUTO"
                    if self.sources == "UAXIS":
                        axis = u_axis
                    elif self.sources == "VAXIS":
                        axis = v_axis
                    cl.deselect_all_edges()
                    self.deselect_faces(context, uv_sync, uv_layer, island)
                    edges = cl.get_edges_by_angle_to_axis(radians(self.angle), axis)
                    z_stripes = UvStripes(edges, cl.uv_layer).get_stripes_from_selection()

                elif self.sources == "BORDERS":
                    self.orient_along = props.orient_along = "ORIGINAL"
                    self.spacing = props.spacing = 'GEOMETRY'
                    self.deselect_faces(context, uv_sync, uv_layer, island)
                    if context.area.type == 'IMAGE_EDITOR' and not uv_sync:
                        context.scene.tool_settings.uv_select_mode = "EDGE"
                    else:
                        bpy.ops.mesh.select_mode(type="EDGE")
                    if self.relax_linked:
                        cl.deselect_all_edges()
                    edges = cl.get_bound_edges()
                    # print("Bound edges: ", edges)
                    if self.select_border or self.relax_linked:
                        for edge in edges:
                            edge.select(context, True)
                    z_stripes = UvStripes(edges, cl.uv_layer).get_stripes_from_borders(self.detect_corners)

                if not z_stripes.result_message:
                    z_stripes.result_message = "Select one or a few edge loops"

                if not z_stripes:
                    self.report({'WARNING'}, "Sources are not found. Perhaps the selected island is partially hidden")
                    return {'FINISHED'}

                scope = z_stripes.stripes
                # clusters.append(cl)
                if not scope:
                    self.report({'WARNING'}, f"Can't figure out current selection. {z_stripes.result_message}")
                    continue
                    # return {'FINISHED'}

                if not self.sources == "BORDERS" and len(scope) == 1:
                    if scope[0].is_cycled()['UV']:
                        self.report({'WARNING'}, "Can't distribute circular selection")
                        return {'FINISHED'}

                lims = StripesLimits(scope)
                for stripe in scope:
                    if stripe.is_cycled()['UV']:
                        continue
                    props.uv_layer = uv_layer

                    du = DistributeUtils(
                        stripe,
                        lims,
                        props
                    )

                bmesh.update_edit_mesh(me, loop_triangles=False)

        if self.relax_linked:
            _relax_linked(self, context)

        return {'FINISHED'}

    def deselect_faces(self, context, uv_sync, uv_layer, island):
        if context.area.type == 'IMAGE_EDITOR' and not uv_sync:
            if ZenPolls.version_greater_3_2_0:
                for lp in [loop[uv_layer] for f in island for loop in f.loops]:
                    lp.select = False
                    lp.select_edge = False
            else:
                for lp in [loop[uv_layer] for f in island for loop in f.loops]:
                    lp.select = False
        else:
            for face in island:
                face.select = False

    def draw_preset_by_axis(self, layout):
        box = layout.box()
        box.prop(self, "angle")
        box.prop(self, "spacing")

    def draw_preset_borders(self, box):
        # box = layout.box()
        box.prop(self, "detect_corners")
        box.prop(self, "border_proportion")
        box.prop(self, "border_offset")
        # box.prop(self, "select_border")

    def draw_preset_selected(self, box):
        box.label(text="Orient loop along:")
        row = box.row(align=True)
        row.prop(self, "orient_along", text="")
        row.prop(self, "reverse_dir", icon_only=True, icon="ARROW_LEFTRIGHT")

        box.label(text="Spacing:")
        box.prop(self, "spacing", text="")


class ZUV_OT_ReshapeIsland(ZUV_OT_DistributeGeneric):
    bl_idname = "uv.zenuv_reshape_island"
    bl_label = "Reshape Island"
    bl_description = Rlabels.RESHAPE_OP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def orient_along_items(self, context):
        if self.sources == "SELECTED":
            return [
                # ("INPLACE", "In Place", ""),
                ("AUTO", "Auto", ""),
                ("U", "U Axis", ""),
                ("V", "V Axis", ""),
                ("INPLACE", "In Place", ""),
                # ("ORIGINAL", "Original", "")
            ]
        elif self.sources in {"UAXIS", "VAXIS"}:
            return [
                # ("INPLACE", "In Place", ""),
                ("AUTO", "Auto", ""),
                ("U", "U Axis", ""),
                ("V", "V Axis", ""),
                ("ORIGINAL", "Original", "")
            ]
        elif self.sources == "BORDERS":
            return [
                # ("INPLACE", "In Place", ""),
                ("AUTO", "Auto", ""),
                ("U", "U Axis", ""),
                ("V", "V Axis", ""),
                ("ORIGINAL", "Original", "")
            ]

    lock_pos: BoolProperty(
        name="Lock",
        description="Locks start and end positions",
        default=True
    )
    sorting: EnumProperty(
        name=Rlabels.PROP_REV_START_LABEL,
        description=Rlabels.PROP_REV_START_DESC,
        items=[
            ("TOP_LEFT", "Top - Left", ""),
            ("BOTTOM_RIGHT", "Bottom - Right", "")
        ],
        default="TOP_LEFT"
    )
    orient_along: EnumProperty(
        name=Rlabels.PROP_ALIGN_TO_LABEL,
        description=Rlabels.PROP_ALIGN_TO_DESC,
        items=orient_along_items
    )
    sources: EnumProperty(
        name="Preset",
        description="",
        items=[
            ("SELECTED", "Selected", ""),
            ("UAXIS", "U Direction", ""),
            ("VAXIS", "V Direction", ""),
            ("BORDERS", "Borders", ""),
        ],
        default="SELECTED"
    )
    starts_pos: EnumProperty(
        name="Start Positions",
        description="Position of starts of loops",
        items=[
            ("ASIS", "As Is", ""),
            ("MAX", "Max", ""),
            ("MID", "Averaged", ""),
            ("MIN", "Min", "")
        ],
        default="ASIS"
    )
    ends_pos: EnumProperty(
        name="End Positions",
        description="Position of ends of loops",
        items=[
            ("ASIS", "As Is", ""),
            ("MAX", "Max", ""),
            ("MID", "Averaged", ""),
            ("MIN", "Min", "")
        ],
        default="ASIS"
    )
    spacing: EnumProperty(
        name=Rlabels.PROP_DISTRIBUTION_FROM_LABEL,
        description=Rlabels.PROP_DISTRIBUTION_FROM_DESC,
        items=[
            ("UV", "UV", ""),
            ("GEOMETRY", "Geometry", ""),
            ("EVENLY", "Evenly", "")
        ],
        default="GEOMETRY"
    )
    reverse_start: BoolProperty(
        name=Rlabels.PROP_REV_START_LABEL,
        description=Rlabels.PROP_REV_START_DESC,
        default=False
    )
    reverse_dir: BoolProperty(
        name=Rlabels.PROP_REV_DIR_LABEL,
        description=Rlabels.PROP_REV_DIR_DESC,
        default=False
    )
    relax_linked: BoolProperty(
        name=Rlabels.PROP_REL_LINK_LABEL,
        description=Rlabels.PROP_REL_LINK_DESC,
        default=True,
    )
    relax_mode: EnumProperty(
        name=Rlabels.PROP_REL_MODE_LABEL,
        description=Rlabels.PROP_REL_MODE_DESC,
        items=[
            ("ANGLE_BASED", "Angle Based", ""),
            ("CONFORMAL", "Conformal", ""),
        ],
        default="ANGLE_BASED"
    )
    angle: FloatProperty(
        name="Angle",
        min=0,
        max=45,
        default=15,
    )
    offset: FloatVectorProperty(
        name="Offset",
        description="The Distance from first loop to last",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ',
        step=0.1
    )
    offset_u: FloatProperty(
        name="Offset U",
        description="The Distance from first loop to last. Red color indicates that the value is not zero.",
        default=0.0,
        step=0.1
    )
    offset_v: FloatProperty(
        name="Offset V",
        description="The Distance from first loop to last. Red color indicates that the value is not zero.",
        default=0.0,
        step=0.1
    )
    select_border: BoolProperty(
        name="Select Border",
        description="Select UV Border",
        default=True,
    )
    border_offset: FloatProperty(
        name="Border Offset",
        description="Offset (scalar) for borders",
        default=1.0,
        step=0.01
    )
    border_proportion: EnumProperty(
        name="Length",
        description="How to calculate the lenght of each loop",
        items=[
            ("UV", "UV", "From length of UV Loop"),
            ("GEOMETRY", "Geometry", "From length of Geometry loop"),
            ("SHORT", "Short", "From distance between start and end of loop")
        ],
        default="SHORT"
    )
    detect_corners: EnumProperty(
        name="Corners By",
        description="How to find corners in borders",
        items=[
            ('CORNER', 'Corner', ''),
            ('PINS', 'Pinned', ''),
            ('CORNER_AND_PINS', 'Pinned & Corner', '')
            ],
        default='CORNER_AND_PINS',
    )

    desc: bpy.props.StringProperty(name="Description", default=Rlabels.PROP_STRAIGHTEN_DESC, options={'HIDDEN'})

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
        layout.label(text="Preset:")
        layout.prop(self, "sources", text="")
        layout.separator_spacer()
        layout.label(text="Properties:")
        box = layout.box()

        if self.sources == "SELECTED":
            self.draw_preset_selected(box)
            self.draw_advanced(layout)
        if self.sources in {"UAXIS", "VAXIS"}:
            self.draw_preset_by_axis(box)
            self.draw_advanced(layout)
        if self.sources == 'BORDERS':
            self.draw_preset_borders(box)

    def draw_relax_linked(self, context, layout):
        layout.prop(self, "relax_linked")
        if context.space_data.type == 'IMAGE_EDITOR':
            row = layout.row(align=True)
            if self.desc == Rlabels.PROP_STRAIGHTEN_DESC:
                pass
            else:
                self.relax_linked = False
            if self.relax_linked:
                row.prop(self, "relax_mode")

    def draw_generic_props(self, box):
        box.label(text=Rlabels.PROP_REV_START_LABEL)
        box.prop(self, "sorting", text="")
        box.label(text="Orient loop along:")
        row = box.row(align=True)
        row.prop(self, "orient_along", text="")
        row.prop(self, "reverse_dir", icon_only=True, icon="ARROW_LEFTRIGHT")

        box.label(text="Spacing:")
        box.prop(self, "spacing", text="")

    def draw_advanced(self, layout):
        layout.separator_spacer()
        layout.label(text="Advanced:")
        box = layout.box()
        box.enabled = self.orient_along != "INPLACE"

        labels_row = box.row(align=True)
        labels_row.split(factor=0.5, align=True)
        labels_row.label(text="Start Position:")
        labels_row.label(text="End Position:")

        row = box.row(align=True)
        row.prop(self, "starts_pos", text="")
        if self.lock_pos:
            lock_icon = "LOCKED"
        else:
            lock_icon = "UNLOCKED"
        row.prop(self, "lock_pos", icon=lock_icon, icon_only=True)
        col = row.column(align=True)
        col.enabled = not self.lock_pos
        col.prop(self, "ends_pos", text="")

        col = box.column(align=True)
        col.label(text="Offset:")
        of_u = col.row()
        of_v = col.row()
        if self.offset_u != 0.0:
            of_u.alert = True
        if self.offset_v != 0.0:
            of_v.alert = True
        of_u.prop(self, "offset_u")
        of_v.prop(self, "offset_v")


class ZUV_OT_DistributeVerts(ZUV_OT_DistributeGeneric):
    bl_idname = "uv.zenuv_distribute_verts"
    bl_label = Rlabels.PROP_DISTRIBUTE_LABEL
    bl_description = Rlabels.PROP_DISTRIBUTE_DESC
    bl_options = {'REGISTER', 'UNDO'}

    lock_pos: BoolProperty(
        name="Lock",
        description="Locks start and end positions",
        default=True
    )
    sorting: EnumProperty(
        name=Rlabels.PROP_REV_START_LABEL,
        description=Rlabels.PROP_REV_START_DESC,
        items=[
            ("TOP_LEFT", "Top - Left", ""),
            ("BOTTOM_RIGHT", "Bottom - Right", "")
        ],
        default="TOP_LEFT"
    )
    orient_along: EnumProperty(
        name=Rlabels.PROP_ALIGN_TO_LABEL,
        description=Rlabels.PROP_ALIGN_TO_DESC,
        items=[
                ("INPLACE", "In Place", ""),
                ("U", "U Axis", ""),
                ("V", "V Axis", ""),
                ("AUTO", "Auto", ""),
                # ("ORIGINAL", "Original", "")
            ],
        default="INPLACE"
    )
    sources: EnumProperty(
        name="Preset",
        description="",
        items=[
            ("SELECTED", "Selected", ""),

        ],
        default="SELECTED"
    )
    starts_pos: EnumProperty(
        name="Start Positions",
        description="Position of starts of loops",
        items=[
            ("ASIS", "As Is", ""),
            ("MAX", "Max", ""),
            ("MID", "Averaged", ""),
            ("MIN", "Min", "")
        ],
        default="ASIS"
    )
    ends_pos: EnumProperty(
        name="End Positions",
        description="Position of ends of loops",
        items=[
            ("ASIS", "As Is", ""),
            ("MAX", "Max", ""),
            ("MID", "Averaged", ""),
            ("MIN", "Min", "")
        ],
        default="ASIS"
    )
    spacing: EnumProperty(
        name=Rlabels.PROP_DISTRIBUTION_FROM_LABEL,
        description=Rlabels.PROP_DISTRIBUTION_FROM_DESC,
        items=[
            ("UV", "UV", ""),
            ("GEOMETRY", "Geometry", ""),
            ("EVENLY", "Evenly", "")
        ],
        default="GEOMETRY"
    )
    reverse_start: BoolProperty(
        name=Rlabels.PROP_REV_START_LABEL,
        description=Rlabels.PROP_REV_START_DESC,
        default=False
    )
    reverse_dir: BoolProperty(
        name=Rlabels.PROP_REV_DIR_LABEL,
        description=Rlabels.PROP_REV_DIR_DESC,
        default=False
    )
    relax_linked: BoolProperty(
        name=Rlabels.PROP_REL_LINK_LABEL,
        description=Rlabels.PROP_REL_LINK_DESC,
        default=False,
    )
    relax_mode: EnumProperty(
        name=Rlabels.PROP_REL_MODE_LABEL,
        description=Rlabels.PROP_REL_MODE_DESC,
        items=[
            ("ANGLE_BASED", "Angle Based", ""),
            ("CONFORMAL", "Conformal", ""),
        ]
    )
    angle: FloatProperty(
        name="Angle",
        min=0,
        max=45,
        default=15,
    )
    offset: FloatVectorProperty(
        name="Offset",
        description="The Distance from first loop to last",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ',
        step=0.1
    )
    offset_u: FloatProperty(
        name="Offset U",
        description="The Distance from first loop to last. Red color indicates that the value is not zero.",
        default=0.0,
        step=0.1
    )
    offset_v: FloatProperty(
        name="Offset V",
        description="The Distance from first loop to last. Red color indicates that the value is not zero.",
        default=0.0,
        step=0.1
    )
    select_border: BoolProperty(
        name="Select Border",
        description="Select UV Border",
        default=True,
    )
    border_offset: FloatProperty(
        name="Border Offset",
        description="Offset (scalar) for borders",
        default=1.0,
        step=0.01
    )
    border_proportion: EnumProperty(
        name="Length",
        description="How to calculate the lenght of each loop",
        items=[
            ("UV", "UV", "From length of UV Loop"),
            ("GEOMETRY", "Geometry", "From length of Geometry loop"),
            ("SHORT", "Short", "From distance between start and end of loop")
        ],
        default="SHORT"
    )
    detect_corners: EnumProperty(
        name="Corners By",
        description="How to find corners in borders",
        items=[
            ('CORNER', 'Corner', ''),
            ('PINS', 'Pinned', ''),
            ('CORNER_AND_PINS', 'Pinned & Corner', '')
            ],
        default='CORNER_AND_PINS',
    )

    desc: bpy.props.StringProperty(name="Description", default=Rlabels.PROP_DISTRIBUTE_DESC, options={'HIDDEN'})

    @classmethod
    def description(cls, context, properties):
        return properties.desc

    def draw(self, context):
        layout = self.layout
        self.draw_preset_selected(layout)
        self.draw_advanced(layout)

    def draw_advanced(self, layout):
        layout.separator_spacer()
        layout.label(text="Advanced:")
        box = layout.box()
        box.enabled = self.orient_along != "INPLACE"

        labels_row = box.row(align=True)
        labels_row.split(factor=0.5, align=True)
        labels_row.label(text="Start Position:")
        labels_row.label(text="End Position:")

        row = box.row(align=True)
        row.prop(self, "starts_pos", text="")
        if self.lock_pos:
            lock_icon = "LOCKED"
        else:
            lock_icon = "UNLOCKED"
        row.prop(self, "lock_pos", icon=lock_icon, icon_only=True)
        col = row.column(align=True)
        col.enabled = not self.lock_pos
        col.prop(self, "ends_pos", text="")
        # box.prop(self, "offset")


def _relax_linked(self, context):
    init_select_mode = context.tool_settings.mesh_select_mode[:]
    objs = list(context.objects_in_mode_unique_data)
    view_layer = context.view_layer
    active_obj = view_layer.objects.active

    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in objs:
        obj.select_set(state=False)

    for obj in objs:
        view_layer.objects.active = obj
        obj.select_set(state=True)
        bpy.ops.object.mode_set(mode='EDIT')

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.verify()
        sync_uv = context.scene.tool_settings.use_uv_select_sync

        init_pins = []
        init_selection = set()

        sync_mode = context.space_data.type == 'IMAGE_EDITOR' and sync_uv
        loops = [loop for face in bm.faces for loop in face.loops]

        for face in bm.faces:
            for loop in face.loops:
                if loop[uv_layer].pin_uv:
                    init_pins.append(loop[uv_layer])
                    loop[uv_layer].pin_uv = False
                if not sync_mode and loop[uv_layer].select:
                    init_selection.add(loop)
                if sync_mode and loop.vert.select:
                    init_selection.add(loop.vert)
                loop[uv_layer].pin_uv = True
        bm.faces.ensure_lookup_table()

        islands = island_util.get_island(context, bm, uv_layer)
        if not sync_mode:
            for island in islands:
                for face in island:
                    for loop in face.loops:
                        loop[uv_layer].pin_uv = loop[uv_layer].select
        else:
            for island in islands:
                for face in island:
                    for loop in face.loops:
                        loop[uv_layer].pin_uv = loop.vert.select

        if not sync_mode:
            for island in islands:
                for face in island:
                    for loop in face.loops:
                        loop[uv_layer].select = True
        else:
            for island in islands:
                for face in island:
                    face.select = True
        if bpy.ops.uv.unwrap.poll():
            bpy.ops.uv.unwrap(
                method=self.relax_mode,
                # fill_holes=self.fill_holes,
                # correct_aspect=self.correct_aspect,
                # ue_subsurf_data=self.use_subsurf_data,
                margin=0
            )

        for loop in loops:
            loop[uv_layer].pin_uv = False

        for loop in init_pins:
            loop.pin_uv = True

        # Restore Init Selection
        if not sync_mode:
            for loop in loops:
                if loop not in init_selection:
                    loop[uv_layer].select = False
        else:
            context.tool_settings.mesh_select_mode = [True, False, False]
            bmesh.select_mode = {'VERT'}
            for v in bm.verts:
                v.select = v in init_selection
            bm.select_flush_mode()

        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(state=False)

    for obj in objs:
        obj.select_set(state=True)
    view_layer.objects.active = active_obj
    bpy.ops.object.mode_set(mode='EDIT')
    context.tool_settings.mesh_select_mode = init_select_mode


uv_reshape_classes = (
    ZUV_OT_ReshapeIsland,
    ZUV_OT_DistributeVerts
)

if __name__ == '__main__':
    pass
