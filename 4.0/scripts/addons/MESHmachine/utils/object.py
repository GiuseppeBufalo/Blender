import bpy
from mathutils import Matrix
from uuid import uuid4
from . modifier import get_mod_obj


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


def flatten(obj, depsgraph=None, preserve_data_layers=False):
    if not depsgraph:
        depsgraph = bpy.context.evaluated_depsgraph_get()

    oldmesh = obj.data

    if preserve_data_layers:
        obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
    else:
        obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    obj.modifiers.clear()

    bpy.data.meshes.remove(oldmesh, do_unlink=True)


def add_facemap(obj, name="", ids=[]):
    fmap = obj.face_maps.new(name=name)

    if ids:
        fmap.add(ids)

    return fmap


def update_local_view(space_data, states):
    if space_data.local_view:
        for obj, local in states:
            obj.local_view_set(space_data, local)


def get_object_tree(obj, obj_tree, mod_objects=True, depth=0, debug=False):
    
    depthstr = " " * depth

    if debug:
        print(f"\n{depthstr}{obj.name}")

    for child in obj.children:
        if debug:
            print(f" {depthstr}child: {child.name}")

        if child not in obj_tree:
            obj_tree.append(child)

            get_object_tree(child, obj_tree, mod_objects=mod_objects, depth=depth + 1, debug=debug)

    if mod_objects:
        for mod in obj.modifiers:
            mod_obj = get_mod_obj(mod)

            if debug:
                print(f" {depthstr}mod: {mod.name} | obj: {mod_obj.name if mod_obj else mod_obj}")

            if mod_obj:
                if mod_obj not in obj_tree:
                    obj_tree.append(mod_obj)

                    get_object_tree(mod_obj, obj_tree, mod_objects=mod_objects, depth=depth + 1, debug=debug)
