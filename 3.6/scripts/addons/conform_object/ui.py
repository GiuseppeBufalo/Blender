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

classes = [
    CONFORMOBJECT_PT_VertexVisPanel
    ]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in classes:
        unregister_class(cls)
