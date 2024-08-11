##################################################
# Properties for orchestration
##################################################

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        EnumProperty,
        StringProperty,
        PointerProperty,
        CollectionProperty
        )
from . import decorators
from ..plating_gen.plating_props import PlatingGeneratorPropsPropertyGroup
from ..greeble_gen.greeble_props import GreeblePropsPropertyGroup

class FaceRef(PropertyGroup):
    """Reference ids for faces."""
    face_id : IntProperty(default=-1)

class EdgeRef(PropertyGroup):
    """Reference ids for edges."""
    edge_id : IntProperty(default=-1)

# global references to enumerators that Blender needs.
selection_types = {}
empty = []
def get_selection_types(self, context):
    """get possible selection types for the level."""
    global selection_types
    global empty
    if self.type in selection_types:
        selection_types[self.name].clear()

    if 0 <= int(self.selection_level) - 1 < len(context.active_object.plating_generator.levels):
        selection_level = context.active_object.plating_generator.levels[int(self.selection_level) -1]
        selection_types[self.name] = decorators.get_selection_types(selection_level.type)
        if len(selection_types[self.name]) == 1:
            return empty
        return selection_types[self.name]

    return empty

def update_all(self, context):
    """Update everything in the active object is it is in the right state."""
    if context.active_object and \
            context.active_object.plating_generator.is_plating_obj and \
                context.active_object.plating_generator.auto_update:
        decorators.decorate(context.active_object, context)

def update_level(self, context):
    """Update all if that level is enabled."""
    if self.is_enabled and context.active_object and \
            context.active_object.plating_generator.is_plating_obj and \
                context.active_object.plating_generator.auto_update:
        decorators.decorate(context.active_object, context)

# global reference for Blender.
selection_levels = {}
def get_selection_levels(self, context):
    """Get all possible selection levels for this level, ie the ones below it."""
    if context.active_object:
        global selection_levels
        if 'DEFAULT' not in selection_levels:
            selection_levels['DEFAULT'] = ('0', 'Original Object', '')
        current_index = context.active_object.plating_generator.levels.find(self.name)
        levels = context.active_object.plating_generator.levels
        if self.name in selection_levels:
            selection_levels[self.name].clear()
        numbers = []
        numbers.append(selection_levels['DEFAULT'])
        for i in range(0, current_index):
            numbers.append((str(i+1), 'Level ' + str(i+1) + ': ' + levels[i].level_name, ''))
        selection_levels[self.name] = numbers
        return numbers
    global empty
    return empty

def update_selection_level(self, context):
    """When a level is updated, set the selection type to default."""
    try:
        self.selection_type = {'0'}
    except ValueError:
        pass
    update_level(self, context)
    return None

class Level(PropertyGroup):
    """Class represeting a level and its properties for orchestration."""
    # level name.
    level_name : StringProperty(default="<Enter Name>")
    # Whether it is enabled for processing or not.
    is_enabled : BoolProperty(default=False, name="Is Enabled", description="Enable the Level for processing", update=update_all)
    visible : BoolProperty(default=True, name="Is Visible", description="Whether the Level is visible", update=update_all)
    # type of the level.
    type : EnumProperty(name="Level Type", items=decorators.decorator_method_items, update=update_level)
    #properties pertaining to the decorators.
    plating_props : PointerProperty(type=PlatingGeneratorPropsPropertyGroup)
    greeble_props : PointerProperty(type=GreeblePropsPropertyGroup)
    # which level this level will be processing on top of.
    selection_level : EnumProperty(name ="Build On", items=get_selection_levels, update=update_selection_level)
    # the type of selection the selection level can operate on (e.g Tops and Bottoms)
    selection_type : EnumProperty(name="Selection Type", items=get_selection_types, update=update_level, options = {"ENUM_FLAG"})
    select_remaining : BoolProperty(default=False, name="Select Remaining", description="Only select faces that have not been used by previous levels.", update=update_all)

    # Minimum allowed face area to perform processing on.
    min_selection_area : FloatProperty(
                name = "Min Face Area",
                description = "Minimum size of the faces to allowed",
                min=0,
                default=0,
                step=1,
                precision=3,
                update=update_level
            )
    # how much of the faces should be operated on, a random percentage of them.
    selection_amount : FloatProperty(
            name="Selection %",
            description="Amount of faces to select",
            subtype="PERCENTAGE",
            min=0,
            max=100,
            default=100,
            step=1,
            update=update_level
            )
    # how to randomise the selection amount.
    selection_amount_seed : IntProperty(
            name="Selection Seed",
            description="Random Seed Value for selecting faces",
            min=0,
            default=123456,
            update=update_level
            )
    # associated color of the level.
    level_color : FloatVectorProperty(name="Level Color",
                                        description="Color for distingishing between levels in User Interface",
                                        subtype='COLOR',
                                        size=4,
                                        default=[1, 0.266, 0, 1])

class PlatingObject(PropertyGroup):
    """Class that represents a plating object"""
    # Is this a plating object?
    is_plating_obj : BoolProperty(default=False)

    auto_update : BoolProperty(
        name="Auto Update",
        description="Updating a property will automatically update the object",
        default=True)

    master_seed : IntProperty(
            name="Master Seed",
            description="Master Seed Value for generating greeble",
            min=0,
            default=123456,
            update=update_all
            )

    # the reference object for generating effects on.
    parent_obj : PointerProperty(type=bpy.types.Object)

    # references to selected face ids and edges ids when manipulating the base mesh.
    face_ids: CollectionProperty(type=FaceRef)
    edge_ids: CollectionProperty(type=EdgeRef)

    # what levels this plating object has.
    levels :  CollectionProperty(type=Level)
    level_index : IntProperty(name = "", default = 0)#, update=update_selection)

    generate_uvs : BoolProperty (
        name= "Generate UVS",
        description = "Automatically generate UVs.  Otherwise, the existing mapping will be kept.",
        default = True,
        update = update_all
    )

    uv_projection_limit : FloatProperty(
            name="Angle Limit",
            description="For mapping UVs. Lower for more projection groups, higher for less distortion.",
            default=66.0,
            min=1,
            max=89,
            update=update_all
            )

    

render_engines = []
def get_render_engines(self, context):
    """Get a list of the available render engines."""
    global render_engines
    render_engines = []
    render_engines.append(("SAME" , "Same as Scene" , ""))
    render_engines.append(("BLENDER_EEVEE" , "Eevee" , ""))
    render_engines.append(("BLENDER_WORKBENCH", "Workbench", ""))
    for render_engine_cls in bpy.types.RenderEngine.__subclasses__():
        render_engines.append((render_engine_cls.bl_idname, render_engine_cls.bl_label, ""))
    return render_engines

class PlatingGeneratorIterator(PropertyGroup):
    """Class holding properties for the plating generator iterator."""

    file_path: StringProperty(
            name = 'Folder Path',
            description = 'Folder Output Path',
            subtype = 'DIR_PATH',
            default = '/tmp\\')

    def check_start(self, context):
        if self.start_seed >= self.end_seed:
            self.end_seed = self.start_seed + 1

    start_seed : IntProperty(
            name='Start Random Seed',
            description='Seed Value for generating',
            min=0,
            default=0,
            update = check_start
            )

    def check_end(self, context):
        if self.end_seed <= self.start_seed:
            self.start_seed = self.end_seed - 1

    end_seed : IntProperty(
            name='End Random Seed',
            description='Seed Value for generating',
            min=0,
            default=0,
            update = check_end
            )

    render_engine : EnumProperty(
        name = "Render Engine",
        description = "Engine to use while rendering",
        default=0,
        items = get_render_engines
    )


classes = [FaceRef, EdgeRef, Level, PlatingObject, PlatingGeneratorIterator]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.plating_generator = PointerProperty(name='Plating Generator Properties', type=PlatingObject)
    bpy.types.Scene.plating_generator_iterator = PointerProperty(name='Shape Generator Iterator', type=PlatingGeneratorIterator)
    

def unregister():
    del bpy.types.Scene.plating_generator_iterator
    del bpy.types.Object.plating_generator
    for cls in classes:
        bpy.utils.unregister_class(cls)