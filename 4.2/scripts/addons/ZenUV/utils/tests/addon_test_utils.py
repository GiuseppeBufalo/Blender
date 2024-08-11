import bpy
import bmesh
from typing import List
from mathutils import Vector, Matrix
import numpy as np

from ZenUV.utils import get_uv_islands as island_util
from .test_geometry import TestCube, TestCylinder
from ZenUV.utils.transform import BoundingBox2d
from ZenUV.utils.constants import TEST_OBJ_NAME_CUBE, TEST_OBJ_NAME_CYLINDER


def _get_objs(context):
    return context.objects_in_mode_unique_data


def _set_sync_uv(context, state):
    context.scene.tool_settings.use_uv_select_sync = state


def _select_objs_by_names(context, names, active_name):
    _set_object_mode(context)
    bpy.ops.object.select_all(action='DESELECT')
    for name in names:
        obj = context.scene.objects[name]
        obj.select_set(True)
        if name == active_name:
            context.view_layer.objects.active = obj


def _move_uv(context, offset=(0, 0), all_objs=False):
    if all_objs:
        objs = _get_objs(context)
    else:
        objs = [context.object, ]
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = [loop for face in bm.faces for loop in face.loops]
        for loop in loops:
            loop[uv_layer].uv += Vector(offset)
        bmesh.update_edit_mesh(obj.data)

    return faces


def _move_uv_by_faces_id(context, ids, offset=(0, 0), all_objs=False):
    if all_objs:
        objs = _get_objs(context)
    else:
        objs = [context.object, ]
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        for loop in [loop for i in ids for loop in bm.faces[i].loops]:
            loop[uv_layer].uv += Vector(offset)
        bmesh.update_edit_mesh(obj.data)


def _scale_uv(context, scale=(0, 0), all_objs=False):
    if all_objs:
        objs = _get_objs(context)
    else:
        objs = [context.object, ]
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = [loop for face in bm.faces for loop in face.loops]
        for loop in loops:
            loop[uv_layer].uv *= Vector(scale)
        bmesh.update_edit_mesh(obj.data)

    return faces


def _rotate_uv(context, angle=12, pivot=Vector((0.5, 0.5)), all_objs=True):
    p = 1
    pivot = Vector((0.5, 0.5))
    R = Matrix((
                (np.cos(angle), np.sin(angle) / p),
                (-p * np.sin(angle), np.cos(angle)),
            ))
    if all_objs:
        objs = _get_objs(context)
    else:
        objs = [context.object, ]

    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        loops = [loop for face in bm.faces for loop in face.loops]
        uvs = np.empty([len(loops), 2])
        for i in range(len(loops)):
            uvs[i] = list(loops[i][uv_layer].uv)
        uvs = np.dot(
            uvs.reshape((-1, 2)) - pivot, R) + pivot
        for loop, co in zip(loops, uvs):
            loop[uv_layer].uv = co
        bmesh.update_edit_mesh(obj.data)


def _select_faces_by_id_active_obj(context, ids):
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for i in ids:
        bm.faces[i].select = True
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data)


def _hide_faces_by_id_active_obj(context, ids):
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for i in ids:
        bm.faces[i].hide_set(True)
    bmesh.update_edit_mesh(obj.data)


def _get_hided_faces_ids(context):
    objs = _get_objs(context)
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        faces.extend([f.index for f in bm.faces if f.hide])
        bm.free()
    return faces


def _select_edges_by_id_active_obj(context, ids, state=True):
    obj = context.object
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    for i in ids:
        bm.edges[i].select = state
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data)


def _get_seam_edges_ids(context):
    objs = _get_objs(context)
    edges = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        edges.extend([e.index for e in bm.edges if e.seam])
        bm.free()
    return edges


def _get_selected_edges_ids(context):
    objs = _get_objs(context)
    edges = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        edges.extend([e.index for e in bm.edges if e.select])
        bm.free()
    return edges


def _get_selected_faces_ids(context):
    objs = _get_objs(context)
    faces = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        faces.extend([f.index for f in bm.faces if f.select])
        bm.free()
    return faces


def _set_seams(context, edge_idxs, state=True):
    objs = _get_objs(context)
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for i in edge_idxs:
            bm.edges[i].seam = state
        bmesh.update_edit_mesh(obj.data)


def _set_sharp(context, edge_idxs, state=True):
    objs = _get_objs(context)
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        for i in edge_idxs:
            bm.edges[i].smooth = not state
        bmesh.update_edit_mesh(obj.data)


def _get_sharp_edges_ids(context):
    objs = _get_objs(context)
    edges = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data).copy()
        edges.extend([e.index for e in bm.edges if not e.smooth])
        bm.free()
    return edges


def _get_bounding_box(context):
    points = []
    for obj in _get_objs(context):
        bm = bmesh.from_edit_mesh(obj.data).copy()
        uv_layer = bm.loops.layers.uv.verify()
        islands = island_util.get_islands(context, bm)
        points.extend({loop[uv_layer].uv.copy().freeze() for island in islands for face in island for loop in face.loops})
        bm.free()
    return BoundingBox2d(points=points)


def _ensure_facemap(bm, facemap_name):
    """ Return facemap int type or create new """
    facemap = bm.faces.layers.int.get(facemap_name)
    if not facemap:
        facemap = bm.faces.layers.int.new(facemap_name)
    return facemap


def get_prefs_within_tests():
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons["ZenUV"].preferences


def _set_object_mode(context):
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if context.mode != 'OBJECT':
        raise AddonTestError('PREPARE> Object mode is expected!')


def _set_edit_mode(context):
    if context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')

    if context.mode != 'EDIT_MESH':
        raise AddonTestError('PREPARE> Edit mode is expected!')


def set_skip_tests(tests: List):
    skipped = []
    for skp in tests:
        skipped.extend([f.__name__ for f in skp])
    return skipped


class AddonTestError(Exception):
    """ Critical error in test """
    pass


class AddonTestManual(Exception):
    """ Manual test """
    pass


def _prepare_test(context, model="CUBE", count=2):
    try:
        if context.mode != 'EDIT_MESH':
            if bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode='EDIT')

    except Exception:
        pass

    _set_object_mode(context)

    for p_obj in bpy.data.objects:
        bpy.data.objects.remove(p_obj)

    if len(bpy.data.objects):
        raise AddonTestError('PREPARE> Expect empty scene without objects!')

    loc = [0, 0, 0]
    uv_pos = [0, 0]
    for i in range(count):
        # TestGeometry.create(context, model=model)
        TestGeometry.create(context, model=model, location=loc, uv_position=uv_pos)
        loc[0] += -4
        uv_pos[0] += -1

    # elif model == "CYLINDER":
    #     bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    #     print("Model Cylinder Created")

    # bpy.ops.mesh.primitive_cube_add(enter_editmode=False)
    # bpy.ops.mesh.primitive_cube_add(enter_editmode=True, location=(-4, 0, 0))

    _set_edit_mode(context)
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    if context.mode != 'EDIT_MESH':
        raise AddonTestError('PREPARE> Edit mode is expected!')

    if context.active_object is None:
        raise AddonTestError('PREPARE> Active object was not created!')


def _check_mgr_mode_prepared(p_cls_mgr, context, p_scene):
    p_scene.zen_sets_active_mode = p_cls_mgr.id_group
    p_cls_mgr.set_mesh_select_mode(context)

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.reveal(select=False)


def _check_group_prepared(p_cls_mgr, context, p_scene, p_obj):

    _check_mgr_mode_prepared(p_cls_mgr, context, p_scene)

    p_list = p_cls_mgr.get_list(p_scene)
    if len(p_list) != 1:
        raise AddonTestError('TEST> List length != 1')

    p_obj_list = p_cls_mgr.get_list(p_obj)
    if len(p_obj_list) != 1:
        raise AddonTestError('TEST> List length != 1')

    sel_count = p_cls_mgr.get_selected_count(p_obj)
    if sel_count:
        raise AddonTestError('TEST> Selection was not cleared!')


def _check_object_mgr_mode_prepared(p_cls_mgr, p_scene):
    p_scene.zen_object_collections_mode = p_cls_mgr.id_group

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.hide_view_clear(select=False)


def _check_selected_count(p_cls_mgr, p_obj, p_bm_items, expected_indices):
    i_expected_count = len(expected_indices)
    i_sel_count = p_cls_mgr.get_selected_count(p_obj)
    if i_sel_count != i_expected_count:
        raise AddonTestError(f'TEST> Expected selected count {i_expected_count} but got {i_sel_count}')

    for i in expected_indices:
        if not p_bm_items[i].select:
            raise AddonTestError(f'TEST> BMesh Element:{i} is not selected!')


def _check_hidden_count(p_cls_mgr, p_obj, p_bm_items, expected_indices):
    i_expected_count = len(expected_indices)
    i_hidden_count = len([item for item in p_bm_items if item.hide])
    if i_hidden_count != i_expected_count:
        raise AddonTestError(f'TEST> Expected hidden count {i_expected_count} but got {i_hidden_count}')

    for i in expected_indices:
        if not p_bm_items[i].hide:
            raise AddonTestError(f'TEST> BMesh Element:{i} is not hidden!')


class TestGeometry:

    @classmethod
    def create(cls, context, model, location=(0, 0, 0), uv_position=(0, 0)):

        if model == 'CUBE':
            mesh_source = TestCube
            name = TEST_OBJ_NAME_CUBE

        elif model == 'CYLINDER':
            mesh_source = TestCylinder
            name = TEST_OBJ_NAME_CYLINDER

        verts = [co + Vector((location)) for co in mesh_source.verts]
        faces = mesh_source.faces
        uv_co = [uv + Vector((uv_position)) for uv in mesh_source.loops_uv_co]
        seams = mesh_source.seams

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)

        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        _set_edit_mode(context)

        import bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        for edge, state in zip(bm.edges, seams):
            edge.seam = state

        loops = [loop for face in bm.faces for loop in face.loops]

        for loop, co in zip(loops, uv_co):
            loop[uv_layer].uv = co

        bmesh.update_edit_mesh(obj.data)

        _set_object_mode(context)
