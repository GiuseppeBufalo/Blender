import bpy

from .. utils import addon


class CURVEBASH_OT_draw_curve_tool(bpy.types.Operator):

    bl_idname = 'object.curvebash_draw_curve'
    bl_label = 'ARMORED Draw Curve Tool'
    bl_description = 'Activates the Draw Curve tool'
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
        # return context.mode in ['OBJECT']
        # return context.mode in ['OBJECT', 'EDIT_MESH']

    def execute(self, context):
        
        bpy.ops.curve.primitive_bezier_curve_add()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.delete(type='VERT')

        bpy.ops.wm.tool_set_by_id(name='builtin.draw')

        bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = 'SURFACE'
        bpy.context.scene.tool_settings.curve_paint_settings.error_threshold = 16
        bpy.context.scene.tool_settings.curve_paint_settings.use_offset_absolute = True
        # bpy.context.scene.tool_settings.curve_paint_settings.surface_offset = 0.1

        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.separator()
    self.layout.operator('object.curvebash_draw_curve', text='Draw Curve', icon='CURVE_BEZCURVE')


classes = (
    CURVEBASH_OT_draw_curve_tool,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_curve_add.append(draw_menu)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_curve_add.remove(draw_menu)
