import bpy, os
from .bone_edit import *
from .context import *


def append_from_arp(nodes=None, type=None):
    context = bpy.context
    scene = context.scene

    addon_directory = os.path.dirname(os.path.abspath(__file__))
    addon_directory = os.path.dirname(addon_directory)
    addon_directory = os.path.dirname(addon_directory)
    filepath = addon_directory + "/armature_presets/" + "master.blend"
    
    if type == "object":
        # Clean the cs_ materials names (avoid .001, .002...)
        for mat in bpy.data.materials:
            if mat.name[:3] == "cs_":
                if mat.name[-3:].isdigit() and bpy.data.materials.get(mat.name[:-4]) == None:
                    mat.name = mat.name[:-4]

        # make a list of current custom shapes objects in the scene for removal later
        cs_objects = [obj.name for obj in bpy.data.objects if obj.name[:3] == "cs_"]

        # Load the objects data in the file
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name in nodes]

        # Add the objects in the scene
        for obj in data_to.objects:
            if obj:
                # Link
                bpy.context.scene.collection.objects.link(obj)

                # Apply existing scene material if exists
                if len(obj.material_slots) > 0:
                    mat_name = obj.material_slots[0].name
                    found_mat = None

                    for mat in bpy.data.materials:
                        if mat.name == mat_name[:-4]:  # substract .001, .002...
                            found_mat = mat.name
                            break

                    # Assign existing material if already in file and delete the imported one
                    if found_mat:
                        obj.material_slots[0].material = bpy.data.materials[found_mat]
                        bpy.data.materials.remove(bpy.data.materials[mat_name], do_unlink=True)

                # If we append a custom shape
                if "cs_" in obj.name or "c_sphere" in obj.name:
                    cs_grp = bpy.data.objects.get("cs_grp")
                    if cs_grp:
                        # parent the custom shape
                        obj.parent = cs_grp

                        # assign to new collection
                        assigned_collections = []
                        for collec in cs_grp.users_collection:
                            collec.objects.link(obj)
                            assigned_collections.append(collec)

                        if len(assigned_collections) > 0:
                            # remove previous collections
                            for i in obj.users_collection:
                                if not i in assigned_collections:
                                    i.objects.unlink(obj)
                            # and the scene collection
                            try:
                                bpy.context.scene.collection.objects.unlink(obj)
                            except:
                                pass

                # If we append other objects,
                # find added/useless custom shapes and delete them
                else:
                    for obj in bpy.data.objects:
                        if obj.name[:3] == "cs_":
                            if not obj.name in cs_objects:
                                bpy.data.objects.remove(obj, do_unlink=True)

                    if 'obj' in locals():
                        del obj

    if type == "text":
        # Load the objects data in the file
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            data_to.texts = [name for name in data_from.texts if name in nodes]
        print("Loading text file:", data_to.texts)
        bpy.context.evaluated_depsgraph_get().update()

    if type == "font":
        # Load the data in the file
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            data_to.fonts = [name for name in data_from.fonts if name in nodes]
        print("Loading font file:", data_to.fonts)
        bpy.context.evaluated_depsgraph_get().update()


def get_object(name, view_layer_change=False):
    ob = bpy.data.objects.get(name)
    if ob:
        if view_layer_change:
            found = False
            for v_o in bpy.context.view_layer.objects:
                if v_o == ob:
                    found = True
            if not found:# object not in view layer, add to the base collection
                bpy.context.collection.objects.link(ob)

    return ob
    

def get_object_id(arp_id):
    for _ob in bpy.data.objects:
        if len(_ob.keys()):
            if 'arp_id' in _ob.keys():
                if _ob['arp_id'] == arp_id:
                    return _ob
    return None
    

def is_object_id(_ob, arp_id, suffix_only=False):
    object_has_id = False
    if len(_ob.keys()):
        if 'arp_id' in _ob.keys():
            if suffix_only:
                if _ob['arp_id'].endswith(arp_id):
                    object_has_id = True
            else:
                if _ob['arp_id'] == arp_id:
                    object_has_id = True
                
    return object_has_id


def delete_object(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def set_active_object(object_name):
     bpy.context.view_layer.objects.active = bpy.data.objects[object_name]
     bpy.data.objects[object_name].select_set(state=True)


def hide_object(obj_to_set):
    try:# object may not be in current view layer
        obj_to_set.hide_set(True)
        obj_to_set.hide_viewport = True
    except:
        pass


def hide_object_visual(obj_to_set):
    obj_to_set.hide_set(True)


def is_object_hidden(obj_to_get):
    try:
        if obj_to_get.hide_get() == False and obj_to_get.hide_viewport == False:
            return False
        else:
            return True
    except:# the object must be in another view layer, it can't be accessed
        return True


def unhide_object(obj_to_set):
    # we can only operate on the object if it's in the active view layer...
    try:
        obj_to_set.hide_set(False)
        obj_to_set.hide_viewport = False
    except:
        print("Could not reveal object:", obj_to_set.name)


def duplicate_object(new_name=""):
    try:
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
    except:
        bpy.ops.object.duplicate('TRANSLATION', False)
    if new_name != "":
        bpy.context.active_object.name = new_name


def delete_children(passed_node, type):
    if passed_node:
        if type == "OBJECT":
            parent_obj = passed_node
            children = []

            for obj in bpy.data.objects:
                if obj.parent:
                    if obj.parent == parent_obj:
                        children.append(obj)
                        for _obj in children:
                            for obj_1 in bpy.data.objects:
                                if obj_1.parent:
                                    if obj_1.parent == _obj:
                                        children.append(obj_1)

            meshes_data = []

            for child in children:
                # store the mesh data for removal afterward
                try:
                    if child.data:
                        if not child.data.name in meshes_data:
                            meshes_data.append(child.data.name)
                except:
                    continue

                bpy.data.objects.remove(child, do_unlink=True, do_id_user=True, do_ui_user=True)

            for data_name in meshes_data:
                current_mesh = bpy.data.meshes.get(data_name)
                if current_mesh:
                    bpy.data.meshes.remove(current_mesh, do_unlink=True, do_id_user=True, do_ui_user=True)

            bpy.data.objects.remove(passed_node, do_unlink=True)

        elif type == "EDIT_BONE":
            current_mode = bpy.context.mode

            bpy.ops.object.mode_set(mode='EDIT')

            if bpy.context.active_object.data.edit_bones.get(passed_node.name):

                # Save displayed layers
                _layers = [bpy.context.active_object.data.layers[i] for i in range(0, 32)]

                # Display all layers
                for i in range(0, 32):
                    bpy.context.active_object.data.layers[i] = True

                bpy.ops.armature.select_all(action='DESELECT')
                bpy.context.evaluated_depsgraph_get().update()
                bpy.context.active_object.data.edit_bones.active = get_edit_bone(passed_node.name)
                bpy.ops.armature.select_similar(type='CHILDREN')
                bpy.ops.armature.delete()

                for i in range(0, 32):
                    bpy.context.active_object.data.layers[i] = _layers[i]

            # restore saved mode
            restore_current_mode(current_mode)


def parent_objects(_obj_list, target, mesh_only=True):
    for obj in _obj_list:
        if mesh_only:
            if obj.type != "MESH":
                continue
        #print("parenting", obj.name)
        obj_mat = obj.matrix_world.copy()
        obj.parent = target
        obj.matrix_world = obj_mat