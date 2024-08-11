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

""" Zen UV Stack System Utils """


import bmesh
import bpy
import numpy
from bpy.types import Operator
from mathutils import Vector, Color
from ZenUV.utils.transform import (
    bound_box,
    calculate_fit_scale,
    scale_island,
    move_island_to_position,
    rotate_island,
    scale2d
)
from ZenUV.utils.transform import align_vertical, align_horizontal
from ZenUV.utils.texel_density import (
    get_texel_density_from_faces,
    set_texel_density_to_faces,
    TdContext,
    UV_faces_area
)
from ZenUV.utils.generic import (
    distance_vec,
    get_mesh_data,
    resort_by_type_mesh,
    clear_tag_data,
    set_tag_data
)
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.clib.lib_init import getText, init_progress, finish_progress, StackSolver
from ZenUV.utils.blender_zen_utils import ZenPolls


PROGRESS_BAR = None
PROGRESS_MAX = 0

STACK_LAYER_NAME = "zen_stack"
M_STACK_LAYER_NAME = "zen_manual_stack"

STATISTIC = {
    "types": {
        "NATURAL": 0,
        "SYNTHETIC": 0,
        "OPENBOX": 0,
        "NGON": 0,
        "QUAD": 0,
        "RECTANGLE": 0,
        },
    "errors": []
    }


def fill_progress(sim_data):
    max_progress = 0
    # current_progress = 0
    for data in sim_data.values():
        for islands in data["objs"].values():
            max_progress += len(islands)
    return max_progress


def show_statistic():
    print("Statistic: ")
    total_islands = 0
    for tp, value in STATISTIC["types"].items():
        total_islands += value
        print("Type: {}, Count: {}".format(tp, value))
    print("\nTotal Islands: {}".format(total_islands))
    print("\nErrors: ")
    if STATISTIC["errors"]:
        for error in STATISTIC["errors"]:
            print("\n{}".format(error))
    else:
        print("Without Errors.")
    # Clear previous statistic data
    STATISTIC["types"].update({}.fromkeys(STATISTIC["types"], 0))
    STATISTIC["errors"] = []


class ZMS_OT_ShowSimIndex(Operator):
    """ Set Stack from active group to current object stack. """
    bl_description = "Show Sim Index of the selected island"
    bl_idname = "uv.zenuv_show_sim_index"
    bl_label = "Show sim index"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     return context.object.mode == 'EDIT' and context.object.zen_stack_list

    def execute(self, context):
        print("\nOperator Start_________________________")
        for obj in context.objects_in_mode:
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            # select_all(bm, action=False)
            uv_layer = bm.loops.layers.uv.verify()
            # faces = [f for f in bm.faces if f.select]
            island = island_util.get_island(context, bm, uv_layer)
            # s_layer = enshure_stack_layer(bm, stack_layer_name=M_STACK_LAYER_NAME)

            print("\n\nIn Show: Sim Index", get_island_sim_index(island[0], uv_layer))
            cluster = Cluster(context, obj, island[0])
            print("Sim Index As Cluster", cluster.sim_index)
            print("TYPE: ", cluster.type)
            # for f in faces:
            #     self.report({'INFO'}, "Face: {}. Sim Index: {} ".format(f.index, round(f[s_layer], 3)))
            bmesh.update_edit_mesh(me, loop_triangles=False)
        return {'FINISHED'}


class Cluster:

    def __init__(self, context, obj, island):
        self.context = context
        self.obj = self.object_container(obj)
        self.island_indexes = island
        self.bm = self.get_bm()
        self.uv_layer = self.bm.loops.layers.uv.verify()
        self._init_cluster()

    def _init_cluster(self):

        self.offset = get_prefs().stack_offset
        self.destroy_bm = False
        self.island = self.island_container(self.island_indexes)
        self.loops = {loop.index: loop for face in self.island for loop in face.loops}
        self.cluster = dict()
        self.adj_dict = dict()
        # self.spl_store = dict()
        self.remap_data = dict()
        self.loops_adj = dict()
        self.splitted_id = dict()
        self.verts = {vert.index: vert for face in self.island for vert in face.verts}
        self.v_uv_co = dict((loop.vert.index, loop[self.uv_layer].uv) for loop in self.loops.values())
        # self.l_uv_co = dict((loop.index, loop[self.uv_layer].uv) for loop in self.loops.values())
        self.geometry_bound_edges = {e.index: e for e in {e for f in self.island for e in f.edges} if e.is_boundary}
        self.geometry_bound_verts = {v.index: v for v in {v for f in self.island for v in f.verts} if v.is_boundary}
        self.uv_bound_edges = self.cluster_bound_edges()
        self.uv_bound_verts = {v.index: v for v in {v for f in self.island for v in f.verts} if v.is_boundary}
        self.type = self.cl_type()
        self.mode = False  # Switch mode to remap as set of faces
        self.area = round(sum([f.calc_area() for f in self.island]), 3)
        self.perimeter = self.get_perimeter()
        self.bbox = bound_box(islands=[self.island, ], uv_layer=self.uv_layer)
        self.geometry = {
            "verts_ids": [i for i in self.verts.keys()],
            "edges_ids": [e.index for f in self.island for e in f.edges],
            "faces_ids": [f.index for f in self.island]
            }
        self.sim_index = self.get_sim_index()
        self.compare = {
            "NATURAL": self.remap_natural,
            "SYNTHETIC": self.remap_synthetic,
            "OPENBOX": self.remap_openbox,
            "NGON": self.remap_ngon,
            "QUAD": self.remap_ngon,
            "RECTANGLE": self.remap_ngon,
            }
        self.store_cluster()
        # self.splitted_loops()

    # Deleting (Calling destructor)
    def __del__(self):
        if self.destroy_bm:
            self.bm.free

    def set_uv_layer(self, uv_layer_name):
        layer = self.bm.loops.layers.uv[uv_layer_name]
        if layer:
            self.uv_layer = layer
            self._init_cluster()
            return True
        else:
            return False

    def get_bm(self):
        if self.obj.mode == "EDIT":
            return bmesh.from_edit_mesh(self.obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(self.obj.data)
            self.destroy_bm = True
            return bm

    def draw_data(self):
        verts = []
        face_colors = []
        face_tri_indices = []
        return verts, face_colors, face_tri_indices

    def select(self, select=True):
        area = self.context.area.type
        uv_sync = self.context.scene.tool_settings.use_uv_select_sync
        if area == 'VIEW_3D':
            for f in self.island:
                f.select = select
        elif area == 'IMAGE_EDITOR':
            if ZenPolls.version_greater_3_2_0:
                if uv_sync:
                    for f in self.island:
                        f.select = select
                else:
                    for loop in self.loops.values():
                        loop[self.uv_layer].select = select
                        loop[self.uv_layer].select_edge = select
            else:
                if uv_sync:
                    for f in self.island:
                        f.select = select
                else:
                    for loop in self.loops.values():
                        loop[self.uv_layer].select = select

        self.update_mesh()

    def update_mesh(self):
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False)

    def island_container(self, island):
        if not isinstance(island, list):
            island = list(island)
        if not isinstance(island[0], int):
            return island
        else:
            self.bm.faces.ensure_lookup_table()
            return [self.bm.faces[index] for index in island]

    def object_container(self, obj):
        if isinstance(obj, str):
            return self.context.scene.objects[obj]
        else:
            return obj

    def _update_bbox(self):
        self.bbox = bound_box(islands=[self.island, ], uv_layer=self.uv_layer)

    def distortion_factor(self):
        """ Returns the distortion factor for a given set of polygons """
        def get_dir_vector(pos_0, pos_1):
            """ Return direction Vector from 2 Vectors """
            return Vector(pos_1 - pos_0)
        distortion = 0
        for loop in self.loops.values():
            mesh_angle = loop.calc_angle()
            vec_0 = get_dir_vector(loop[self.uv_layer].uv, loop.link_loop_next[self.uv_layer].uv)
            vec_1 = get_dir_vector(loop[self.uv_layer].uv, loop.link_loop_prev[self.uv_layer].uv)
            uv_angle = vec_0.angle(vec_1, 0.00001)
            distortion += abs(mesh_angle - uv_angle)
        if not self.in_uv_area():
            distortion += 1
        return distortion

    def match_td(self, master):
        td_inputs = TdContext(self.context)
        master_td = get_texel_density_from_faces(master.obj, master.island, td_inputs)
        td_inputs.td = master_td[0]
        td_inputs.set_mode = "island"
        set_texel_density_to_faces(self.context, self.obj, self.island, td_inputs)

    def set_td(self, td_value):
        td_inputs = TdContext(self.context)
        # master_td = get_texel_density_from_faces(master.obj, master.island, td_inputs)
        td_inputs.td = td_value
        td_inputs.set_mode = "island"
        set_texel_density_to_faces(self.context, self.obj, self.island, td_inputs)

    def get_td(self):
        "Return Texel Density"
        td_inputs = TdContext(self.context)
        return get_texel_density_from_faces(self.obj, self.island, td_inputs)

    def get_uv_area(self):
        "Return UV Area"
        return UV_faces_area(self.island, self.uv_layer)

    def fit(self, master, st_fit_mode, keep_proportion=True):
        scale = calculate_fit_scale(st_fit_mode, 0.0, self.bbox, keep_proportion, bounds=Vector((master.bbox["len_x"], master.bbox["len_y"])))
        scale_island(self.island, self.uv_layer, scale, anchor=self.bbox["cen"])
        self._update_bbox()

    def in_uv_area(self):
        def check(value):
            if 0.0 <= value <= 1.0:
                return True
            return False
        center = self.bbox["cen"]
        return check(center.x) and check(center.y)

    def orient(self, orientation="VERTICAL"):
        solver = {"VERTICAL": align_vertical, "HORIZONTAL": align_horizontal}
        angle = solver[orientation](list(self.v_uv_co.values()))
        self.rotate(angle=angle)
        self._update_bbox()

    def rotate(self, angle=1.5708, anchor=None):
        """ angle in radians """
        if not anchor:
            anchor = self.bbox["cen"]
        rotate_island(self.island, self.uv_layer, angle, anchor)
        self._update_bbox()

    def match_position(self, master):
        move_island_to_position(self.island, self.uv_layer, master.bbox["cen"], self.offset)
        self._update_bbox()

    def move_to(self, position):
        move_island_to_position(self.island, self.uv_layer, position)
        self._update_bbox()

    def scale(self, scale, anchor):
        """ Scale island by given scale from given anchor """
        for loop in self.loops.values():
            loop[self.uv_layer].uv = scale2d(loop[self.uv_layer].uv, scale, anchor)
        self._update_bbox()

    def cluster_bound_edges(self):
        edge_indexes = island_util.uv_bound_edges_indexes(self.island, self.uv_layer)
        if not edge_indexes and len(self.island) == 1:
            edge_indexes = [e.index for f in self.island for e in f.edges]
        return {e.index: e for f in self.island for e in f.edges if e.index in edge_indexes}

    def get_perimeter(self):
        return round(sum([e.calc_length() for e in self.uv_bound_edges.values()]), 3)

    def get_sim_index(self):
        geometry_factor = sum([len(data) for data in self.geometry.values()])
        # print("Sim Index In Cluster: area: {}, GF: {}, perim: {}".format(self.area, geometry_factor, self.perimeter))
        sim_index_p2 = float('0.' + str(self.area + self.perimeter).replace('.', ''))
        return geometry_factor + sim_index_p2

    def store_cluster(self):
        for vertex in self.verts.values():
            self.cluster.update(
                {
                    vertex.index: {
                        "v_loops": {loop.index for loop in vertex.link_loops if loop.index in self.loops.keys()},
                        "neighbours": self.neighbours(vertex),
                        }
                }
            )
        self.create_adj_data()

    def cl_type(self):
        if self.quad():
            if self.rectangle():
                return "RECTANGLE"
            return "QUAD"
        if self.openbox():
            return "OPENBOX"
        if self.synthetic():
            return "SYNTHETIC"
        if self.ngon():
            return "NGON"
        return "NATURAL"

    def synthetic(self):
        return len(self.verts) != len(list({loop[self.uv_layer].uv.copy().freeze() for loop in self.loops.values()}))

    def openbox(self):
        return len(self.geometry_bound_edges.keys()) == 4

    def ngon(self):
        return len(self.island) == 1 and len(list(self.island)[0].verts) > 4

    def quad(self):
        return len(self.island) == 1 and len(list(self.island)[0].verts) == 4

    def rectangle(self):
        self.bm.edges.ensure_lookup_table()
        edge_length = [self.bm.edges[e].calc_length() for e in self.cluster_bound_edges()]
        length_mid = round(sum(edge_length) / len(edge_length), 5)
        return not length_mid == round(edge_length[0], 5)

    def remap_synthetic(self, master):
        # print("Cluster is SYNTHETIC: Remapping...")
        message = "Islands different."
        stack_solver = StackSolver()
        iso, outMapping, ec = stack_solver.calcMapping(master.adj_dict, self.adj_dict)
        if iso:
            match = dict(zip([i for i in self.adj_dict.keys()], outMapping))
            message = self.transfer_uv_coords_synthetic(master, match)
        return iso, message

    def remap_openbox(self, master):
        # print("Cluster is OPENBOX: Remapping...")
        message = "Islands different."
        stack_solver = StackSolver()
        v_adj_master = master.adj_dict
        v_adj_pair = self.adj_dict
        master_injection = self.injection_outsider(master)
        pair_injection = self.injection_outsider(self)
        v_adj_master.update(master_injection)
        v_adj_pair.update(pair_injection)
        iso, outMapping, ec = stack_solver.calcMapping(master.adj_dict, self.adj_dict)
        if iso:
            for index in master_injection.keys():
                outMapping.remove(index)
            for index in pair_injection.keys():
                v_adj_pair.pop(index, None)
            match = dict(zip([i for i in self.adj_dict.keys()], outMapping))
            if self.synthetic():
                # print("Cluster also synthetic")
                self.transfer_uv_coords_synthetic(master, match)
            else:
                # print("Cluster Pure Openbox")
                self.transfer_uv_coords_natural(master, match)
        return iso, message

    def injection_outsider(self, cluster):
        return {max(cluster.verts.keys()) + 1: cluster.geometry_bound_verts.keys()}

    def injection_ngon(self, cluster):

        def particular_injection(injector, intruders, cluster_v_index):
            for i in intruders:
                cluster_v_index += 1
                injector.update({cluster_v_index: [cluster_v_index - 1]})
                injector[cluster_v_index].extend(i)
            return injector, cluster_v_index
        verts = sorted(cluster.verts.keys())
        cluster_v_index = max(verts) + 1
        injector = {cluster_v_index: verts}
        injector_co = cluster.island[0].calc_center_median()
        imphaser = set()
        for v in cluster.verts.values():
            imphaser.add(round(distance_vec(injector_co, v.co), 2))
        if len(imphaser) == 1 and not cluster.type == "RECTANGLE":
            return injector
        sorter = dict()
        for edge in cluster.uv_bound_edges.values():
            index = round(edge.calc_length(), 3)
            if index not in sorter.keys():
                sorter.update({index: []})
            sorter[index].append([v.index for v in edge.verts])
        # try to catch an error where is no sorter keys presents.
        # It is can be meant that is no uv_bound_edges
        if not sorter.keys():
            return False
        min_index = min(sorter.keys())
        max_index = max(sorter.keys())
        intruders_min = sorted(sorter[min_index])
        injector, cluster_v_index = particular_injection(injector, intruders_min, cluster_v_index)
        intruders_max = sorted(sorter[max_index])
        injector, cluster_v_index = particular_injection(injector, intruders_max, cluster_v_index)
        return injector

    def remap_ngon(self, master):
        # print("Cluster is NGON: Remapping...")
        message = "Islands different."
        stack_solver = StackSolver()
        v_adj_master = master.adj_dict
        v_adj_pair = self.adj_dict
        master_injection = self.injection_ngon(master)
        self_injection = self.injection_ngon(self)
        if not master_injection or not self_injection:
            return False, "Seems like island have no area."

        v_adj_master.update(master_injection)
        v_adj_pair.update(self_injection)
        iso, outMapping, ec = stack_solver.calcMapping(master.adj_dict, self.adj_dict)
        if iso:
            for index in master_injection.keys():
                outMapping.remove(index)
            for index in self_injection.keys():
                v_adj_pair.pop(index, None)
            match = dict(zip([i for i in self.adj_dict.keys()], outMapping))
            self.transfer_uv_coords_natural(master, match)
        # try:
        #     for v in m_new_verts:
        #         v_adj_pair.remove(v)
        #         v_mapping.remove(v)
        # except Exception:
        #     print("-------------------------- EXCEPTION --------------------------\n \
        #         MASTER: {}\nPAIR:  {}\n \
        #             ---------------------------------------------------------------".format(m_faces, [f.index for f in self.island]))

        # iso = True
        return iso, message

    # def compare_synthetic(self, v_adj_master, v_adj_pair):
    #     # from ZenUV.utils.clib.lib_init import ZenUv
    #     stack_solver = self.StackSolver()
    #     iso, outMapping, ec = stack_solver.calcMapping(v_adj_master, v_adj_pair)
    #     print("MAPPING: ", outMapping)
    #     return iso, dict(zip([i for i in self.loops_adj.keys()], outMapping))

    def remap_natural(self, master):
        # print("Cluster is NATURAL: Remapping...")
        message = "Islands different."
        stack_solver = StackSolver()
        iso, outMapping, ec = stack_solver.calcMapping(master.adj_dict, self.adj_dict)
        if iso:
            match = dict(zip([i for i in self.adj_dict.keys()], outMapping))
            self.transfer_uv_coords_natural(master, match)
            message = "Finished"
        return iso, message

    def transfer_uv_coords_natural(self, master, match):
        for loop_index in self.loops.keys():
            v_index = self.loops[loop_index].vert.index
            self.loops[loop_index][self.uv_layer].uv = master.v_uv_co[match[v_index]] + self.offset

    def transfer_uv_coords_synthetic(self, master, match):

        def get_master_face(master_face_verts):
            for m_face in master.island:
                f_verts = sorted([vert.index for vert in m_face.verts])
                if f_verts == master_face_verts:
                    return(m_face)

        for face in self.island:
            f_loops = [loop for loop in face.loops]
            for loop in f_loops:
                # l_vert = loop.vert.index
                face_verts = sorted([vert.index for vert in face.verts])
                for index in face_verts:
                    if index not in match.keys():
                        continue
                master_face_verts = sorted([match[index] for index in face_verts])
            # get master face
            m_face = get_master_face(master_face_verts)
            try:
                for loop in face.loops:
                    loop_vert = loop.vert.index
                    m_vert_idx = match[loop_vert]
                    master_loop = [m_loop for m_loop in m_face.loops if m_loop.vert.index == m_vert_idx][0]
                    loop[self.uv_layer].uv = master_loop[master.uv_layer].uv + self.offset
            except Exception:
                print("Face: ", master_face_verts)
            message = "Finished"
        return message

    def remap(self, master, transfer_params=False, match_position=False, match_mode=None, st_fit_mode="cen", move_only=False, keep_proportion=True):
        """
            inputs:
                master - Other Cluster(),
                transfer_params - bool (transfer paramethers mode)
                match_position - bool
                match_mode - enum in {"FIT", "TD"}

        """
        message = "Selected and stored islands has different geometry"
        if move_only:
            self.match_position(master)
            iso = True
            message = "Moved."
        else:
            if not StackSolver() or self.sim_index != master.sim_index or transfer_params:
                if StackSolver() and self.mode and not transfer_params:
                    iso, message = self.compare[self.type](master)
                if transfer_params:
                    if match_mode == 'TD':
                        self.match_td(master)
                    elif match_mode == 'FIT':
                        self.fit(master, st_fit_mode, keep_proportion=keep_proportion)
                    if match_position:
                        self.match_position(master)
                    iso = True
                    message = "Parameters transferred."
                else:
                    return False, message
            else:
                iso, message = self.compare[self.type](master)
        return iso, message

    def neighbours(self, vertex):
        return{e.other_vert(vertex).index for e in vertex.link_edges for loop in e.link_loops if loop.index in self.loops}

    def create_adj_data(self):
        for index, data in sorted(self.cluster.items()):
            self.adj_dict.update({index: data["neighbours"]})

    def show_cluster(self, addition=False):
        # print("Cluster: --------------------------------------")
        if addition:
            print("Cluster Faces:", [f.index for f in self.island])
            print("Adjacents: ", self.adj_dict)
            print("Type: ", self.type)
            print("Area: {}, Perimeter: {}, geometry{}, Sim Index {}".format(self.area, self.perimeter, self.geometry, self.sim_index))
            print("-----------------------------------------------")
        else:
            for v_index, data in self.cluster.items():
                print("V ID: {}, V Loops: {}, Neighs: {}".format(v_index, data["v_loops"], data["neighbours"]))


class StacksSystem:

    def __init__(self, context):
        self.context = context
        self.sync_uv = context.scene.tool_settings.use_uv_select_sync
        self.uv_area_only = context.scene.zen_display.st_uv_area_only
        # self.bm = None  # Current bmesh representation
        self.StackedColor = get_prefs().StackedColor
        self.objs = resort_by_type_mesh(context)
        self.ASD = dict()  # Already Stacked Data (ASD). Dict with already stacked clusters
        self.SimData = dict()  # Dict with similarity data

    def get_stacked(self):
        for obj in self.objs:
            self.obj_name = obj.name
            self.bm = bmesh.from_edit_mesh(obj.data).copy()
            self.bm.faces.ensure_lookup_table()
            self.fill_data_for_ASD()
            self.bm.free()
        self.expose_counts_ASD()
        self.filter_ASD()
        return self.ASD

    def detect_master_in_stack(self, stack, selected=False):
        distortion_dict = dict()
        clustered_stack = []
        master_cluster = None
        master_island_name = ""
        if selected:
            master_island_name = stack['select']
            if master_island_name:
                for obj_name, islands in stack["objs"].items():
                    if master_island_name in islands.keys():
                        master_cluster = Cluster(self.context, obj_name, islands[master_island_name])

        for obj_name, islands in stack["objs"].items():
            for island_name, indices in islands.items():
                if not island_name == master_island_name:
                    cluster = Cluster(self.context, obj_name, indices)
                    clustered_stack.append(cluster)
        if not master_cluster:
            for cl in clustered_stack:
                distortion_dict.update({cl.distortion_factor(): cl})
            master_cluster = distortion_dict[min(sorted(distortion_dict.keys()))]
            clustered_stack.remove(master_cluster)

        return master_cluster, clustered_stack

    def clustered_full_forecast_with_masters(self, m_stack=False, sim_index=None, s_layer_name=None):
        try:
            stacks = self.forecast(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name)
            progress_current = 0
            progress = {"PB": init_progress(self.context), "PM": fill_progress(stacks)}
            for stack in stacks.values():
                yield self.detect_master_in_stack(stack)
                progress["PB"].setTaskbarProgress(progress_current + 1, progress["PM"], False, text=getText("Stacking:", "of", progress_current, progress["PM"]))
                progress_current += sum([len(islands) for islands in stack["objs"].values()])
            finish_progress(progress["PB"])
        except Exception:
            finish_progress(progress["PB"])

    def clustered_stacks_with_masters(self, selected):
        try:
            stacks = self.forecast_stacks()
            progress_current = 0
            progress = {"PB": init_progress(self.context), "PM": fill_progress(stacks)}
            for stack in stacks.values():
                yield self.detect_master_in_stack(stack)
                progress["PB"].setTaskbarProgress(progress_current + 1, progress["PM"], False, text=getText("Stacking:", "of", progress_current, progress["PM"]))
                progress_current += sum([len(islands) for islands in stack["objs"].values()])
            finish_progress(progress["PB"])
        except Exception:
            finish_progress(progress["PB"])

    def clustered_selected_stacks_with_masters(self, selected, area_match=True):
        try:
            stacks = self.forecast_selected(area_match=area_match)
            progress_current = 0
            progress = {"PB": init_progress(self.context), "PM": fill_progress(stacks)}
            for stack in stacks.values():
                yield self.detect_master_in_stack(stack, selected=selected)
                progress["PB"].setTaskbarProgress(progress_current + 1, progress["PM"], False, text=getText("Unstacking:", "of", progress_current, progress["PM"]))
                progress_current += sum([len(islands) for islands in stack["objs"].values()])
            finish_progress(progress["PB"])
        except Exception:
            finish_progress(progress["PB"])

    def clustered_singletons(self):
        try:
            stacks = self.forecast_singletons()
            progress_current = 0
            progress = {"PB": init_progress(self.context), "PM": fill_progress(stacks)}
            for stack in stacks.values():
                for obj_name, islands in stack["objs"].items():
                    for island_name, indices in islands.items():
                        cluster = Cluster(self.context, obj_name, indices)
                yield cluster
                progress["PB"].setTaskbarProgress(progress_current + 1, progress["PM"], False, text=getText("Unstacking:", "of", progress_current, progress["PM"]))
                progress_current += sum([len(islands) for islands in stack["objs"].values()])
            finish_progress(progress["PB"])
        except Exception:
            finish_progress(progress["PB"])

    def show_current_data(self, _dict):
        for index, data in _dict.items():
            print(index, data)

    def get_overlapped(self):
        bpy.ops.uv.select_overlap()
        stacked = self.get_stacked()
        all_overlaps = self.filter_overlapped(self.forecast_selected_only())
        idxs_for_remove = []
        for stkd_data in stacked.values():
            sim_index = stkd_data["sim_index"]
            for index, _data in all_overlaps.items():
                if _data["sim_index"] == sim_index:
                    idxs_for_remove.append(index)
        for index in idxs_for_remove:
            all_overlaps.pop(index, None)
        return all_overlaps

    def fill_data_for_ASD(self):
        """
        found bbox data and solve which cluster stacked
        """
        uv_layer = self.bm.loops.layers.uv.verify()
        islands_ind = island_util.get_islands_in_indices(self.bm)
        iterator = 0
        axis_x = Vector((1.0, 0.0))
        axis_y = Vector((0.0, 1.0))
        for island in islands_ind:
            i_faces = [self.bm.faces[index] for index in island]
            sim_index, gd = get_island_sim_index(i_faces, uv_layer)
            points = [loop[uv_layer].uv for index in island for loop in self.bm.faces[index].loops]
            bbox = bound_box(points=points, uv_layer=uv_layer)
            position = bbox["cen"]
            pos_magnitude = round(position.magnitude, 6)
            angle_x = position.angle_signed(axis_x, 0.1)
            angle_y = position.angle_signed(axis_y, 0.1)
            bbox_data = pos_magnitude + bbox["len_x"] + bbox["len_y"]
            island_name = "island" + str(iterator)
            # print("DATA: position: {}, sum_pos: {}, angle_y: {}, angle_x: {}".format(position, position.x + position.y, angle_y, angle_x))
            if self.uv_area_only:
                if angle_y < 0 and angle_x > 0 and position.x < 1 and position.y < 1:
                    self.append_to_asd(island, bbox_data, island_name, sim_index)
            else:
                self.append_to_asd(island, bbox_data, island_name, sim_index)
            iterator += 1

    def show_data_ASD(self):
        """
        print out current data stored in ASD
        """
        print("\nAlready Stacked Islands (ASD):\n")
        if not self.ASD:
            print("Already Stacked Data is absent.")
        for index, data in self.ASD.items():
            print(index, data)

    def show_data_Sim(self, data_type="forecast"):
        """
        print out current data stored in SimData
        """
        data_types = ["forecast", "singleton", "stacks"]
        if data_type in data_types:
            print("\nOutput Data: {}".format(data_type))
            if not self.SimData:
                print("Sim Data is absent.")
            if data_type == "forecast":
                out_data = self.SimData.items()
            elif data_type == "singleton":
                out_data = {sim_index: data for sim_index, data in self.SimData.items() if data["count"] == 1}
            elif data_type == "stacks":
                out_data = {sim_index: data for sim_index, data in self.SimData.items() if data["count"] != 1}
            for index, data in out_data:
                print(index, data)
        else:
            print("Set Data Type. Must be: {}".format(data_types))

    def expose_counts_ASD(self):
        """
        implement parameter "counts" which represents count clusters in one stack in ASD dict
        """
        for index, data in self.ASD.items():
            self.ASD[index].update({"count": sum([len(islands) for obj_name, islands in self.ASD[index]["objs"].items()])})

    def expose_counts_SimData(self, stacks_dict):
        """
        implement parameter "counts" which represents count clusters in one stack in SimData dict
        """
        for sim_index, data in stacks_dict.items():
            stacks_dict[sim_index]["count"] = sum([len(islands) for obj_name, islands in data["objs"].items()])

    def filter_ASD(self):
        """
        Filter ASD for remove Unstacked clusters
        """
        self.ASD = {index: data for index, data in self.ASD.items() if data["count"] > 1}

    def filter_overlapped(self, overlapped):
        """
        Filter ASD for remove Unstacked clusters
        """
        OVER = {index: data for index, data in overlapped.items() if data["count"] > 1}
        return OVER

    @staticmethod
    def get_stacked_faces_ids(InputDict):
        """
        found and return face indexes which represents the islands
        """
        out_dict = dict()
        for index, data in InputDict.items():
            for obj_name, islands in data["objs"].items():
                if obj_name not in out_dict:
                    out_dict.update({obj_name: []})
                for island_name, island in islands.items():
                    out_dict[obj_name].extend([f for f in island])
        return out_dict

    def get_stack_faces_ids(self, InputDict):
        """
        found and return face indexes which represents the islands
        """
        out_dict = dict()
        for obj_name, islands in InputDict.items():
            if obj_name not in out_dict:
                out_dict.update({obj_name: []})
            for island_name, island in islands.items():
                out_dict[obj_name].extend([f for f in island])
        return out_dict

    def ASD_for_OSL_rebound(self):
        """
        return data for displaying in OSL
        returned type: dict {obj_name: "verts": [], "faces": [], "colors": []}
        """
        def rebound_indexes(looptris, _index):
            match = dict()
            # _index = 0
            for loop in looptris:
                match.update({loop.vert.index: _index})
                _index += 1
            return match, _index

        out_dict = dict()
        ids_dict = self.get_stacked_faces_ids(self.ASD)
        color = self.StackedColor

        for obj_name, faces_ids in ids_dict.items():
            bm, obj = self.get_bmesh(obj_name)
            lp = [loops for loops in bm.calc_loop_triangles() if loops[0].face.select]
            vertices = numpy.empty((len(bm.verts), 3), 'f')
            # tris = bgl.Buffer(bgl.GL_INT, (len(lp), 3))
            tris = numpy.empty((len(lp), 3), 'i')
            for i, ltri in enumerate(lp):
                # print(i, ltri)
                tris[i] = ltri[0].vert.index, ltri[1].vert.index, ltri[2].vert.index
                for k in ltri:
                    vertices[k.vert.index] = obj.matrix_world @ k.vert.co

            out_dict.update({obj_name: {"verts": vertices}})
            out_dict[obj_name].update({"faces": tris})
            out_dict[obj_name].update({"colors": (color,) * len(vertices)})
            bm.free()
        # print('OUT_DICT: ', out_dict)
        return out_dict

    def ASD_for_OSL(self):
        """
        return data for displaying in OSL
        returned type: dict {obj_name: "verts": [], "faces": [], "colors": []}
        """
        out_dict = dict()
        ids_dict = self.get_stacked_faces_ids(self.ASD)
        color = self.StackedColor

        for obj_name, faces_ids in ids_dict.items():
            bm, obj = self.get_bmesh(obj_name)
            clear_tag_data(bm)
            set_tag_data(bm, ids_dict[obj_name])
            verts = [(obj.matrix_world @ v.co) for v in bm.verts]
            face_tri_indices = [[loop.vert.index for loop in looptris]
                                for looptris in bm.calc_loop_triangles() if looptris[0].face.tag]
            out_dict.update({obj_name: {"verts": verts}})
            out_dict[obj_name].update({"faces": face_tri_indices})
            out_dict[obj_name].update({"colors": (color,) * len(verts)})
            bm.free()
        return out_dict

    def get_bmesh(self, obj_name):
        obj = self.context.scene.objects[obj_name]
        bm = bmesh.from_edit_mesh(obj.data).copy()
        bm.faces.ensure_lookup_table()
        return bm, obj

    def append_to_asd(self, island, bbox_data, island_name, sim_index):
        """
        fill ASD
        """
        if bbox_data not in self.ASD:
            self.ASD.update({bbox_data: {"objs": {self.obj_name: {island_name: island}}, "sim_index": sim_index}})
        else:
            if self.obj_name not in self.ASD[bbox_data]["objs"]:
                self.ASD[bbox_data]["objs"].update({self.obj_name: {island_name: island}})
            self.ASD[bbox_data]["objs"][self.obj_name][island_name] = island

    def forecast(self, m_stack=False, sim_index=None, s_layer_name=None):
        """ Return full forecast """
        self._create_similarity_data(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name)
        return self.SimData

    def forecast_selected(self, m_stack=False, sim_index=None, s_layer_name=None, area_match=True):
        """ Return forecast for selected islands """
        self._create_similarity_data(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name, area_match=area_match)
        return {sim_index: data for sim_index, data in self.SimData.items() if data["select"]}

    def forecast_selected_only(self, m_stack=False, sim_index=None, s_layer_name=None):
        """ Return forecast for selected islands """
        self._create_similarity_data(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name, only_selected_islands=True)
        return {sim_index: data for sim_index, data in self.SimData.items() if data["select"]}

    def forecast_singletons(self, m_stack=False, sim_index=None, s_layer_name=None):
        """ Return unique islands which has no pairs """
        self._create_similarity_data(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name)
        return {sim_index: data for sim_index, data in self.SimData.items() if data["count"] == 1}

    def forecast_stacks(self, m_stack=False, sim_index=None, s_layer_name=None):
        """ Return forecast with only stacks without singletons """
        self._create_similarity_data(m_stack=m_stack, sim_index=sim_index, s_layer_name=s_layer_name)
        return {sim_index: data for sim_index, data in self.SimData.items() if data["count"] != 1}

    def _create_similarity_data(self, m_stack=False, sim_index=None, s_layer_name=None, only_selected_islands=False, area_match=True):
        """ Create similarity dict """
        self.SimData.clear()
        for obj in self.objs:
            bm, obj = self.get_bmesh(obj.name)
            uv_layer = bm.loops.layers.uv.verify()

            if m_stack:  # gathering Manual Stack Data
                if obj.zen_stack_list.items():
                    sim_index = obj.zen_stack_list[obj.zms_list_index].sim_index
                    faces = get_islands_from_stack(bm, s_layer_name, sim_index)
                    islands = island_util.get_islands_by_face_list(self.context, bm, faces, uv_layer)
                else:
                    islands = []
            else:
                islands = island_util.get_islands(self.context, bm)
            index = 0
            for island in islands:
                if m_stack and len(obj.zen_stack_list) > 0:
                    geometry_data = get_geometry(island)
                    sim_index = obj.zen_stack_list[obj.zms_list_index].sim_index
                else:
                    sim_index, geometry_data = get_island_sim_index(island, uv_layer)
                    if len(island) == 1 and len(list(island)[0].verts) == 4:
                        _island = list(island)[0]
                        improver = (
                            distance_vec(_island.loops[0].vert.co, _island.loops[2].vert.co) +
                            distance_vec(_island.loops[1].vert.co, _island.loops[3].vert.co)
                        )
                        sim_index += round(improver, 3)
                if not area_match:
                    sim_index = int(sim_index)
                if sim_index not in self.SimData:
                    self.SimData.update({sim_index: {"objs": {obj.name: {}}, 'select': False, 'count': 0, "sim_index": sim_index}})
                if obj.name not in self.SimData[sim_index]["objs"]:
                    self.SimData[sim_index]["objs"].update({obj.name: {}})
                island_name = self._get_island_name(sim_index, uv_layer, island, index)
                if only_selected_islands and not island_name[0] == "s":
                    index += 1
                    continue
                self.SimData[sim_index]["objs"][obj.name].update({island_name: geometry_data["faces_ids"]})
                index += 1
            bm.free()

        self.expose_counts_SimData(self.SimData)

    def _get_island_name(self, sim_index, uv_layer, island, index):
        island_name = "island" + str(index)
        if self.context.area.type == 'VIEW_3D':
            if True in [f.select for f in island]:
                island_name = "s_" + island_name
                self.SimData[sim_index]["select"] = island_name
        elif self.context.area.type == 'IMAGE_EDITOR':
            if self.sync_uv:
                # In the UV Editor Works correct only in FACE selection mode. This is due to the peculiarity Selections of the blender.
                if True in [f.select for f in island]:  # or True in [e.select for f in island for e in f.edges]:
                    island_name = "s_" + island_name
                    self.SimData[sim_index]["select"] = island_name
            else:
                if True in [loop[uv_layer].select for face in island for loop in face.loops if face.select]:
                    island_name = "s_" + island_name
                    self.SimData[sim_index]["select"] = island_name
        return island_name

        # return stacks

    def color_by_sim_index(self, sim_index):
        # solver returns order alpha, color.value, color.saturation
        solver = {0: (0.95, 0.0, 0.7)}
        s_index = 0.001 + sim_index * 1000
        color = [int(d)/10 for d in str(s_index) if d != '.']
        color = Color((color[0], color[1], color[2]))
        alpha, color.v, color.s = solver.get(sum(color), (0.5, 0.7, 0.7))
        return (color[0], color[1], color[2], alpha)

    def SimData_for_OSL(self):
        out_dict = dict()
        # ids_dict = self.get_stacked_faces_ids(self.SimData)
        face_tri_indices = []

        for sim_index, data in self.SimData.items():

            for obj_name, islands in data["objs"].items():
                face_colors = []
                # if data["count"] == 1:
                #     sim_index = 0.0
                # print(obj_name, islands)
                bm, obj = self.get_bmesh(obj_name)
                clear_tag_data(bm)
                ids_dict = self.get_stack_faces_ids(data["objs"])
                set_tag_data(bm, ids_dict[obj_name])
                t_faces = [bm.faces[idx] for idxs in ids_dict.values() for idx in idxs]
                face_verts = {v.index for f in t_faces for v in f.verts}
                verts = [(obj.matrix_world @ v.co) for v in bm.verts]
                face_tri_indices.extend([[loop.vert.index for loop in looptris]
                                        for looptris in bm.calc_loop_triangles() if looptris[0].face.tag])
                face_colors.extend([self.color_by_sim_index(sim_index) for v_idx in range(len(face_verts))])

                bm.free()

                out_dict.update({obj_name: {"verts": verts}})
                out_dict[obj_name].update({"faces": face_tri_indices})
                out_dict[obj_name].update({"colors": face_colors})
        return out_dict


def get_area(island):
    area = round(sum([f.calc_area() for f in island]), 3)
    return area


def get_perimeter(island, uv_layer):
    edge_indexes = island_util.uv_bound_edges_indexes(island, uv_layer)
    # print("ISLAND EDGES INDEXES: ", len(edge_indexes))
    edges = {e for f in island for e in f.edges if e.index in edge_indexes}
    # print("PERIMETER EDGES: ", [e.index for e in edges], len(edges))
    return round(sum([e.calc_length() for e in edges]), 3)


def get_geometry(island):
    faces = [f.index for f in island]
    edges = [e.index for f in island for e in f.edges]
    verts = list({v.index for f in island for v in f.verts})
    return {"verts_ids": verts, "edges_ids": edges, "faces_ids": faces}


def get_island_sim_index(island, uv_layer):
    """ Return similarity index of the given island and geometry data dict """
    area_factor = get_area(island)
    perimeter = get_perimeter(island, uv_layer)
    geometry_data = get_geometry(island)
    geometry_factor = len(geometry_data["verts_ids"]) + len(geometry_data["edges_ids"]) + len(geometry_data["faces_ids"])
    sim_index_p2 = float('0.' + str(area_factor + perimeter).replace('.', ''))
    return geometry_factor + sim_index_p2, geometry_data


def get_master_parameters(context, obj_name, indices):
    master_loop_indices = dict()
    master_face_indices = dict()
    obj = context.scene.objects[obj_name]
    me, bm_master = get_mesh_data(obj)
    uv_layer = bm_master.loops.layers.uv.verify()
    bm_island = [bm_master.faces[index] for index in indices]
    master_loop_indices[obj_name] = [loop.index for f in bm_island for loop in f.loops]
    master_face_indices[obj_name] = indices
    points = [loop[uv_layer].uv for index in indices for loop in bm_master.faces[index].loops]
    position = bound_box(points=points, uv_layer=uv_layer)["cen"]
    td_inputs = TdContext(context)
    master_td = get_texel_density_from_faces(obj, bm_island, td_inputs)
    return master_loop_indices, position, master_td, master_face_indices


def get_master_island_position(bm_master, indices):
    # master = dict()
    # obj = context.scene.objects[obj_name]
    # me, bm_master = get_mesh_data(obj)
    uv_layer = bm_master.loops.layers.uv.verify()
    # bm_island = [bm_master.faces[index] for index in indices]
    # master[obj_name] = [loop.index for f in bm_island for loop in f.loops]
    bm_master.faces.ensure_lookup_table()
    points = [loop[uv_layer].uv for index in indices for loop in bm_master.faces[index].loops]
    position = bound_box(points=points, uv_layer=uv_layer)["cen"]
    return position


def enshure_stack_layer(bm, stack_layer_name):
    """ Return layer float type or create new """
    layer = bm.faces.layers.float.get(stack_layer_name)
    if not layer:
        layer = bm.faces.layers.float.new(stack_layer_name)
    return layer or bm.faces.layers.float.new(stack_layer_name)


def set_island_sim_index(bm, island, layer_name, sim_index):
    _layer = enshure_stack_layer(bm, stack_layer_name=layer_name)
    for face in island:
        face[_layer] = sim_index


def get_islands_from_stack(bm, layer_name, sim_index):
    _layer = enshure_stack_layer(bm, stack_layer_name=layer_name)
    faces = [f for f in bm.faces if round(f[_layer], 3) == round(sim_index, 3)]
    return faces


def singleton(stack):
    island_count = 0
    for obj_name, islands in stack["objs"].items():
        for island in islands:
            island_count += 1
    if island_count > 1:
        return False
    return True


def write_sim_data_to_layer(context, sim_data):
    for sim_index, stack in sim_data.items():
        if singleton(stack):
            sim_index = 0.0
        for obj_name, islands in stack["objs"].items():
            obj = context.scene.objects[obj_name]
            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            _layer = enshure_stack_layer(bm, stack_layer_name=STACK_LAYER_NAME)
            for island_name, island in islands.items():
                for f_idx in island:
                    bm.faces[f_idx][_layer] = sim_index
            bmesh.update_edit_mesh(me, loop_triangles=False)
