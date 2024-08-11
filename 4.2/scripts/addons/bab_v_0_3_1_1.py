from random import shuffle
import bgl
from gpu_extras.batch import batch_for_shader
import gpu
from bpy.types import (
    Panel, PropertyGroup
)
import bmesh
import bpy
import mathutils
import math
import numpy as np
import time

bl_info = {
    "name": "Bevel After Boolean",
    "author": "Rodinkov Ilya",
    "version": (0, 3, 1, 1, "b"),
    "blender": (2, 91, 0),
    "location": "View3D > Tools > Boolean Bevel > Bevel",
    "description": "Create bevel after boolean",
    "warning": "This add-on is still in development.",
    "wiki_url": "",
    "category": "Object",
}

DEBUG = True


# def select_loop(bm, angle, self):
#     selected_edges = [edge for edge in bm.edges if edge.select]
#     if not selected_edges:
#         self.report({'INFO'}, "No selected edges")
#         return

#     if len(selected_edges) > 1:
#         self.report({'INFO'}, "Not stable for several selected edges")

#     if isinstance(bm.select_history[-1], bmesh.types.BMEdge):
#         current_vert = bm.select_history[-1].verts[0]
#     else:
#         current_vert = selected_edges[0].verts[0]

#     while True:
#         current_vert = get_next_vert(current_vert, angle, selected_edges)

#         if current_vert is None:
#             break

#     for edge in selected_edges:
#         if not edge.select:
#             edge.select_set(True)

def find_sharp_verts(verts_loop, sharp_angle, cyclic, invert=False):
    sharp_verts_index = []
    count = len(verts_loop)

    if cyclic:
        start = 0
        end = count
    else:
        start = 1
        end = count - 1

    for i in range(start, end):
        prev = i - 1

        if i == count - 1:
            next = 0
        else:
            next = i + 1

        vec1 = verts_loop[prev].co - verts_loop[i].co
        vec2 = verts_loop[next].co - verts_loop[i].co
        angle = vec1.angle(vec2)

        if angle is None:
            continue

        if angle > math.pi:
            # print("Угол больше 180:", angle)
            angle = math.pi * 2 - angle

        if angle < sharp_angle and not invert:
            sharp_verts_index.append(i)

        elif angle > sharp_angle and invert:
            sharp_verts_index.append(i)

    return sharp_verts_index


def smooth_verts_by_index(verts_loop, factor, cyclic, verts_index=False):
    if not verts_index:
        verts_index = [*range(len(verts_loop))]

    new_coords = []
    count = len(verts_loop)

    if not cyclic:
        if verts_index[0] == 0 and verts_index[-1] == count - 1:
            verts_index = verts_index[1:-1]
        elif verts_index[0] == 0:
            verts_index = verts_index[1:]
        elif verts_index[-1] == count - 1:
            verts_index = verts_index[:-1]

    for i in verts_index:
        prev = i - 1

        if i == count - 1:
            next = 0
        else:
            next = i + 1

        middle_vec = (verts_loop[prev].co + verts_loop[next].co) / 2
        new_coord = verts_loop[i].co.lerp(middle_vec, factor)
        new_coords.append(new_coord)

    for index, i in enumerate(verts_index):
        verts_loop[i].co = new_coords[index]


def select_loop(bm, angle, self):
    selected_edges = [edge for edge in bm.edges if edge.select]
    if not selected_edges:
        self.report({'INFO'}, "No selected edges")
        return

    if len(selected_edges) > 1:
        self.report({'INFO'}, "Not stable for several selected edges")

    if isinstance(bm.select_history[-1], bmesh.types.BMEdge):
        current_vert = bm.select_history[-1].verts[0]
    else:
        current_vert = selected_edges[0].verts[0]

    while current_vert is not None:
        current_vert = get_next_vert(current_vert, angle, selected_edges)

    for edge in selected_edges:
        if not edge.select:
            edge.select_set(True)


def get_next_vert(current_vert, angle, ignore_edges):
    for edge in current_vert.link_edges:

        if edge in ignore_edges:
            continue

        elif edge.calc_face_angle() >= angle:
            ignore_edges.append(edge)
            return edge.other_vert(current_vert)
    return None


def erase_3d_lines(handlers=[]):
    for handler in handlers:
        bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
        handler = None
    handlers.clear()


def draw_3d_line(line_points=[], line_color=(1, 0, 0, 0), line_width=2,
                 dot_points=None, dot_color=None,
                 dot_width=None, use_dot=True):
    if not line_points:
        return

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": line_points})
    bgl.glLineWidth(line_width)
    shader.bind()
    shader.uniform_float("color", line_color)
    batch.draw(shader)

    if use_dot:
        if dot_points is None:
            dot_points = line_points

        if dot_color is None:
            dot_color = line_color

        if dot_width is None:
            dot_width = line_width + 1

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'POINTS', {"pos": dot_points})
        bgl.glLineWidth(dot_width)
        shader.bind()
        shader.uniform_float("color", dot_color)
        batch.draw(shader)

    bgl.glLineWidth(1)


def smooth_side(bm, radius, iterations, verts, align, center, obj_bvh,
                angle=math.pi / 6, save_sharp=True):
    if save_sharp:
        smooth_verts = [
            vert for vert in verts if vert.calc_edge_angle() < angle]
    else:
        smooth_verts = verts

    for i in range(iterations):
        bmesh.ops.smooth_vert(bm, verts=smooth_verts, factor=0.5,
                              use_axis_x=True, use_axis_y=True,
                              use_axis_z=True)

        # Выравнивание по исходному мешу после сглаживания
        for index, vert in enumerate(verts):
            dist = radius - (vert.co - center[index].co).length
            direct = (vert.co - center[index].co).normalized()
            if align:
                location, normal, indx, distance = obj_bvh.find_nearest(
                    vert.co + direct * dist)
            else:
                location, normal, index, distance = obj_bvh.find_nearest(
                    vert.co)
            vert.co = location


def slide_verts(verts=[], factor=0.5, angle=math.pi / 6,
                save_sharp=True):
    """
    """
    factor -= round(math.floor(factor), 6)
    # factor %= 1
    if factor == 0.0:
        return

    # # Ограничиваем диапозон factor от -1.0 до 1.0
    # if factor > 1.0:
    #     factor = 1.0

    # if factor < -1.0:
    #     factor = -1.0

    #  меняем порядок вершин (Для противоположного направления)
    if factor < 0.0:
        verts = verts[::-1]
        factor *= -1

    # Получаем исходные координаты
    coords = [vert.co.to_3d() for vert in verts]

    for i, vert in enumerate(verts):
        # пропускаем острые грани
        if vert.calc_edge_angle() > angle:
            continue
        # получаем смещение
        dist = (coords[i - 1] - coords[i]).length
        # получаем направление смещения
        direct = (coords[i - 1] - coords[i]).normalized()
        # меняем положение вершины
        vert.co += direct * dist * factor


def create_shell(bm, loop, edges_side1, edges_side2, center_edges, verts_side1,
                 verts_side2):
    shell_edges = []

    for index, vert in enumerate(loop):
        shell_edges.append(bm.edges.new([verts_side1[index], vert]))
        shell_edges.append(bm.edges.new([verts_side2[index], vert]))

    bmesh.ops.holes_fill(bm, edges=shell_edges +
                                   center_edges + edges_side1 + edges_side2, sides=4)


def new_loop(bm, points):
    verts_side = []

    for point in points:
        verts_side.append(bm.verts.new(point))
    edges_side = []

    for index, vert in enumerate(verts_side):
        edges_side.append(bm.edges.new([vert, verts_side[index - 1]]))

    return verts_side, edges_side


def get_side_points(points, side_faces, obj_bvh):
    for i, point in enumerate(points):

        dist = (points[i - 1] - point).length

        direct = (points[i - 1] - point).normalized()

        location, normal, index, distance = obj_bvh.ray_cast(
            point, direct, dist)

        if location is not None:
            if index in side_faces:
                point_side1 = location
            else:
                point_side2 = location
    return point_side1, point_side2


def edge_loops_from_edges(bm, edges=None):
    """
    Edge loops defined by edges

    Takes me.edges or a list of edges and returns the edge loops

    return a list of vertex indices.
    [ [1, 6, 7, 2], ...]

    closed loops have matching start and end values.
    """
    line_polys = []
    # Get edges not used by a face
    if edges is None:
        edges = bm.edges[:]

    if not hasattr(edges, "pop"):
        edges = edges[:]

    while edges:
        current_edge = edges.pop()
        vert_end, vert_start = current_edge.verts[:]
        line_poly = [vert_start, vert_end]

        ok = True
        while ok:
            ok = False
            # for i, ed in enumerate(edges):
            i = len(edges)
            while i:
                i -= 1
                ed = edges[i]
                v1, v2 = ed.verts
                if v1 == vert_end:
                    line_poly.append(v2)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_end:
                    line_poly.append(v1)
                    vert_end = line_poly[-1]
                    ok = 1
                    del edges[i]
                    # break
                elif v1 == vert_start:
                    line_poly.insert(0, v2)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    # break
                elif v2 == vert_start:
                    line_poly.insert(0, v1)
                    vert_start = line_poly[0]
                    ok = 1
                    del edges[i]
                    # break
        line_polys.append(line_poly)
    return line_polys


def get_circle_points(radius, count, index, vert, loop):
    center_co = vert.co

    if round(vert.calc_edge_angle(), 10) == round(0.0, 10):
        v = (loop[index - 1].co - vert.co).orthogonal().normalized()
    else:
        if index == len(loop) - 1:
            a = (loop[0].co - vert.co).normalized()
        else:
            a = (loop[index + 1].co - vert.co).normalized()
        b = (loop[index - 1].co - vert.co).normalized()
        v = (a + b).normalized()
    if index == len(loop) - 1:
        u = mathutils.geometry.normal(
            vert.co + v, loop[0].co, loop[index - 1].co)
    else:
        u = mathutils.geometry.normal(
            vert.co + v, loop[index + 1].co, loop[index - 1].co)

    angle = math.pi * 2 / count
    points = []

    for i in range(count):
        co = center_co + u * radius * \
             math.cos(angle * i) + v * radius * math.sin(angle * i)
        points.append(co)
    return points


def smooth_verts(bm, verts=[], smooth_iter=1, angle=math.pi / 6, save_sharp=True):
    if save_sharp:
        smooth_verts = [
            vert for vert in verts if vert.calc_edge_angle() < angle]
    else:
        smooth_verts = verts

    for _ in range(smooth_iter):
        bmesh.ops.smooth_vert(bm, verts=smooth_verts, factor=0.5,
                              use_axis_x=True, use_axis_y=True,
                              use_axis_z=True)


def create_kd_tree(bm):
    size = len(bm.verts)
    kd = mathutils.kdtree.KDTree(size)
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    kd.balance()
    return kd


def clear_radius(bm, radius, verts):
    kd = create_kd_tree(bm)
    indexs = set()
    for point in verts:
        indexs = indexs | {index for (
            co, index, dist) in kd.find_range(point.co, radius)}

    temp = bm.verts[:]

    del_verts = [temp[index] for index in indexs if temp[index] not in verts]
    bmesh.ops.delete(bm, geom=del_verts, context="VERTS")


def get_intesection(bm, obj):
    verts_index = [vert.index for vert in obj.data.vertices if not vert.groups]
    temp = bm.verts[:]
    verts = [temp[index] for index in verts_index]
    temp = bm.edges[:]
    edges = [edge for edge in temp if edge.verts[0]
             in verts and edge.verts[1] in verts]

    dupli_geom = bmesh.ops.duplicate(bm, geom=edges)["geom"]

    center_verts = [el for el in dupli_geom if isinstance(
        el, bmesh.types.BMVert)]

    center_edges = [el for el in dupli_geom if isinstance(
        el, bmesh.types.BMEdge)]

    return center_verts, center_edges


def clear_vertex_groups(obj):
    # Удаляем группы вершин
    if obj.vertex_groups:
        obj.vertex_groups.clear()


def new_vertex_group(obj, verts_index=[], name="Group"):
    # Создаем группу вершин
    obj.vertex_groups.new(name=name)
    # Добавляем в нее все вершины
    obj.vertex_groups.active.add(verts_index, 1, 'ADD')


def subdiv_big_edges(bm=None, edges=[], dist=0.01, smooth=0.0):
    """
    """
    for edge in edges[:]:
        edge_length = edge.calc_length()
        if edge_length > dist:
            geom = bmesh.ops.subdivide_edges(
                bm,
                edges=[edge], cuts=round(
                    edge_length / dist) - 1,
                smooth=smooth)["geom"]
            edges += [el for el in geom if isinstance(
                el, bmesh.types.BMEdge)]
    edges = set(edges)
    new_edges = [edge for edge in edges if edge.is_valid]
    new_verts = list({vert for edge in edges for vert in edge.verts})
    return new_edges, new_verts


def bevel(self, context=bpy.context, radius=0.2, dist=0.1, subdiv_smooth=0.0,
          smooth_iter=5, circle_count=12, smooth_side_a=5, smooth_side_b=5,
          align_side_a=True, align_side_b=True, segments=12, bevel=False,
          prev=False):
    obj = context.active_object
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    side_faces1 = [face.index for face in bm.faces if face.select]
    # создаем bvh дерево для поиска пересечений
    obj_bvh = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.001)
    # дублируем пересечение
    center_verts, center_edges = get_intesection(bm, obj)
    # подразделяем длинные ребра
    # center_verts, center_edges = subdiv_big_edges(
    #     bm, edges=center_edges, dist=dist)

    # # сглаживаем пересечение
    # smooth_verts(bm, verts=center_verts, smooth_iter=smooth_iter)

    # удаляем все вершины в радиусе от перечечения
    if not prev:
        clear_radius(bm, radius, center_verts)

    connect_side1 = [
        edge for edge in bm.edges if edge.select and edge.is_boundary]

    connect_side2 = [
        edge for edge in bm.edges if not edge.select and edge.is_boundary]

    center_edges, center_verts = subdiv_big_edges(
        bm, edges=center_edges, dist=self.dist)

    # сортируем ребра и вершины
    loops = edge_loops_from_edges(bm, edges=center_edges[:])
    bab_props = context.window_manager.bab_props
    #
    for loop in loops:
        points_side1 = []
        points_side2 = []
        loop = loop[:-1]

        slide_verts(verts=loop, factor=self.factor, save_sharp=False)

        if bab_props.handlers:
            erase_3d_lines(handlers=bab_props.handlers)

        for index, vert in enumerate(loop):
            points = get_circle_points(radius, 12, index, vert, loop)

            # # test
            # handler = bpy.types.SpaceView3D.draw_handler_add(draw_3d_line, (points, ), 'WINDOW', 'POST_VIEW')
            # bab_props.handlers.append(handler)

            point_side1, point_side2 = get_side_points(
                points, side_faces1, obj_bvh)

            points_side1.append(point_side1)
            points_side2.append(point_side2)

        # self.coords = points_side1 + points_side2

        verts_side1, edges_side1 = new_loop(bm, points_side1)

        verts_side2, edges_side2 = new_loop(bm, points_side2)

        # сглаживаем пересечение
        smooth_verts(bm, verts=center_verts, smooth_iter=smooth_iter,
                     angle=self.angle, save_sharp=self.save_sharp)

        smooth_side(bm, radius, smooth_side_a,
                    verts_side1, align_side_a, loop, obj_bvh, angle=self.angle, save_sharp=self.save_sharp_a)

        smooth_side(bm, radius, smooth_side_b,
                    verts_side2, align_side_b, loop, obj_bvh, angle=self.angle, save_sharp=self.save_sharp_b)

        smooth_verts(bm, verts=center_verts, smooth_iter=self.smooth_center,
                     angle=self.angle, save_sharp=self.save_sharp_center)

        if self.prev:
            mat = obj.matrix_world

            coords1 = [
                mat @ vert.co for edge in edges_side1 for vert in edge.verts]
            color1 = (1.0, 0.0, 0.0, 1.0)

            coords2 = [
                mat @ vert.co for edge in edges_side2 for vert in edge.verts]
            color2 = (0.0, 1.0, 0.0, 1.0)

            coordsc = [
                mat @ vert.co for edge in center_edges for vert in edge.verts]
            colorc = (0.0, 0.0, 1.0, 1.0)

            handler1 = bpy.types.SpaceView3D.draw_handler_add(
                draw_3d_line, (coords1, color1), 'WINDOW', 'POST_VIEW')
            bab_props.handlers.append(handler1)

            handler2 = bpy.types.SpaceView3D.draw_handler_add(
                draw_3d_line, (coords2, color2), 'WINDOW', 'POST_VIEW')
            bab_props.handlers.append(handler2)

            handler3 = bpy.types.SpaceView3D.draw_handler_add(
                draw_3d_line, (coordsc, colorc), 'WINDOW', 'POST_VIEW')
            bab_props.handlers.append(handler3)

        if not self.prev:
            if bab_props.handlers:
                erase_3d_lines(handlers=bab_props.handlers)

            # соединяем части
            if connect_side1:
                bmesh.ops.bridge_loops(bm, edges=connect_side1 + edges_side1)

            if connect_side2:
                bmesh.ops.bridge_loops(bm, edges=connect_side2 + edges_side2)

            create_shell(bm, loop, edges_side1, edges_side2,
                         center_edges, verts_side1, verts_side2)

    if not self.prev:
        if bevel and not prev:
            bevel_segments = self.segments - 1
            bevel_width = 100 - (200 / (bevel_segments + 3))
            offset = 100 - segments
            bmesh.ops.bevel(bm, geom=center_edges, offset=bevel_width,
                            offset_type='PERCENT', segments=bevel_segments, profile=0.5,
                            loop_slide=True, affect='EDGES')

        # применяем изменения на меш
        bm.to_mesh(obj.data)
        # обновляем меш
        obj.data.update()
        # освобождаем память
    bm.free()


# bevel()


class BAB_Props(PropertyGroup):
    # Other
    offset: bpy.props.FloatProperty(
        name="Bevel Radius", default=0.05, min=0.00002, max=1000.0, step=1,
        subtype='DISTANCE')
    stop_calc: bpy.props.BoolProperty(name="Stop calculations", default=False)
    wire: bpy.props.BoolProperty(name="Wire", default=False)
    create_slice: bpy.props.BoolProperty(name="Slice", default=False)

    apply_all: bpy.props.BoolProperty(name="Skip Boolean", default=True)

    remove_all: bpy.props.BoolProperty(name="Skip Boolean", default=True)

    hide: bpy.props.BoolProperty(name="Show modifiers", default=True)

    show_render: bpy.props.BoolProperty(name="Show in render", default=False)
    display_as: bpy.props.EnumProperty(name="Display as", items=(("BOUNDS", "Bounds", "On visibility"),
                                                                 ("WIRE", "Wire",
                                                                  "Off visibility"),
                                                                 ("SOLID", "Solid",
                                                                  "Off visibility"),
                                                                 ("TEXTURED", "Textured",
                                                                  "Off visibility"),
                                                                 ),
                                       description="Display as",
                                       default="TEXTURED")

    axis: bpy.props.EnumProperty(name="Axis",
                                 items=(("X", "X", "Use x axis"),
                                        ("Y", "Y", "Use y axis"),
                                        ("Z", "Z", "Use z axis"),
                                        ),
                                 description="Axis",
                                 default="X")

    flip_direction: bpy.props.BoolProperty(
        name="Flip Direction", default=False)

    merge_threshold: bpy.props.FloatProperty(
        name="Merge Dist", default=0.001, min=0.0, max=1.0, step=1, subtype='DISTANCE')

    pipe_radius: bpy.props.FloatProperty(
        name="Pipe Radius", default=0.05, min=0.00002, max=1000.0, step=1, subtype='DISTANCE')
    pipe_wire: bpy.props.BoolProperty(name="Wire", default=False)
    pipe_stop: bpy.props.BoolProperty(name="Stop calculations", default=False)
    handlers = []


class BAB_PT_Panel(Panel):
    """Main Panel of add-on"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BaB"
    bl_label = "Bevel After Boolean "

    def draw(self, context):
        bab_props = context.window_manager.bab_props
        layout = self.layout
        box = layout.box()
        box.label(text="Bevel:")
        box.operator("bab.bevel")
        box.prop(bab_props, "offset")
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.prop(bab_props, "wire")
        row.prop(bab_props, "stop_calc")
        box.prop(bab_props, "create_slice")

        #

        box = layout.box()
        box.label(text="New objects:")

        # box.layout.separator(factor=1.0)
        box.prop(bab_props, "pipe_radius")
        box.operator("bab.create_pipe")
        row = box.row(align=True)
        row.alignment = 'LEFT'
        row.prop(bab_props, "pipe_wire")
        row.prop(bab_props, "pipe_stop")
        box.operator("bab.slice")

        box = layout.box()
        box.label(text="Modifiers:")
        box.alignment = 'CENTER'
        box.operator("bab.apply_modifiers")
        box.prop(bab_props, "apply_all")
        box.operator("bab.remove_modifiers")
        box.prop(bab_props, "remove_all")
        box.operator("bab.hide_modifiers")
        box.prop(bab_props, "hide")

        box = layout.box()
        box.label(text="Visibility:")
        box.prop(bab_props, "show_render")
        box.prop(bab_props, "display_as")
        box.operator("bab.visibility")

        box = layout.box()
        box.label(text="Symmetrize:")
        box.operator("bab.symmetrize")
        box.prop(bab_props, "axis")
        box.prop(bab_props, "flip_direction")
        box.prop(bab_props, "merge_threshold")

        box = layout.box()
        box.label(text="Tests:")
        box.operator("bab.test")
        box.operator("bab.remove_3d_lines")

        box.operator("bab.select_loop")
        box.operator("bab.smooth_loop")


def circle(radius, count, center_co, u, v, bm):
    for i in range(count):
        angle = math.radians(360 / count)
        co = center_co + u * radius * \
             math.cos(angle * i) + v * radius * math.sin(angle * i)
        bmesh.ops.create_vert(bm, co=co)


class BAB_OP_SMOOTH_LOOP(bpy.types.Operator):
    """Create bevel on object"""
    bl_idname = "bab.smooth_loop"
    bl_label = "Smooth loop"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    angle: bpy.props.FloatProperty(
        name="angle", default=math.pi / 6, min=0.0, max=math.pi, step=10, subtype="ANGLE")

    invert: bpy.props.BoolProperty(name="Invert", default=False)
    repeat_count: bpy.props.IntProperty(name="Repeat", default=1, min=0, step=1)

    smooth_by_angle: bpy.props.BoolProperty(name="Smooth by angle", default=False)

    factor: bpy.props.FloatProperty(name="Factor", default=0.5, min=0.0, max=1.0, step=10)
    sharp_every: bpy.props.BoolProperty(name="Find angle every iteration", default=False)
    project: bpy.props.BoolProperty(name="Project", default=False)
    project_every: bpy.props.BoolProperty(name="Project every iteration", default=False)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Smooth loop:")
        box.prop(self, "factor")
        box.prop(self, "repeat_count")
        box.prop(self, "smooth_by_angle")
        box.prop(self, "invert")
        if self.smooth_by_angle:
            box.prop(self, "angle")
            box.prop(self, "sharp_every")
        box.prop(self, "project")
        box.prop(self, "project_every")

    def execute(self, context):
        if DEBUG:
            time_start = time.time()

        if bpy.context.object is None:
            self.report({'INFO'}, "Object not found")
            return {'FINISHED'}

        mesh = bpy.context.object.data

        if not mesh.is_editmode:
            self.report({'INFO'}, "Only for Edit mode")
            return {'FINISHED'}

        bm = bmesh.from_edit_mesh(mesh)

        if not bm.faces:
            self.project = False

        select_edges = [edge for edge in bm.edges if edge.select]
        loops = edge_loops_from_edges(bm, select_edges)

        if self.project:
            obj_bvh = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.0)

        for loop in loops:
            if loop[0] == loop[-1]:
                cyclic = True
                loop = loop[:-1]
            else:
                cyclic = False

            if self.smooth_by_angle and self.sharp_every:
                for _ in range(self.repeat_count):
                    sharp_verts_index = find_sharp_verts(loop, self.angle, cyclic, self.invert)

                    if sharp_verts_index:
                        smooth_verts_by_index(loop, self.factor, cyclic, sharp_verts_index)

                        if self.project and self.project_every:
                            for vert in loop:
                                location, normal, index, distance = obj_bvh.find_nearest(vert.co)
                                vert.co = location
                    else:
                        break

            elif self.smooth_by_angle and not self.sharp_every:
                sharp_verts_index = find_sharp_verts(loop, self.angle, cyclic, self.invert)

                if sharp_verts_index:
                    for _ in range(self.repeat_count):
                        smooth_verts_by_index(loop, self.factor, cyclic, sharp_verts_index)

                        if self.project and self.project_every:
                            for vert in loop:
                                location, normal, index, distance = obj_bvh.find_nearest(vert.co)
                                vert.co = location

            else:
                for _ in range(self.repeat_count):
                    smooth_verts_by_index(loop, self.factor, cyclic)

                    if self.project and self.project_every:
                        for vert in loop:
                            location, normal, index, distance = obj_bvh.find_nearest(vert.co)
                            vert.co = location

            if self.project and not self.project_every:
                for vert in loop:
                    location, normal, index, distance = obj_bvh.find_nearest(vert.co)
                    vert.co = location

        mesh.update()

        if DEBUG:
            print("invoke: %.4f sec\n" % (time.time() - time_start))
        return {'FINISHED'}


class BAB_OP_SELECT_LOOP(bpy.types.Operator):
    """Create bevel on object"""
    bl_idname = "bab.select_loop"
    bl_label = "Select loop"
    bl_options = {'REGISTER', 'UNDO'}

    angle: bpy.props.FloatProperty(
        name="angle", default=math.pi / 6, min=0.0, max=math.pi, step=10, subtype="ANGLE")

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Select loop by angle:")
        box.prop(self, "angle")

    def execute(self, context):
        if DEBUG:
            time_start = time.time()
        if bpy.context.object is None:
            self.report({'INFO'}, "Object not found")
            return {'FINISHED'}

        mesh = bpy.context.object.data

        if not mesh.is_editmode:
            self.report({'INFO'}, "Only for Edit mode")
            return {'FINISHED'}

        bm = bmesh.from_edit_mesh(mesh)
        select_loop(bm, self.angle, self)
        mesh.update()
        if DEBUG:
            print("invoke: %.4f sec\n" % (time.time() - time_start))
        return {'FINISHED'}


class BAB_OP_TESTS(bpy.types.Operator):
    """Create bevel on object"""
    bl_idname = "bab.test"
    bl_label = "Tests"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    radius: bpy.props.FloatProperty(
        name="radius", default=0.1, min=0.01, max=5000, step=10, subtype='DISTANCE')

    dist: bpy.props.FloatProperty(
        name="dist", default=0.1, min=0.01, max=5000, step=10, subtype='DISTANCE')

    factor: bpy.props.FloatProperty(
        name="factor", default=0.0, min=-1000.0, max=1000.0, step=10)
    bevel: bpy.props.BoolProperty(name="bevel", default=False)
    prev: bpy.props.BoolProperty(name="prev", default=False)

    angle: bpy.props.FloatProperty(
        name="angle", default=math.pi / 6, min=0.0, max=math.pi, step=10, subtype="ANGLE")

    save_sharp: bpy.props.BoolProperty(name="save_sharp", default=True)
    save_sharp_a: bpy.props.BoolProperty(name="save_sharp", default=True)
    save_sharp_b: bpy.props.BoolProperty(name="save_sharp", default=True)
    save_sharp_center: bpy.props.BoolProperty(name="save_sharp", default=True)

    smooth_iter: bpy.props.IntProperty(
        name="Smooth", default=5, min=0, max=5000, step=1)
    smooth_center: bpy.props.IntProperty(
        name="Smooth center", default=0, min=0, max=5000, step=1)
    smooth_side_a: bpy.props.IntProperty(
        name="smooth_side_a", default=5, min=0, max=5000, step=1)
    smooth_side_b: bpy.props.IntProperty(
        name="smooth_side_b", default=5, min=0, max=5000, step=1)

    align_side_a: bpy.props.BoolProperty(name="align_side_a", default=True)
    align_side_b: bpy.props.BoolProperty(name="align_side_b", default=True)

    segments: bpy.props.IntProperty(
        name="segments", default=10, min=2, max=5000, step=1)

    # smooth_iter: bpy.props.FloatProperty(name="smooth", default=0.0, min=0.0, max=1.0, step=1)
    # angle: bpy.props.FloatProperty(name="angle", default=math.pi/36, min=0.0, max=math.pi, step=10, subtype="ANGLE")

    # coords = []
    # handler = None
    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    # batch = batch_for_shader(shader, 'LINES', {"pos": coords})

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Bevel:")
        box.prop(self, "radius")
        box.prop(self, "dist")
        box.prop(self, "factor")

        box.prop(self, "bevel")
        box.prop(self, "prev")

        box.prop(self, "angle")
        box.prop(self, "save_sharp")

        box.prop(self, "smooth_iter")

        # box.prop(self, "save_sharp_center")
        # box.prop(self, "smooth_center")

        box.prop(self, "save_sharp_a")
        box.prop(self, "smooth_side_a")

        box.prop(self, "save_sharp_b")
        box.prop(self, "smooth_side_b")

        box.prop(self, "align_side_a")
        box.prop(self, "align_side_b")
        box.prop(self, "segments")

    def execute(self, context):
        src_obj = context.active_object
        # Снимаем выделение со всех объектов
        bpy.ops.object.select_all(action='DESELECT')
        # объект boolean
        bool_obj = src_obj.modifiers[-1].object
        # Режим отрисовки для boolean
        bool_obj.display_type = 'BOUNDS'

        # Удаляем группы вершин
        if src_obj.vertex_groups:
            src_obj.vertex_groups.clear()

        # Удаляем группы вершин
        if bool_obj.vertex_groups:
            bool_obj.vertex_groups.clear()

        # Скрываем все модификаторы
        src_obj.modifiers.foreach_set(
            'show_viewport', [False] * len(src_obj.modifiers))

        # Создаем группу вершин
        src_obj.vertex_groups.new(name=src_obj.name)
        # Добавляем в нее все вершины
        src_obj.vertex_groups.active.add(
            range(len(src_obj.data.vertices)), 1, 'ADD')

        # Применяем модификаторы
        apply_modifiers(src_obj.modifiers, src_obj)

        # Применяем масштаб
        bpy.ops.object.transform_apply(
            location=False, rotation=False, scale=True)

        # Заходим в режим редактирования
        bpy.ops.object.mode_set(mode='EDIT')
        # Режим вершин
        # Метод 1
        bpy.ops.mesh.select_mode(type='VERT')
        # Выделяем вершины без групп
        bpy.ops.mesh.select_ungrouped(extend=False)
        bpy.ops.mesh.select_mode(type='FACE')

        src_obj.vertex_groups.new(name=bool_obj.name)
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_more(use_face_step=True)
        src_obj.vertex_groups.active_index = 0
        bpy.ops.object.vertex_group_remove_from()

        # bpy.ops.mesh.region_to_loop()

        # # Заходим в режим редактирования
        # bpy.ops.object.mode_set(mode='EDIT')
        # # Режим вершин
        # bpy.ops.mesh.select_mode(type='VERT')
        # # Выделяем вершины без групп
        # bpy.ops.mesh.select_ungrouped(extend=False)
        # # группа вершин для части булена
        # bpy.ops.mesh.select_less(use_face_step=True)
        # src_obj.vertex_groups.new(name=bool_obj.name)
        # bpy.ops.object.vertex_group_assign()
        # bpy.ops.mesh.select_more(use_face_step=True)
        bpy.ops.object.mode_set(mode='OBJECT')

        bevel(self, context=context, radius=self.radius, dist=0.1,
              subdiv_smooth=0.0, smooth_iter=self.smooth_iter, circle_count=12,
              smooth_side_a=self.smooth_side_a, smooth_side_b=self.smooth_side_b,
              align_side_a=self.align_side_a, align_side_b=self.align_side_b,
              segments=self.segments, bevel=self.bevel, prev=self.prev)

        # if handler is None and self.prev:
        #     print("Рисуем линию")
        #     obj = context.active_object
        #     handler = bpy.types.SpaceView3D.draw_handler_add(
        #         line, (), 'WINDOW', 'POST_VIEW')

        # elif handler is not None and not self.prev:
        #     bpy.types.SpaceView3D.draw_handler_remove(handler, "WINDOW")
        #     handler = None
        #     print("Удаляем линию")
        return {'FINISHED'}

    # def finish(self, context):
    #     print("Выход")
    #     if self.test is not None:
    #         bpy.types.SpaceView3D.draw_handler_remove(self.test, "WINDOW")
    #         self.test = None


class BAB_OP_Bevel(bpy.types.Operator):
    """Create bevel on object"""
    bl_idname = "bab.bevel"
    bl_label = "Bevel"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, "wire")
        row.prop(self, "preview_curve")
        row.prop(self, "stop_calc")

        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, "save_settings")
        if not self.edit_mode:
            row.prop(self, "create_slice")

        box.label(text="Basic Parameters:")
        if not self.edit_mode:
            box.prop(self, "operation")
        box.prop(self, "offset")

        if not self.edit_mode:
            box = layout.box()
            box.label(text="Subsurf:")
            column = box.column()
            if self.src_subsrf_index == -1:
                column.enabled = False
            column.prop(self, "subdiv_a", text=self.obj_name)
            column = box.column()
            if self.bool_subsrf_index == -1:
                column.enabled = False
            column.prop(self, "subdiv_b", text=self.bool_name)

        box = layout.box()
        box.label(text="Bevel:")

        box.prop(self, "density_on")
        if self.density_on:
            box.prop(self, "density")

        box.prop(self, "bevel_profile")
        box.prop(self, "bevel_segments")
        box.prop(self, "corner")
        box.prop(self, "fix_outside")
        box.prop(self, "abs_size")
        if self.abs_size:
            box.prop(self, "corner_dist")
        else:
            box.prop(self, "corner_size")
        box = layout.box()

        box.label(text="Normals:")
        box.prop(self, "transfer")
        box.prop(self, "transfer_factor")

        box.prop(self, "triangulate")

        if self.triangulate:
            box.prop(self, "method")

        box = layout.box()
        box.label(text="Patch Parameters:")
        box.prop(self, "smooth")
        box.prop(self, "factor")
        box.prop(self, "remove_doubles")
        box.prop(self, "subdivide")
        box.prop(self, "simplify")

        box = layout.box()
        box.label(text="Refine:")
        box.prop(self, "refine")

        box.prop(self, "refine_type")
        if self.refine_type == "DIST":
            box.prop(self, "refine_dist")

        if self.refine_type == "COUNT":
            box.prop(self, "refine_count")

        box.prop(self, "refine_multiply")
        box.prop(self, "refine_shift")
        box.prop(self, "refine_accuracy")

        box = layout.box()
        box.label(text="Pipe settings:")
        box.prop(self, "refine_res")
        box.prop(self, "mean_tilt")
        box.prop(self, "twist_smooth")
        # box.prop(self, "pipe_smooth")

    def invoke(self, context, event):
        if DEBUG:
            time_start = time.time()

        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.stop_calc = bab_props.stop_calc
        self.wire = bab_props.wire
        self.offset = bab_props.offset
        self.create_slice = bab_props.create_slice

        self.wire_pre = bab_props.wire
        self.offset_pre = bab_props.offset
        self.create_slice_pre = bab_props.create_slice

        # исходный объект
        src_obj = context.active_object
        # передаем имя объекта в props
        self.obj_name = src_obj.name
        # Находим индекс boolean'а
        self.bool_index = get_boolean_index(src_obj)

        self.edit_mode = src_obj.data.is_editmode

        if not self.edit_mode:
            # Проверяем что boolean добавлен к объекту
            if self.bool_index == -1:
                self.report({'ERROR'}, "Boolean not found")
                return {'CANCELLED'}
            # объект boolean
            bool_obj = src_obj.modifiers[self.bool_index].object
            # Проверяем, что boolean не пустой
            if not bool_obj:
                self.report({'ERROR'}, "Boolean disabled")
                return {'CANCELLED'}
            # Передаем имя boolean в props
            self.bool_name = bool_obj.name
            # Передаем в props операцию boolean
            self.operation = src_obj.modifiers[self.bool_index].operation
            # ищем subsurf у объекта
            self.src_subsrf_index = get_subsurf_index(src_obj)
            # меняем значение props на нужное
            if self.src_subsrf_index > -1:
                self.subdiv_a = src_obj.modifiers[self.src_subsrf_index].levels
            else:
                self.subdiv_a = 0
            # ищем subsurf у boolean
            self.bool_subsrf_index = get_subsurf_index(bool_obj)
            # меняем значение props на нужное
            if self.bool_subsrf_index > -1:
                self.subdiv_b = bool_obj.modifiers[self.bool_subsrf_index].levels
            else:
                self.subdiv_b = 0
            # запускаем главный цикл

        if DEBUG:
            print("invoke: %.4f sec\n" % (time.time() - time_start))
        return self.execute(context)

    # boolean operation
    operation: bpy.props.EnumProperty(name="Operation",
                                      items=(("UNION", "Union", "Use Union"),
                                             ("DIFFERENCE", "Difference",
                                              "Use Difference"),
                                             ("INTERSECT", "Intersect",
                                              "Use Intersect"),
                                             ),
                                      description="Boolean Operation",
                                      default="UNION")

    create_slice: bpy.props.BoolProperty(name="Slice", default=False)

    stop_calc: bpy.props.BoolProperty(name="Stop", default=False)
    wire: bpy.props.BoolProperty(name="Wire", default=False)
    preview_curve: bpy.props.BoolProperty(name="Curve", default=False)

    offset: bpy.props.FloatProperty(
        name="Bevel Radius", default=0.05, min=0.00002, max=1000.0, step=1, subtype='DISTANCE')
    twist_smooth: bpy.props.IntProperty(
        name="Pipe Twist Smooth", default=64, min=0, max=5000)
    mean_tilt: bpy.props.FloatProperty(
        name="Mean Tilt", default=math.pi / 4, min=-6.28, max=6.28, step=10, subtype='ANGLE')

    # refine
    refine_accuracy: bpy.props.IntProperty(
        name="Accuracy", default=64, min=1, max=1024)
    refine: bpy.props.BoolProperty(name="Refine", default=True)
    refine_res: bpy.props.IntProperty(
        name="Pipe Segments", default=4, min=0, max=30)
    refine_type: bpy.props.EnumProperty(name="Refine Type",
                                        items=(("DIST", "Dist", "Use Distantion"),
                                               ("COUNT", "Count", "Use Conunt"),
                                               ("AUTO", "Original",
                                                "Use Original Conunts"),
                                               ),
                                        description="Refine Type",
                                        default="AUTO")

    refine_count: bpy.props.IntProperty(
        name="Count", default=50, min=4, max=5000)
    refine_dist: bpy.props.FloatProperty(
        name="Dist", default=0.08, min=0.001, max=1000.0, subtype='DISTANCE')
    refine_shift: bpy.props.FloatProperty(
        name="Shift", default=0.0, min=-1000, max=1000.0, subtype='DISTANCE')
    refine_multiply: bpy.props.FloatProperty(
        name="Multiply", default=1.0, min=0.001, max=1000.0)

    # bevel
    bevel_profile: bpy.props.FloatProperty(
        name="Bevel Profile", default=0.5, min=0, max=1.0)
    bevel_segments: bpy.props.IntProperty(
        name="Bevel Segments", default=10, min=0, max=2000)
    bevel_corner: bpy.props.FloatProperty(
        name="Bevel Corner", default=1.0, min=0, max=1)
    corner: bpy.props.FloatProperty(
        name="Corner Profile", default=1.0, min=0.0, max=1.0)
    abs_size: bpy.props.BoolProperty(name="Absolute size", default=False)
    corner_size: bpy.props.FloatProperty(
        name="Corner Size", default=1.0, min=0.001, max=1.0, step=10)
    corner_dist: bpy.props.FloatProperty(
        name="Corner Radius", default=0.05, min=0.001, max=1000.0, step=1, subtype='DISTANCE')
    fix_outside: bpy.props.BoolProperty(
        name="Fix Outside Corner", default=True)

    # patch
    remove_doubles: bpy.props.FloatProperty(
        name="Remove Doubles", default=0.001, min=0.0, max=1.0, step=1, subtype='DISTANCE')
    subdivide: bpy.props.IntProperty(
        name="Subdivide Patch", default=0, min=0, max=5000)
    smooth: bpy.props.IntProperty(
        name="Smooth Patch", default=0, min=0, max=5000)
    factor: bpy.props.FloatProperty(
        name="Smooth Factor", default=0.5, min=0.0, max=1.0, step=1)
    simplify: bpy.props.FloatProperty(
        name="Simplify", default=0.0, min=0.0, max=180.0, step=1, subtype="ANGLE")

    # сохранение настроек
    save_settings: bpy.props.BoolProperty(name="Save settings", default=True)

    # Subsurf
    subdiv_a: bpy.props.IntProperty(name="Subdiv A", default=0, min=0, max=6)
    subdiv_b: bpy.props.IntProperty(name="Subdiv B", default=0, min=0, max=6)

    # data_transfer
    transfer: bpy.props.BoolProperty(name="Transfer Normals", default=True)
    transfer_factor: bpy.props.FloatProperty(
        name="Transfer Factor", default=1.0, min=0.0, max=1.0, step=1)
    triangulate: bpy.props.BoolProperty(name="Split NGon", default=False)
    method: bpy.props.EnumProperty(name="Method",
                                   items=(("BEAUTY", "BEAUTY", "Use BEAUTY"),
                                          ("CLIP", "CLIP", "Use CLIP")),
                                   description="Method for splitting the polygons into triangles",
                                   default="BEAUTY")

    density_on: bpy.props.BoolProperty(
        name="Density on/off", default=True)
    density: bpy.props.IntProperty(
        name="Density", default=4, min=0, max=30)

    wire_pre = False
    create_slice_pre = False
    offset_pre = 0.05

    obj_name = ""
    bool_name = ""
    bool_index = -1
    src_subsrf_index = -1
    bool_subsrf_index = -1
    edit_mode = False

    def execute(self, context):
        if self.density_on:
            self.refine_res = self.density
            circle_sides = 4 + 2 * self.density
            circle_length = 2 * math.pi * self.offset
            self.remove_doubles = (circle_length / circle_sides) / 2

            self.refine = True
            self.refine_type = "DIST"
            self.refine_dist = (circle_length / circle_sides) / 2
            self.bevel_segments = int(circle_sides / 2)

        # исходный объект
        src_obj = context.active_object
        # bool_obj = src_obj.modifiers[self.bool_index].object

        # Включаем и выключаем сетку
        src_obj.show_wire = self.wire
        src_obj.show_all_edges = self.wire
        # останавливаем выполнение скрипта
        if self.stop_calc:
            return {'FINISHED'}

        if not self.edit_mode:
            # подготавливаем объект и получаем curve на местах пересечения
            curve, bool_obj, transfer_obj, slice_obj = prepare_in_obj(
                self, context, src_obj)
        else:
            curve, bool_obj, transfer_obj = prepare_in_edit(
                self, context, src_obj)

        for spline in curve.data.splines:
            pipe, guide = create_pipe(self, context, curve)
            # Удаляем сплайн
            curve.data.splines.remove(spline)
            inside_vertices = find_inside(pipe, guide, self.offset)

            fail = fix_corner(self, pipe, inside_vertices,
                              sides=4 + 2 * self.refine_res)

            if self.preview_curve or fail:
                pipe.show_wire = True
                pipe.show_all_edges = True
                pipe.show_in_front = True
                guide.display_type = 'BOUNDS'
                curve.display_type = 'BOUNDS'
                pipe.select_set(True)
                bpy.ops.object.shade_flat()
                if fail:
                    self.report({'INFO'}, "self-Intersect")
                return {'FINISHED'}

            # Применяем boolean
            do_boolean(context, pipe, src_obj)
            # Выравниваем вершины
            align(src_obj, pipe, guide, sides=4 + 2 * self.refine_res)
            if self.create_slice:
                # bpy.ops.object.mode_set(mode='OBJECT')
                # Применяем boolean
                context.view_layer.objects.active = slice_obj
                bpy.ops.object.mode_set(mode='OBJECT')
                # return {"FINISHED"}
                do_boolean(context, pipe, slice_obj)
                # Выравниваем вершины
                align(slice_obj, pipe, guide, sides=4 + 2 * self.refine_res)
                context.view_layer.objects.active = src_obj

            pipe.select_set(True)
            guide.select_set(True)
            bpy.ops.object.delete(use_global=False)

        bpy.ops.object.mode_set(mode='EDIT')
        # Режим вершин
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_less(use_face_step=True)
        bpy.ops.object.vertex_group_assign()
        # return
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.remove_doubles(threshold=0.0, use_unselected=False)

        # чистим от лишних ребер и точек
        bpy.ops.mesh.select_more(use_face_step=False)
        bpy.ops.mesh.select_all(action='INVERT')
        # удаляем лишние вершины
        bpy.ops.mesh.edge_collapse()
        bpy.ops.mesh.dissolve_verts(
            use_face_split=True, use_boundary_tear=False)

        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more(use_face_step=True)
        bpy.ops.mesh.hide(unselected=True)

        bpy.ops.mesh.select_face_by_sides(number=3, type='EQUAL', extend=False)
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.edge_collapse()

        bpy.ops.mesh.reveal()

        # выворачиваем нормали
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.mesh.select_all(action='DESELECT')

        if self.transfer:
            bpy.context.tool_settings.vertex_group_weight = self.transfer_factor
            src_obj.vertex_groups.active_index = 0
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more(use_face_step=True)
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.select_all(action='DESELECT')

            src_obj.vertex_groups.active_index = 1
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more(use_face_step=True)
            bpy.ops.object.vertex_group_assign()

            bpy.context.tool_settings.vertex_group_weight = 1.0

            bpy.ops.object.mode_set(mode='OBJECT')

            data_transfer_modifier = src_obj.modifiers.new(
                name="Boolean Bevel Custom Normals", type="DATA_TRANSFER")
            data_transfer_modifier.show_viewport = False
            data_transfer_modifier.object = transfer_obj
            data_transfer_modifier.use_loop_data = True
            data_transfer_modifier.data_types_loops = {"CUSTOM_NORMAL"}
            data_transfer_modifier.loop_mapping = "POLYINTERP_NEAREST"
            data_transfer_modifier.vertex_group = src_obj.vertex_groups[0].name

            apply_name_1 = data_transfer_modifier.name
            data_transfer_modifier = src_obj.modifiers.new(
                name="Boolean Bevel Custom Normals", type="DATA_TRANSFER")
            data_transfer_modifier.show_viewport = False
            data_transfer_modifier.object = bool_obj
            data_transfer_modifier.use_loop_data = True
            data_transfer_modifier.data_types_loops = {"CUSTOM_NORMAL"}
            data_transfer_modifier.loop_mapping = "POLYINTERP_NEAREST"
            data_transfer_modifier.vertex_group = src_obj.vertex_groups[1].name

            apply_name_2 = data_transfer_modifier.name

            src_obj.vertex_groups.active_index = 2

        if self.triangulate:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more(use_face_step=True)
            bpy.ops.mesh.select_more(use_face_step=True)
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.quads_convert_to_tris(
                quad_method='BEAUTY', ngon_method=self.method)
            bpy.ops.mesh.select_all(action='DESELECT')

        do_bevel(self)
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.create_slice:
            context.view_layer.objects.active = slice_obj
            bpy.ops.object.mode_set(mode='EDIT')
            # Режим вершин
            bpy.ops.mesh.select_mode(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.select_less(use_face_step=True)
            bpy.ops.object.vertex_group_assign()

            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.remove_doubles(threshold=0.0, use_unselected=False)

            # чистим от лишних ребер и точек
            bpy.ops.mesh.select_more(use_face_step=False)
            bpy.ops.mesh.select_all(action='INVERT')
            # удаляем лишние вершины
            bpy.ops.mesh.edge_collapse()
            bpy.ops.mesh.dissolve_verts(
                use_face_split=True, use_boundary_tear=False)

            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more(use_face_step=True)
            bpy.ops.mesh.hide(unselected=True)

            bpy.ops.mesh.select_face_by_sides(
                number=3, type='EQUAL', extend=False)
            bpy.ops.object.vertex_group_deselect()
            bpy.ops.mesh.edge_collapse()

            bpy.ops.mesh.reveal()

            # выворачиваем нормали
            # bpy.ops.mesh.select_all(action='SELECT')
            # bpy.ops.mesh.normals_make_consistent(inside=False)

            bpy.ops.mesh.select_all(action='DESELECT')

            if self.transfer:
                bpy.context.tool_settings.vertex_group_weight = self.transfer_factor
                slice_obj.vertex_groups.active_index = 0
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_more(use_face_step=True)
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')

                slice_obj.vertex_groups.active_index = 1
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_more(use_face_step=True)
                bpy.ops.object.vertex_group_assign()

                bpy.context.tool_settings.vertex_group_weight = 1.0

                bpy.ops.object.mode_set(mode='OBJECT')

                data_transfer_modifier = slice_obj.modifiers.new(
                    name="Boolean Bevel Custom Normals", type="DATA_TRANSFER")
                data_transfer_modifier.show_viewport = False
                data_transfer_modifier.object = transfer_obj
                data_transfer_modifier.use_loop_data = True
                data_transfer_modifier.data_types_loops = {"CUSTOM_NORMAL"}
                data_transfer_modifier.loop_mapping = "POLYINTERP_NEAREST"
                data_transfer_modifier.vertex_group = slice_obj.vertex_groups[0].name

                apply_name_1 = data_transfer_modifier.name
                data_transfer_modifier = slice_obj.modifiers.new(
                    name="Boolean Bevel Custom Normals", type="DATA_TRANSFER")
                data_transfer_modifier.show_viewport = False
                data_transfer_modifier.object = bool_obj
                data_transfer_modifier.use_loop_data = True
                data_transfer_modifier.data_types_loops = {"CUSTOM_NORMAL"}
                data_transfer_modifier.loop_mapping = "POLYINTERP_NEAREST"
                data_transfer_modifier.vertex_group = slice_obj.vertex_groups[1].name

                apply_name_2 = data_transfer_modifier.name

                slice_obj.vertex_groups.active_index = 2

            if self.triangulate:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.select_more(use_face_step=True)
                bpy.ops.mesh.select_more(use_face_step=True)
                bpy.ops.object.vertex_group_deselect()
                bpy.ops.mesh.quads_convert_to_tris(
                    quad_method='BEAUTY', ngon_method=self.method)
                bpy.ops.mesh.select_all(action='DESELECT')

            do_bevel(self)

        # context.view_layer.objects.active = src_obj
        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = src_obj

        if self.transfer:
            if self.operation == "DIFFERENCE":
                vert = bool_obj.data
                vert.flip_normals()
                vert.update()

            bpy.ops.object.modifier_apply(
                modifier=apply_name_1)
            bpy.ops.object.modifier_apply(
                modifier=apply_name_2)

            # apply_modifiers(src_obj.modifiers, src_obj)

            if self.operation == "DIFFERENCE":
                vert = bool_obj.data
                vert.flip_normals()
                vert.update()
            if self.create_slice:
                context.view_layer.objects.active = slice_obj
                # включаем автосглаживание
                context.object.data.use_auto_smooth = True
                # угол авто скглаживания
                context.object.data.auto_smooth_angle = 3.14159
                bpy.ops.object.modifier_apply(
                    modifier=apply_name_1)
                bpy.ops.object.modifier_apply(
                    modifier=apply_name_2)
                context.view_layer.objects.active = src_obj
            bpy.data.objects['BAB_TRANSFER'].select_set(True)

        curve.select_set(True)

        bpy.ops.object.delete(use_global=False)

        bab_props = context.window_manager.bab_props
        if self.save_settings:
            bab_props.wire = self.wire
            bab_props.offset = self.offset
            bab_props.create_slice = self.create_slice
        else:
            bab_props.wire = self.wire_pre
            bab_props.offset = self.offset_pre
            bab_props.create_slice = self.create_slice_pre
        return {'FINISHED'}


class BAB_OP_Slice(bpy.types.Operator):
    """Add Slice object"""
    bl_idname = "bab.slice"
    bl_label = "Create Slice"

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        obj = context.active_object
        bool_index = get_boolean_index(obj)

        if bool_index == -1:
            self.report({'ERROR'}, "Boolean not found")
            return {'FINISHED'}
        obj.modifiers[bool_index].operation = "DIFFERENCE"

        # выделяем объект
        obj.select_set(True)
        # Делаем его копию
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
        # Снимаем выделение
        obj.select_set(False)
        # Добавляем переменную
        slice_obj = context.active_object
        # Переминовываем для удобства
        slice_obj.name = obj.name + '_Slice'
        slice_obj.modifiers[bool_index].operation = "INTERSECT"
        return {'FINISHED'}


class BAB_OP_Create_Pipe(bpy.types.Operator):
    """Create pipe from active object"""
    bl_idname = "bab.create_pipe"
    bl_label = "Create Pipe"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    @classmethod
    def poll(cls, context):
        return context.active_object and len(context.selected_objects) < 2

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, "wire")
        row.prop(self, "stop_calc")

        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, "save_settings")
        row.prop(self, "in_front")

        box = layout.box()
        box.label(text="Pipe:")

        box.prop(self, "density_on")
        if self.density_on:
            box.prop(self, "density")

        box.prop(self, "offset")
        box.prop(self, "is_band")
        box.prop(self, "cap")

        box.prop(self, "refine_res")
        box.prop(self, "mean_tilt")
        box.prop(self, "twist_smooth")

        box = layout.box()
        box.label(text="Refine:")
        box.prop(self, "refine")

        box.prop(self, "refine_type")
        if self.refine_type == "DIST":
            box.prop(self, "refine_dist")

        if self.refine_type == "COUNT":
            box.prop(self, "refine_count")

        box.prop(self, "refine_multiply")
        box.prop(self, "refine_shift")
        box.prop(self, "refine_accuracy")

        box = layout.box()
        box.label(text="Self-intersect:")
        box.prop(self, "fix_corner")
        box.prop(self, "corner")

        box.prop(self, "fix_outside")

        box.prop(self, "abs_size")

        if self.abs_size:
            box.prop(self, "corner_dist")
        else:
            box.prop(self, "corner_size")

        box = layout.box()
        box.label(text="Patch Parameters:")
        box.prop(self, "smooth")
        box.prop(self, "factor")
        box.prop(self, "remove_doubles")
        box.prop(self, "subdivide")
        box.prop(self, "simplify")

    def invoke(self, context, event):
        if DEBUG:
            time_start = time.time()

        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.stop_calc = bab_props.pipe_stop
        self.wire = bab_props.pipe_wire
        self.offset = bab_props.pipe_radius

        self.wire_pre = bab_props.pipe_wire
        self.offset_pre = bab_props.pipe_radius

        if DEBUG:
            print("invoke: %.4f sec\n" % (time.time() - time_start))
        return self.execute(context)

    stop_calc: bpy.props.BoolProperty(name="Stop calculations", default=False)
    wire: bpy.props.BoolProperty(name="Wire", default=False)

    offset: bpy.props.FloatProperty(
        name="Pipe Radius", default=0.05, min=0.00002, max=1000.0, step=1, subtype='DISTANCE')
    twist_smooth: bpy.props.IntProperty(
        name="Pipe Twist Smooth", default=64, min=0, max=5000)
    mean_tilt: bpy.props.FloatProperty(
        name="Mean Tilt", default=math.pi / 4, min=-6.28, max=6.28, step=10, subtype='ANGLE')
    is_band: bpy.props.BoolProperty(name="Band", default=False)

    # refine
    refine_accuracy: bpy.props.IntProperty(
        name="Accuracy", default=64, min=1, max=1024)
    refine: bpy.props.BoolProperty(name="Refine", default=True)
    refine_res: bpy.props.IntProperty(
        name="Pipe Segments", default=4, min=0, max=30)
    refine_type: bpy.props.EnumProperty(name="Refine Type",
                                        items=(("DIST", "Dist", "Use Distantion"),
                                               ("COUNT", "Count", "Use Conunt"),
                                               ("AUTO", "Original",
                                                "Use Original Conunts"),
                                               ),
                                        description="Refine Type",
                                        default="DIST")

    refine_count: bpy.props.IntProperty(
        name="Count", default=50, min=4, max=5000)
    refine_dist: bpy.props.FloatProperty(
        name="Dist", default=0.08, min=0.001, max=1000.0, subtype='DISTANCE')
    refine_shift: bpy.props.FloatProperty(
        name="Shift", default=0.0, min=-1000, max=1000.0, subtype='DISTANCE')
    refine_multiply: bpy.props.FloatProperty(
        name="Multiply", default=1.0, min=0.001, max=1000.0)

    cap: bpy.props.EnumProperty(name="Cap Fill Type",
                                items=(("NOTHING", "Nothing", "Don’t fill at all"),
                                       ("NGON", "Ngon", "Use ngons"),
                                       #  ("TRIFAN", "Triangle Fan", "Use triangle fans"),
                                       ),
                                description="Cap Fill Type",
                                default="NGON")

    # fixes
    fix_corner: bpy.props.BoolProperty(name="Fix Corners", default=True)
    corner: bpy.props.FloatProperty(
        name="Corner Profile", default=1.0, min=0.0, max=1.0)
    abs_size: bpy.props.BoolProperty(name="Absolute size", default=False)
    corner_size: bpy.props.FloatProperty(
        name="Corner Size", default=1.0, min=0.001, max=1.0, step=10)
    corner_dist: bpy.props.FloatProperty(
        name="Corner Radius", default=0.05, min=0.001, max=1000.0, step=1, subtype='DISTANCE')
    fix_outside: bpy.props.BoolProperty(
        name="Fix Outside Corner", default=True)

    # patch
    remove_doubles: bpy.props.FloatProperty(
        name="Remove Doubles", default=0.001, min=0.0, max=1.0, step=1, subtype='DISTANCE')
    subdivide: bpy.props.IntProperty(
        name="Subdivide Patch", default=0, min=0, max=5000)
    smooth: bpy.props.IntProperty(
        name="Smooth Patch", default=0, min=0, max=5000)
    factor: bpy.props.FloatProperty(
        name="Smooth Factor", default=0.5, min=0.0, max=1.0, step=1)
    simplify: bpy.props.FloatProperty(
        name="Simplify", default=0.0, min=0.0, max=180.0, step=1, subtype="ANGLE")

    # сохранение настроек
    save_settings: bpy.props.BoolProperty(name="Save settings", default=True)

    in_front: bpy.props.BoolProperty(name="Show in Front", default=True)

    density_on: bpy.props.BoolProperty(
        name="Density on/off", default=True)
    density: bpy.props.IntProperty(
        name="Density", default=4, min=0, max=30)

    wire_pre = False
    offset_pre = 0.05

    def execute(self, context):

        if self.density_on:
            self.refine_res = self.density
            circle_sides = 4 + 2 * self.density
            circle_length = 2 * math.pi * self.offset
            self.remove_doubles = (circle_length / circle_sides) / 2

            self.refine = True
            self.refine_type = "DIST"
            self.refine_dist = (circle_length / circle_sides) / 2

        curve = context.active_object

        if self.stop_calc:
            return {'FINISHED'}
        bool_index = get_boolean_index(curve)

        is_editmode = curve.data.is_editmode
        if bool_index > -1 and not is_editmode:
            # выделяем объект
            curve.select_set(True)
            # Делаем его копию
            bpy.ops.object.duplicate_move(
                OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
            # Снимаем выделение
            curve.select_set(False)

            # Добавляем переменную
            temp_obj = context.active_object
            temp_obj.select_set(False)
            # Переминовываем для удобства
            temp_obj.name = 'Temp_OBJ'

            # Скрываем все модификаторы
            temp_obj.modifiers.foreach_set(
                'show_viewport', [False] * len(temp_obj.modifiers))

            # Создаем группу вершин
            temp_obj.vertex_groups.new(name=temp_obj.name)
            # Добавляем в нее все вершины
            temp_obj.vertex_groups.active.add(
                range(len(temp_obj.data.vertices)), 1, 'ADD')

            # Применяем модификаторы до boolean
            solver = temp_obj.modifiers[-1].solver
            apply_modifiers(temp_obj.modifiers, temp_obj)

            # Заходим в режим редактирования
            bpy.ops.object.mode_set(mode='EDIT')
            # Режим вершин
            # Метод 1
            bpy.ops.mesh.select_mode(type='VERT')
            # Выделяем вершины без групп
            bpy.ops.mesh.select_ungrouped(extend=False)
            bpy.ops.mesh.select_mode(type='FACE')
            if solver == "EXACT":
                bpy.ops.mesh.select_more()
            bpy.ops.mesh.region_to_loop()
            # bpy.ops.mesh.select_mode(type='EDGE')

        if is_editmode or bool_index > -1:
            bpy.ops.mesh.duplicate_move()
            # bpy.ops.mesh.edge_face_add()
            # Удаляем дубли вершин
            if self.remove_doubles:
                bpy.ops.mesh.remove_doubles(
                    threshold=self.remove_doubles, use_unselected=False)

            if self.simplify:
                bpy.ops.mesh.dissolve_limited(
                    angle_limit=self.simplify, use_dissolve_boundaries=False)
            # Подразделяем, если нужно
            if self.subdivide:
                bpy.ops.mesh.subdivide(
                    number_cuts=self.subdivide, smoothness=0.0)
            # Сглаживаем, если нужно
            if self.smooth:
                bpy.ops.mesh.vertices_smooth(
                    factor=self.factor, repeat=self.smooth, xaxis=True, yaxis=True, zaxis=True)
            bpy.ops.mesh.separate(type='SELECTED')

            bpy.ops.object.mode_set(mode='OBJECT')
            curve.select_set(False)
            # curve.display_type = 'BOUNDS'
            curve = context.selected_objects[0]
            curve.select_set(False)

            if bool_index > -1 and not is_editmode:
                # Удаление
                temp_obj.select_set(True)
                bpy.ops.object.delete(use_global=False)

            context.view_layer.objects.active = curve

        if curve.type == "CURVE":
            curve.select_set(True)
            bpy.ops.object.convert(target='MESH', keep_original=False)

        curve.select_set(True)
        bpy.ops.object.convert(target='CURVE', keep_original=False)
        curve.select_set(False)
        # curve.data.twist_smooth = self.twist_smooth

        for spline in curve.data.splines:
            pipe, new_curve = create_pipe(
                self, context, curve, self.is_band, self.cap)
            curve.data.splines.remove(spline)

            if self.fix_corner:
                indexs = find_inside(pipe, new_curve, self.offset)
                if self.is_band:
                    sides = 2
                else:
                    sides = sides = 4 + 2 * self.refine_res

                if fix_corner(self, pipe, indexs, sides=sides):
                    self.report({'INFO'}, "Error")

            # Удаление
            new_curve.select_set(True)
            bpy.ops.object.delete(use_global=False)

            pipe.select_set(True)
            bpy.ops.object.shade_flat()
            pipe.select_set(False)
            pipe.show_in_front = self.in_front

            if self.wire:
                pipe.show_wire = True

        curve.select_set(True)
        # pipe.select_set(True)
        bpy.ops.object.delete(use_global=False)

        bab_props = context.window_manager.bab_props
        if self.save_settings:
            bab_props.pipe_wire = self.wire
            bab_props.pipe_radius = self.offset
        else:
            bab_props.pipe_wire = self.wire_pre
            bab_props.pipe_radius = self.offset_pre

        return {'FINISHED'}


class BAB_OP_Apply_Modifiers(bpy.types.Operator):
    """Aplly modifiers on active object"""
    bl_idname = "bab.apply_modifiers"
    bl_label = "Apply Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "skip_boolean")

    skip_boolean: bpy.props.BoolProperty(name="Skip boolean", default=True)

    def invoke(self, context, event):
        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.skip_boolean = bab_props.apply_all
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        # bool_index = [modifier.type for modifier in obj.modifiers].index("BOOLEAN")
        bool_index = get_boolean_index(obj)
        if self.skip_boolean and bool_index > -1:
            apply_modifiers(obj.modifiers[:bool_index], obj)
        else:
            apply_modifiers(obj.modifiers, obj)
        bab_props = context.window_manager.bab_props
        bab_props.apply_all = self.skip_boolean
        return {'FINISHED'}


class BAB_OP_Remove_Modifiers(bpy.types.Operator):
    """Remove modifiers on active object"""
    bl_idname = "bab.remove_modifiers"
    bl_label = "Remove Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "skip_boolean")

    skip_boolean: bpy.props.BoolProperty(name="Skip boolean", default=True)

    def invoke(self, context, event):
        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.skip_boolean = bab_props.remove_all
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object

        bool_index = get_boolean_index(obj)
        if self.skip_boolean and bool_index > -1:
            remove_modifiers(obj.modifiers[:bool_index], obj)
        else:
            remove_modifiers(obj.modifiers, obj)

        bab_props = context.window_manager.bab_props
        bab_props.remove_all = self.skip_boolean
        return {'FINISHED'}


class BAB_OP_Hide_Modifiers(bpy.types.Operator):
    """Hide modifiers on active object"""
    bl_idname = "bab.hide_modifiers"
    bl_label = "Show/Hide Modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "hide")

    hide: bpy.props.BoolProperty(name="Show modifiers", default=True)

    def invoke(self, context, event):
        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.hide = bab_props.hide
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        obj.modifiers.foreach_set(
            "show_viewport", [self.hide] * len(obj.modifiers))
        obj.data.update()

        bab_props = context.window_manager.bab_props
        bab_props.hide = self.hide
        return {'FINISHED'}


class BAB_OP_Visibility(bpy.types.Operator):
    """Change visibility on selected objects"""
    bl_idname = "bab.visibility"
    bl_label = "Apply"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "show_render")
        box.prop(self, "display_as")

    show_render: bpy.props.BoolProperty(name="Show in render", default=False)
    display_as: bpy.props.EnumProperty(name="Display as",
                                       items=(("BOUNDS", "Bounds", "On visibility"),
                                              ("WIRE", "Wire", "Off visibility"),
                                              ("SOLID", "Solid", "Off visibility"),
                                              ("TEXTURED", "Textured",
                                               "Off visibility"),
                                              ),
                                       description="Display as",
                                       default="TEXTURED")

    def invoke(self, context, event):
        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.show_render = bab_props.show_render
        self.display_as = bab_props.display_as
        return self.execute(context)

    def execute(self, context):
        for obj in context.selected_objects:
            obj.display_type = self.display_as
            obj.hide_render = not self.show_render

        bab_props = context.window_manager.bab_props
        bab_props.show_render = self.show_render
        bab_props.display_as = self.display_as
        return {'FINISHED'}


class BAB_OP_Remove3dLines(bpy.types.Operator):
    """Remove 3d lines"""
    bl_idname = "bab.remove_3d_lines"
    bl_label = "Remove 3d lines"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bab_props = context.window_manager.bab_props
        if bab_props.handlers:
            erase_3d_lines(handlers=bab_props.handlers)
        return {'FINISHED'}


class BAB_OP_Symmetrize(bpy.types.Operator):
    """Symmetrize active object"""
    bl_idname = "bab.symmetrize"
    bl_label = "Symmetrize"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, "axis")

        box.prop(self, "flip_direction")
        box.prop(self, "merge_threshold")

    axis: bpy.props.EnumProperty(name="Axis",
                                 items=(("X", "X", "Use x axis"),
                                        ("Y", "Y", "Use y axis"),
                                        ("Z", "Z", "Use z axis"),
                                        ),
                                 description="Axis",
                                 default="X")

    flip_direction: bpy.props.BoolProperty(
        name="Flip Direction", default=False)

    merge_threshold: bpy.props.FloatProperty(
        name="Merge Dist", default=0.001, min=0.0, max=1.0, step=1, subtype='DISTANCE')

    def invoke(self, context, event):
        # Меняем значения
        bab_props = context.window_manager.bab_props
        self.axis = bab_props.axis
        self.flip_direction = bab_props.flip_direction
        self.merge_threshold = bab_props.merge_threshold
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        # Удаляем группы вершин
        if obj.vertex_groups:
            obj.vertex_groups.clear()

        # выделяем объект
        obj.select_set(True)
        # Делаем его копию
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
        # Снимаем выделение
        obj.select_set(False)
        # Добавляем переменную
        transfer_obj = context.active_object
        # Переминовываем для удобства
        transfer_obj.name = 'BAB_TRANSFER'

        # Меняем отображение для удобства
        transfer_obj.display_type = 'BOUNDS'
        # Меняем shading объектов
        bpy.ops.object.shade_smooth()
        # Снимаем выделение
        transfer_obj.select_set(False)
        # делаем активным исходный объект
        context.view_layer.objects.active = obj
        obj.select_set(True)

        modifier = obj.modifiers.new(name="BAB_Mirror", type="MIRROR")
        modifier.show_viewport = False
        modifier.use_mirror_merge = True
        modifier.use_mirror_vertex_groups = False
        modifier.merge_threshold = self.merge_threshold

        modifier.use_bisect_axis = [True, True, True]
        modifier.use_bisect_flip_axis = [self.flip_direction] * 3
        if self.axis == 'X':
            modifier.use_axis = [True, False, False]
        elif self.axis == 'Y':
            modifier.use_axis = [False, True, False]
        else:
            modifier.use_axis = [False, False, True]

        bpy.ops.object.modifier_apply(modifier=modifier.name)

        if self.axis == 'X':
            indexs = [v.index for v in obj.data.vertices if v.co.x == 0.0]
        elif self.axis == 'Y':
            indexs = [v.index for v in obj.data.vertices if v.co.y == 0.0]
        else:
            indexs = [v.index for v in obj.data.vertices if v.co.z == 0.0]

        # Создаем группу вершин
        obj.vertex_groups.new(name="transfer")

        if indexs:
            # Добавляем в нее indexs
            obj.vertex_groups.active.add(indexs, 1, 'ADD')

            data_transfer_modifier = obj.modifiers.new(
                name="BAB_Transfer", type="DATA_TRANSFER")
            data_transfer_modifier.show_viewport = False
            data_transfer_modifier.object = transfer_obj
            data_transfer_modifier.use_loop_data = True
            data_transfer_modifier.data_types_loops = {"CUSTOM_NORMAL"}
            data_transfer_modifier.loop_mapping = "POLYINTERP_NEAREST"
            data_transfer_modifier.vertex_group = 'transfer'
            bpy.ops.object.modifier_apply(
                modifier=data_transfer_modifier.name)

        obj.select_set(False)
        transfer_obj.select_set(True)

        bpy.ops.object.delete(use_global=False)
        obj.select_set(True)

        bab_props = context.window_manager.bab_props
        bab_props.axis = self.axis
        bab_props.flip_direction = self.flip_direction
        bab_props.merge_threshold = self.merge_threshold
        return {'FINISHED'}


# functions


def create_pipe(self, context, src_curve, is_band=False, cap="NGON"):
    if DEBUG:
        time_start = time.time()

    # создаем новую кривую
    curve_data = bpy.data.curves.new('BAB_PIPE', type='CURVE')

    # src_curve.data.twist_smooth = self.twist_smooth
    # создаем новый сплайн
    spline = curve_data.splines.new("BEZIER")
    spline.use_cyclic_u = src_curve.data.splines[0].use_cyclic_u

    if self.refine:
        # узнаем длинну сплайна
        spline_length = src_curve.data.splines[0].calc_length()

        if self.refine_type == "DIST":
            refine_count = round(
                (spline_length / self.refine_dist) * self.refine_multiply)
        elif self.refine_type == "AUTO":
            refine_count = round(
                len(src_curve.data.splines[0].points) * self.refine_multiply)
        else:
            refine_count = round(self.refine_count * self.refine_multiply)

        if refine_count < 4:
            refine_count = 4
        src_curve.data.resolution_u = self.refine_accuracy
        # добавляем в него нужное количеств вершин
        # spline.points.add(refine_count-1)
        spline.bezier_points.add(refine_count - 1)

        # Создаем новый массив координат для вершин
        points_co = np.zeros(refine_count * 3)
        # заполяем x с равномерным смещением
        if spline.use_cyclic_u:
            points_co[::3] = np.linspace(
                0 + self.refine_shift, spline_length + self.refine_shift, refine_count, endpoint=False)
        else:
            if self.refine_shift == 0.0:
                refine_shift = 0.001
                # refine_shift = 0.0
            else:
                refine_shift = self.refine_shift
            points_co[::3] = np.linspace(
                0 - refine_shift, spline_length + refine_shift, refine_count, endpoint=True)
        # заменяем x координаты
        # spline.points.foreach_set('co', points_co)
        spline.bezier_points.foreach_set('co', points_co)
        spline.bezier_points.foreach_set('handle_left', points_co)
        spline.bezier_points.foreach_set('handle_right', points_co)

        spline.bezier_points[0].handle_left = spline.bezier_points[1].co
        spline.bezier_points[0].handle_right = spline.bezier_points[1].co

        spline.bezier_points[-1].handle_left = spline.bezier_points[-2].co
        spline.bezier_points[-1].handle_right = spline.bezier_points[-2].co
    else:
        # добавляем в него нужное количеств вершин
        # spline.points.add(len(src_curve.data.splines[0].points)-1)
        spline.bezier_points.add(len(src_curve.data.splines[0].points) - 1)
        # Создаем новый массив координат для вершин
        points_co = np.empty(len(src_curve.data.splines[0].points) * 4)
        src_curve.data.splines[0].points.foreach_get('co', points_co)

        points_co1 = np.empty(len(src_curve.data.splines[0].points) * 3)

        points_co1[0::3] = points_co[0::4]
        points_co1[1::3] = points_co[1::4]
        points_co1[2::3] = points_co[2::4]

        # заменяем x координаты
        # spline.points.foreach_set('co', points_co)
        spline.bezier_points.foreach_set('co', points_co1)

        spline.bezier_points.foreach_set('co', points_co1)
        spline.bezier_points.foreach_set('handle_left', points_co1)
        spline.bezier_points.foreach_set('handle_right', points_co1)

        spline.bezier_points[0].handle_left = spline.bezier_points[1].co
        spline.bezier_points[0].handle_right = spline.bezier_points[1].co

        spline.bezier_points[-1].handle_left = spline.bezier_points[-2].co
        spline.bezier_points[-1].handle_right = spline.bezier_points[-2].co

    # spline.points.foreach_set('tilt', [self.mean_tilt] * len(spline.points))
    spline.bezier_points.foreach_set(
        'tilt', [self.mean_tilt] * len(spline.bezier_points))

    # spline.bezier_points.foreach_set('handle_left_type', [2] * len(spline.bezier_points))
    # spline.bezier_points.foreach_set('handle_right_type', [2] * len(spline.bezier_points))

    curve = bpy.data.objects.new('BAB_CURVE', curve_data)
    curve.matrix_world = src_curve.matrix_world
    context.collection.objects.link(curve)

    curve.select_set(True)
    context.view_layer.objects.active = curve

    if self.refine:
        curve_modifier = curve.modifiers.new(name="Refine", type='CURVE')
        curve_modifier.show_viewport = False
        curve_modifier.use_apply_on_spline = True
        curve_modifier.object = src_curve
        bpy.ops.object.modifier_apply(
            modifier=curve_modifier.name)

    # curve.show_wire = True
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.fill_mode = 'FULL'
    if is_band:
        curve_data.extrude = self.offset
    else:
        curve_data.bevel_depth = self.offset
    curve_data.bevel_resolution = self.refine_res
    curve_data.twist_smooth = self.twist_smooth
    # curve_data.twist_mode = "TANGENT"

    # конвертируем в mesh
    bpy.ops.object.convert(target='MESH', keep_original=True)
    curve.select_set(False)

    pipe = context.selected_objects[0]
    pipe.name = "BAB_PIPE"
    if not spline.use_cyclic_u and not is_band and cap != "NOTHING":
        context.view_layer.objects.active = pipe
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.edge_face_add()
        if cap == "TRIFAN":
            bpy.ops.mesh.poke()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
    pipe.select_set(False)

    # Создаем группы вершин
    pipe.vertex_groups.new(name="temp")
    pipe.vertex_groups.new(name="temp")
    pipe.vertex_groups.new(name="bevel")

    # Добавляем в нее все вершины
    pipe.vertex_groups.active.add(range(len(pipe.data.vertices)), 1, 'ADD')

    if DEBUG:
        print("create_pipe: %.4f sec\n" % (time.time() - time_start))
    return pipe, curve


def get_boolean_index(obj):
    """Find and return First Boolean modifer index"""
    if DEBUG:
        time_start = time.time()
    index = -1
    for i, modifier in enumerate(obj.modifiers):
        if modifier.type == "BOOLEAN":
            index = i
            break
    if DEBUG:
        print("get_boolean_index: %.4f sec\n" % (time.time() - time_start))
    return index


def get_subsurf_index(obj):
    """Find and return lastSubSurf modifer index"""
    if DEBUG:
        time_start = time.time()
    index = -1
    for i, modifier in enumerate(obj.modifiers):
        if modifier.type == "SUBSURF":
            index = i
    if DEBUG:
        print("get_subsurf_index: %.4f sec\n" % (time.time() - time_start))
    return index


def apply_modifiers(modifiers, obj):
    if DEBUG:
        time_start = time.time()
    for modifier in modifiers:
        try:
            bpy.ops.object.modifier_apply(
                modifier=modifier.name)
        except:
            obj.modifiers.remove(modifier)
    if DEBUG:
        print("apply_modifiers: %.4f sec\n" % (time.time() - time_start))


def remove_modifiers(modifiers, obj):
    if DEBUG:
        time_start = time.time()
    for modifier in modifiers:
        obj.modifiers.remove(modifier)
    if DEBUG:
        print("apply_modifiers: %.4f sec\n" % (time.time() - time_start))


def find_inside(obj, guide, radius):
    """Find verteces inside pipe"""
    if DEBUG:
        time_start = time.time()

    indexs = set()
    kd = create_tree(obj)
    print("Создание дерева: %.4f sec\n" % (time.time() - time_start))
    for point in guide.data.splines[0].bezier_points:
        indexs = indexs | {index for (co, index, dist) in kd.find_range(
            point.co, radius) if dist < radius - 0.01}

        # indexs = indexs | {index for (co, index, dist) in kd.find_range(point.co, radius-0.00001)}
    if DEBUG:
        print("find_inside: %.4f sec\n" % (time.time() - time_start))
    return indexs


def create_tree(obj):
    size = len(obj.data.vertices)
    kd = mathutils.kdtree.KDTree(size)
    for i, v in enumerate(obj.data.vertices):
        kd.insert(v.co, i)
    kd.balance()
    return kd


def fix_corner(self, obj, indexs, sides=12):
    """Try to fix corners"""
    if DEBUG:
        time_start = time.time()

    if not indexs:
        False

    if self.fix_outside:
        out_indexs = set()
        for i in indexs:
            loop_int = i // sides * sides
            out_indexs = out_indexs | {
                j for j in range(loop_int, loop_int + sides)}
        indexs = out_indexs

    while indexs:
        temp_index = indexs.pop()
        loop_int = temp_index - temp_index // sides * sides
        obj_indexs = [i for i in range(len(obj.data.vertices))]
        loop = obj_indexs[loop_int::sides]

        temp_index = loop.index(temp_index) + len(loop)

        cyclyc_loop = loop * 3

        left_index = temp_index - 1
        rigt_index = temp_index + 1

        while cyclyc_loop[left_index] in indexs:
            indexs.discard(cyclyc_loop[left_index])
            left_index -= 1

        while cyclyc_loop[rigt_index] in indexs:
            indexs.discard(cyclyc_loop[rigt_index])
            rigt_index += 1

        if len(cyclyc_loop[left_index:rigt_index]) >= len(loop):
            return True

        line_a1 = obj.data.vertices[cyclyc_loop[rigt_index]].co
        line_a2 = obj.data.vertices[cyclyc_loop[rigt_index + 1]].co

        line_b1 = obj.data.vertices[cyclyc_loop[left_index]].co
        line_b2 = obj.data.vertices[cyclyc_loop[left_index - 1]].co

        intesect_points = mathutils.geometry.intersect_line_line(
            line_a1, line_a2, line_b1, line_b2)

        if intesect_points:
            new_coord = (intesect_points[0] + intesect_points[0]) / 2
        else:
            return True

        dist1 = line_a1 - new_coord
        dist2 = line_b1 - new_coord

        if self.abs_size:
            corner_multiply1 = self.corner_dist
            corner_multiply2 = self.corner_dist

            if corner_multiply1 > dist2.length:
                corner_multiply1 = dist2.length
            if corner_multiply2 > dist1.length:
                corner_multiply2 = dist1.length

        else:
            corner_multiply1 = dist2.length * self.corner_size
            corner_multiply2 = dist1.length * self.corner_size

        knot1 = new_coord + dist2.normalized() * corner_multiply1
        knot2 = new_coord + dist1.normalized() * corner_multiply2

        # This is the correct method, but it doesn’t work as well as the wrong one.
        # handle1 = new_coord
        # handle2 = new_coord

        handle1 = (knot1 - line_b2).normalized() * \
                  self.corner * corner_multiply1 + knot1
        handle2 = (knot2 - line_a2).normalized() * \
                  self.corner * corner_multiply2 + knot2

        resolution = len(cyclyc_loop[left_index:rigt_index + 1])
        new_points = mathutils.geometry.interpolate_bezier(
            knot1, handle1, handle2, knot2, resolution)
        test = cyclyc_loop[left_index: rigt_index + 1]

        for i in range(1, resolution - 1):
            obj.data.vertices[test[i]].co = new_points[i]

    if DEBUG:
        print("fix_inside: %.4f sec\n" % (time.time() - time_start))

    return False


def do_boolean(context, curve_cut, obj):
    if DEBUG:
        time_start = time.time()
    curve_cut.display_type = 'BOUNDS'
    boolean_modifier = obj.modifiers.new(name="BooleanBevel", type='BOOLEAN')
    boolean_modifier.solver = "FAST"
    boolean_modifier.show_viewport = False
    boolean_modifier.object = curve_cut
    boolean_modifier.operation = "UNION"
    # boolean_modifier.double_threshold = 0.0
    # bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(
        modifier=boolean_modifier.name)
    if DEBUG:
        print("do_boolean: %.4f sec\n" % (time.time() - time_start))


def prepare_in_obj(self, context, src_obj):
    if DEBUG:
        time_start = time.time()
    # Снимаем выделение со всех объектов
    bpy.ops.object.select_all(action='DESELECT')
    # объект boolean
    bool_obj = src_obj.modifiers[self.bool_index].object
    # Режим отрисовки для boolean
    bool_obj.display_type = 'BOUNDS'

    if DEBUG:
        print("prepare_in_obj: %.4f sec\n" % (time.time() - time_start))

    # Удаляем группы вершин
    if src_obj.vertex_groups:
        src_obj.vertex_groups.clear()

    # Удаляем группы вершин
    if bool_obj.vertex_groups:
        bool_obj.vertex_groups.clear()

    # Скрываем все модификаторы
    src_obj.modifiers.foreach_set(
        'show_viewport', [False] * len(src_obj.modifiers))

    # Создаем группу вершин
    src_obj.vertex_groups.new(name=src_obj.name)
    # Добавляем в нее все вершины
    src_obj.vertex_groups.active.add(
        range(len(src_obj.data.vertices)), 1, 'ADD')

    # Меняем подразделение
    change_subsurf(src_obj, self.src_subsrf_index, self.subdiv_a)
    change_subsurf(bool_obj, self.bool_subsrf_index, self.subdiv_b)
    # Применяем модификаторы до boolean
    apply_modifiers(src_obj.modifiers[:self.bool_index], src_obj)

    if self.create_slice:

        # выделяем объект
        src_obj.select_set(True)
        # Делаем его копию
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
        # Снимаем выделение
        src_obj.select_set(False)
        # Добавляем переменную
        slice_obj = context.active_object
        # Переминовываем для удобства
        slice_obj.name = src_obj.name + 'SLICE'
        slice_obj.select_set(False)
        # делаем активным исходный объект
        context.view_layer.objects.active = src_obj
        # Меняем оперцию
        self.operation = "DIFFERENCE"
        slice_obj.modifiers[0].operation = "INTERSECT"

    else:
        slice_obj = False
    # Меняем оперцию
    src_obj.modifiers[0].operation = self.operation

    if self.transfer:
        # выделяем объект
        src_obj.select_set(True)
        # Делаем его копию
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
        # Снимаем выделение
        src_obj.select_set(False)
        # Добавляем переменную
        transfer_obj = context.active_object
        # Переминовываем для удобства
        transfer_obj.name = 'BAB_TRANSFER'
        # Меняем отображение для удобства
        transfer_obj.display_type = 'BOUNDS'

        bool_obj.select_set(True)
        # выделяем исходный объект
        src_obj.select_set(True)
        if self.create_slice:
            slice_obj.select_set(True)
        # Меняем shading объектов
        bpy.ops.object.shade_smooth()

        # Снимаем выделение
        transfer_obj.select_set(False)
        bool_obj.select_set(False)
        if self.create_slice:
            slice_obj.select_set(False)

        # делаем активным исходный объект
        context.view_layer.objects.active = src_obj
        # включаем автосглаживание
        context.object.data.use_auto_smooth = True
        # угол авто скглаживания
        context.object.data.auto_smooth_angle = 3.14159
        # снимаем выделение
        src_obj.select_set(False)
    else:
        transfer_obj = False

    solver = src_obj.modifiers[0].solver
    # Применяем булеан
    bpy.ops.object.modifier_apply(
        modifier=src_obj.modifiers[0].name)

    # Применяем масштаб
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Заходим в режим редактирования
    bpy.ops.object.mode_set(mode='EDIT')
    # Метод 1
    bpy.ops.mesh.select_mode(type='VERT')
    # Выделяем вершины без групп
    bpy.ops.mesh.select_ungrouped(extend=False)
    bpy.ops.mesh.select_mode(type='FACE')
    if solver == "EXACT":
        bpy.ops.mesh.select_more()

    # # Метод 2
    # bpy.ops.mesh.select_mode(type='FACE')
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.object.vertex_group_select()
    # bpy.ops.mesh.select_more()
    # bpy.ops.mesh.select_all(action='INVERT')

    # группа вершин для части булена
    src_obj.vertex_groups.new(name=bool_obj.name)
    bpy.ops.object.vertex_group_assign()
    # Выделяем пересечение
    bpy.ops.mesh.region_to_loop()
    bpy.ops.object.vertex_group_remove_from()

    bpy.ops.mesh.duplicate_move()
    # Удаляем дубли вершин
    if self.remove_doubles:
        bpy.ops.mesh.remove_doubles(
            threshold=self.remove_doubles, use_unselected=False)

    if self.simplify:
        bpy.ops.mesh.dissolve_limited(
            angle_limit=self.simplify, use_dissolve_boundaries=False)
    # Подразделяем, если нужно
    if self.subdivide:
        bpy.ops.mesh.subdivide(number_cuts=self.subdivide, smoothness=0.0)
    # Сглаживаем, если нужно
    if self.smooth:
        bpy.ops.mesh.vertices_smooth(
            factor=self.factor, repeat=self.smooth, xaxis=True, yaxis=True, zaxis=True)

    # группа вершин для пересечения

    src_obj.vertex_groups.new(name="bevel")
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    curve = context.selected_objects[0]
    context.view_layer.objects.active = curve
    curve.name = "BAB_GUIDE"
    bpy.ops.object.convert(target='CURVE', keep_original=False)
    curve.select_set(False)

    if self.create_slice:
        # делаем активным исходный объект
        context.view_layer.objects.active = slice_obj
        # Применяем булеан
        bpy.ops.object.modifier_apply(
            modifier=slice_obj.modifiers[0].name)
        # Применяем масштаб
        bpy.ops.object.transform_apply(
            location=False, rotation=False, scale=True)
        # Заходим в режим редактирования
        bpy.ops.object.mode_set(mode='EDIT')
        # Метод 1
        bpy.ops.mesh.select_mode(type='VERT')
        # Выделяем вершины без групп
        bpy.ops.mesh.select_ungrouped(extend=False)
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_more()
        # Метод 2
        # bpy.ops.mesh.select_mode(type='FACE')
        # bpy.ops.mesh.select_all(action='DESELECT')
        # bpy.ops.object.vertex_group_select()
        # bpy.ops.mesh.select_more()
        # bpy.ops.mesh.select_all(action='INVERT')
        # # Режим вершин
        # bpy.ops.mesh.select_mode(type='VERT')
        # # Выделяем вершины без групп
        # bpy.ops.mesh.select_ungrouped(extend=False)
        # группа вершин для части булена
        slice_obj.vertex_groups.new(name=bool_obj.name)
        bpy.ops.object.vertex_group_assign()
        # Выделяем пересечение
        bpy.ops.mesh.region_to_loop()
        bpy.ops.object.vertex_group_remove_from()
        # группа вершин для пересечения
        slice_obj.vertex_groups.new(name="bevel")
        # bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.hide(unselected=False)
        context.view_layer.objects.active = curve
        bpy.ops.object.mode_set(mode='OBJECT')

    return curve, bool_obj, transfer_obj, slice_obj


def prepare_in_edit(self, context, src_obj):
    self.operation = "UNION"
    self.create_slice = False
    # Удаляем группы вершин
    if src_obj.vertex_groups:
        src_obj.vertex_groups.clear()

    # Создаем группу вершин
    src_obj.vertex_groups.new(name=src_obj.name)

    # Создаем группу вершин
    src_obj.vertex_groups.new(name=src_obj.name)

    bpy.ops.mesh.duplicate_move()
    # Удаляем дубли вершин
    if self.remove_doubles:
        bpy.ops.mesh.remove_doubles(
            threshold=self.remove_doubles, use_unselected=False)

    if self.simplify:
        bpy.ops.mesh.dissolve_limited(
            angle_limit=self.simplify, use_dissolve_boundaries=False)
    # Подразделяем, если нужно
    if self.subdivide:
        bpy.ops.mesh.subdivide(number_cuts=self.subdivide, smoothness=0.0)
    # Сглаживаем, если нужно
    if self.smooth:
        bpy.ops.mesh.vertices_smooth(
            factor=self.factor, repeat=self.smooth, xaxis=True, yaxis=True, zaxis=True)

    # группа вершин для пересечения
    src_obj.vertex_groups.new(name="bevel")
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.mesh.hide(unselected=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    src_obj.select_set(False)
    curve = context.selected_objects[0]
    context.view_layer.objects.active = curve
    curve.name = "BAB_GUIDE"
    bpy.ops.object.convert(target='CURVE', keep_original=False)
    curve.select_set(False)

    if self.transfer:
        # выделяем объект
        src_obj.select_set(True)
        context.view_layer.objects.active = src_obj

        # Делаем его копию
        bpy.ops.object.duplicate_move(
            OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
        # Снимаем выделение
        src_obj.select_set(False)
        # Добавляем переменную
        transfer_obj = context.active_object
        # Переминовываем для удобства
        transfer_obj.name = 'BAB_TRANSFER'
        # Меняем отображение для удобства
        transfer_obj.display_type = 'BOUNDS'

        # выделяем исходный объект
        src_obj.select_set(True)
        # Меняем shading объектов
        bpy.ops.object.shade_smooth()

        # Снимаем выделение
        transfer_obj.select_set(False)

        # делаем активным исходный объект
        context.view_layer.objects.active = src_obj
        # включаем автосглаживание
        context.object.data.use_auto_smooth = True
        # угол авто скглаживания
        context.object.data.auto_smooth_angle = 3.14159
        # снимаем выделение
        src_obj.select_set(False)
        bool_obj = transfer_obj
    else:
        transfer_obj = False
        bool_obj = False
    # Добавляем в нее все вершины
    src_obj.vertex_groups[0].add(range(len(src_obj.data.vertices)), 1, 'ADD')
    # Добавляем в нее все вершины
    src_obj.vertex_groups[1].add(range(len(src_obj.data.vertices)), 1, 'ADD')
    return curve, bool_obj, transfer_obj


def change_subsurf(obj, index, level):
    """Change subsurf level on obj"""
    if DEBUG:
        time_start = time.time()
    if index > -1:
        obj.modifiers[index].levels = level
    if DEBUG:
        print("change_subsurf: %.4f sec\n" % (time.time() - time_start))


def align(obj, pipe, guide, sides=12):
    if DEBUG:
        time_start = time.time()

    cyclic = guide.data.splines[0].use_cyclic_u
    # Создаем дерево
    kd = create_tree(pipe)

    for v in obj.data.vertices:
        if v.groups and not v.hide:
            # co, index, dist = kd.find(v.co)
            index = kd.find(v.co)[1]
            v.co = guide.data.splines[0].bezier_points[index //
                                                       sides - cyclic].co
            obj.vertex_groups[2].remove([v.index])
    if DEBUG:
        print("align: %.4f sec\n" % (time.time() - time_start))


def do_bevel(self):
    if DEBUG:
        time_start = time.time()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.vertex_group_select()

    if self.bevel_segments > 1:
        bevel_segments = self.bevel_segments - 1
        bevel_width = 100 - (200 / (bevel_segments + 3))
        bpy.ops.mesh.bevel(affect='EDGES', offset_type='PERCENT', profile=self.bevel_profile,
                           segments=bevel_segments,
                           clamp_overlap=False, offset_pct=bevel_width, mark_sharp=False, mark_seam=False,
                           loop_slide=True)

    if self.bevel_segments == 0:
        bpy.ops.mesh.dissolve_edges(use_verts=True, use_face_split=False)
    bpy.ops.object.vertex_group_remove_from()

    bpy.ops.mesh.select_all(action='DESELECT')
    # bpy.ops.mesh.hide(unselected=True)

    if DEBUG:
        print("DO_BEVEL: %.4f sec\n" % (time.time() - time_start))


classes = (

    BAB_Props,
    BAB_PT_Panel,

    BAB_OP_Bevel,

    BAB_OP_Slice,
    BAB_OP_Create_Pipe,

    BAB_OP_Apply_Modifiers,
    BAB_OP_Remove_Modifiers,
    BAB_OP_Hide_Modifiers,

    BAB_OP_Visibility,

    BAB_OP_Symmetrize,

    BAB_OP_TESTS,

    BAB_OP_Remove3dLines,

    BAB_OP_SELECT_LOOP,
    BAB_OP_SMOOTH_LOOP,

)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.bab_props = bpy.props.PointerProperty(
        type=BAB_Props)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.bab_props


if __name__ == "__main__":
    register()
