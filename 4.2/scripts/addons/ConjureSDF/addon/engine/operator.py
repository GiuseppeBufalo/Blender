import bpy


class CSDF_OT_RELOADSOURCES(bpy.types.Operator):
    """Operator to force reload of shader source files"""
    bl_idname = 'csdf.reload_sources'
    bl_label = 'Reload Shader Sources'

    def invoke(self, context, event):
        context.scene.csdf.force_reload = True

        return {'FINISHED'}
