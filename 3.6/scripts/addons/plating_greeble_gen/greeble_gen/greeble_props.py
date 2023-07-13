import bpy
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty
        )

from ..orchestration import decorators
from .. import preferences
from . import greeble_functions, greeble_factory
import uuid

_greeble_uuid_to_remove = ''


def update_prop(self, context):

    if self.is_property_group and \
            context.active_object and \
                context.active_object.plating_generator.auto_update and \
                context.active_object.plating_generator.is_plating_obj:
        # get ref to level
        level = context.active_object.plating_generator.levels[context.active_object.plating_generator.level_index]
        if level.is_enabled:
            decorators.decorate(context.active_object, context)

    return None

category_enum_items = []
def get_greeble_categories(self, context):
    global category_enum_items
    category_enum_items = []
    pref = preferences.preference()
    catalogue = pref.catalogue
    for index, g_c in enumerate(greeble_factory.get_greeble_categories(catalogue)):
        category_name = g_c.category_name
        category_enum_items.append((category_name, 
                                category_name, 
                                category_name,
                                index))
    return category_enum_items

image_enum_items = []
def get_greeble_items(self, context):
    global image_enum_items
    pref = preferences.preference()
    catalogue = pref.catalogue

    image_enum_items = []
    for index, g_m in enumerate(greeble_factory.get_greebles_metadata_from_category(catalogue, self.category)):
        image_enum_items.append((g_m.greeble_name, 
                                g_m.greeble_name[:14], 
                                g_m.greeble_name, 
                                g_m.icon_id, 
                                index))
    return image_enum_items

def apply_greeble_settings_to_all_func(self, context, prop_name, greeble_settings, prefix=''):
    if context.active_object.plating_generator.auto_update:
        context.active_object.plating_generator.auto_update = False
        for item in greeble_settings:
            setattr(item, prop_name, getattr(self, 'all_' + prefix + prop_name))
        context.active_object.plating_generator.auto_update = True
    update_prop(self, context)

greeble_pattern_type_items = (('0', 'Overlapping', ''), ('1', 'Non-Overlapping', ''))

def handle_greeble_entries(self):
    # remove a greeble item if it has been flagged for removal.
    global _greeble_uuid_to_remove
    if _greeble_uuid_to_remove != '':
        # search library greebles...
        i = 0
        item_found = False
        for item in self.library_greebles:
            if item.name == _greeble_uuid_to_remove:
                item_found = True
                break
            i+=1
        if item_found:
            self.library_greebles.remove(i)
        #...then search custom greebles
        i = 0
        item_found = False
        for item in self.custom_greebles:
            if item.name == _greeble_uuid_to_remove:
                item_found = True
                break
            i+=1
        if item_found:
            self.custom_greebles.remove(i)

        _greeble_uuid_to_remove = ''





class SceneGreebleObject(bpy.types.PropertyGroup):
    """A class representing an object in a scene"""
    name : bpy.props.StringProperty(name="Object Name", default="Unknown")


def update_scene_setting(self, context):
    if self.is_property_group and \
            context.active_object and \
                context.active_object.plating_generator.auto_update and \
                context.active_object.plating_generator.is_plating_obj:
        # get ref to level
        level = context.active_object.plating_generator.levels[context.active_object.plating_generator.level_index]
        if level.is_enabled:
            props = level.greeble_props
            handle_greeble_entries(props)
            decorators.decorate(context.active_object, context)
    return None
        

class AbstractSceneGreebleSetting():
    """A class representing an object in a scene"""
    is_property_group : BoolProperty(default=False)
            
    def switch_categories(self, context):
        pref = preferences.preference()
        catalogue = pref.catalogue
        new_greebles = greeble_factory.get_greebles_metadata_from_category(catalogue, self.category)
        if len(new_greebles) > 0 and new_greebles[0].greeble_name != '':
            new_greeble = new_greebles[0]
            self.thumbnail = new_greeble.greeble_name
            self.file_path = new_greeble.file_path
        update_scene_setting(self, context)
        return None

    category : EnumProperty(items=get_greeble_categories, update=switch_categories)

    def switch_thumbnail(self, context):
        pref = preferences.preference()
        catalogue = pref.catalogue
        new_greeble = greeble_factory.get_greebles_metadata_from_name_and_category(catalogue, self.thumbnail, self.category)
        if new_greeble is not None:
            self.file_path = new_greeble.file_path
        update_scene_setting(self, context)
        return None

    thumbnail: EnumProperty(items=get_greeble_items, update=switch_thumbnail)

    scene_ref: StringProperty()

    file_path: StringProperty()

    coverage : FloatProperty(
            name="Object Coverage",
            description="Object Coverage",
            min=0,
            max=100,
            default=100,
            precision=1,
            step=1,
            subtype="PERCENTAGE",
            update=update_scene_setting
            )

    override_materials  : BoolProperty(
            name="Override Materials",
            default=False,
            description="Override the materials of this Greeble",
            update=update_scene_setting
            )

    material_index : IntProperty(
            name="Material Index",
            description="Material Index to assign greeble. -1 will use the original materials of the greeble, otherwise this will assign the material index of the target object's materials.",
            min=0,
            default=0,
            update=update_scene_setting
            )

    override_height  : BoolProperty(
            name="Override Heights",
            default=False,
            description="Override the height of this Greeble",
            update=update_scene_setting
            )

    height_override : FloatProperty(
            name="Height",
            description="Override the height of this Greeble",
            min=0,
            default=0.1,
            precision=3,
            step=1,
            update=update_scene_setting
            )

    keep_aspect_ratio  : BoolProperty(
            name="Maintain Aspect Ratio",
            default=True,
            description="Keep the object's proportions",
            update=update_scene_setting
            )

    def remove_greeble_func(self, context):
        """Internal method for handling removal of greble entries."""
        if self.remove_greeble == True:
            global _greeble_uuid_to_remove
            _greeble_uuid_to_remove = self.name
            self.remove_greeble = False
            update_scene_setting(self, context)

    remove_greeble  : BoolProperty(
            name="Remove Greeble Object",
            default=False,
            update = remove_greeble_func
            )


class SceneGreebleSetting(AbstractSceneGreebleSetting, bpy.types.PropertyGroup):
    pass


def scene_chosenobject_poll(self, object):
    """Filters the object chooser."""
    return object.type == 'MESH'

class SceneGreebleSettingPropertyGroup(AbstractSceneGreebleSetting, bpy.types.PropertyGroup):
    is_property_group : BoolProperty(default=True)

    def update_scene_object(self, context):
        if self.scene_object:
            self.scene_ref = self.scene_object.name
        update_scene_setting(self, context)

    scene_object : PointerProperty(type=bpy.types.Object, update=update_scene_object, poll=scene_chosenobject_poll)

#
# Class that contains plate creation logic.
#
class GreebleProps():
    is_property_group : BoolProperty(default=False)

    greeble_pattern_type : bpy.props.EnumProperty(items= greeble_pattern_type_items,
                                                     name = "Pattern Type", default='0', update=update_prop)

    greeble_amount : IntProperty(
            name="Greeble Amount",
            description="Amount of Greebles",
            min=0,
            default=25,
            update=update_prop
            )

    coverage_amount : FloatProperty(
            name="Overall Coverage %",
            description="Percentage amount of coverage for the greebles",
            min=0,
            max=100,
            default=10,
            subtype="PERCENTAGE",
            update=update_prop
            )

    greeble_random_seed : IntProperty(
            name="Greeble Random Seed",
            description="Random Seed Value for creating greebles",
            min=0,
            default=123456,
            update=update_prop
            )

    greeble_subd_levels : IntProperty(
            name="Greeble Division Levels",
            description="Amount of times the face will be split into to map a greeble.  Higher levels will mean greater and smaller greebles",
            min=0,
            default=1,
            soft_max=2,
            update=update_prop
            )

    greeble_deviation : FloatProperty(
            name="Greeble Deviation",
            description="Deviatation from the center of the rectangle allowed",
            min=0,
            max=1,
            default=0.5,
            update=update_prop
            )

    greeble_min_width : FloatProperty(
            name="Greeble Min Width",
            description="Minimum Width of a Greeble",
            min=0,
            max=1,
            default=0.2,
            precision=3,
            step=1,
            update=update_prop
            )

    greeble_max_width : FloatProperty(
            name="Greeble Max Width",
            description="Maximum Width of a Greeble",
            min=0,
            max=1,
            default=0.8,
            precision=3,
            step=1,
            update=update_prop
            )

    greeble_min_length : FloatProperty(
            name="Greeble Min Length",
            description="Minimum Length of a Greeble",
            min=0,
            max=1,
            default=0.2,
            precision=3,
            step=1,
            update=update_prop
            )

    greeble_max_length : FloatProperty(
            name="Greeble Max Length",
            description="Maximum Length of a Greeble",
            min=0,
            max=1,
            default=0.8,
            precision=3,
            step=1,
            update=update_prop
            )

    greeble_min_height : FloatProperty(
            name="Greeble Min Height",
            description="Minimum Height of a Greeble",
            min=0,
            default=0,
            precision=3,
            step=1,
            update=update_prop
            )

    greeble_max_height : FloatProperty(
            name="Greeble Max Height",
            description="Maximum Height of a Greeble",
            min=0,
            default=0.1,
            precision=3,
            step=1,
            update=update_prop
            )

    is_custom_normal_direction : BoolProperty(
            name="Use Custom Direction",
            default=False,
            description="Use a custom direction when adding greebles",
            update=update_prop
            )

    custom_normal_direction : FloatVectorProperty(
            name="Outwards Direction",
            description="Custom upwards direction of greebles",
            subtype='XYZ',
            default=[0,0,1],
            min=-1,
            max=1,
            step=1,
            update=update_prop
            )

    greeble_rotation_seed : IntProperty(
            name="Greeble Random Rotation Seed",
            description="Random Seed Value for rotating greebles",
            min=0,
            default=123456,
            update=update_prop
            )

    is_custom_rotation : BoolProperty(
            name="Do not randomly rotate",
            default=False,
            description="Do not randomly rotate the orientation of the greeble",
            update=update_prop
            )

    custom_rotate_amount : IntProperty(
            name="Number of 90 degree rotations",
            min=0,
            default=0,
            update=update_prop
            )

    add_vertex_colors_to_greebles : BoolProperty(
            name="Add Random Vertex Colors",
            description="Add random vertex coloring to the greebles",
            default=False,
            update=update_prop
            )

    vertex_colors_random_seed : IntProperty(
        name="Vertex Color Random Seed",
        description="Seed for assigning vertex colors",
        default=123456,
        update=update_prop
        )

    vertex_colors_layer_name : StringProperty(
        name="Vertex Color Layer Name",
        description="Name of vertex color layer",
        default="plating_color",
        update=update_prop
        )

    category_to_add_remove : EnumProperty(items=get_greeble_categories,
            update=update_prop)

    def add_from_lib(self, context):
        """Internal function to handle adding of greeble entries"""
        if self.add_greebles_from_lib == True:
            pref = preferences.preference()
            catalogue = pref.catalogue
            for g_m in greeble_factory.get_greebles_metadata_from_category(catalogue, self.category_to_add_remove):
                    item = self.library_greebles.add()
                    #assign a uuid for later handling.
                    item.name = str(uuid.uuid4())
                    item.category = self.category_to_add_remove
                    item.thumbnail = g_m.greeble_name
                    item.file_path = g_m.file_path
            self.add_greebles_from_lib = False
            update_prop(self, context)

    add_greebles_from_lib  : BoolProperty(
            name="Add All Greeble Objects from this library",
            default=False,
            update = add_from_lib
            )

    def remove_from_lib(self, context):
        """Internal function to handle removal of greeble entries"""
        if self.remove_greebles_from_lib == True:
            library_greeble_uuids_to_remove = []
            for library_greeble in self.library_greebles:
                if library_greeble.category == self.category_to_add_remove:
                    library_greeble_uuids_to_remove.append(library_greeble.name)
            for library_greeble_uuid_to_remove in library_greeble_uuids_to_remove:
                for i in range(0, len(self.library_greebles)):
                    library_greeble = self.library_greebles[i]
                    if library_greeble.name == library_greeble_uuid_to_remove:
                        self.library_greebles.remove(i)
                        break
            self.remove_greebles_from_lib = False
            update_prop(self, context)


    remove_greebles_from_lib  : BoolProperty(
            name="Clear All Greeble Objects in this library",
            default=False,
            update = remove_from_lib
            )

    def add_lib(self, context):
        """Internal function to handle adding of greeble entries"""
        if self.add_greeble_lib == True:
            pref = preferences.preference()
            catalogue = pref.catalogue
            item = self.library_greebles.add()
            #assign a uuid for later handling.
            item.name =  str(uuid.uuid4())
            item.category = self.category_to_add_remove
            self.add_greeble_lib = False
            update_prop(self, context)

    add_greeble_lib  : BoolProperty(
            name="Add Greeble Object from this library",
            default=False,
            update = add_lib
            )

    def clear_lib(self, context):
        """Internal function to clear library greeble entries"""
        if self.clear_greeble_lib == True:
            self.library_greebles.clear()
            self.clear_greeble_lib = False
            update_prop(self, context)

    clear_greeble_lib  : BoolProperty(
            name="Clear Greeble Objects",
            default=False,
            update = clear_lib
            )

    def clear_cust(self, context):
        """Internal function to clear custom greeble entries"""
        if self.clear_greeble_cust == True:
            self.custom_greebles.clear()
            self.clear_greeble_cust = False
            update_prop(self, context)

    clear_greeble_cust  : BoolProperty(
            name="Clear Greeble Objects",
            default=False,
            update = clear_cust
            )


    def add_cust(self, context):
        """Internal function to handle adding of greeble entries"""
        if self.add_greeble_cust == True:
            item = self.custom_greebles.add()
            #assign a uuid for later handling.
            item.name =  str(uuid.uuid4())
            self.add_greeble_cust = False
            update_prop(self, context)

    add_greeble_cust  : BoolProperty(
            name="Add Custom Greeble Object",
            default=False,
            update = add_cust
            )

    load_greebles : BoolProperty(default=True)

    library_greebles : CollectionProperty(type=SceneGreebleSetting)

    custom_greebles : CollectionProperty(type=SceneGreebleSetting)

    scene_objects : CollectionProperty(type=SceneGreebleObject, options={'SKIP_SAVE'})

    create_new  : BoolProperty(
            name="Create New Object",
            default=False
            )

    update_draw_only : BoolProperty(default=False, options={'SKIP_SAVE'})
    def update_draw(self, context):
        self.update_draw_only = True

    def apply_greeble_settings_to_keep_aspect_ratio_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'keep_aspect_ratio', self.library_greebles)
        
    def apply_greeble_settings_to_override_materials_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'override_materials', self.library_greebles)

    def apply_greeble_settings_to_override_height_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'override_height', self.library_greebles)

    def apply_greeble_settings_to_custom_keep_aspect_ratio_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'keep_aspect_ratio', self.custom_greebles, 'custom_')
        
    def apply_greeble_settings_to_custom_override_materials_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'override_materials', self.custom_greebles, 'custom_')

    def apply_greeble_settings_to_custom_override_height_func(self, context):
        apply_greeble_settings_to_all_func(self, context, 'override_height', self.custom_greebles, 'custom_')

    all_keep_aspect_ratio  : BoolProperty(
            name="Maintain Aspect Ratio",
            default=True,
            description="Keep the object's proportions",
            update=apply_greeble_settings_to_keep_aspect_ratio_func,
            options={'SKIP_SAVE'}
            )

    all_override_materials  : BoolProperty(
            name="Override Materials",
            default=False,
            description="Override the materials of this Greeble",
            update=apply_greeble_settings_to_override_materials_func
            )

    all_override_height  : BoolProperty(
            name="Override Heights",
            default=False,
            description="Override the height of this Greeble",
            update=apply_greeble_settings_to_override_height_func
            )
    

    all_custom_keep_aspect_ratio  : BoolProperty(
            name="Maintain Aspect Ratio",
            default=True,
            description="Keep the object's proportions",
            update=apply_greeble_settings_to_custom_keep_aspect_ratio_func
            )

    all_custom_override_materials  : BoolProperty(
            name="Override Materials",
            default=False,
            description="Override the materials of this Greeble",
            update=apply_greeble_settings_to_custom_override_materials_func
            )

    all_custom_override_height  : BoolProperty(
            name="Override Heights",
            default=False,
            description="Override the height of this Greeble",
            update=apply_greeble_settings_to_custom_override_height_func
            )



    #cosmetics

    show_greeble_pattern_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_greeble_parameters_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_default_greebles_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_custom_greebles_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})
    show_greeble_orientation_panel : BoolProperty(default=False,update=update_draw, options={'SKIP_SAVE'})

    default_greeble_names = ['Square',
                                'Double Square',
                                'Triple Square',
                                'L Shape',
                                'T Shape',
                                'Cylinder']


   
class GreeblePropsPropertyGroup(GreebleProps, bpy.types.PropertyGroup):
    is_property_group : BoolProperty(default=True)

    library_greebles : CollectionProperty(type=SceneGreebleSettingPropertyGroup)

    custom_greebles : CollectionProperty(type=SceneGreebleSettingPropertyGroup)