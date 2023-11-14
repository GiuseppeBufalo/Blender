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
from ZenUV.stacks.utils import Cluster
from ZenUV.ui.labels import ZuvLabels


class dsProps:

    def __init__(self, sort_to, inplace, base_pos, margin, reverse, axis) -> None:
        self.sort_to = sort_to
        self.inplace = inplace
        self.base_position = base_pos
        self.margin = Vector((margin, margin))
        self.reverse = reverse
        self.axis = {"U": Vector((1, 0)), "V": Vector((0, 1))}[axis]
        self.opposite_axis = {"V": Vector((1, 0)), "U": Vector((0, 1))}[axis]


class dsCluster(Cluster):

    def __init__(self, context, obj, island, props) -> None:
        super().__init__(context, obj, island)
        self.index = None

        self.s_value = {
            "NONE": 1,
            "UVAREA": self.get_uv_area(),
            "MESHAREA": self.area,
            "TD": self.get_td()[0],
            "UVCOVERAGE": self.get_td()[1],
            "MESH_X": self.get_mesh_position("X"),
            "MESH_Y": self.get_mesh_position("Y"),
            "MESH_Z": self.get_mesh_position("Z"),
        }[props.sort_to]
        self.position = None

    def get_mesh_position(self, axis):
        pos = sum([self.obj.matrix_world @ v.co for v in self.verts.values()], Vector()) / len(self.verts)
        return {"X": pos.x, "Y": pos.y, "Z": pos.z}[axis]


class Chart:

    def __init__(self, PROPS) -> None:

        self.PROPS = PROPS
        self.scope = []
        self.b_position = PROPS.base_position

    def append(self, dsCluster):
        dsCluster.index = len(self.scope)
        self.scope.append(dsCluster)

    def _fill_position(self):
        position = self.b_position
        margin = self.PROPS.margin
        for cluster in self.scope:
            cluster.position = position + (Vector((cluster.bbox["len_x"], cluster.bbox["len_y"])) / 2) * self.PROPS.axis
            position = position + (Vector((cluster.bbox["len_x"], cluster.bbox["len_y"])) + margin) * self.PROPS.axis

    def _sort_by_value(self, f):
        return f.s_value

    def correct_position(self):
        for cl in self.scope:
            cl.position += cl.bbox["cen"] * self.PROPS.opposite_axis

    def _sort(self):
        self.scope = sorted(self.scope, key=self._sort_by_value, reverse=self.PROPS.reverse)
        # print("Sorted Scope --> ", [i.s_value for i in self.scope])
        self._fill_position()
        if self.PROPS.inplace:
            self.correct_position()

    def set_to_position(self):
        self._sort()

        for cl in self.scope:
            cl.move_to(cl.position)
            cl.update_mesh()


def sort_island_faces(f):
    return f.index


def sort_islands_by_i_index(f):
    return f[0].index


class ZUV_OT_Distribute_Islands(bpy.types.Operator):
    bl_idname = "uv.zenuv_distribute_islands"
    bl_label = "Distribute"
    bl_description = "Distributes and sorts the selected islands."
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        description="Direction Axis",
        items=[
            ("U", "U", "U Axis"),
            ("V", "V", "V Axis")
            ]
    )

    from_where: FloatVectorProperty(
        name=ZuvLabels.PROP_FROM_WHERE_LABEL,
        description=ZuvLabels.PROP_FROM_WHERE_DESC,
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ'
    )
    sort_to: EnumProperty(
        name=ZuvLabels.PROP_SORT_TO_LABEL,
        description=ZuvLabels.PROP_SORT_TO_DESC,
        items=[
            ("NONE", "None", ""),
            ("UVAREA", "UV Area", ""),
            ("MESHAREA", "Mesh Area", ""),
            ("TD", "Texel Density", ""),
            ("UVCOVERAGE", "UV Coverage", ""),
            ("MESH_X", "Island Mesh Position X", ""),
            ("MESH_Y", "Island Mesh Position Y", ""),
            ("MESH_Z", "Island Mesh Position Z", "")
        ],
        default="NONE"
    )
    reverse: BoolProperty(
        name=ZuvLabels.PROP_REV_SORT_LABEL,
        description=ZuvLabels.PROP_REV_SORT_DESC,
        default=False
    )
    margin: FloatProperty(
        name=ZuvLabels.PROP_SORT_MARGIN_LABEL,
        description=ZuvLabels.PROP_SORT_MARGIN_LABEL,
        min=0.0,
        default=0.005,
        precision=3
    )

    inplace: BoolProperty(
        name="In Place",
        description="Leave not active axis as is",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Direction Axis: ")
        row.prop(self, "axis", expand=True)
        layout.prop(self, "from_where")
        layout.prop(self, "sort_to")
        row = layout.row()
        row.enabled = not self.sort_to == "NONE"
        row.prop(self, "reverse")
        layout.prop(self, "margin")
        layout.prop(self, "inplace")

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {"CANCELLED"}
        PROPS = dsProps(self.sort_to, self.inplace, self.from_where, self.margin, self.reverse, self.axis)
        chart = Chart(PROPS)
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            islands = self.distribute_sort_islands(island_util.get_island(context, bm, uv_layer))

            for island in islands:
                chart.append(dsCluster(context, obj, island, PROPS))

        chart.set_to_position()

        return {'FINISHED'}

    def distribute_sort_islands(self, islands):
        ''' Sorting distributed islands '''
        scope = []
        for island in islands:
            scope.append(sorted(island, key=sort_island_faces))
        return sorted(scope, key=sort_islands_by_i_index)


uv_distribute_classes = (
    ZUV_OT_Distribute_Islands,
)

if __name__ == '__main__':
    pass
