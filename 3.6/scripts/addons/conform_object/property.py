import sys
import traceback

import bpy

from bpy.types import PropertyGroup, CollectionProperty, StringProperty, PointerProperty, BoolProperty, FloatProperty
from bpy.props import *
from bpy.utils import register_class, unregister_class

class conform_object(PropertyGroup):
    is_conform_obj : BoolProperty(default=False)
    is_conform_shrinkwrap : BoolProperty(default=False)
    is_grid_obj : BoolProperty(default=False)
    original_matrix : bpy.props.FloatVectorProperty(
                                                    size=16,
                                                    subtype="MATRIX")


class conform_object_ui(PropertyGroup):
    update_draw_only : BoolProperty(default=False, options={'SKIP_SAVE'})
    def update_draw(self, context):
        self.update_draw_only = True

    show_projection_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})
    show_orientation_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})
    show_grid_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})
    show_gradient_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})
    show_blend_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})
    show_other_panel : BoolProperty(default=False, update=update_draw, options={'SKIP_SAVE'})

    enable_viewer : BoolProperty(
                    default=False, 
                    options={'SKIP_SAVE'}, 
                    name="Enable Object Mode Vertex Group Visualisation.",
                    description="Enable Object Mode Vertex Group Visualisation. Performance will be slow on complex objects.")
    vertex_group_view_size : IntProperty(default=8, min=1, description="Visual size of the vertices.")
    vertex_group_selection_opts : EnumProperty(items= (
                                        ('SELECTED', 'Selected', 'Display the active vertex groups of all selected objects.'),
                                        ('ACTIVE', 'Active', 'Only display the Active object\'s active vertex group.'),
                                        ('ALL', 'All', 'Display all active vertex groups for all visible objects.')
                                        ),
                                        name = "Zero Weights", default='SELECTED', description='Which objects to display vertex groups for.')

    zero_weights_opts : EnumProperty(items= (('NONE', 'None', 'Do not display vertices which have not been assigned a weight.'),
                                        ('ALL', 'All', 'Display all zero or unassigned weights.')),
                                        name = "Zero Weights", default='ALL', description='How to display weights with zero or none value')

classes = [
    conform_object_ui,
    conform_object]


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.conform_object_ui = PointerProperty(name='Conform Object UI', type=conform_object_ui)
    bpy.types.Object.conform_object = PointerProperty(name='Conform Object', type=conform_object)


def unregister():
    del bpy.types.Object.conform_object

    for cls in classes:
        unregister_class(cls)
