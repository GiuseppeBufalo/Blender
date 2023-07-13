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

# from ZenUV.utils.base_clusters.zen_cluster import UvVertex
from ZenUV.utils.base_clusters.base_elements import UvVertex
from ZenUV.utils.generic import Distortion, Scope


class CheckerZcluster:

    def chk_broken_borders_v_01(self):

        safe_loops = range(10)
        for c in safe_loops:
            b_verts = self.get_bound_verts()
            scope = Scope()
            for vert in b_verts:
                scope.append(vert.uv_co, vert)

            ids_scope = []
            for i, ve in scope.data.items():
                if len(ve) > 2:
                    ids_scope.append(list({v.index for v in ve}))

            if ids_scope:
                for ids in ids_scope:
                    if len(ids) == 1:
                        id = ids[0]
                        # print("here", self.uv_verts[id])
                        vert = self.uv_verts[id]
                        for i in range(len(vert.link_loops) - 1):
                            new_vert = UvVertex(
                                len(self.uv_verts) + 1,
                                vert.mesh_vert,
                                [vert.link_loops.pop(), ],
                                vert.uv_layer
                                )
                            new_vert.move_by(Distortion.get_vector_2d(0.0001))
                            self.uv_verts.append(new_vert)
            else:
                print("Regular Exit.", "++ " * 10)
                print("Total Cycles: ", c)
                return True
            self.coo_deps = {}
            self._collect_uv_verts()
            self._collect_uv_edges()
        print("Emergency Exit.", "-- " * 50)
        return False

    def douplicate_uv_vertex(self, in_vertex):
        new_vert = UvVertex(
            len(self.uv_verts) + 1,
            in_vertex.mesh_vert,
            [in_vertex.link_loops.pop(), ],
            in_vertex.uv_layer
            )
        self.uv_verts.append(new_vert)
        return new_vert

    def chk_broken_borders(self):

        safe_loops = range(10)
        for c in safe_loops:
            b_verts = self.get_bound_verts()
            scope = Scope()
            for vert in b_verts:
                scope.append(vert.uv_co, vert)

            ids_scope = []
            for i, ve in scope.data.items():
                if len(ve) > 2:
                    ids_scope.append(list({v.index for v in ve})[0])
        return ids_scope

    def fix_broken_borders(self):
        bborders = self.chk_broken_borders()
        if not bborders:
            return None
        sorter = {}
        verts = [self.uv_verts[i] for i in bborders]

        for v in verts:
            sorter.update({v: []})
            faces = [f for f in v.link_uv_faces]
            full_set = []
            while faces:
                start_f = faces.pop()
                sub_set = [start_f, ]
                es1 = set(e.index for e in start_f.mesh_face.edges)
                i = len(faces)
                while i:
                    i -= 1
                    es2 = set(e.index for e in faces[i].mesh_face.edges)
                    if es1.intersection(es2):
                        sub_set.append(faces[i])
                        del faces[i]
                sorter[v].append(sub_set)
        counter = 0
        for vert, full_set in sorter.items():
            for i in range(1, len(full_set)):
                n_vert = self.douplicate_uv_vertex(vert)
                n_vert.link_uv_faces = full_set[i]
                n_vert_loops = set([loop for uv_face in n_vert.link_uv_faces for loop in uv_face.mesh_face.loops])
                vert_loops = set(vert.link_loops)
                intersection = vert_loops.intersection(n_vert_loops)
                n_vert.link_loops = list(intersection)
                n_vert.move_by(Distortion.get_vector_2d(0.0001))
                counter += 1

        # print(f"Created {counter} new uv veritces.")

        return True

    def check_multiple_loops(self):
        # manifold_edges = []
        # for edge in {e for f in self.island for e in f.edges}:
        #     if len(edge.link_loops) > 2:
        #         manifold_edges.append[edge.index]
        return [edge.index for edge in {e for f in self.island for e in f.edges} if len(edge.link_loops) > 2]
