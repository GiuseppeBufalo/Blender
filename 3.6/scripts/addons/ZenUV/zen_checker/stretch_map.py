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

"""
    Zen UV Stretch Map
"""
import bpy
import bmesh
from mathutils import Vector, Color
from ZenUV.utils.generic import resort_by_type_mesh
from ZenUV.utils.generic import (
    get_mesh_data,
    select_islands
)
from ZenUV.zen_checker.zen_checker_labels import ZCheckerLabels as label
from ZenUV.ui.labels import ZuvLabels
from ZenUV.ui.pie import ZsPieFactory


class StretchMap():
    uv_layer = None
    colors = []
    baseColor = Color((0.0, 0.0, 1.0))
    alpha = 0.6

    def __init__(self, context):
        self.context = context
        self.objs = resort_by_type_mesh(context)

    def get_dir_vector(self, pos_0, pos_1):
        """ Return direction Vector from 2 Vectors """
        return Vector(pos_1 - pos_0)

    def fill_colors(self, bm):
        self.colors.clear()
        self.uv_layer = bm.loops.layers.uv.verify()
        angles_map = [self.calc_distortion_fac(vertex) for vertex in bm.verts]
        for angles in angles_map:
            self.colors.append((0.2, self.baseColor.g + angles, self.baseColor.b - angles, self.alpha))

    def calc_distortion_fac(self, vertex):
        """ Returns the distortion factor for a given vertex"""
        distortion = 0
        loops = vertex.link_loops
        for loop in loops:
            mesh_angle = loop.calc_angle()
            vec_0 = self.get_dir_vector(loop[self.uv_layer].uv, loop.link_loop_next[self.uv_layer].uv)
            vec_1 = self.get_dir_vector(loop[self.uv_layer].uv, loop.link_loop_prev[self.uv_layer].uv)
            uv_angle = vec_0.angle(vec_1, 0)
            distortion += abs(mesh_angle - uv_angle)
        return distortion

    def get_distorted_verts(self):
        out = dict()
        for obj in self.objs:
            bm, obj = self.get_bmesh(obj.name)
            self.uv_layer = bm.loops.layers.uv.verify()
            out.update({obj: [self.calc_distortion_fac(vertex) for vertex in bm.verts]})
            bm.free()
            return out

    def create_osl_buffer(self):
        out_dict = dict()

        for obj in self.objs:
            bm, obj = self.get_bmesh(obj.name)
            self.fill_colors(bm)
            verts = [(obj.matrix_world @ v.co) for v in bm.verts]
            face_tri_indices = [[loop.vert.index for loop in looptris] for looptris in bm.calc_loop_triangles() if not looptris[0].face.hide]
            out_dict.update({obj.name: {"verts": verts}})
            out_dict[obj.name].update({"faces": face_tri_indices})
            out_dict[obj.name].update({"colors": self.colors.copy()})
            bm.free()
        return out_dict

    def get_bmesh(self, obj_name):
        obj = self.context.scene.objects[obj_name]
        bm = bmesh.from_edit_mesh(obj.data).copy()
        bm.faces.ensure_lookup_table()
        return bm, obj


class ZUV_OT_SelectStretchedIslands(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_stretched_islands"
    bl_label = label.OT_STRETCH_SELECT_LABEL
    bl_description = label.OT_STRETCH_SELECT_DESC
    bl_options = {'REGISTER', 'UNDO'}

    Filter: bpy.props.FloatProperty(
        name=label.PROP_STRETCHED_FILTER_LABEL,
        description=label.PROP_STRETCHED_FILTER_DESC,
        min=0.1,
        default=0.1,
        precision=2,
    )

    def draw(self, context):
        self.layout.prop(self, "Filter")

    def invoke(self, context, event):
        self.objs = resort_by_type_mesh(context)
        if not self.objs:
            return {"CANCELLED"}
        sm = StretchMap(context)
        self.data = sm.get_distorted_verts()
        return self.execute(context)

    def execute(self, context):
        context.tool_settings.mesh_select_mode = [True, False, False]
        for obj, fac in self.data.items():
            me, bm = get_mesh_data(obj)
            bm.verts.ensure_lookup_table()
            for i in range(len(fac)):
                bm.verts[i].select = fac[i] > self.Filter
            bmesh.update_edit_mesh(me, loop_triangles=False)
        select_islands(context, self.objs)
        context.tool_settings.mesh_select_mode = [False, False, True]

        return {'FINISHED'}


class ZUV_OT_StretchMapSwitch(bpy.types.Operator):
    bl_idname = "uv.switch_stretch_map"
    bl_label = ZuvLabels.OT_STRETCH_DISPLAY_LABEL
    bl_description = ZuvLabels.OT_STRETCH_DISPLAY_DESC
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):

        ZsPieFactory.mark_pie_cancelled()

        if context.area.type == 'VIEW_3D':
            context.scene.zen_display.stretch = not context.scene.zen_display.stretch
        elif context.area.type == 'IMAGE_EDITOR':
            context.space_data.uv_editor.show_stretch = not context.space_data.uv_editor.show_stretch
        else:
            return {'CANCELLED'}

        return {'FINISHED'}


if __name__ == "__main__":
    pass
