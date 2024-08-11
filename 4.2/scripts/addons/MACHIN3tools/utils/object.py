from typing import Union
import bpy
import bmesh
from mathutils import Vector
from uuid import uuid4
from . math import flatten_matrix
from . modifier import get_mod_obj
from . view import ensure_visibility, is_on_viewlayer

def is_valid_object(obj):
    return obj and ' invalid>' not in str(obj)

def is_instance_collection(obj):
    if obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' and obj.instance_collection:
        return obj.instance_collection

def is_linked_object(obj, debug=False):

    if debug:
        print("\nchecking if", obj.name, "is linked")

    linked = []

    if obj.library:
        linked.append(obj)

    if data := obj.data:
        if data.library:
            linked.append(data)

    elif icol := is_instance_collection(obj):

        if icol.library:
            linked.append(icol)

        for ob in icol.objects:
            if ob.library:
                linked.append(ob)

            if data := ob.data:
                if data.library:
                    linked.append(data)
    if debug:
        for id in linked:
            print(type(id), id.name, id.library)

    return linked

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
    objects = getattr(view_layer, 'objects', None)
    
    if objects:
        return [obj for obj in objects if obj and obj.visible_get(view_layer=view_layer)]
    return []

def has_bbox(obj):
    return obj.bound_box and not all(Vector(co) == Vector() for co in obj.bound_box)

def get_eval_bbox(obj):
    return [Vector(co) for co in obj.bound_box]

def remove_obj(obj):
    if not obj.data:
        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.data.users > 1:
        bpy.data.objects.remove(obj, do_unlink=True)

    elif obj.type == 'MESH':
        bpy.data.meshes.remove(obj.data, do_unlink=True)

    else:
        bpy.data.objects.remove(obj, do_unlink=True)

def duplicate_objects(context, objects):
    bpy.ops.object.select_all(action='DESELECT')

    originals = {str(uuid4()): (obj, obj.visible_get(), obj.hide_viewport) for obj in objects}

    for dup_hash, (obj, vis, hide_viewport) in originals.items():
        ensure_visibility(context, obj, view_layer=False, local_view=True, unhide=True, unhide_viewport=True, select=True)

        obj.M3.dup_hash = dup_hash

    bpy.ops.object.duplicate(linked=False)

    duplicates = []

    for dup in context.selected_objects:
        duplicates.append(dup)

        orig, vis, hide_viewport = originals[dup.M3.dup_hash]

        orig.hide_set(not vis)
        dup.hide_set(not vis)

        orig.hide_viewport = hide_viewport
        dup.hide_viewport = hide_viewport

        orig.M3.dup_hash = ''
        dup.M3.dup_hash = ''
    
    return duplicates

def set_obj_origin(obj, mx, bm=None, decalmachine=False, meshmachine=False):
    omx = obj.matrix_world.copy()

    children = [c for c in obj.children]
    compensate_children(obj, omx, mx)

    deltamx = mx.inverted_safe() @ obj.matrix_world

    obj.matrix_world = mx

    if bm:
        bmesh.ops.transform(bm, verts=bm.verts, matrix=deltamx)
        bmesh.update_edit_mesh(obj.data)
    else:
        obj.data.transform(deltamx)

    if obj.type == 'MESH':
        obj.data.update()

    if decalmachine and children:

        for c in [c for c in children if c.DM.isdecal and c.DM.decalbackup]:
            backup = c.DM.decalbackup
            backup.DM.backupmx = flatten_matrix(deltamx @ backup.DM.backupmx)

    if meshmachine:

        for stash in obj.MM.stashes:

            if getattr(stash, 'version', False) and float('.'.join([v for v in stash.version.split('.')[:2]])) >= 0.7:
                stashdeltamx = stash.obj.MM.stashdeltamx

                if stash.self_stash:
                    if stash.obj.users > 2:
                        print(f"INFO: Duplicating {stash.name}'s stashobj {stash.obj.name} as it's used by multiple stashes")

                        dup = stash.obj.copy()
                        dup.data = stash.obj.data.copy()
                        stash.obj = dup

                stash.obj.MM.stashdeltamx = flatten_matrix(deltamx @ stashdeltamx)
                stash.obj.MM.stashorphanmx = flatten_matrix(mx)

                stash.self_stash = False

            else:
                stashdeltamx = stash.obj.MM.stashtargetmx.inverted_safe() @ stash.obj.MM.stashmx

                stash.obj.MM.stashmx = flatten_matrix(omx @ stashdeltamx)
                stash.obj.MM.stashtargetmx = flatten_matrix(mx)

            stash.obj.data.transform(deltamx)
            stash.obj.matrix_world = mx

def flatten(obj, depsgraph=None):
    if not depsgraph:
        depsgraph = bpy.context.evaluated_depsgraph_get()

    oldmesh = obj.data

    obj.data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    obj.modifiers.clear()

    bpy.data.meshes.remove(oldmesh, do_unlink=True)

def parent(obj, parentobj):
    if obj.parent:
        unparent(obj)

    obj.parent = parentobj
    obj.matrix_parent_inverse = parentobj.matrix_world.inverted_safe()

def get_parent(obj, recursive=False, debug=False):
    if recursive:
        parents = []

        while obj.parent and is_on_viewlayer(obj.parent):
            parents.append(obj.parent)
            obj = obj.parent

        return parents

    else:
        if obj.parent and is_on_viewlayer(obj.parent):
            return obj.parent

def unparent(obj):
    if obj.parent:
        omx = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = omx

def unparent_children(obj):
    children = []

    for c in obj.children:
        unparent(c)
        children.append(c)

    return children

def compensate_children(obj, oldmx, newmx):
    deltamx = newmx.inverted_safe() @ oldmx
    children = [c for c in obj.children]

    for c in children:
        pmx = c.matrix_parent_inverse
        c.matrix_parent_inverse = deltamx @ pmx

def get_object_hierarchy_layers(context, debug=False):
    def add_layer(layers, depth, debug=False):
        if debug:
            print()
            print("layer", depth)

        children = []

        for obj in layers[-1]:
            if debug:
                print("", obj.name)

            for obj in obj.children:
                children.append(obj)

        if children:
            depth += 1

            layers.append(children)

            add_layer(layers, depth=depth, debug=debug)

    depth = 0

    top_level_objects = [obj for obj in context.view_layer.objects if not obj.parent]

    layers = [top_level_objects]

    add_layer(layers, depth, debug=debug)

    return layers

def get_object_tree(obj, obj_tree, mod_objects=True, mod_dict=None, mod_type_ignore=[], depth=0, find_disabled_mods=False, check_if_on_viewlayer=False, debug=False):

    depthstr = " " * depth

    if debug:
        print()
        print("depth:", depth, "tree:", [obj.name for obj in obj_tree])
        print(f"{depthstr}{obj.name}")

    for child in obj.children:
        if debug:
            print(f" {depthstr}child: {child.name}", "is on viewlayer:", is_on_viewlayer(child))

        if child not in obj_tree:
            if check_if_on_viewlayer and not is_on_viewlayer(child):
                if debug:
                    print(f"  {depthstr}! ignoring child '{child.name}' as it's not on the view layer")
                continue

            obj_tree.append(child)

            get_object_tree(child, obj_tree, mod_objects=mod_objects, mod_dict=mod_dict, mod_type_ignore=mod_type_ignore, depth=depth + 1, find_disabled_mods=find_disabled_mods, check_if_on_viewlayer=check_if_on_viewlayer, debug=debug)

    if mod_objects:
        for mod in obj.modifiers:

            if mod.type not in mod_type_ignore and (mod.show_viewport or find_disabled_mods):
                mod_obj = get_mod_obj(mod)

                if debug:
                    if mod_obj:
                        print(f" {depthstr}mod: {mod.name} | obj: {mod_obj.name}", "is on viewlayer:", is_on_viewlayer(mod_obj))

                    else:
                        print(f" {depthstr}mod: {mod.name} | obj: None")

                if mod_obj:
                    if check_if_on_viewlayer and not is_on_viewlayer(mod_obj):
                        if debug:
                            print(f"  {depthstr}! ignoring mod object '{mod_obj.name}' as it's not on the view layer")
                        continue

                    if mod_dict is not None:
                        if mod_obj in mod_dict:
                            mod_dict[mod_obj].append(mod)
                        else:
                            mod_dict[mod_obj] = [mod]

                    if mod_obj not in obj_tree:
                        obj_tree.append(mod_obj)

                        get_object_tree(mod_obj, obj_tree, mod_objects=mod_objects, mod_dict=mod_dict, mod_type_ignore=mod_type_ignore, depth=depth + 1, find_disabled_mods=find_disabled_mods, check_if_on_viewlayer=check_if_on_viewlayer, debug=debug)
