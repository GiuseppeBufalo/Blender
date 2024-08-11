import bpy

from .renderer import CSDFRenderEngine

from .operator import CSDF_OT_RELOADSOURCES
from .settings import CSDFLightSettings, CSDFRendererSettings
from .panels import CSDF_LIGHT_PT_light, CSDF_RENDER_PT_settings, CSDF_RENDER_PT_settings_sources, CSDF_RENDER_PT_settings_viewport

# Classes to (un)register as part of this addon
classes = (
    CSDFRenderEngine,

    # Operators
    CSDF_OT_RELOADSOURCES,

    # Settings
    CSDFRendererSettings,
    CSDFLightSettings,

    # Renderer panels
    CSDF_RENDER_PT_settings,
    CSDF_RENDER_PT_settings_viewport,
    CSDF_RENDER_PT_settings_sources,

    # Light panels
    CSDF_LIGHT_PT_light
)

# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
        'VIEWLAYER_PT_filter',
        'VIEWLAYER_PT_layer_passes',
        'RENDER_PT_freestyle',
        'RENDER_PT_simplify',
        'RENDER_PT_gpencil',
        'DATA_PT_vertex_colors',
        'DATA_PT_preview',
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels

def register_render_engines():
    """Register panels, operators, and the render engine itself"""
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add(CSDFRenderEngine.bl_idname)

def unregister_render_engines():
    for panel in get_panels():
        if CSDFRenderEngine.bl_idname in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove(CSDFRenderEngine.bl_idname)

    """Unload everything previously registered"""
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
