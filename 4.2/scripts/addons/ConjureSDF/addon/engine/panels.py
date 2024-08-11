import bpy

from bpy.types import Panel

from .renderer import CSDFRenderEngine



class BasePanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    COMPAT_ENGINES = {CSDFRenderEngine.bl_idname}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

class CSDF_RENDER_PT_settings(Panel, BasePanel):
    """Parent panel for renderer settings"""
    bl_label = 'General'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.csdf
        # No controls at top level.

class CSDF_RENDER_PT_settings_viewport(Panel, BasePanel):
    """Global viewport configurations"""
    bl_label = 'Viewport'
    bl_parent_id = 'CSDF_RENDER_PT_settings'

    def get_shading(cls, context):
        # Get settings from 3D viewport or OpenGL render engine
        view = context.space_data
        if view.type == 'VIEW_3D':
            return view.shading
        else:
            return context.scene.display.shading

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.csdf

        col = layout.column(align=True)
        col.prop(settings, 'clear_color')
        # col.prop(settings, 'ambient_color')

        layout.separator()

        col = layout.column(align=True)
        col.label(text="Quality settings")
        col.prop(settings, 'max_steps')
        col.prop(settings, 'max_distance')
        col.prop(settings, 'min_surface_distance')
        col.prop(settings, 'marching_scale')




class CSDF_RENDER_PT_settings_sources(Panel, BasePanel):
    """Shader source file references and reload settings"""
    bl_label = 'Shader Compiler'
    bl_parent_id = 'CSDF_RENDER_PT_settings'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.csdf

        # col = layout.column(align=True)
        # col.prop(settings, 'vert_filename')
        # col.prop(settings, 'frag_filename')
        # col.prop(settings, 'tesc_filename')
        # col.prop(settings, 'tese_filename')
        # col.prop(settings, 'geom_filename')

        # layout.separator()

        # col = layout.column(align=True)
        # row = col.row(align=True)
        # row.prop(settings, "live_reload", text="Live Reload")
        # row.operator("csdf.reload_sources", text = "Reload")

        # Alert message on compile error
        col = layout.column(align=True)
        col.alert = True

        if settings.last_shader_error:
            col.label(text='Compilation error(s):', icon='ERROR')
            lines = settings.last_shader_error.split('\n')
            for line in lines:
                col.label(text=line)

class CSDF_LIGHT_PT_light(Panel, BasePanel):
    """Custom per-light settings editor for this render engine"""
    bl_label = 'CSDF Light Settings'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return context.light and BasePanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        light = context.light

        settings = context.light.csdf

        col = layout.column(align=True)

        # Only a primary sun light is supported
        if light.type != 'SUN':
            col.label(text='Only Sun lights are supported by CSDF')
            return

        col.prop(light, 'color')

        col.separator()
        col.prop(settings, 'intensity')
