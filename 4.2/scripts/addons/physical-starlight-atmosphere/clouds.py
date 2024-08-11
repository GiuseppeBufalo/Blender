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
from bpy.types import Panel
from . ui import DrawablePanel, RIG_WT, RIG_TB
from . sunlight import sun_calculation
from . variables import *


class PhysicalClouds(DrawablePanel):
    bl_label = "Clouds"
    icon_name = 'MOD_FLUID'

    def draw(self, context):
        asettings = context.scene.world.psa_atmosphere_settings
        psa_gsettings = context.scene.world.psa_general_settings
        clouds_type = asettings.clouds_type
        layout = self.layout
        layout.enabled = psa_gsettings.enabled

        row = layout.row(align=True)
        row.prop(asettings, 'clouds_type', expand=True)

        if clouds_type in {'procedural'}:
            col = self.indentedColumn()
            col.prop(asettings, 'clouds_scale')
            col.prop(asettings, 'clouds_thickness')
            col.label(text='Coverage:')
            col.prop(asettings, 'clouds_min')
            col.prop(asettings, 'clouds_max')
            col.label(text='Lighting:')
            col.prop(asettings, 'clouds_lighting_intensity')
            col.prop(asettings, 'clouds_amount')
            col.prop(asettings, 'clouds_power')
            row = col.row(align=True)
            row.label(text='Inscattering:')
            row.prop(asettings, 'clouds_scattering')
            col.prop(asettings, 'clouds_location')
            col.prop(asettings, 'clouds_rotation')


class RIG_PT_PhysicalCloudsWT(RIG_WT, Panel, PhysicalClouds):
    pass


class RIG_PT_PhysicalCloudsTB(RIG_TB, Panel, PhysicalClouds):
    pass

# UI checkbox handler
def toggle_clouds(self, context):
    asettings = bpy.context.scene.world.psa_atmosphere_settings
    if asettings.clouds_type == 'procedural':
        link_clouds()
    else:
        unlink_clouds()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    sun_calculation(bpy.context, depsgraph, 'rendering')

def clouds_update_handler(self, context):
    node_tree = bpy.context.scene.world.node_tree
    if node_tree.nodes.get(PHYSICAL_CLOUDS_NODE_NAME) is not None:
        inputs = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].inputs
        inputs['Scale'].default_value = context.scene.world.psa_atmosphere_settings.clouds_scale
        inputs['Min'].default_value = context.scene.world.psa_atmosphere_settings.clouds_min
        inputs['Max'].default_value = context.scene.world.psa_atmosphere_settings.clouds_max
        inputs['Thickness'].default_value = context.scene.world.psa_atmosphere_settings.clouds_thickness
        inputs['Val1'].default_value = context.scene.world.psa_atmosphere_settings.clouds_amount
        inputs['Val2'].default_value = context.scene.world.psa_atmosphere_settings.clouds_power
        inputs['Scattering'].default_value = context.scene.world.psa_atmosphere_settings.clouds_scattering
        inputs['Intensity'].default_value = context.scene.world.psa_atmosphere_settings.clouds_lighting_intensity
        inputs['Location'].default_value = context.scene.world.psa_atmosphere_settings.clouds_location
        inputs['Rotation'].default_value = context.scene.world.psa_atmosphere_settings.clouds_rotation
    

def link_clouds(): 
    node_tree = bpy.context.scene.world.node_tree
    if PHYSICAL_CLOUDS_NODE_NAME in node_tree.nodes:
        output = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].outputs["Result"]
        input = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME].inputs["in_clouds"]
        node_tree.links.new(output, input)


def unlink_clouds():
    node_tree = bpy.context.scene.world.node_tree
    if PHYSICAL_CLOUDS_NODE_NAME in node_tree.nodes:
        output = node_tree.nodes[PHYSICAL_CLOUDS_NODE_NAME].outputs["Result"]
        input = node_tree.nodes[STARLIGHT_ATMOSPHERE_NODE_NAME].inputs["in_clouds"]
        for l in output.links :
            if l.to_socket == input :
                node_tree.links.remove(l)
    