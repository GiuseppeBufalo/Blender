
import bpy
import json
# from . import distributors
from .. orchestration.properties import PlatingObject
# from kitops.addon.utility import addon as kitops_addon
import uuid


def as_recipe(dct):
     if '__recipe__' in dct:
         return complex(dct['real'], dct['imag'])
     return dct

def _encode_plating_props(props):
    """Encode Plating Properties"""

    dict_to_return = {}

    for pointer in dir(props):
        if '__' in pointer or pointer in {'bl_rna', 'rna_type', 'type', 'face_count', 'falloff_curve', 'vertex_indices', 'vertex_indices_set', 'is_property_group', 'auto_update'}:
            continue

        self_attr = getattr(props, pointer, None)
        
        if self_attr != None:
            # try:
            if pointer in {'plating_materials'}:
                plating_materials = self_attr
                plating_mat_names = [mat.name for mat in plating_materials]
                
                dict_to_return[pointer] = plating_mat_names

                #     plating_materials = getattr(self, pointer, None)
                #     for plating_material in plating_materials:
                #         plating_materials_to_copy.append(plating_material)
            else:
                dict_to_return[pointer] = self_attr
                # setattr(props, pointer, self_attr)
            # except AttributeError:
            #     print('Trouble copying: ', pointer)

    return dict_to_return


def _encode_greeble_props(props):
    """Encode Greeble Properties"""

    dict_to_return = {}

    for pointer in dir(props):
        if '__' in pointer or pointer in {'bl_rna', 'rna_type', 'type', 'face_count', 'falloff_curve', 'vertex_indices', 'vertex_indices_set', 'is_property_group', 'auto_update', 'update_draw_only'}:
            continue

        self_attr = getattr(props, pointer, None)
        
        if self_attr != None:

            if pointer in  {'library_greebles', 'custom_greebles', 'scene_objects'}:
                setting_entries = []
                entries = self_attr
                for entry in entries:
                    item = _encode_SceneGreebleSetting(entry)

                    setting_entries.append(item)
                
                dict_to_return[pointer] = setting_entries

            elif pointer in {'custom_normal_direction'}:
                dict_to_return[pointer] = (self_attr[0], self_attr[1], self_attr[2])

            elif pointer in {'plating_materials'}:
                plating_materials = self_attr
                plating_mat_names = [mat.name for mat in plating_materials]
                
                dict_to_return[pointer] = plating_mat_names

                #     plating_materials = getattr(self, pointer, None)
                #     for plating_material in plating_materials:
                #         plating_materials_to_copy.append(plating_material)
            else:
                dict_to_return[pointer] = self_attr
                # setattr(props, pointer, self_attr)
            # except AttributeError:
            #     print('Trouble copying: ', pointer)

    return dict_to_return

def _encode_SceneGreebleSetting(props):

    return {
            'name'                  : props.name,
            'category'              : props.category,
            'thumbnail'             : props.thumbnail,
            'scene_ref'             : props.scene_ref,
            'file_path'             : props.file_path,
            'coverage'              : props.coverage,
            'override_materials'    : props.override_materials,
            'material_index'        : props.material_index,
            'override_height'       : props.override_height,
            'height_override'       : props.height_override,
            'keep_aspect_ratio'     : props.keep_aspect_ratio,
            'remove_greeble'        : props.remove_greeble,
            'scene_object' : props.scene_object.name if props.scene_object else None
    }

def _encode_distribution(level):
    distribution_class_name = level.distribution
    distributor = getattr(distributors, distribution_class_name)()
    return {
        'type' : level.distribution,
        'parameters' : distributor.encode(level)
    }

class PresetEncoder(json.JSONEncoder):
    """Encodes a Plating Generator Preset"""
    def default(self, obj):
        plating_generator = obj
        levels_to_encode = [{
                                'name' : level.name,
                                'level_name' : level.level_name,
                                'is_enabled' : level.is_enabled,
                                'visible' : level.visible,
                                'type' : level.type,
                                'plating_props' : _encode_plating_props(level.plating_props),
                                'greeble_props' : _encode_greeble_props(level.greeble_props),
                                'selection_level' : level.selection_level,
                                'selection_type' : [selection_type for selection_type in level.selection_type],
                                'select_remaining' : level.select_remaining,
                                'min_selection_area' : level.min_selection_area,
                                'selection_amount' : level.selection_amount,
                                'selection_amount_seed' : level.selection_amount_seed,
                                'level_color' : (level.level_color[0], level.level_color[1], level.level_color[2], level.level_color[3]),

                            } for level in plating_generator.levels]
        return {
            'master_seed' : plating_generator.master_seed, # TODO implement description?
            'generate_uvs' : plating_generator.generate_uvs,
            'uv_projection_limit' : plating_generator.uv_projection_limit,
            'levels' : levels_to_encode
        }


def _decode_plating_props(propsJSON, props):
    for propJSON in propsJSON:
        if propJSON == 'plating_materials':
            props.plating_materials.clear()
            for mat in propsJSON[propJSON]:
                plating_material = props.plating_materials.add()
                plating_material.name = mat

        else:
            setattr(props, propJSON, propsJSON[propJSON])

def _decode_SceneGreebleSetting(propsJSON, props):
        props.name = propsJSON['name']
        props.category = propsJSON['category']
        props.thumbnail = propsJSON['thumbnail']
        props.scene_ref = propsJSON['scene_ref']
        props.file_path = propsJSON['file_path']
        props.coverage = propsJSON['coverage']
        props.override_materials = propsJSON['override_materials']
        props.material_index = propsJSON['material_index']
        props.override_height = propsJSON['override_height']
        props.height_override = propsJSON['height_override']
        props.keep_aspect_ratio = propsJSON['keep_aspect_ratio']
        props.remove_greeble = propsJSON['remove_greeble']

        if propsJSON['scene_object']:
            if propsJSON['scene_object'] in bpy.data.objects:
                obj = bpy.data.objects[propsJSON['scene_object']]
                props.scene_object = obj

def _decode_greeble_props(propsJSON, props):
    for propJSON in propsJSON:
        if propJSON in {'library_greebles', 'custom_greebles', 'scene_objects'}:
            entries = propsJSON[propJSON]
            getattr(props, propJSON).clear()
            for entry in entries:
                item = getattr(props, propJSON).add()
                _decode_SceneGreebleSetting(entry, item)

        else:
            setattr(props, propJSON, propsJSON[propJSON])

def decode_preset(recipeJSON, context):
    plating_generator = context.active_object.plating_generator
    plating_generator.master_seed = recipeJSON['master_seed']
    plating_generator.generate_uvs = recipeJSON['generate_uvs']
    plating_generator.uv_projection_limit = recipeJSON['generate_uvs']

    plating_generator.level_index = 0
    plating_generator.levels.clear()
    for levelJSON in recipeJSON['levels']:
        level = plating_generator.levels.add()        
        level.name = levelJSON['name']
        level.level_name = levelJSON['level_name']
        level.is_enabled = levelJSON['is_enabled']
        level.visible = levelJSON['visible']
        level.type = levelJSON['type']
        _decode_plating_props(levelJSON['plating_props'] , level.plating_props)
        _decode_greeble_props(levelJSON['greeble_props'] , level.greeble_props)
        level.selection_level = levelJSON['selection_level']
        selection_type_set = []
        for selection_type in levelJSON['selection_type']:
            selection_type_set.append(selection_type)
        level.selection_type = set(selection_type_set)
        level.select_remaining  = levelJSON['select_remaining']
        level.min_selection_area = levelJSON['min_selection_area']
        level.selection_amount = levelJSON['selection_amount']
        level.selection_amount_seed = levelJSON['selection_amount_seed']
        level_color = levelJSON['level_color']
        level.level_color = level_color



    

