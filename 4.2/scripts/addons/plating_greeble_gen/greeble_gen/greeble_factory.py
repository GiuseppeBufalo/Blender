# Greeble factory class for managing greebles.
import os
import re
import bpy
from bpy.utils import previews
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        FloatVectorProperty,
        EnumProperty
        )

preview_collections = {}

def _clear_icons():
    for custom_icons in preview_collections.values():
        previews.remove(custom_icons)
    preview_collections.clear()

def refresh_greebles(catalogue):
    """Register greebles given a set of directory paths."""
    _clear_icons()

    custom_icons = previews.new()
    preview_collections['Main'] = custom_icons
    

    for category in catalogue.categories:
        try:
            category.greebles.clear()
            images = []
            greebles = []

            category.folder_path = os.path.abspath(bpy.path.abspath(category.folder_path))
            directory_path = category.folder_path

            directory = os.listdir(directory_path)
            for file_path  in directory:
                if file_path.lower().endswith('.png'):
                    full_path = os.path.abspath(os.path.join(directory_path, file_path))

                    thumb = custom_icons.load(os.path.basename(full_path), full_path, 'IMAGE')
                    icon_id = thumb.icon_id
                    images.append((file_path[:-4], icon_id, full_path))

            for index, image in enumerate(images):
                blend_filename = images[index][2][:-4] + '.blend'

                if os.path.isfile(blend_filename):
                    greeble_metadata = category.greebles.add()
                    greeble_metadata.greeble_name = images[index][0]
                    greeble_metadata.icon_id = images[index][1]
                    greeble_metadata.file_path = blend_filename
                
            category_name = os.path.basename(directory_path)
            
            # _greeble_categories[category_name] = greebles
            category.category_name = category_name

        except OSError as err:
            print("Error loading greebles: ".format(err))

    if len(catalogue.categories) > 0:
        catalogue.default_category = catalogue.categories[0].category_name

def get_greebles_metadata_from_category(catalogue, category_name):
    """Get Greeble Reference Details by name"""
    for category in catalogue.categories:
        if category.category_name == category_name:
            return category.greebles
    return []

def get_greebles_metadata_from_name_and_category(catalogue, greeble_name, category_name):
    """Get Greeble Reference Details by name"""
    for category in catalogue.categories:
        if category.category_name == category_name:
            for greeble in category.greebles:
                if greeble.greeble_name == greeble_name:
                    return greeble
    return None

def get_greeble_categories(catalogue):
    return catalogue.categories

_trailing_dupe_pattern = re.compile("\.\d{1,3}(?:\s\d{3}){0,2}") # e.g.  .001
def get_greeble_obj(greeble_obj_meta, merge_materials = True, names=['greeble', 'object']):
    """Gets greeble Object from name returning None if it is not found."""
    if os.path.isfile(greeble_obj_meta.file_path):
        mat_dupes = None
        with bpy.data.libraries.load(greeble_obj_meta.file_path) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name.lower() in names]
            if merge_materials:
                mat_dupes = [mat for mat in data_from.materials if mat in bpy.data.materials]

        for obj in data_to.objects:
            if obj.type == 'MESH':
                if merge_materials:
                    mats_to_remove = []
                    # Handle any duplicate materials by merging them with the scene.
                    for obj_mat in obj.data.materials:
                        for mat_dupe in mat_dupes:
                            if obj_mat.name.startswith(mat_dupe) and \
                                _trailing_dupe_pattern.match(obj_mat.name[len(mat_dupe):len(obj_mat.name)]):
                                # this is one of the dupes.
                                orig_scene_material = bpy.data.materials[mat_dupe]
                                for slot in obj.material_slots:
                                    if slot.material == obj_mat:
                                        slot.material = orig_scene_material
                                        mats_to_remove.append(obj_mat)
                    for mat_to_remove in mats_to_remove:
                        bpy.data.materials.remove(mat_to_remove)
                return obj
            
    return None



def remove():
    _clear_icons()