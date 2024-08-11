import bpy

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from bpy.types import PropertyGroup

from .viewport.overlays import update_wire_display

# Constants not exported from bgl for some reason despite
# being documented in https://docs.blender.org/api/current/bgl.html
GL_TESS_EVALUATION_SHADER = 36487
GL_TESS_CONTROL_SHADER = 36488
GL_PATCHES = 14



class CSDFRendererSettings(PropertyGroup):
    """Collection of user configurable settings for the renderer"""

    # Shader source files
    vert_filename: StringProperty(
        name='Vertex Shader',
        description='Source file path',
        default='',
        subtype='FILE_PATH'
        # update=force_shader_reload
    )

    frag_filename: StringProperty(
        name='Fragment Shader',
        description='Source file path',
        default='',
        subtype='FILE_PATH'
        # update=force_shader_reload
    )

    tesc_filename: StringProperty(
        name='Tess Control Shader',
        description='Source file path',
        default='',
        subtype='FILE_PATH'
        # update=force_shader_reload
    )

    tese_filename: StringProperty(
        name='Tess Evaluation Shader',
        description='Source file path',
        default='',
        subtype='FILE_PATH'
        # update=force_shader_reload
    )

    geom_filename: StringProperty(
        name='Geometry Shader',
        description='Source file path',
        default='',
        subtype='FILE_PATH'
        # update=force_shader_reload
    )

    live_reload: BoolProperty(
        name='Live Reload',
        description='Reload source files on change',
        default=True
    )

    clear_color: FloatVectorProperty(
        name='Background Color',
        subtype='COLOR',
        default=(0.05, 0.05, 0.05),
        min=0.0, max=1.0,
        description='Background color of the scene'
    )

    ambient_color: FloatVectorProperty(
        name='Matcap Color',
        subtype='COLOR',
        default=(0.23, 0.5, 0.4),
        min=0.0, max=1.0,
        description='Matcap color of the scene'
    )


    max_distance: FloatProperty(
        name='Max distance',
        subtype='DISTANCE',
        default=100.0,
        min=0.0, max=2000.0,
        description='Maximum view distance'
    )
    max_steps: IntProperty(
        name='Maximum steps',
        default=100,
        min=1, max=1024,
        description='Maximum raymarching steps. Improves silhouette definition',

    )
    min_surface_distance: FloatProperty(
        name='Minimum size',
        subtype='DISTANCE',
        default=0.01,
        min=0.000001, max=1,
        description='Smallest renderable detail'
    )
    marching_scale: FloatProperty(
        name='Ray scale',
        default=1.0,
        min=0.5, max=1.0,
        description='Reduces certain view dependent artifacts, by scaling distance estimate while raymarching'
    )

    block_index_callback: BoolProperty(
        name='Block Outliner callback',
        description="stops cyclical function calls",
        default=False,
    )

    block_selection_handler: BoolProperty(
        name='Block selection handler',
        description="stops cyclical function calls",
        default=False,
    )

    force_reload: BoolProperty(
        name='Force Reload'
    )

    last_shader_error: StringProperty(
        name='Last Shader Error'
    )

    draw_wire: BoolProperty(
        name='Display Diff/Inset as wire',
        description="Changes the drawing type of all difference/inset primitives in the scene to wireframe when enabled",
        default=False,
        update=update_wire_display,
    )


    @classmethod
    def register(cls):
        bpy.types.Scene.csdf = PointerProperty(
            name='CSDF Render Settings',
            description='',
            type=cls
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.csdf

class CSDFLightSettings(PropertyGroup):
    color: FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.15, 0.15, 0.15),
        min=0.0, max=1.0,
        description='color picker'
    )

    intensity: FloatProperty(
        name='Intensity',
        default=1.0,
        description='Brightness of the light',
        min=0.0
    )

    @classmethod
    def register(cls):
        bpy.types.Light.csdf = PointerProperty(
            name='CSDF Light Settings',
            description='',
            type=cls
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Light.csdf