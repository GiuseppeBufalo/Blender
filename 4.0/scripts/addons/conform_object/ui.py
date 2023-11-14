import bpy
from bpy.types import Panel, UIList
from bpy.utils import register_class, unregister_class

class CONFORMOBJECT_PT_VertexVisPanel(bpy.types.Panel):
    """Conform Object Panel"""
    bl_idname = "CONFORMOBJECT_PT_VertexVisPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay_object'
    bl_label = "Vertex Object Mode Visualization"


    @classmethod
    def poll(self, context):
        return context.object.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "INVOKE_DEFAULT"
        layout.prop(context.window_manager.conform_object_ui, 'enable_viewer', text="Vertex Group Weights")
        layout_sub = layout.column()
        layout_sub.enabled = context.window_manager.conform_object_ui.enable_viewer
        layout_sub.prop(context.window_manager.conform_object_ui, 'vertex_group_view_size', text="Vertex Size")

        
        layout_sub_row = layout_sub.row()
        layout_sub_row.label(text="Selection")
        layout_sub_row.prop(context.window_manager.conform_object_ui, 'vertex_group_selection_opts', expand=True)

        
        layout_sub_row = layout_sub.row()
        layout_sub_row.label(text="Zero Weights")
        layout_sub_row.prop(context.window_manager.conform_object_ui, 'zero_weights_opts', expand=True)


class OBJECT_PT_conform_panel(bpy.types.Panel):
    bl_label = "Conform Object"
    bl_idname = "OBJECT_PT_conform"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    # bl_parent_id = 'DATA_PT_lattice'

    @classmethod
    def poll(cls, context):
        return context.view_layer.objects.active and context.view_layer.objects.active.conform_object.is_conform_obj

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        grid_obj = None
        grid_objs = [c for c in context.view_layer.objects.active.children if c.conform_object.is_grid_obj]
        if grid_objs:
            grid_obj = grid_objs[0]
        depressed = not grid_obj.hide_viewport
        col.operator('conform_object.toggle_grid_visibility_from_source_object', text="Toggle Grid Visibility", depress=depressed )

        if grid_obj:
            lattice_obj = None
            lattice_objs = [l for l in grid_obj.children if l.type == 'LATTICE' and l.conform_object.is_conform_lattice]
            if lattice_objs:
                lattice_obj = lattice_objs[0]
                depressed=not lattice_obj.hide_viewport
                col.operator('conform_object.toggle_lattice_visibility_from_source_object', text="Toggle Lattice Visibility", depress=depressed )
        

class LATTICE_PT_conform_panel(bpy.types.Panel):
    bl_label = "Conform Object"
    bl_idname = "LATTICE_PT_conform"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = 'DATA_PT_lattice'

    @classmethod
    def poll(cls, context):
        return context.lattice is not None and context.view_layer.objects.active and context.view_layer.objects.active.conform_object.source_obj

    def draw(self, context):
        layout = self.layout

        hide_select = context.view_layer.objects.active.conform_object.source_obj.hide_select
        snapping_mode = context.scene.tool_settings.use_snap and context.scene.tool_settings.snap_elements == {'FACE'} and \
                        context.scene.tool_settings.use_snap_align_rotation and context.scene.tool_settings.use_snap_project


        col = layout.column(align=True)
        col.separator()
        col.prop(context.view_layer.objects.active, 'show_in_front', text="Show Lattice in Front", toggle=True)
        col.separator()
        col.prop(context.view_layer.objects.active.conform_object, 'toggle_lattice_visible', text=" Toggle Lattice Visibility", toggle=True)
        
        col = layout.column(align=True)
        box = col.box()
        col = box.column(align=True)
        col.prop(context.view_layer.objects.active.conform_object, 'toggle_lattice_edit_mode', text="Toggle All Lattice Edit Mode Settings", icon="SNAP_ON", toggle=True)
        col.separator()
        col.operator('conform_object.toggle_active_unselectable', depress=hide_select, text="Source Object Non-Selectable" if hide_select else "Source Object Selectable", icon="FILTER" )
        col.operator('conform_object.toggle_snapping', icon='SNAP_FACE', depress=snapping_mode, text="Surface Snapping")
        col.prop(context.scene.tool_settings, 'use_snap_selectable', text="Exclude Non-Selectable", toggle=True, icon='RESTRICT_SELECT_OFF')

        col = layout.column(align=True)
        depressed = context.view_layer.objects.active.parent and context.view_layer.objects.active.parent.conform_object.is_grid_obj and not context.view_layer.objects.active.parent.hide_viewport
        col.operator('conform_object.toggle_grid_visibility_from_lattice', text="Toggle Grid Visibility", depress=depressed )

classes = [
    CONFORMOBJECT_PT_VertexVisPanel, LATTICE_PT_conform_panel, OBJECT_PT_conform_panel
    ]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
