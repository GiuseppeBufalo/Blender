import bpy
import os.path

def append_geo_node_tree(object, rec_path, geo_tree):

    curr_path = os.path.dirname(os.path.abspath(__file__))
    addon_path = curr_path.split("util")[0]
    blend_path = os.path.join(addon_path, rec_path)

    # Test whether the file exist
    if not os.path.isfile(blend_path):
        return None
    
    if not bpy.data.node_groups.get(geo_tree):
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name.startswith(geo_tree)]

        # -> Test whether the object exist
        if not data_to.node_groups:
            return None
    
    # add geonodes modifier
    bpy.ops.object.modifier_add(type='NODES')
    object.modifiers[-1].node_group = bpy.data.node_groups[geo_tree]

    return True


# based on https://blenderartists.org/t/how-to-append-only-certain-objects-from-other-blend-files/1476231/10
def append_object(rec_path, objname, collection):
    curr_path = os.path.dirname(os.path.abspath(__file__))
    addon_path = curr_path.split("util")[0]
    blend_path = os.path.join(addon_path, rec_path)   

    # Test whether the file exist
    if not os.path.isfile(blend_path):
        return None   
    
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects if name.startswith(objname)]

    # -> Test whether the object exist
    if not data_to.objects:
        return None
    
    for obj in data_to.objects:
        # based on https://blender.stackexchange.com/questions/132112/whats-the-blender-2-8-command-for-adding-an-object-to-a-collection-using-python
        collection.objects.link(obj)

    return data_to.objects
