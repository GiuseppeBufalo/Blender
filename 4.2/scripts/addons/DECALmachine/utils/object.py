from typing import Union
import bpy
from mathutils import Matrix
from . modifier import add_boolean, get_subd, get_shrinkwrap

def remove_obj(obj, debug=False):
    if not obj.data:
        if debug:
            print("   remove empty object")

        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.data.users > 1:
        if debug:
            print("   remove object only, as the mesh is used elsewhere")

        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.type == 'MESH':
        if debug:
            print("   remove mesh and object")

        bpy.data.meshes.remove(obj.data, do_unlink=True)

    else:
        if debug:
            print("   remove non-mesh and object")

        bpy.data.objects.remove(obj, do_unlink=True)

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

def get_active_object(context) -> Union[bpy.types.Object, None]:
    objects = getattr(context.view_layer, 'objects', None)

    if objects:
        return getattr(objects, 'active', None)

def get_selected_objects(context) -> list[bpy.types.Object]:
    objects = getattr(context.view_layer, 'objects', None)

    if objects:
        return getattr(objects, 'selected', [])

    return []

def get_visible_objects(context, local_view=False) -> list[bpy.types.Object]:
    view_layer = context.view_layer
    objects = getattr(view_layer, 'objects', [])

    return [obj for obj in objects if obj.visible_get(view_layer=view_layer)]
