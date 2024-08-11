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

import math
from mathutils import Vector
from ZenUV.utils.constants import Planes
from ZenUV.utils.generic import MeshBuilder


class pVector:

    def __init__(self, vec) -> None:
        self.start = vec[0]
        self.end = vec[1]
        self.vec = self.end - self.start
        self.length = self.get_length()
        self.angle_to_y = self.angle_to_y_2d()
        # self.bbox = BoundingBox2d(points=(self.start[:2], self.end[:2]))
        # print("==== pVector:")
        # print(f"Input: {vec}\nStart: {self.start}\nEnd: {self.end}\nVec: {self.vec}")
        # print("====")

    def get_length(self):
        return self.vec.magnitude

    # def angle_to_x(self):
    #     return self.vec.angle(Planes.x, 0)

    def angle_to_y_2d(self):
        # if self.length == 0.0:
        #     print("************************************** Zero VEC")
        return self.vec.angle_signed(Planes.axis_y, 0)

    # def _get_vector(self):
    #     if self.end.magnitude < self.start.magnitude:
    #         self._revert()
    #     return self.end - self.start

    # def _revert(self):
    #     backup = self.start
    #     self.start = self.end
    #     self.end = backup
    #     self.reverted = True


class Projection:

    def __init__(self, ma_transform, bm, edge) -> None:
        self.ma_tr = ma_transform
        self.bm = bm
        self.edge = edge
        self.point_01 = self.ma_tr @ self.edge.vert.mesh_vert.co
        self.point_02 = self.ma_tr @ self.edge.other_vert.mesh_vert.co
        self.reversed = False
        self._set_orientation()
        self.anchor = self.edge.vert.uv_co
        # print(f"Projection -> Matrix -> {self.ma_tr}")
        # self.planes = Planes()
        # print("\nCreating Projections: -----------------")
        self.projected = []
        # self.project_mesh()
        self.real_length = edge.mesh_edge.calc_length()
        # print(f"Edge Real Length: {self.real_length}")
        # print("---------------------------------------\n")
        # output
        # for pr in self.projected:
        #     print("Length: ", pr.length())
        #     print("Angle: ", math.radians(pr.angle_to_x_2d()))
        # print("correct_angle: ", math.radians(self.get_angle_by_length()))
        # print("---------------------------------------\n")

    def uni_project(self, axis):
        solver = {
            "x": self.project_x(),
            "y": self.project_y(),
            "z": self.project_z(),
            "-x": self.project_x_negative(),
            "-y": self.project_y_negative(),
            "-z": self.project_z_negative()
        }
        return solver[axis]

    def project_to_cluster(self, cluster_normal):
        v1 = self.project_onto_plane(self.point_01, cluster_normal)
        v2 = self.project_onto_plane(self.point_02, cluster_normal)
        projection = Vector((v1[1], v1[2])), Vector((v2[1], v2[2]))
        # print(f" - X: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def _set_orientation(self):
        if (self.point_01).z > (self.point_02).z:
            self.edge.reverse()
            store = self.point_01
            self.point_01 = self.point_02
            self.point_02 = store
            self.reversed = True

    def project_x_negative(self):
        v1 = self.project_onto_plane(self.point_01, Planes.x3_negative)
        v2 = self.project_onto_plane(self.point_02, Planes.x3_negative)
        projection = Vector((v1[1], v1[2])), Vector((v2[1], v2[2]))
        # print(f" - X: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_y_negative(self):
        v1 = self.project_onto_plane(self.point_01, Planes.y3_negative)
        v2 = self.project_onto_plane(self.point_02, Planes.y3_negative)
        projection = Vector((v1[0], v1[2])), Vector((v2[0], v2[2]))
        # print(f" - Y: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_z_negative(self):
        v1 = self.project_onto_plane(self.point_01, Planes.z3_negative)
        v2 = self.project_onto_plane(self.point_02, Planes.z3_negative)
        projection = Vector((v1[0], v1[1])), Vector((v2[0], v2[1]))
        # print(f" - Z: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_x(self):
        v1 = self.project_onto_plane(self.point_01, Planes.x3)
        v2 = self.project_onto_plane(self.point_02, Planes.x3)
        projection = Vector((v1[1], v1[2])), Vector((v2[1], v2[2]))
        # print(f"X: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_y(self):
        v1 = self.project_onto_plane(self.point_01, Planes.y3)
        v2 = self.project_onto_plane(self.point_02, Planes.y3)
        projection = Vector((v1[0], v1[2])), Vector((v2[0], v2[2]))
        # print(f"Y: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_z(self):
        v1 = self.project_onto_plane(self.point_01, Planes.z3)
        v2 = self.project_onto_plane(self.point_02, Planes.z3)
        projection = Vector((v1[0], v1[1])), Vector((v2[0], v2[1]))
        # print(f"Z: v1 - {v1}, v2 - {v2}\n  Proj - {projection}")
        return pVector(projection)

    def project_mesh(self):
        self.projected.append(self.project_x())
        self.projected.append(self.project_y())
        self.projected.append(self.project_z())
        print("Projections data output: ------------------")
        axes = ("X: ", "Y: ", "Z: ")
        for axe, pr in zip(axes, self.projected):
            print(f"{axe}Angle {math.degrees(pr.angle_to_y)}, Length: {pr.length}")
        print("-------------------------------------------")

    def build_projections(self):
        builder = MeshBuilder(self.bm)
        for pr in self.projected:
            coords = (pr.start.resized(3), pr.end.resized(3))
            print("coords: ", coords)
            builder.create_edge(coords)

    def project_mesh_rev_01(self):
        for plane in Planes.pool_3d:
            self.projected.append(
                pVector(
                    [
                        Vector((self.project_onto_plane(self.point_01, plane))),
                        Vector((self.project_onto_plane(self.point_02, plane)))
                    ]
                )
            )
        # self.x = self.projected[0]
        # self.y = self.projected[1]
        # self.z = self.projected[2]

    def project_uv(self):
        return pVector((self.edge.vert.uv_co, self.edge.other_vert.uv_co))

    def get_angle_by_length(self):
        length = 0.0
        angle = 0.0
        print("PR: ----")
        for pr in self.projected:
            print(pr.get_length())
            new_length = pr.get_length()
            if new_length > length:
                length = new_length
                angle = pr.angle_to_y_2d()
        return angle

    # def get_angle_by_ratio(self):
    #     ratio = 0.0
    #     angle = 0.0
    #     for pr in self.projected:
    #         new_ratio = pr.bbox.len_x / (pr.bbox.len_y + 0.000000001)
    #         if new_ratio > ratio:
    #             ratio = new_ratio
    #             angle = pr.angle_to_x_2d()
    #     return angle

    def dot_product(self, x, y):
        return sum([x[i] * y[i] for i in range(len(x))])

    def norm(self, x):
        return math.sqrt(self.dot_product(x, x))

    def normalize(self, x):
        return [x[i] / self.norm(x) for i in range(len(x))]

    def project_onto_plane(self, x, n):
        d = self.dot_product(x, n) / self.norm(n)
        p = [d * self.normalize(n)[i] for i in range(len(n))]
        return [x[i] - p[i] for i in range(len(x))]
