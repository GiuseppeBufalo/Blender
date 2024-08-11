# ##### BEGIN GPL LICENSE BLOCK #####
# Physical Starlight and Atmosphere is is a completely volumetric procedural
# sky, sunlight, and atmosphere simulator addon for Blender
# Copyright (C) 2022  Physical Addons

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import *
from . ui import *  # RIG_PT_StarlightAtmosphere
from . clouds import RIG_PT_PhysicalCloudsTB
from . handlers import enable_atmosphere
from . sunlight import sun_calculation
from . variables import *


def update_toolbar_label(self, context):
    classes = [
        RIG_PT_StarlightAtmosphereTB,
        RIG_PT_SunTB,
        RIG_PT_BinarySunTB,
        RIG_PT_AtmosphereTB,
        RIG_PT_StarsTB,
        RIG_PT_PhysicalCloudsTB,
        RIG_PT_ObjectFogTB,
        RIG_PT_GroundTB,
        RIG_PT_ArtisticControlsTB,
        RIG_PT_FooterTB,
    ]

    panel_exists = hasattr(bpy.types, 'RIG_PT_StarlightAtmosphereTB')
    if panel_exists:
        for cls in classes:
            bpy.utils.unregister_class(cls)

    # Set Toolbar Label
    RIG_PT_StarlightAtmosphereTB.bl_category = self.toolbar_label
    for cls in classes:
        bpy.utils.register_class(cls)


def toggle_physical_values(self, context):
    prefs = context.preferences.addons['physical-starlight-atmosphere'].preferences
    gsettings = context.scene.world.psa_general_settings
    if prefs.use_physical_values:
        gsettings.intensity_multiplier = 64
    else:
        gsettings.intensity_multiplier = 1
    if gsettings.enabled:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        sun_calculation(bpy.context, depsgraph, 'realtime')  # redraw


def toggle_aces(self, context):
    psa_gsettings = context.scene.world.psa_general_settings
    if psa_gsettings.enabled:
        node_tree = context.scene.world.node_tree
        world_output_name = context.scene.world.psa_exposed.output_node_name
        world_output_node = node_tree.nodes.get(world_output_name)
        # output = node_tree.nodes['World Output']
        atmosphere = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME]
        converter = node_tree.nodes[ACES_CONVERTER_NODE_NAME]
        if self.use_aces == 1:
            node_tree.links.new(converter.outputs[0], world_output_node.inputs[0])
            node_tree.links.new(atmosphere.outputs[0], converter.inputs[0])
        else:
            node_tree.links.new(atmosphere.outputs[0], world_output_node.inputs[0])

class RIG_OT_OpenDocumentation(bpy.types.Operator):
    bl_idname = 'rig.open_exp_features_page'
    bl_label = 'Read more'
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_description = "Read about Experimental Features in documentation"
    link: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.wm.url_open(url='https://www.physicaladdons.com/psa/customization/#experimental-features')
        return {'FINISHED'}


class RIG_MT_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = "physical-starlight-atmosphere"  # __name__ would be physical-starlight-atmosphere.preferences

    use_physical_values: bpy.props.BoolProperty(
        default=False,
        description="Use real world physical values",
        update=toggle_physical_values
    )

    # use_experimental_features: bpy.props.BoolProperty(
    #     default=True,
    #     description="Use experimental features",
    # )

    use_aces: bpy.props.BoolProperty(
        default=False,
        description="Use ACES color space",
        update=toggle_aces
    )

    toolbar_enabled: bpy.props.BoolProperty(
        default=True,
        description="Toggle Toolbar (N panel)",
    )

    toolbar_label: StringProperty(
        description="Choose addon name for the Toolbar (N panel)",
        default="Atmosphere",
        update=update_toolbar_label
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.prop(self, "toolbar_enabled", text="Toolbar enabled")
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')
        btn.link = 'https://www.physicaladdons.com/psa/customization/#toolbar-enabled'
        col.label(text="Toolbar label:")
        row = col.split(factor=0.5, align=True)
        row.prop(self, "toolbar_label", text="")

        # box = layout.box()
        # col = box.column()
        # col.alert = True
        # col.scale_y = 0.8
        # col.label(
        #     text="Experimental features may not be fully functional and tested for all cases",
        #     icon="ERROR"
        # )

        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "use_aces", text="Use ACES color space" )
        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')
        btn.link = 'https://www.physicaladdons.com/psa/customization/#use-aces'

        row = box.row(align=True)
        row.prop(self, "use_physical_values", text="Use real world physical values")

        operatorColumn = row.column(align=True)
        operatorColumn.alignment = "RIGHT"
        btn = operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')
        btn.link = 'https://www.physicaladdons.com/psa/customization/#use-real-world-physical-values'
        # row = box.row(align=True)
        # labelColumn = row.column(align=True)
        # labelColumn.prop(self, "use_experimental_features", text="Experimental Features")

        # operatorColumn = row.column(align=True)
        # operatorColumn.alignment = "RIGHT"
        # operatorColumn.operator(RIG_OT_OpenDocumentation.bl_idname, icon='URL')
