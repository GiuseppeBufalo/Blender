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

""" Zen UV Generic Functions"""
import bpy
import bmesh
import time
import math
import numpy as np
from mathutils import Vector
from ZenUV.utils import get_uv_islands as island_util
# from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.blender_zen_utils import ZenPolls

ADDON_NAME = "ZenUV"

PROCESS_FACEMAP_NAME = "ZenUV_InProcess"
PINNED_FACEMAP_NAME = "ZenUV_Pinned"

HOPS_SHOW_UV_FACEMAP_NAME = "HOPS_Show_UV"

ZUV_PANEL_CATEGORY = "Zen UV"
ZUV_REGION_TYPE = "UI"
ZUV_CONTEXT = "mesh_edit"
ZUV_SPACE_TYPE = "VIEW_3D"


class UnitsConverter:

    """ Current system is centimeters based. """

    convertor = {
            'km': 100000,
            'm': 100,
            'cm': 1,
            'mm': 0.1,
            'um': 0.0001,
            'mil': 160934,
            'ft': 30.48,
            'in': 2.54,
            'th': 0.00254
        }

    base_mult = 1
    base_unit = 'cm'

    @classmethod
    def get_mult_for(self, units):
        if self._units_valid(units):
            return self.convertor[units] * self.base_mult
        else:
            return None

    @classmethod
    def convert_raw_world_distance(self, distance=None, units='m'):
        if distance and self._units_valid(units):
            return distance * 100 / self.get_mult_for(units)

    @classmethod
    def _units_valid(self, units):
        return units in self.convertor.keys()

    def set_base_units(self, unit):
        if not self._units_valid(unit):
            print("Units Converter --> The requested units is not valid.")
            return None
        self.base_mult = 1 / self.convertor[unit]
        self.base_unit = unit
        return self.base_mult

    def get_base_units(self):
        base_unit = [key for key in self.convertor.keys() if self.convertor[key] * self.base_mult == 1]
        if base_unit:
            return base_unit[0]
        return None


class Scope():
    """ Creates dict data wit automatic structure """
    def __init__(self) -> None:
        self.data = {}

    def append(self, key, value):
        """ Creates dict {key: [value, ]}"""
        if key not in self.data.keys():
            self.data.update({key: [value]})
        else:
            self.data[key].append(value)

    def get_singles_keys(self):
        """ Return keys where len(values) == 1 """
        for key, value in self.data.items():
            if len(value) == 1:
                yield key

    def get_mults_keys(self):
        """ Return keys where len(values) > 1 """
        for key, value in self.data.items():
            if len(value) > 1:
                yield key

    def get_mults_values(self):
        """ Return value from [values, ] where len([values, ]) > 1 """
        for key, value in self.data.items():
            if len(value) > 1:
                for v in value:
                    yield v


class Distortion:

    def get_vector_2d(size=1):
        return Vector((np.random.rand(1, 2) * size).tolist()[0])

    def get_vector_3d(size=1):
        return Vector((np.random.rand(1, 3) * size).tolist()[0])


class MeshBuilder:

    def __init__(self, bm) -> None:
        self.bm = bm

    def create_vertices_3d(self, coors):
        verts = []
        for co in coors:
            verts.append(self.bm.verts.new(co))
        # self.update_mesh()
        return verts

    def create_edge(self, coords):
        if len(coords) == 2:
            verts = self.create_vertices_3d(coords)
            # edges = []
            return self.bm.edges.new(verts)
        else:
            print("Builder: Needed exactly 2 coordinates.")


class ZenKeyEventSolver:

    def __init__(self, context, event, a_prefs) -> None:
        self.current_modifier = a_prefs.zen_key_modifier
        self.event = event
        # print(f"Current Key Modifier: {self.current_modifier}")
        # self._solve()

    # @classmethod
    def solve(self):
        if self.event.type == "LEFTMOUSE":
            if self.event.alt and self.current_modifier == "ALT":
                return True
            elif self.event.ctrl and self.current_modifier == "CTRL":
                return True
            elif self.event.shift and self.current_modifier == "SHIFT":
                return True

            else:
                return False

    def __del__(self):
        del self.current_modifier
        del self.event


class Timer:
    ''' Small class to measure run time of critical parts'''
    def __enter__(self):
        self.start = time.process_time()
        return self

    def __exit__(self, *args):
        self.end = time.process_time()
        self.interval = self.end - self.start

    def delta(self):
        return "{0:.6f} sec".format(self.interval)


def store_loops(bm):
    return [loop for f in bm.faces for loop in f.loops]


def update_loops_indexes(bm):
    loops = [loop for f in bm.faces for loop in f.loops]
    for index, ele in enumerate(loops):
        ele.index = index


def remap_ranges(value, base_range, new_range):
    # print("INPUTS", value, base_range, new_range)
    reverse = False
    if new_range[0] > new_range[1]:
        reverse = True
    b_min = min(base_range)
    b_max = max(base_range)
    n_min = min(new_range)
    n_max = max(new_range)
    b_range = (b_max - b_min)
    n_range = (n_max - n_min)
    # print("                         Ranges inside", base_range, new_range)
    if b_range == 0:
        result = n_min
    else:
        result = (((value - b_min) * n_range) / b_range) + n_min
    # print("                         Result:", result)
    if reverse:
        result = new_range[1] + (new_range[0] - result)
    return result


def lerp_two_colors(c1, c2, steps=10):
    return (c1[0]+(c2[0]-c1[0])*steps, c1[1]+(c2[1]-c1[1])*steps, c1[2]+(c2[2]-c1[2])*steps)


def hex_to_RGB(hex):
    ''' "#FFFFFF" -> [255,255,255] '''
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i+2], 16) for i in range(1, 6, 2)]


def RGB_to_hex(RGB):
    ''' [255,255,255] -> "#FFFFFF" '''
    # Components need to be integers for hex to make sense
    if isinstance(RGB[0], float):
        RGB = [round(x * 255) for x in RGB]
    RGB = [int(x) for x in RGB]
    return "#"+"".join(["0{0:x}".format(v) if v < 16 else
                        "{0:x}".format(v) for v in RGB])


def to_hex(c):
    if c < 0.0031308:
        srgb = 0.0 if c < 0.0 else c * 12.92
    else:
        srgb = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055

    return hex(max(min(int(srgb * 255 + 0.5), 255), 0))


def toHex(color):
    rgb = color[:]
    result = ""
    i = 0
    while i < 3:
        val = str(to_hex(rgb[i]))
        val = val[2:]
        if len(val) == 1:
            val += val
        result += val
        i += 1
    return result


def edge_loops_from_uvs(loops, uv_layer):
    """
    Edge loops defined by loops

    Takes [mesh loops] and returns the loop loops
    as lists of loops.
    [ [loop, loop, loop, loop], ...]

    closed loops have matching start and end values.
    """
    def loops_from_co(co, loops):
        stripes = []
        for stripe in co:
            sorted_loops = []
            for uv_vert_co in stripe:
                uv_verts = [loop for loop in loops if loop[uv_layer].uv == uv_vert_co]
                sorted_loops.append(uv_verts)
            stripes.append(sorted_loops)
        return stripes

    def collect_uv_edges(uv_layer, loops):
        uv_edges = set()
        for loop in loops:
            next_loop = loop.link_loop_next
            if next_loop in loops:
                l1 = loop[uv_layer].uv.copy().freeze()
                l2 = next_loop[uv_layer].uv.copy().freeze()
                if (l2, l1) not in uv_edges:
                    uv_edges.add((l1, l2))
        return uv_edges

    line_polys = []
    unsorted_edges = list(collect_uv_edges(uv_layer, loops))

    while unsorted_edges:
        current_edge = unsorted_edges.pop()
        vert_end, vert_start = current_edge[:]
        line_poly = [vert_start, vert_end]

        ok = True
        while ok:
            ok = False
            i = len(unsorted_edges)
            while i:
                i -= 1
                edge = unsorted_edges[i]
                v1, v2 = edge[:]
                if v1 == vert_end:
                    line_poly.append(v2)
                    vert_end = line_poly[-1]
                    ok = 1
                    del unsorted_edges[i]
                elif v2 == vert_end:
                    line_poly.append(v1)
                    vert_end = line_poly[-1]
                    ok = 1
                    del unsorted_edges[i]
                elif v1 == vert_start:
                    line_poly.insert(0, v2)
                    vert_start = line_poly[0]
                    ok = 1
                    del unsorted_edges[i]
                elif v2 == vert_start:
                    line_poly.insert(0, v1)
                    vert_start = line_poly[0]
                    ok = 1
                    del unsorted_edges[i]

        line_polys.append(line_poly)
    return loops_from_co(line_polys, loops)


def edge_loops_from_bmedges(bmesh, bm_edges):
    """
    Edge loops defined by edges

    Takes [mesh edge indices] and returns the edge loops
    as lists of vertex indices.
    [ [1, 6, 7, 2], ...]

    closed loops have matching start and end values.
    """
    line_polys = []
    unsorted_edges = bm_edges.copy()  # so as not to mutate the input list

    while unsorted_edges:
        current_edge = bmesh.edges[unsorted_edges.pop()]
        vert_e, vert_st = current_edge.verts[:]
        vert_end, vert_start = vert_e.index, vert_st.index
        line_poly = [vert_start, vert_end]

        ok = True  # just to get started
        while ok:
            ok = False
            i = len(unsorted_edges)
            while i:
                i -= 1
                edge = bmesh.edges[unsorted_edges[i]]
                vertex_1, vertex_2 = edge.verts
                v1, v2 = vertex_1.index, vertex_2.index
                if v1 == vert_end:
                    line_poly.append(v2)
                    vert_end = line_poly[-1]
                    ok = 1
                    del unsorted_edges[i]
                    # break
                elif v2 == vert_end:
                    line_poly.append(v1)
                    vert_end = line_poly[-1]
                    ok = 1
                    del unsorted_edges[i]
                    # break
                elif v1 == vert_start:
                    line_poly.insert(0, v2)
                    vert_start = line_poly[0]
                    ok = 1
                    del unsorted_edges[i]
                    # break
                elif v2 == vert_start:
                    line_poly.insert(0, v1)
                    vert_start = line_poly[0]
                    ok = 1
                    del unsorted_edges[i]
                    # break
        line_polys.append(line_poly)
    # print(f"Line Polys: {line_polys}")
    return line_polys


def clear_tag_data(bm):
    """
    clear tag data for all faces in bmesh representation
    """
    for f in bm.faces:
        f.tag = False


def set_tag_data(bm, face_ids):
    """
    tag given faces face.tag
    """
    faces = [bm.faces[_id].index for _id in face_ids if not bm.faces[_id].hide]
    for f_id in faces:
        bm.faces[f_id].tag = True


def get_dir_vector(pos_0, pos_1):
    """ Return direction Vector from 2 Vectors """
    return Vector(pos_1 - pos_0)


def distance_vec(point1: Vector, point2: Vector) -> float:
    """Calculate distance between two points."""
    return (point2 - point1).length


def create_new_mesh(bm, name):
    """ Create New Mesh object in scene based on bm data"""
    mesh_data = bpy.data.meshes.new(name)
    bm.to_mesh(mesh_data)
    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)


def update_indexes(objs):
    for obj in objs:
        # obj.update_from_editmode()
        me, bm = get_mesh_data(obj)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bmesh.update_edit_mesh(me, loop_triangles=False)


def resort_by_type_mesh(context):
    return [obj for obj in context.selected_objects if obj.type == 'MESH' and len(obj.data.polygons) != 0]


def resort_by_type_mesh_in_edit_mode(context):
    return [obj for obj in context.objects_in_mode if obj.type == 'MESH' and len(obj.data.polygons) != 0]


def filter_instances(objs):
    ''' Removes instance meshes from input list (objs) '''
    unique_data = {p_obj.data: p_obj for p_obj in objs if p_obj.type == 'MESH'}
    return unique_data.values()


def resort_by_type_mesh_in_edit_mode_and_sel(context):
    """ Return objects in edit mode and selected
        without instances """
    selected = ({obj for obj in context.selected_objects if obj.type == 'MESH' and len(obj.data.polygons) != 0})
    in_mode = ({obj for obj in context.objects_in_mode_unique_data if obj.type == 'MESH' and len(obj.data.polygons) != 0})
    common = filter_instances(selected.union(in_mode))
    return common


def face_indexes_by_sel_mode(context, bm):
    """ Return face indexes converted from selected elements """
    uv_layer = bm.loops.layers.uv.verify()
    selection = []
    sync_uv = context.scene.tool_settings.use_uv_select_sync
    if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
        sel_faces = set()
        # sel_faces.update([f.index for f in bm.faces for loop in f.loops if loop[uv_layer].select])
        # sel_faces.update({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select})
        if ZenPolls.version_greater_3_2_0:
            sel_faces.update({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select and loop[uv_layer].select_edge})
        else:
            sel_faces.update({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select})
        if sel_faces:
            selection.extend(list(sel_faces))
    else:
        mode = context.tool_settings.mesh_select_mode
        if mode[1]:
            selection = [face.index for edge in [e for e in bm.edges if e.select] for face in edge.link_faces if not face.hide]
        elif mode[2]:
            selection = [face.index for face in bm.faces if face.select and not face.hide]
        elif mode[0]:
            selection = [face.index for vert in [v for v in bm.verts if v.select] for face in vert.link_faces if not face.hide]
    return selection


def loops_by_sel_mode(
    context: bpy.types.Context,
    bm: bmesh.types.BMesh,
    only_uv_edges=False,
    groupped: bool = False
) -> list:
    """ Return loops converted from selected elements """
    uv_layer = bm.loops.layers.uv.verify()
    selection = []
    sync_uv = context.scene.tool_settings.use_uv_select_sync
    if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
        if not only_uv_edges:
            selection = list({loop for face in bm.faces for loop in face.loops if face.select and loop[uv_layer].select})
        else:
            selection = list({loop for face in bm.faces for loop in face.loops if loop[uv_layer].select_edge})
    else:
        mode = context.tool_settings.mesh_select_mode
        if mode[1] or mode[0]:
            selection = [loop for vertex in [v for v in bm.verts if v.select] for loop in vertex.link_loops]
            # selection = [loop for edge in [e for e in bm.edges if e.select] for loop in edge.link_loops]
        elif mode[2]:
            selection = [loop for face in [face for face in bm.faces if face.select and not face.hide] for loop in face.loops]
        # elif mode[0]:
        #     selection = [loop for vertex in [v for v in bm.verts if v.select] for loop in vertex.link_loops]
    if groupped:
        return compound_groups_from_loops(selection, uv_layer)
    # print(f"Selection Count --> {len(selection)}\nSelection  --> {selection}\n")
    return selection


def compound_groups_from_loops(
    loops: list,
    uv_layer: bmesh.types.BMLayerItem,
    _sorted: bool = True
) -> list:

    def sort_by_index(f):
        return f.index

    def update_storages(upd):
        cluster.update(upd)
        stack.update(upd)

    _groups = []
    loops = set(loops)

    while len(loops) != 0:
        init_loop = loops.pop()
        cluster = {init_loop}
        stack = {init_loop}
        while len(stack) != 0:
            loop = stack.pop()

            linked = [lp for lp in loop.vert.link_loops if lp in loops and lp not in cluster and lp[uv_layer].uv == loop[uv_layer].uv]
            update_storages(linked)
            linked.append(loop)

            adj = [lp.link_loop_next for lp in linked if lp.link_loop_next in loops and lp.link_loop_next not in cluster]
            adj.extend([lp.link_loop_prev for lp in linked if lp.link_loop_prev in loops and lp.link_loop_prev not in cluster])
            update_storages(adj)

        for lp in cluster:
            loops.discard(lp)
        _groups.append(list(cluster))

    if _sorted:
        return [sorted(cluster, key=sort_by_index) for cluster in _groups]

    return _groups


def select_by_context(context, bm, islands, state=True):
    blender_sync_mode = context.scene.tool_settings.use_uv_select_sync
    uv_layer = bm.loops.layers.uv.verify()
    if context.area.type == "VIEW_3D":
        select_faces(islands, state=state)
    if context.area.type == "IMAGE_EDITOR":
        if blender_sync_mode:
            select_faces(islands, state=state)
        elif not blender_sync_mode:
            select_loops(islands, uv_layer, state=state)


def select_faces(islands, state=True):
    """ Select faces from tuple islands """
    faces = [face for island in islands for face in island]
    for face in faces:
        face.select = state


def select_loops(islands, uv_layer, state=True):
    """ Select loops from tuple islands """
    loops = [loop for island in islands for face in island for loop in face.loops]
    for loop in loops:
        loop[uv_layer].select = state
    if ZenPolls.version_greater_3_2_0:
        for loop in loops:
            loop[uv_layer].select_edge = state


def get_padding_in_pct(context, value_px):
    addon_prefs = context.preferences.addons[ADDON_NAME].preferences
    side_min = min(addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeY)
    return value_px / side_min


def get_padding_in_px(context, value_pct):
    addon_prefs = context.preferences.addons[ADDON_NAME].preferences
    side_min = min(addon_prefs.TD_TextureSizeX, addon_prefs.TD_TextureSizeY)
    return value_pct * side_min


def get_mesh_data_unified(context, obj):
    """
        Input obj or obj.name
        Return me as obj.data and bm as bmesh.from_edit_mesh(me)
    """
    if isinstance(obj, str):
        obj = context.scene.objects.get(obj)
    if not obj:
        return None
    else:
        return obj.data, bmesh.from_edit_mesh(obj.data)


def get_mesh_data(obj):
    "Return me as obj.data and bm as bmesh.from_edit_mesh(me)"
    # obj = context.edit_object
    # me = obj.data
    return obj.data, bmesh.from_edit_mesh(obj.data)


def resort_objects(context, objs):
    objects = []
    sync_uv = context.scene.tool_settings.use_uv_select_sync

    if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            if True in [loop[uv_layer].select for f in bm.faces for loop in f.loops if not f.hide]:
                objects.append(obj)
    else:
        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            if True in [e.select for e in bm.faces] or \
                True in [e.select for e in bm.edges] or \
                    True in [e.select for e in bm.verts]:
                objects.append(obj)
    return objects


def resort_objects_by_data(objs):
    objects = []
    for obj in objs:
        if len(obj.data.polygons) != 0:
            if True in [x.select for x in obj.data.polygons] or \
                True in [x.select for x in obj.data.edges] or \
                    True in [x.select for x in obj.data.vertices]:
                objects.append(obj)
    return objects


def pin_island(island, uv_layer, _pin_action):
    for face in island:
        for loop in face.loops:
            loop[uv_layer].pin_uv = _pin_action


def vert_border_from_island(uv_layer, island):
    """ Return border edges of given island """
    _vertices = []
    _bound_verts = []
    for face in island:
        _vertices.extend([v for v in face.verts])
    for vertex in _vertices:
        uv_coords = []
        for loop in vertex.link_loops:
            if loop[uv_layer].uv not in uv_coords:
                uv_coords.append(loop[uv_layer].uv)
        if len(uv_coords) > 1:
            _bound_verts.append(vertex)
    return _bound_verts


def move_2d_cursor(context, position=Vector((0.0, 0.0))):
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.spaces.active.cursor_location = position


def edges_between_verts(_verts):
    """ Return edges connectet between given vertices """
    edges = []
    between_edges = []
    # collect all the edges
    for vertex in _verts:
        edges.extend([e for e in vertex.link_edges])

    for edge in edges:
        if edge.verts[0] in _verts and edge.verts[1] in _verts:
            between_edges.append(edge)
    return between_edges


def Diff(li1, li2):
    """ Find difference of two lists """
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
    return li_dif


def check_selection_mode(context):
    """ Detect current Blender Selection mode """
    work_mode = 'VERTEX'
    if context.tool_settings.mesh_select_mode[:] == (False, True, False):
        work_mode = 'EDGE'
    elif context.tool_settings.mesh_select_mode[:] == (False, False, True):
        work_mode = 'FACE'
    return work_mode


def restore_selection(mode, faces, edges, verts=None, indexes=False, bm=None):
    """ Restore selected elements depending of Blender selection Mode """
    if mode == 'VERTEX' and verts:
        if indexes and bm:
            bm.verts.ensure_lookup_table()
            for index in verts:
                bm.verts[index].select = True
        else:
            for vert in verts:
                vert.select = True
    if mode == 'FACE':
        if indexes and bm:
            bm.faces.ensure_lookup_table()
            for index in faces:
                bm.faces[index].select = True
        else:
            for face in faces:
                face.select = True
    if mode == 'EDGE':
        if indexes and bm:
            bm.edges.ensure_lookup_table()
            for index in edges:
                bm.edges[index].select = True
        else:
            for edge in edges:
                edge.select = True


def collect_selected_objects_data(context):
    """ Collect Mesh data from every selected object. (bm) """
    bms = {}
    for obj in context.objects_in_mode_unique_data:
        bm_data = bmesh.from_edit_mesh(obj.data)
        bms[obj] = {
            'data': bm_data,
            'pre_selected_verts': [v for v in bm_data.verts if v.select],
            'pre_selected_faces': [f for f in bm_data.faces if f.select],
            'pre_selected_edges': [e for e in bm_data.edges if e.select],
            'pre_selected_verts_index': [v.index for v in bm_data.verts if v.select],
            'pre_selected_faces_index': [f.index for f in bm_data.faces if f.select],
            'pre_selected_edges_index': [e.index for e in bm_data.edges if e.select],
            'sel_islands': []
        }
    return bms


def fit_uv_view(context, mode="selected"):
    """ Make Fit UV Viewport depends of specific types """
    addon_prefs = context.preferences.addons[ADDON_NAME].preferences
    if addon_prefs.autoFitUV:
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "IMAGE_EDITOR":
                    override = {"window": window, "screen": screen, "area": area}
                    try:
                        if mode == "selected":  # mode - True meant fit to selected
                            bpy.ops.image.view_selected(override)
                        elif mode == "all":  # mode - False meant fit to All
                            bpy.ops.image.view_all(override, fit_view=True)
                        elif mode == "checker":
                            bpy.ops.image.view_zoom_ratio(override, ratio=0.5)
                        area.tag_redraw()
                    except Exception:
                        pass
                    break


def update_image_in_uv_layout(context, _image):
    addon_prefs = context.preferences.addons[ADDON_NAME].preferences
    screen = context.screen
    for area in screen.areas:
        if area.type == 'IMAGE_EDITOR':
            if addon_prefs.ShowCheckerInUVLayout and _image:
                area.spaces.active.image = _image
            else:
                area.spaces.active.image = None


def select_islands(context, objs):
    blender_sync_mode = context.scene.tool_settings.use_uv_select_sync
    for obj in objs:
        me, bm = get_mesh_data(obj)
        uv_layer = bm.loops.layers.uv.verify()
        islands_for_select = island_util.get_island(context, bm, uv_layer)
        if not islands_for_select:
            return {"CANCELLED"}
        if context.area.type == "VIEW_3D":
            select_faces(islands_for_select)
        if context.area.type == "IMAGE_EDITOR":
            if blender_sync_mode:
                select_faces(islands_for_select)
            elif not blender_sync_mode:
                select_loops(islands_for_select, uv_layer)

        bmesh.update_edit_mesh(me, loop_triangles=False)


def select_all(bm, action=True):
    """Select or deselect all depend on True or False accordingly"""
    for face in bm.faces:
        face.select = action
    for edge in bm.edges:
        edge.select = action
    for vertex in bm.verts:
        vertex.select = action
    # bmesh.update_edit_mesh(me, loop_triangles=False)


def check_selection(context):
    selection_exist = False
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        if not selection_exist and True in [x.select for x in bm.edges] or True in [x.select for x in bm.faces] or True in [x.select for x in bm.verts]:
            selection_exist = True
    return selection_exist


def set_face_int_tag(_islands_for_process, facemap, int_tag):
    """ Set INT tag for given Islands"""
    faces = [f for island in _islands_for_process for f in island]
    for face in faces:
        face[facemap] = int_tag


def ensure_facemap(bm, facemap_name):
    """ Return facemap int type or create new """
    facemap = bm.faces.layers.int.get(facemap_name)
    if not facemap:
        facemap = bm.faces.layers.int.new(facemap_name)
    return facemap


def enshure_text_block(name):
    """ Return text block or create new """
    block = bpy.data.texts.get(name)
    if not block:
        block = bpy.data.texts.new(name)
    return block


def remove_facemap(bm, facemap_name):
    facemap = bm.faces.layers.int.get(facemap_name)
    if facemap:
        bm.faces.layers.int.remove(facemap)


def select_faces_by_facemap(bm, facemap_name):
    facemap = bm.faces.layers.int.get(facemap_name)
    faces = None
    if facemap:
        faces = [f for f in bm.faces if f[facemap] == 1]
    if faces:
        for face in faces:
            face.select = True


def set_vcolor_to_display(context):
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.color_type = "VERTEX"
                    return True
    return False


def set_texture_to_display(context):
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.color_type = "TEXTURE"
                    return True
    return False


def select_edges(_edges):
    for edge in _edges:
        edge.select = True
    return "DONE"


def select_elements(_set):
    for element in _set:
        element.select = True
    return "DONE"


def select_loop_edges(loops):
    if ZenPolls.version_greater_3_2_0:
        for loop in loops:
            loop.select_edge = True
        return "DONE"
    else:
        return "VER_POLL"


def switch_mesh_to_smooth_mode(context):
    for obj in context.objects_in_mode:
        me, bm = get_mesh_data(obj)
        for face in bm.faces:
            if not face.smooth:
                face.smooth = True

        bmesh.update_edit_mesh(me, loop_triangles=False)


def set_seams_as_sharp(bm):
    for edge in bm.edges:
        if edge.seam:
            edge.smooth = False
        elif not edge.seam:
            edge.smooth = True


def zen_pack_islands(context, me, bm):
    addon_prefs = context.preferences.addons[ADDON_NAME].preferences
    uv_select_sync = context.scene.tool_settings.use_uv_select_sync
    # Pack UV Islands after any isolate action for better visual perception
    context.scene.tool_settings.use_uv_select_sync = True
    select_all(bm, action=True)
    if addon_prefs.averageBeforePack:
        bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands()
    select_all(bm, action=False)
    context.scene.tool_settings.use_uv_select_sync = uv_select_sync


def uv_by_xy(bm, me):
    uv_layer = bm.loops.layers.uv.verify()

    # adjust uv coordinates
    faces = [f for f in bm.faces if not f.hide]
    for face in faces:
        for loop in face.loops:
            loop_uv = loop[uv_layer]
            # use xy position of the vertex as a uv coordinate
            loop_uv.uv = loop.vert.co.xy
    bmesh.update_edit_mesh(me, loop_triangles=False)


def is_island_flipped(island, uv_layer):
    """ Return True if island in given uv_layer have flipped faces """
    for face in island:
        _range = 3
        if len(face.verts) > 4:
            _range = len([loop for loop in face.loops])
        cross_direction = 0
        for i in range(_range):
            uv_a = face.loops[i][uv_layer].uv
            uv_b = face.loops[(i + 1) % _range][uv_layer].uv
            cross_direction += uv_b.cross(uv_a)

        if cross_direction > 0:
            return True
    return False


def rip_geometry_to_pydata(context):
    import os

    out_dirname = "G:\\My Drive\\ZenUV_Dev\\addon\\ZenUV\\Src\\ZenUV\\utils\\tests"
    text_file = os.path.join(out_dirname, 'test_geom_rip.py')

    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.verify()

    loops = [loop[uv_layer].uv for f in bm.faces for loop in f.loops]

    faces = []

    for face in bm.faces:
        face_verts = [v for v in face.verts]
        face_verts_ids = [v.index for v in face_verts]
        faces.append(face_verts_ids)
    verts = [v.co for v in bm.verts]

    with open(text_file, 'w', newline='') as file:

        file.write("faces = [\n")
        for f in faces:
            file.write("    " + str(f) + ",\n")
        file.write("]\n")

        file.write("verts = [\n")
        for v in verts:
            file.write("    Vector(" + str(v[:]) + "),\n")
        file.write("]\n")

        file.write("loops_uv_co = [\n")
        for l in loops:
            file.write("    Vector(" + str(l[:]) + "),\n")
        file.write("]\n")

        file.write("seams = [\n")
        for e in bm.edges:
            file.write("    " + str(e.seam) + ",\n")
        file.write("]\n")


def switch_shading_style(context, style, switch):
    """ Switch Shading style in current viewport """
    for area in context.screen.areas:
        if area.type == 'VIEW_3D' and area == context.area:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if space.shading.color_type == "VERTEX" and style == "VERTEX" and switch:
                        style = "MATERIAL"
                    if space.shading.type != 'WIREFRAME':
                        space.shading.color_type = style
                    return True
    return False


def get_current_shading_style(context):
    """ Return Shading Style from current viewport """
    if context.area.type == 'IMAGE_EDITOR':
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        return space.shading.color_type
    elif context.area.type == 'VIEW_3D':
        for space in context.area.spaces:
            if space.type == 'VIEW_3D':
                return space.shading.color_type
    else:
        return context.scene.zen_uv_checker.prev_color_type


if __name__ == "__main__":
    pass
