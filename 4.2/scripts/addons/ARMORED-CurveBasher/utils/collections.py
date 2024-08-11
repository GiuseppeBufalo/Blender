import bpy
import os

from .. utils import addon


def unlink_libraries():
    cbasher_library = bpy.data.libraries.get('default_cables.blend')
    if cbasher_library is not None:
        bpy.data.libraries.remove(cbasher_library)


def cleanup(self, context):
    '''Removes any empty collections the addon might have created'''

    if not self.default_collection.all_objects:
        bpy.data.collections.remove(self.default_collection)
        
    if not self.caps_collection.all_objects:
        bpy.data.collections.remove(self.caps_collection)
    
    # unlink_libraries()


def get_collection_from_scene(context, name):
    collection = bpy.data.collections.get(name)

    return collection if context.scene.user_of_id(collection) else None


def create_collection(context, name, parent=None) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    
    if collection is None:
        collection = bpy.data.collections.new(name)
    
        if parent is None:
            context.scene.collection.children.link(collection)
        else:
            parent.children.link(collection)

    # Exists in the Blend Data but not in the Scene.
    elif context.scene.user_of_id(collection) == 0:

        # Re-link.
        if parent is None:
            context.scene.collection.children.link(collection)
        else:
            parent.children.link(collection)

    return collection


def link_collection(collection_name):
    '''Link a collection from a different blend file and sort the objects alphabetically.
    Since the collection data is not immediately linked to the scene it will dissapear if not used'''

    # if bpy.data.collections.get(collection_name) is None:
    filepath = os.path.join(addon.get_path(), 'resources', 'default_cables.blend')


    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        data_to.collections = [name for name in data_from.collections 
                if name.lower().startswith(collection_name.lower())]

        # data_to.objects = [name for name in data_from.objects 
        #         if name.lower().startswith('cap'.lower())]

        # data_to.objects = data_from.objects 

    if addon.debug():
        print(f'Linking collection "{collection_name}" to current scene')
    
    child_objects     = bpy.data.collections[collection_name].objects[:]
    child_collections = bpy.data.collections[collection_name].children[:]
    all_elements = child_objects + child_collections

    sorted_col_objects = sorted(all_elements, key=lambda obj: obj.name)

    return sorted_col_objects


def link_all_collections():
    # Runs the Link Collection function for every collection we want to import.
    
    collections_to_import = [
        'Default Basic Types',
        'Default Array Types',
        'Default Kitbash Types',
    ]

    all_source_objects = [link_collection(coll_name) for coll_name in collections_to_import]

    if addon.debug():
        print('')
        
    return all_source_objects