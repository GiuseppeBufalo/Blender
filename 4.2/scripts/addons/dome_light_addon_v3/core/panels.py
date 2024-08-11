# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 3.0.0
#
# ///////////////////////////////////////////////////////////////

import bpy
import os
from bpy.types import Panel
from bpy.utils import previews

# Import functions
from .functions import (
    check_environment_nodes,
)

# Preview Settings
class DOMELIGHT_PT_preview_settings(Panel):
    bl_idname = 'DOMELIGHT_PT_preview_settings'
    bl_label = 'Preview Settings'
    bl_parent_id = 'DOMELIGHT_PT_dome_light'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon='WORKSPACE')

    @classmethod
    def poll(cls, context):
        return check_environment_nodes() == 'OK'

    def draw(self, context):
        layout = self.layout

        # Scene Nodes
        scn = context.scene
        
        # Preview settings
        world = bpy.context.space_data.shading

        col = layout.column(align=True)
        if world.type == 'RENDERED':                 
            if world.use_scene_lights_render:
                col.prop(world, "use_scene_lights_render", text='Show Scene Lights', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_lights_render", text='Show Scene Lights', icon='LIGHT_DATA')
            if world.use_scene_world_render:
                col.prop(world, "use_scene_world_render", text='Show HDR Light', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_world_render", text='Show HDR Light', icon='LIGHT_DATA')
        elif world.type == 'MATERIAL':
            if world.use_scene_lights:
                col.prop(world, "use_scene_lights", text='Show Scene Lights', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_lights", text='Show Scene Lights', icon='LIGHT_DATA')
            if world.use_scene_world:
                col.prop(world, "use_scene_world", text='Show HDR Light', icon='OUTLINER_OB_LIGHT')
            else:
                col.prop(world, "use_scene_world", text='Show HDR Light', icon='LIGHT_DATA')

        # Create a box for Transparent settings
        col = layout.column(align=False)
        transparent_box = col.box()
        transparent_col = transparent_box.column(align=True)
        transparent_col.prop(scn.render, "film_transparent", text="Transparent BG")
        if context.scene.render.engine == 'CYCLES':
            transparent_col.prop(scn.cycles, "film_transparent_glass", text="Transparent glass")

        # Create a box for Render engine
        render_engine_box = col.box()
        render_engine_col = render_engine_box.column(align=True)
        render_engine_col.label(text='Render Engine:', icon='RESTRICT_RENDER_OFF')
        render_engine_col_select = render_engine_box.column(align=True)
        render_engine_col_select.prop(scn.render, "engine", text='', expand=False)
        if context.scene.render.engine == 'CYCLES':
            render_engine_col_select.prop(scn.cycles, "feature_set", text='', expand=False)
            render_engine_col_select.prop(scn.cycles, "device", text='', expand=False)
