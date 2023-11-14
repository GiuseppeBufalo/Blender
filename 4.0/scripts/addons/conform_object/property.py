import sys
import traceback

import bpy

from bpy.types import PropertyGroup, CollectionProperty, StringProperty, PointerProperty, BoolProperty, FloatProperty
from bpy.props import *
from bpy.utils import register_class, unregister_class

def set_lattice_visibility(self, context):
    if context.lattice and context.view_layer.objects.active.type == 'LATTICE':
        is_visible = not self.toggle_lattice_visible
        context.object.hide_set(is_visible) # EYE icon
        context.object.hide_viewport = is_visible # MONITOR icon
        context.object.hide_render = is_visible # RENDER icon
        
    return None

def set_lattice_edit_mode(self, context):

    context.scene.tool_settings.use_snap = self.toggle_lattice_edit_mode
    if context.scene.tool_settings.use_snap:
        context.scene.tool_settings.snap_elements = {'FACE'}
    else:
        context.scene.tool_settings.snap_elements = {'INCREMENT'}
    context.scene.tool_settings.use_snap_align_rotation = context.scene.tool_settings.use_snap
    context.scene.tool_settings.use_snap_project = context.scene.tool_settings.use_snap
    
    # set outliner display.
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'OUTLINER':
                for space in area.spaces:
                    if space.type == 'OUTLINER':
                        # now you can access space.show_restrict_column_select
                        space.show_restrict_column_select = True
                        break


    # Set active object unselectable
    if context.view_layer.objects.active.conform_object.source_obj:
        context.view_layer.objects.active.conform_object.source_obj.hide_select = self.toggle_lattice_edit_mode

    context.scene.tool_settings.use_snap_selectable=self.toggle_lattice_edit_mode

    '''Redraw every region in Blender.'''
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            for region in area.regions:
                region.tag_redraw()
    
    return None

class conform_object(PropertyGroup):
    is_conform_obj : BoolProperty(default=False)
    is_conform_shrinkwrap : BoolProperty(default=False)
    is_grid_obj : BoolProperty(default=False)
    is_conform_lattice : BoolProperty(default=False)
    source_obj : PointerProperty(type=bpy.types.Object)
    original_matrix : bpy.props.FloatVectorProperty(
                                                    size=16,
                                                    subtype="MATRIX")
    toggle_lattice_edit_mode : BoolProperty(
        default=False, 
        description="Toggle all settings to make the lattice editable without the source object interfering",
        update=set_lattice_edit_mode
    )

    toggle_lattice_visible : BoolProperty(
        default=True, 
        description="Toggle Lattice visibility in viewport and render modes",
        update=set_lattice_visibility
    )

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
