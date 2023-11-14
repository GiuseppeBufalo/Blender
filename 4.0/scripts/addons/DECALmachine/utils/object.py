import bpy
from mathutils import Matrix
from . modifier import add_boolean, get_subd, get_shrinkwrap


def parent(obj, parentobj):
    if obj.parent:
        unparent(obj)

    obj.parent = parentobj
    obj.matrix_parent_inverse = parentobj.matrix_world.inverted_safe()


def unparent(obj):
    if obj.parent:
        omx = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = omx


def intersect(obj, target, solver='FAST'):
    return add_boolean(obj, target, method='INTERSECT', solver=solver)


def unshrinkwrap(obj):
    subd = get_subd(obj)
    shrinkwrap = get_shrinkwrap(obj)

    if subd:
        obj.modifiers.remove(subd)

    if shrinkwrap:
        obj.modifiers.remove(shrinkwrap)


def flatten(obj, depsgraph=None):
    if not depsgraph:
        depsgraph = bpy.context.evaluated_depsgraph_get()

    oldmesh = obj.data

    obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    obj.modifiers.clear()

    bpy.data.meshes.remove(oldmesh, do_unlink=True)


def update_local_view(space_data, states):
    if space_data.local_view:
        for obj, local in states:
            obj.local_view_set(space_data, local)


def lock(obj):
    obj.lock_location = (True, True, True)
    obj.lock_rotation = (True, True, True)
    obj.lock_rotation_w = True
    obj.lock_scale = (True, True, True)


def unlock(obj):
    obj.lock_location = (False, False, False)
    obj.lock_rotation = (False, False, False)
    obj.lock_rotation_w = False
    obj.lock_scale = (False, False, False)
