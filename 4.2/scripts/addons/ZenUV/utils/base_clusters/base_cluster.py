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

import bmesh
import math
import numpy as np
from mathutils import Vector, Matrix
from ZenUV.utils.transform import (
    BoundingBox2d,
    BoundingBox3d,
    rotate_island,
    make_rotation_transformation,
    calculate_fit_scale,
    scale_island
)
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.constants import Planes
from ZenUV.utils.projection import Projection, pVector
from mathutils.geometry import box_fit_2d

# Debugging Purposes
# from ZenUV.utils.generic import Timer
from ZenUV.utils.generic import MeshBuilder
from ZenUV.utils.blender_zen_utils import ZenPolls


class BaseCluster():
    def __init__(self, context, obj, island, bm=None) -> None:
        self.island = self._island_container(island)
        self.context = context
        self.obj = self._object_container(obj)
        self.bm = self._get_bm() if bm is None else bm
        # self.bm.faces.ensure_lookup_table()
        self.destroy_bm = False
        self.transform_ma = self.obj.matrix_world
        self.loops = {loop.index: loop for face in self.island for loop in face.loops}
        self.uv_layer = self.bm.loops.layers.uv.verify()
        self.init_co = [loop[self.uv_layer].uv.copy().freeze() for loop in self.loops.values()]
        self.uv_layer_name = self.uv_layer.name

        self.bbox = BoundingBox2d(islands=[self.island, ], uv_layer=self.uv_layer)

        self.bound_uv_edges = self._cluster_bound_edges()

    def select(self, context, state=True):
        C = context
        uv_layer = self.uv_layer
        # self.mesh_edge.select = True
        sync_uv = C.scene.tool_settings.use_uv_select_sync
        if C.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            for loop in self.loops.values():
                loop[uv_layer].select = state
            if ZenPolls.version_greater_3_2_0:
                for loop in self.loops.values():
                    loop[uv_layer].select_edge = state
        else:
            for f in self.island:
                f.select = state

    def reset(self):
        for loop, co in zip(self.loops.values(), self.init_co):
            loop[self.uv_layer].uv = co

    def update_bounds(self):
        self.bound_uv_edges = self._cluster_bound_edges()

    def update_mesh(self):
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False)

    def _object_container(self, obj):
        if isinstance(obj, str):
            return self.context.scene.objects[obj]
        else:
            return obj

    def _check_zeroarea(self):
        zeroarea = [f for f in self.island if f.calc_area() == 0]
        return zeroarea

    def _island_container_worked(self, island):
        if not isinstance(island, list):
            island = list(island)
        if not isinstance(island[0], int):
            return island
        else:
            self.bm.faces.ensure_lookup_table()
            return [self.bm.faces[index] for index in island]

    def _island_container(self, island):
        if not isinstance(island, list):
            island = list(island)
        if not isinstance(island[0], int):
            return island
            # Fixed #371
            # return [f for f in island if f.calc_area() != 0]
        else:
            self.bm.faces.ensure_lookup_table()
            # Fixed #371
            # return [f for f in [self.bm.faces[index] for index in island] if f.calc_area() != 0]
            return [f for f in [self.bm.faces[index] for index in island]]

    def _get_bm(self):
        if self.obj.mode == "EDIT":
            return bmesh.from_edit_mesh(self.obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(self.obj.data)
            self.destroy_bm = True
            return bm

    def _cluster_bound_edges(self):
        edge_indexes = island_util.uv_bound_edges_indexes(self.island, self.uv_layer)
        edges = [e for f in self.island for e in f.edges if e.index in edge_indexes]
        loops = [loop for edge in edges for loop in edge.link_loops if loop in self.loops.values()]
        ex = []
        for loop in loops:
            ex.append(loop.link_loop_next)
        return loops + ex

    # Deleting (Calling destructor)
    def __del__(self):
        if self.destroy_bm:
            self.bm.free


class ProjectionPlane:
    i = 1
    j = 1
    direction = Vector((-1.0, 0.0, 0.0))
    transform = Matrix.Rotation(math.radians(45.0), 4, 'Z') @ Matrix.Rotation(math.radians(-20.0), 4, 'X')
    # transform = Matrix()
    s = transform @ Vector((0.0, 0.0, 0.0))
    x = transform @ Vector((1.0, 0.0, 0.0)) * i
    y = transform @ Vector((0.0, 0.0, 1.0)) * j
    s_uv = Vector((0.0, 0.0))
    x_uv = Vector((1.0, 0.0))
    y_uv = Vector((0.0, 1.0))


# class ProjectCluster(BaseCluster):
class ProjectCluster():

    def set_fit_to_uv(self, fit=False):
        self.fit_to_uv_area = fit

    def set_object(self, obj):
        self.obj = obj

    def set_transform(self, ma):
        self.ma = ma

    def project_hybrid_cluster(self):
        """ Creates a projection based on BaseCluster and ZenCluster data """
        self.project()

        edges = [edge for edge in self.uv_edges if edge.is_border()]
        distortion = (np.random.rand(len(edges), 2) * 0.001).tolist()
        verts = [[edge.vert, edge.other_vert] for edge in edges]
        for v_edge, dist in zip(verts, distortion):
            vec = Vector(dist)
            v_edge[0].move_by(vec)
            v_edge[1].move_by(vec)
    
    def project_face_loops(self, loops, uv_layer, input_plane=None, s_factor=1.0):
        plane = self.check_input_plane(input_plane, rough_fit=True)

        base_co, base_uv, to_uv = self._project(plane)

        for lp in loops:
            lp[uv_layer].uv = base_uv + (self.ma @ lp.vert.co - base_co) @ to_uv * s_factor

    def project(self, input_plane=None, s_factor=1.0):
        """ plane - Vectors list size 3
        Sample  [Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0))]
        Mapping [zero, x, y]
        """
        if not hasattr(self, "ma"):
            self.ma = Matrix()

        plane = self.check_input_plane(input_plane, rough_fit=True)

        base_co, base_uv, to_uv = self._project(plane)

        for lp in self.loops.values():
            lp[self.uv_layer].uv = base_uv + (self.ma @ lp.vert.co - base_co) @ to_uv * s_factor

        # Fit to UV Area
        if hasattr(self, "fit_to_uv_area") and self.fit_to_uv_area:
            points = [lp[self.uv_layer].uv for lp in self.loops.values()]
            points = np.array(points)
            points = self._fit_to_uv_area(points)
            points *= s_factor

            for lp, co in zip(self.loops.values(), points):
                lp[self.uv_layer].uv = co

    def _project(self, plane):
        base_co = plane.s
        x = plane.x - base_co
        y = plane.y - base_co
        normal = x.cross(y)

        base_uv = plane.s_uv

        u = plane.x_uv - base_uv
        v = plane.y_uv - base_uv

        to_uv = Matrix([x, y, normal]).inverted(Matrix([x, y, normal])) @ Matrix([u, v, [0, 0]])
        return base_co, base_uv, to_uv

    def check_input_plane(self, input_plane, rough_fit=True):
        if not input_plane:
            plane = ProjectionPlane()

            # Try to fit Plane to Object bbox.
            if rough_fit:
                bbox = BoundingBox3d(self.obj)
                plane.s = bbox.lo_point * Vector((1, 0, 1))
                factor = bbox.max_dim
                plane.x = plane.s + plane.x * factor
                plane.y = plane.s + plane.y * factor

        else:
            plane = ProjectionPlane()
            plane.s = input_plane[0]
            plane.x = input_plane[1]
            plane.y = input_plane[2]
        return plane

    def project_zen_cluster(self, input_plane=None, s_factor=1.0):
        """ Create projection only for ZenCluster. """
        plane = self.check_input_plane(input_plane, rough_fit=True)

        base_co, base_uv, to_uv = self._project(plane)

        for edge in self.uv_edges:
            distortion = np.random.rand(1, 2)[0] * 0.001 if edge.is_border() else [0, 0]
            for v in (edge.vert, edge.other_vert):
                v.set_position(Vector(distortion) + base_uv + (v.mesh_vert.co - base_co) @ to_uv * s_factor)

    def preproject(self):
        """ Create simple preprojection in general purposes.
            Main goal is to avoid zero uv coordinates. """
        coo = np.random.rand(len(self.loops), 2)
        for lp, co in zip(self.loops.values(), coo):
            lp[self.uv_layer].uv = co

    def project_obj_mode(self, input_plane=None, s_factor=1.0):
        """ Create projection in OBJECT MODE.
        self.obj need to be specified. self.set_object(obj)."""

        if not hasattr(self, "ma"):
            self.ma = Matrix()

        plane = self.check_input_plane(input_plane, rough_fit=True)
        base_co, base_uv, to_uv = self._project(plane)

        me = self.obj.data
        uv_layer = me.uv_layers.active.data

        for lp in me.loops:
            vertex_co = self.ma @ me.vertices[lp.vertex_index].co
            uv_layer[lp.index].uv = base_uv + (vertex_co - base_co) @ to_uv * s_factor

        # Fit to UV Area
        if hasattr(self, "fit_to_uv_area") and self.fit_to_uv_area:
            loops = {uv_layer[lp.index]: uv_layer[lp.index].uv for lp in me.loops}
            points = np.array(list(loops.values()))

            points = self._fit_to_uv_area(points)
            points *= s_factor

            for loop, coo in zip(loops.keys(), points):
                loop.uv = coo

    def _fit_to_uv_area(self, points):
        factor = self._get_factor(points=points.tolist())
        points *= factor
        shift = self._get_shift(points=points.tolist())
        points += shift
        return points

    def _get_shift(self, points):
        bbox = BoundingBox2d(points=points)
        return bbox.shift_to_uv_area

    def _get_factor(self, points):
        bbox = BoundingBox2d(points=points)
        return bbox.factor_to_uv_area


# class TransformCluster(ZenCluster):
class TransformCluster():

    # def __init__(self, context, obj, island, bm=None) -> None:
    #     super().__init__(context, obj, island, bm)

    def rotate(self, angle=1.5708, anchor=None):
        """ angle in radians """
        if not anchor:
            anchor = self.bbox.center
        rotate_island(self.island, self.uv_layer, angle, anchor)

    def fit(self, fit_mode="cen", keep_proportion=True, bounds=Vector((1.0, 1.0))):
        scale = calculate_fit_scale(fit_mode, 0.0, self.bbox, keep_proportion, bounds=bounds)
        scale_island(self.island, self.uv_layer, scale, anchor=self.bbox.center)

    def move_to_pos(self, pos):
        loops = [loop[self.uv_layer] for loop in self.loops.values()]
        uvs = np.array(loop.uv for loop in loops)
        uvs += pos
        for lp, uv in zip(loops, uvs):
            lp.uv = uv


# class OrientCluster(TransformCluster):
class OrientCluster():

    def __init__(self):
        self.f_orient = False
        self.axis_direction = {
                "x": 0.0,
                "-x": 0.0,
                "y": 0.0,
                "-y": 0.0,
                "z": 0.0,
                "-z": 0.0,
            }
        self.show_info = False
        self.compensate_transform = False
        self.primary_edges = None
        self.cluster_normal_axis = None
        # self.real_matrix = self.transform_ma.inverted_safe().transposed().to_3x3()
        self.transform_ma = Matrix()
        self.cluster_normal = None

        self._cluster_parametrization()

        self.edge_anchor = None
        self.uv_angle = 0
        self.mesh_angle = 0
        self.master_edge = None
        self.select_master_edge = False
        self.type = 'ORGANIC'

    def select_by_axis(self, input_axis):
        dot = -100
        axis = 0

        for ax, plane in Planes.pool_3d_orient_dict.items():
            current_dot = self.cluster_normal.dot(plane)
            if current_dot > dot:
                dot = current_dot
                axis = ax
        axis = self._test_for_z(self.cluster_normal, axis)

        if input_axis[axis]:
            for face in self.island:
                face.select = True

    def set_direction(self, direction):
        rev_values = {True: math.pi, False: 0.0}
        for axis, _dir in direction.items():
            self.axis_direction[axis] = rev_values[_dir]

    def _set_compensate_transform(self, state):
        if state:
            self.transform_ma = self.real_matrix
        else:
            self.transform_ma = Matrix().inverted_safe().transposed().to_3x3()
        self.compensate_transform = state
        # print(f"Matrix:\n{self.transform_ma}")

    def orient_to_world(self):
        if self.type == 'ORGANIC':
            self._orient_organic()
        elif self.type == 'HARD':
            self._orient_hard()
        else:
            print("The Cluster TYPE is not defined. Define the TYPE first.(HARD, ORGANIC)")

    def show_data(self):
        self.show_info = True
        print("\nOrient Cluster Data: ")
        print("Master Edge Index ->", self.master_edge.mesh_edge.index)
        print("UV Angle: ", math.degrees(self.uv_angle))
        print("Mesh Angle: ", math.degrees(self.mesh_angle))

    def _find_min_vertical(self, edge):
        verts_co_z = []
        for vert in edge.mesh_verts:
            verts_co_z.append((self.transform_ma @ vert.co).z)
        return min(verts_co_z)

    def _find_min_horizontal(self, edge):
        verts_co_y = []
        for vert in edge.mesh_verts:
            verts_co_y.append((self.transform_ma @ vert.co).y)
        return min(verts_co_y)

    def _cluster_parametrization(self):

        self.primary_edges = self._find_primary_edges()
        normal = self.get_cluster_overall_normal()
        if normal.magnitude < 1:
            normal = self.get_cluster_simple_normal()

        normal.normalize()

        self.cluster_normal = normal
        self.cluster_normal_axis = self._get_cluster_normal_axis()

        if "z" in self.cluster_normal_axis:
            self.primary_edges = self._find_primary_edges(vertical=False)

    def get_cluster_simple_normal(self):
        edge = self.primary_edges[0]
        normals = [loop.face.normal for loop in edge.loops]
        normal = Vector()
        for n in normals:
            normal += n
        normal = self.transform_ma @ normal
        return normal

    def get_cluster_overall_normal(self):
        normal = Vector()
        for face in self.island:
            normal = normal + face.normal
        normal = self.transform_ma @ normal
        return normal

    def build_vector(self, normal):
        builder = MeshBuilder(self.bm)
        coords = (Vector(), normal)
        builder.create_edge(coords)

    def _test_for_z(self, normal, axis):

        if round(normal.x, 4) == round(Planes.z3_negative.x, 4) and \
           round(normal.y, 4) == round(Planes.z3_negative.y, 4) and \
           round(normal.z, 4) == round(Planes.z3_negative.z, 4):
            return "-z"

        if round(normal.x, 4) == round(Planes.z3.x, 4) and \
           round(normal.y, 4) == round(Planes.z3.y, 4) and \
           round(normal.z, 4) == round(Planes.z3.z, 4):
            return "z"

        return axis

    def _orient_hard(self):
        axis = self.cluster_normal_axis
        self.master_edge = self.primary_edges[0]

        prj = Projection(self.transform_ma, self.bm, self.master_edge)
        proj = prj.uni_project(axis)
        self.mesh_angle = proj.angle_to_y_2d()
        self.uv_angle = pVector((
            self.master_edge.vert.uv_co,
            self.master_edge.other_vert.uv_co)).angle_to_y_2d() * -1
        if self.show_info:
            print(f"MASTER EDGE: {self.master_edge.vert.uv_co}")

        if axis == "-x":
            dif_angle = self.uv_angle - self.mesh_angle
        if axis == "x":
            dif_angle = self.uv_angle + self.mesh_angle
        if axis == "y":
            dif_angle = self.uv_angle - self.mesh_angle
        if axis == "-y":
            dif_angle = self.uv_angle + self.mesh_angle
        if axis == "-z":
            dif_angle = self.uv_angle - self.mesh_angle
            dif_angle += math.pi
        if axis == "z":
            dif_angle = self.uv_angle + self.mesh_angle

        dif_angle += self.axis_direction[axis]

        if self.select_master_edge:
            self.master_edge.mesh_edge.select = True

        self.rotate(angle=dif_angle, anchor=self.edge_anchor)

        for vert in self.uv_verts:
            vert.update_uv_co()
        if self.f_orient:
            dif_angle = self.further_orient()
            if axis == "-z":
                dif_angle += math.pi
            dif_angle += self.axis_direction[axis]
            self.rotate(angle=dif_angle, anchor=self.edge_anchor)

        if self.show_info:
            print(f"Axis: {axis}")
            print("Diff Angle: ", math.degrees(dif_angle))

    def _get_cluster_normal_axis(self):
        dot = -100
        axis = 0

        for ax, plane in Planes.pool_3d_orient_dict.items():
            current_dot = self.cluster_normal.dot(plane)
            if current_dot > dot:
                dot = current_dot
                axis = ax
        axis = self._test_for_z(self.cluster_normal, axis)
        return axis

    def is_orient_vertical(self, points):
        treshold = 2.0
        bbox = BoundingBox2d(points=points)
        scope = [bbox.len_x, bbox.len_y]

        # x = min(scope) * 100 / max(scope)
        if 100 - (min(scope) * 100 / max(scope)) < treshold:
            return None
        elif bbox.len_y > bbox.len_x:
            return True
        elif bbox.len_y < bbox.len_x:
            return False

    def _get_angle_to_horizontal(self, points, base_indexes):
        angle = self._get_angle_to_vertical(points, base_indexes)
        angle += math.pi / 2

        r_points = self.fake_rotation(points, angle)

        if r_points[base_indexes[0]].y > r_points[base_indexes[1]].y:
            angle += math.pi

        return angle

    def _get_angle_to_vertical(self, points, base_indexes):
        bi_01 = base_indexes[0]
        bi_02 = base_indexes[1]

        angle = proposed_angle = box_fit_2d(points)

        if math.pi + 0.0349066 > proposed_angle > math.pi - 0.0349066:
            angle = 0.0

        r_points = self.fake_rotation(points, angle)

        if not self.is_orient_vertical(r_points):
            if angle > 0:
                angle -= math.pi / 2
            else:
                angle += math.pi / 2
            r_points = self.fake_rotation(points, angle)

        if round(r_points[bi_01].y, 4) == round(r_points[bi_02].y, 4):
            angle -= math.pi
            r_points = self.fake_rotation(r_points, angle)

        if r_points[bi_01].y > r_points[bi_02].y:
            angle += math.pi
            r_points = self.fake_rotation(points, angle)

        return angle

    def print_r_points(self, r_points):
        print("r_points -->")
        for p in r_points:
            print(p)
        print("r_points <--")

    def fake_rotation(self, points, angle):
        r_points = []
        bbox = BoundingBox2d(points=points)
        rotated = make_rotation_transformation(angle, bbox.center)

        for i in range(len(points)):
            r_points.append(Vector(rotated(points[i])))
        return r_points

    def further_orient(self):
        edge = self._find_base_vector()[0]
        self.append_uv_edge(edge)
        base_vector_vert_indexes = [edge.vert.index, edge.other_vert.index]
        points = [vert.uv_co for vert in self.uv_verts]
        vertical = self.is_orient_vertical(points)
        if vertical is None:
            return 0.0
        elif vertical:
            angle = self._get_angle_to_vertical(points, base_vector_vert_indexes)
        elif not vertical:
            angle = self._get_angle_to_horizontal(points, base_vector_vert_indexes)

        return angle

    def _orient_organic(self):
        edge = self._find_base_vector()[0]

        dot = -100
        axis = 0

        for ax, plane in Planes.pool_3d_orient_dict.items():
            current_dot = self.cluster_normal.dot(plane)
            if current_dot > dot:
                dot = current_dot
                axis = ax
        axis = self._test_for_z(self.cluster_normal, axis)
        self.master_edge = None
        prj = Projection(self.transform_ma, self.bm, edge)
        proj = prj.uni_project(axis)
        self.mesh_angle = proj.angle_to_y_2d()
        self.uv_angle = pVector((
            edge.vert.uv_co,
            edge.other_vert.uv_co)).angle_to_y_2d()

        dif_angle = - self.uv_angle + self.mesh_angle

        if axis == "-x":
            dif_angle = - self.uv_angle - self.mesh_angle
        if axis == "x":
            dif_angle = - self.uv_angle + self.mesh_angle
        if axis == "y":
            dif_angle = - self.uv_angle - self.mesh_angle
        if axis == "-y":
            dif_angle = - self.uv_angle + self.mesh_angle
        if axis == "-z":
            dif_angle += math.pi
        if axis == "-z":
            dif_angle = - self.uv_angle + self.mesh_angle

        dif_angle += self.axis_direction[axis]

        self.rotate(angle=dif_angle, anchor=self.edge_anchor)

        if self.show_info:
            print(f"Axis: {axis}")
            print("Diff Angle: ", math.degrees(dif_angle))

    def _find_base_vector(self):
        fake_edge = self.primary_edges[0]
        scope = dict()
        for vert in self.uv_verts:
            if "z" not in self.cluster_normal_axis:
                co = (self.transform_ma @ vert.mesh_vert.co).z
            else:
                co = (self.transform_ma @ vert.mesh_vert.co).y
            if co not in scope.keys():
                scope.update({co: []})
            scope[co].append(vert)
        v01 = scope[min(scope.keys())][0]
        v02 = scope[max(scope.keys())][0]
        fake_edge.vert = v01
        fake_edge.other_vert = v02
        fake_edge.verts_co = [v01.uv_co, v02.uv_co]
        fake_edge.mesh_verts = [v01.mesh_vert, v02.mesh_vert]

        return [fake_edge, ]

    def _find_primary_edges(self, vertical=True):
        uv_edges = self.uv_edges
        scope = dict()
        for edge in uv_edges:
            if vertical:
                min_value = self._find_min_vertical(edge)
            else:
                min_value = self._find_min_horizontal(edge)
            if min_value not in scope.keys():
                scope.update({min_value: []})
            scope[min_value].append(edge)

        stored_edges = scope[min(scope.keys())]
        scope = dict()
        for edge in stored_edges:
            v01 = edge.mesh_verts[0]
            v02 = edge.mesh_verts[1]
            vec_edge = (self.transform_ma @ v01.co) - (self.transform_ma @ v02.co)
            if vertical:
                current_dot = abs(vec_edge.dot(Planes.z3))
            else:
                current_dot = abs(vec_edge.dot(Planes.y3))
            if current_dot not in scope.keys():
                scope.update({current_dot: []})
            scope[current_dot].append(edge)
        result_edges = scope[max(scope.keys())]
        return result_edges
