import bpy
from bpy.types import Menu

# Import functions
from .functions import (
    check_environment_nodes
)

# Menu class
class DOMELIGHT_MT_menu(Menu):
    bl_idname = "VIEW3D_MT_open_menu"
    bl_label = "Dome Light Menu"

    def draw(self, context):
        # Scene Objects
        scn = context.scene
        cycles_scn = scn.cycles
        engine = scn.render.engine
        view_settings = scn.view_settings
        active_world = scn.world

        # Enable Mix HDR
        enable_second_light = active_world.enable_second_light

        # Node Properties
        nodes = scn.world.node_tree.nodes

        layout = self.layout
        
        col = layout.column(align=True)

        if check_environment_nodes() == 'OK':
            col.label(text = 'Settings:', icon = 'LIGHT')
            col.separator()
            if 'DOMELIGHT_environment' in nodes:
                col.prop(nodes['DOMELIGHT_environment'], "projection", text = '')
                col.separator()
            if 'DOMELIGHT_math_add' in nodes:
                col.prop(nodes['DOMELIGHT_math_add'].inputs[1], "default_value", text = 'Intensity')
            if 'DOMELIGHT_math_multiply' in nodes:
                col.prop(nodes['DOMELIGHT_math_multiply'].inputs[1], "default_value", text = 'Sun Intensity')
            if 'DOMELIGHT_gamma' in nodes:
                col.prop(nodes['DOMELIGHT_gamma'].inputs[1], "default_value", text = "Gamma")
            if 'DOMELIGHT_saturation' in nodes:
                col.prop(nodes['DOMELIGHT_saturation'].inputs[1], "default_value", text = "Saturation")                

            col = col.column(align=True)
            col.separator()
            col.label(text = "Rotation:", icon = 'FILE_REFRESH')
            col.prop(nodes["DOMELIGHT_mapping"].inputs[2], "default_value", text = "")

            if enable_second_light:
                col.separator()
                col.label(text = "Rotation HDR 2:", icon = 'FILE_REFRESH')                
                col.prop(nodes["DOMELIGHT_mapping_2"].inputs[2], "default_value", text = "")
            
            col = col.column(align=True)
            col.separator()
            col.label(text = "Exposure:", icon = 'SCENE')
            if engine == 'CYCLES':
                col.prop(cycles_scn, "film_exposure", text = "Cycles Exposure")
            col.prop(view_settings, "exposure", text = "Color Exposure")
        else:
            col.label(text = 'Create a light first', icon = 'INFO')