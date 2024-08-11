import bpy
from bpy.types import Panel

from ...engine.renderer import CSDFRenderEngine

class BasePanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    
    COMPAT_ENGINES = {CSDFRenderEngine.bl_idname}

    @classmethod
    def poll(cls, context):

        if context.engine in cls.COMPAT_ENGINES:
            if context.space_data.shading.type == 'RENDERED':
                return True

        return False

class CSDF_PT_shading_lighting(Panel, BasePanel):
    bl_parent_id = 'VIEW3D_PT_shading'
    bl_label = "Lighting"

    def get_shading(cls, context):
        # Get settings from 3D viewport or OpenGL render engine
        view = context.space_data
        if view.type == 'VIEW_3D':
            return view.shading
        else:
            return context.scene.display.shading

    def draw(self, context):
        layout = self.layout
        shading = context.scene.display.shading

        # not allowed in panel draw
        # shading.light = 'MATCAP'

        # only affects the solid (unrendered) view
        # area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
        # for sp in area.spaces:
        #     if sp.type == 'VIEW_3D':
        #         sp.shading.light = 'MATCAP'

        # context.space_data.shading.light = 'MATCAP'


        col = layout.column()
        split = col.split(factor=0.9)

        split.row().prop(shading, "light", expand=True)
        col = split.column()

        split = layout.split(factor=0.9)
        col = split.column()
        sub = col.row()

        sub.scale_y = 0.6  # smaller studiolight preview
        sub.template_icon_view(shading, "studio_light", scale_popup=3.0)


class CSDF_PT_overlays(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    
    COMPAT_ENGINES = {CSDFRenderEngine.bl_idname}

    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "ConjureSDF Overlays"

    def draw(self, context):
        layout = self.layout

        settings = context.scene.csdf

        col = layout.column()
        col.prop(settings, "draw_wire", text="Display non Unions as wire")
