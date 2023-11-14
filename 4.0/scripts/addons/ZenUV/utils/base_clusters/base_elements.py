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

from mathutils import Vector
from math import pi
from ZenUV.utils.blender_zen_utils import ZenPolls
from ZenUV.utils.constants import u_axis, v_axis


class UvEdge:

    def __init__(self, index, GEdge, loops, uv_vert, other_uv_vert, uv_layer) -> None:
        self.index = index
        self.uv_layer = uv_layer
        self.mesh_edge = GEdge
        self.mesh_verts = GEdge.verts
        self.vert = uv_vert
        self.other_vert = other_uv_vert
        self.verts = [self.vert, self.other_vert]
        self.verts_co = [self.vert.uv_co, self.other_vert.uv_co]
        self.loops = loops
        self.index_in_stripe = 0
        self.orientation = None

    def select(self, context, state=True):
        C = context
        uv_layer = self.uv_layer
        # self.mesh_edge.select = True
        sync_uv = C.scene.tool_settings.use_uv_select_sync
        if C.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            if ZenPolls.version_greater_3_2_0:
                if C.scene.tool_settings.uv_select_mode == "EDGE":
                    for loop in self.loops:
                        loop[uv_layer].select_edge = state
                    for v in self.verts:
                        v.select_state(context, state)
                else:
                    for v in self.verts:
                        v.select_state(context, state)
            else:
                for v in self.verts:
                    v.select_state(context, state)
        else:
            C.tool_settings.mesh_select_mode = [False, True, False]
            self.mesh_edge.select = state

    def get_len(self):
        return (self.verts_co[1] - self.verts_co[0]).magnitude

    def get_select_state(self, context):
        selected = False
        C = context
        uv_layer = self.uv_layer
        sync_uv = C.scene.tool_settings.use_uv_select_sync
        if C.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            if ZenPolls.version_greater_3_2_0:
                selected = True in [loop[uv_layer].select_edge for loop in self.loops]
            else:
                selected = False not in [v.get_select_state(context) for v in self.verts]
        else:
            mode = C.tool_settings.mesh_select_mode
            if mode[0]:
                if self.vert.mesh_vert.select and self.other_vert.mesh_vert.select:
                    selected = True
            elif mode[1]:
                if self.mesh_edge.select:
                    selected = True
        return selected

    def get_orientation(self):
        edge_vector = self.verts_co[1] - self.verts_co[0]
        if abs(edge_vector.dot(u_axis)) < abs(edge_vector.dot(v_axis)):
            self.direction = v_axis
            return v_axis
        else:
            self.direction = u_axis
            return u_axis

    def get_orientation_by_angle(self, angle, axis):
        points = ({(self.verts_co[1] * axis).magnitude: self.verts_co[1], (self.verts_co[0] * axis).magnitude: self.verts_co[0]})
        head = max(points.keys())
        tail = min(points.keys())
        edge_vector = points[head] - points[tail]
        edge_vector *= edge_vector.normalized()
        angle_to_axis = edge_vector.angle(axis, pi * 0.5)
        if 0 <= angle_to_axis < angle:
            return True
        return False

    def reverse(self):
        self.verts_co = [self.other_vert.uv_co, self.vert.uv_co]
        hold_vert = self.vert
        self.vert = self.other_vert
        self.other_vert = hold_vert
        # self.verts = [self.vert, self.other_vert]
        self.verts = [self.other_vert, self.vert]

    def is_border(self):
        return len(self.loops) == 1

    def get_direction(self):
        if self.is_border():
            loop = self.loops[0]
            if loop[self.uv_layer].uv == self.vert.uv_co:
                return "CCV"
        return "CV"

    def orient_to_world(self):
        if self.vert.mesh_vert.co.z > self.other_vert.mesh_vert.co.z:
            self.reverse()
            return True
        return False


class UvVertex:

    def __init__(self, index, GVertex, loops, uv_layer) -> None:
        self.index = index
        self.mesh_vert = GVertex
        self.link_loops = loops
        self.uv_layer = uv_layer
        self.link_uv_faces = []
        self.uv_co = loops[0][uv_layer].uv.copy().freeze() or Vector()
        self.corner = None
        self.pinned = None

    def update_corner(self):
        self.corner = len(self.link_uv_faces) == 1

    def update_pinned(self):
        self.pinned = True in [loop[self.uv_layer].pin_uv for loop in self.link_loops]

    def select_state(self, context, state):
        C = context
        uv_layer = self.uv_layer
        sync_uv = C.scene.tool_settings.use_uv_select_sync
        if C.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            for loop in self.link_loops:
                loop[uv_layer].select = state
        else:
            self.mesh_vert.select = state

    def get_select_state(self, context):
        C = context
        uv_layer = self.uv_layer
        sync_uv = C.scene.tool_settings.use_uv_select_sync
        if C.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            return False not in [loop[uv_layer].select for loop in self.link_loops]
        else:
            return self.mesh_vert.select

    def set_position(self, coords):
        for loop in self.link_loops:
            loop[self.uv_layer].uv = coords
        # self.uv_co = self.link_loops[0][self.uv_layer].uv.copy().freeze()
        self.update_uv_co()

    def move_by(self, coords):
        for loop in self.link_loops:
            loop[self.uv_layer].uv += coords
        # self.uv_co = self.link_loops[0][self.uv_layer].uv.copy().freeze()
        self.update_uv_co()

    def update_uv_co(self):
        self.uv_co = self.link_loops[0][self.uv_layer].uv.copy().freeze() or Vector()


class UvFace:

    def __init__(self, index, Gface) -> None:
        self.index = index
        self.mesh_face = Gface
        self.uv_verts = []
        self.uv_edges = []
