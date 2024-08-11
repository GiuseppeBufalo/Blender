import bpy
from bpy.types import PropertyGroup, Scene
from bpy.props import EnumProperty, PointerProperty, BoolProperty
from pathlib import Path
from .t3dn_bip import previews

class Procedural_Crowds_Data:
    crowd_system_path:Path = Path()
    crowd_system_enum:list = []
    crowd_model_path:Path = Path()
    crowd_model_enum:list = []
    model_categories_path:Path = Path()
    model_categories_enum:list = []
    category_model_map:dict={}
    selected_category = ''
    animation_path:Path = Path()
    animation_enum:list = []
    thumbnails = previews.new(max_size=(128, 128))


class Procedural_Crowds_Properties(PropertyGroup):

    def get_crowd_systems(self, context):
        enum_items=[]
        crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            return enum_items

        path = Path(crowd_sys_dir) / 'Crowd-Systems'
        if path == crowds_data.crowd_system_path:
            return crowds_data.crowd_system_enum
        print(f"Scanning directory: {path}")
        crowds_data.crowd_system_path = path
        for i, dir in enumerate(path.iterdir()):
            if not dir.is_dir():
                continue
            thumbnail_path = next(dir.glob("thumbnail.*"), None)
            thumbnail = 'SYSTEM'
            if thumbnail_path:
                thumbnail = crowds_data.thumbnails.load_safe(dir.name.lower(),str(thumbnail_path),'IMAGE').icon_id
            enum_items.append((dir.name, dir.name.capitalize(), '', thumbnail, i))
        crowds_data.crowd_system_enum = enum_items
        return enum_items

    def get_crowd_models(self, context):
            enum_items=[]
            crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
            crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
            if not crowd_sys_dir:
                return enum_items

            path = Path(crowd_sys_dir) / 'Crowd-Models'
            if path == crowds_data.crowd_model_path:
                return crowds_data.crowd_model_enum
            print(f"Scanning directory: {path}")
            crowds_data.crowd_model_path = path
            for i, dir in enumerate(path.iterdir()):
                if not dir.is_dir():
                    continue
                enum_items.append((dir.name, dir.name.capitalize(), '', 'COLLECTION', i))
            crowds_data.crowd_model_enum = enum_items
            return enum_items


    crowd_system: EnumProperty(items=get_crowd_systems,name="Crowd System", description="")
    crowd_models: EnumProperty(items=get_crowd_models,name="Crowd System", description="")
    
    def get_model_category(self, context):
        enum_items=[]
        crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            return enum_items

        path = Path(crowd_sys_dir) / 'Individuals' / 'Models'
        if path == crowds_data.model_categories_path:
            return crowds_data.model_categories_enum
        print(f"Looking for Model Categories")
        print(f"Scanning directory: {path}")
        crowds_data.model_categories_path = path
        for i, dir in enumerate(path.iterdir()):
            if not dir.is_dir():
                continue
            enum_items.append((dir.name, dir.name, ''))
        crowds_data.model_categories_enum = enum_items
        return enum_items
    
    def update_model_category(self, context):
        props = context.scene.procedural_crowds
        crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
        print(f"Updating category to {props.individual_model_categories}")
        crowds_data.selected_category = props.individual_model_categories

    def get_individual_models(self, context):
        enum_items=[]
        props = context.scene.procedural_crowds
        crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            return enum_items

        path = Path(crowd_sys_dir) / 'Individuals' / 'Models' / props.individual_model_categories
        if props.individual_model_categories == crowds_data.selected_category \
            and props.individual_model_categories != '' \
            and props.individual_model_categories in crowds_data.category_model_map.keys():
                return crowds_data.category_model_map[props.individual_model_categories]
        
        print(f"Looking for Individual Models of category {props.individual_model_categories}")
        print(f"Scanning directory: {path}")
        crowds_data.selected_category = props.individual_model_categories
        for i, dir in enumerate(path.iterdir()):
            if not dir.is_dir():
                continue

            thumbnail_path = next(dir.glob("thumbnail.*"), None)
            thumbnail = 'ASSET_MANAGER'
            if thumbnail_path:
                thumbnail = crowds_data.thumbnails.load_safe(dir.name.lower(),str(thumbnail_path),'IMAGE').icon_id
            enum_items.append((dir.name, dir.name.capitalize(), '', thumbnail, i))
        crowds_data.category_model_map[props.individual_model_categories] = enum_items
        return enum_items
    
    def get_individual_animations(self, context):
        enum_items=[]
        props = context.scene.procedural_crowds
        crowds_data:Procedural_Crowds_Data = context.scene.procedural_crowds_data
        crowd_sys_dir = context.preferences.addons[__package__].preferences.filepath
        if not crowd_sys_dir:
            return enum_items

        path = Path(crowd_sys_dir) / 'Individuals' / 'Animations'
        if path == crowds_data.animation_path:
            return crowds_data.animation_enum
        
        print(f"Looking for Animations")
        print(f"Scanning directory: {path}")
        crowds_data.animation_path = path
        for i, dir in enumerate(path.iterdir()):
            if not dir.is_dir():
                continue
            thumbnail_path = next(dir.glob("thumbnail.*"), None)
            thumbnail = 'ARMATURE_DATA'
            if thumbnail_path:
                thumbnail = crowds_data.thumbnails.load_safe(dir.name.lower(),str(thumbnail_path),'IMAGE').icon_id
            enum_items.append((dir.name, dir.name, '', thumbnail, i))
        crowds_data.animation_enum = enum_items
        return enum_items
    
    individual_model_categories: EnumProperty(items=get_model_category, update=update_model_category, name="Category")
    individual_models: EnumProperty(items=get_individual_models)
    link_individual_models: BoolProperty(name='Link Objects', default= False)
    individual_animations: EnumProperty(items=get_individual_animations)

class Procedural_Crowds_GeoNode_Workaround(PropertyGroup):
    
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    image: bpy.props.PointerProperty(type=bpy.types.Image)
    texture: bpy.props.PointerProperty(type=bpy.types.Texture)
    

classes = [Procedural_Crowds_Properties,Procedural_Crowds_GeoNode_Workaround]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    Scene.procedural_crowds_data = Procedural_Crowds_Data()
    Scene.procedural_crowds = PointerProperty(type=Procedural_Crowds_Properties)
    Scene.procedural_crowds_gn_workaround = PointerProperty(type=Procedural_Crowds_GeoNode_Workaround)
def unregister():
    previews.remove(Scene.procedural_crowds_data.thumbnails)
    del Scene.procedural_crowds
    del Scene.procedural_crowds_data
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)