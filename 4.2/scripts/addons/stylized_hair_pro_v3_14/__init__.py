"""<br>Copyright (C) 2024 Dean Zarkov<br>deanzarkov@protonmail.com<br><br>Created by Dean Zarkov<br><br>This file is part of "Stylized Hair PRO".<br>
<br> "Stylized Hair PRO" is free software; you can redistribute it and/or<br> modify it under the terms of the GNU General Public License<br>
as published by the Free Software Foundation; either version 3<br> of the License, or (at your option) any later version.<br><br>
This program is distributed in the hope that it will be useful,<br> but WITHOUT ANY WARRANTY; without even the implied warranty of<br>
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the<br> GNU General Public License for more details.<br><br>
You should have received a copy of the GNU General Public License<br> along with this program; if not, see <https://www.gnu.org<br>/licenses>.<br>"""

bl_info = {
    "name": "Stylized Hair PRO",
    "blender": (4, 00, 0),
    "category": "3D View",
    "author": "Dean Zarkov",
    "version": (3, 1, 4),
    "location": "View3D > Sidebar > 'Stylized Hair PRO' tab",
}

import bpy
import time
import os
from bpy.app.handlers import persistent
import bpy.utils.previews
from bpy.types import Menu
from .shp_modifier_data import SHP_MODIFIER_INPUTS as smi, SHP_GLOBAL_VALUES as sgv, SHP_NODE_GROUPS as sng

# initialize variable to store the previously selected object (used in 'shp_selection_handler')
prev_active_object = None

# initialize icons preview collection
preview_collections = {}

# formatting function for the modifier sockets
def shp_inp(identifier):
    return f'["{bpy.utils.escape_identifier(identifier)}"]'

################################
#   UPDATE FUNCTIONS
################################

# Add SHP setup
def shp_add_setup(all=True):
        # Specify the path to the assets .blend file and the node group name
        blend_file_path = os.path.join(os.path.dirname(__file__), "SHP_assets.blend")
        node_group_name = "Stylized Hair PRO"
        material_node_group_name = "Stylized Hair PRO - Hair Attributes"

        # Check if the node group exists in bpy.data.node_groups
        if node_group_name not in bpy.data.node_groups:
            # Link the blend file
            with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
                data_to.node_groups = data_from.node_groups

            # Append the node group from the linked data
            # appended_node_group = bpy.data.node_groups[node_group_name].copy()
        # else:
        # print(f"The node group '{node_group_name}' already exists.")

        # Check if the node group exists in bpy.data.node_groups
        if material_node_group_name not in bpy.data.node_groups:
            # Link the blend file
            with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
                data_to.node_groups = data_from.node_groups

            # Append the node group from the linked data
            # appended_material_node_group = bpy.data.node_groups[material_node_group_name].copy()
        # else:
        # print(f"The node group '{material_node_group_name}' already exists.")

        # Check if the node group modifier exists in bpy.context.object.modifiers
        if all:
            for hair_curve in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = hair_curve # Set the curve as the active object
                if node_group_name not in hair_curve.modifiers:
                    # Check if the active object is a curve
                    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'}:
                        bpy.ops.object.modifier_add(type='NODES')
                        hair_curve.modifiers.active.name = node_group_name
                        hair_curve.modifiers.active.node_group = bpy.data.node_groups[node_group_name]
                        hair_curve.modifiers.active.show_group_selector = False
                    else:
                        print("The active object is not a curve. Select a curve object.")
                else:
                    print(f"The node group modifier '{node_group_name}' already exists.")
        else:
            hair_curve = bpy.context.object
            if hair_curve:
                if node_group_name not in hair_curve.modifiers:
                # Check if the active object is a curve
                    if hair_curve.type in {'CURVE', 'CURVES'}:
                        bpy.ops.object.modifier_add(type='NODES')
                        hair_curve.modifiers.active.name = node_group_name
                        hair_curve.modifiers.active.node_group = bpy.data.node_groups[node_group_name]
                        hair_curve.modifiers.active.show_group_selector = False


# Remove SHP setup
def shp_remove_setup():
    node_group_name = "Stylized Hair PRO"
    for hair_curve in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = hair_curve # Set the curve as the active object
        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            bpy.ops.object.modifier_remove(modifier=node_group_name)


# Update the SHP panel
def shp_select_update(obj):
    shp_modf = bpy.context.object.modifiers["Stylized Hair PRO"]
    shp_ctrl = bpy.context.scene.shp_addon

    if "Stylized Hair PRO" in bpy.context.object.modifiers:
        # for profile
        if shp_modf[smi['profile_type']] == 1:
            shp_ctrl.profile_selector = 'TAB_1'
        elif shp_modf[smi['profile_type']] == 2:
            shp_ctrl.profile_selector = 'TAB_2'
        elif shp_modf[smi['profile_type']] == 3:
            shp_ctrl.profile_selector = 'TAB_3'
        elif shp_modf[smi['profile_type']] == 4:
            shp_ctrl.profile_selector = 'TAB_4'
        elif shp_modf[smi['profile_type']] == 5:
            shp_ctrl.profile_selector = 'TAB_5'
        elif shp_modf[smi['profile_type']] == 6:
            shp_ctrl.profile_selector = 'TAB_6'

        # for ornament
        if shp_modf[smi['ornaments_type']] == 1:
            shp_ctrl.ornament_selector = 'TAB_1'
        elif shp_modf[smi['ornaments_type']] == 2:
            shp_ctrl.ornament_selector = 'TAB_2'
        elif shp_modf[smi['ornaments_type']] == 3:
            shp_ctrl.ornament_selector = 'TAB_3'
        elif shp_modf[smi['ornaments_type']] == 4:
            shp_ctrl.ornament_selector = 'TAB_4'

        # for custom ornament
        if not shp_modf[smi['ornaments_custom']]:
            shp_ctrl.custom_ornament_tab = 'TAB_1'
        elif shp_modf[smi['ornaments_custom']]:
            shp_ctrl.custom_ornament_tab = 'TAB_2'

        # for ornament collection
        bpy.context.scene.shp_addon.ornaments_custom_collection = shp_modf[smi['ornaments_collection']]

        # for ornament deform axis
        if shp_modf[smi['ornaments_deform_axis']] == 1:
            shp_ctrl.ornament_deform_axis = 'TAB_1'
        elif shp_modf[smi['ornaments_deform_axis']] == 2:
            shp_ctrl.ornament_deform_axis = 'TAB_2'
        elif shp_modf[smi['ornaments_deform_axis']] == 3:
            shp_ctrl.ornament_deform_axis = 'TAB_3'

        # for hair material
        bpy.context.scene.shp_addon.hair_material = shp_modf[smi['material_hair']]

        # for ornament material
        bpy.context.scene.shp_addon.ornament_material = shp_modf[smi['material_ornament']]

        # for shading style
        if shp_modf[smi['settings_shading_type']] == 1:
            shp_ctrl.shading_style_selector = 'TAB_1'
        elif shp_modf[smi['settings_shading_type']] == 2:
            shp_ctrl.shading_style_selector = 'TAB_2'
        elif shp_modf[smi['settings_shading_type']] == 3:
            shp_ctrl.shading_style_selector = 'TAB_3'

        # for wind generation type
        if not shp_modf[smi['dynamics_wind_generation_type']]:
            shp_ctrl.wind_generation_type = 'TAB_1'
        elif shp_modf[smi['dynamics_wind_generation_type']]:
            shp_ctrl.wind_generation_type = 'TAB_2'

        # for turbulence type
        if not shp_modf[smi['dynamics_wind_turbulence_type']]:
            shp_ctrl.turbulence_type = 'TAB_1'
        elif shp_modf[smi['dynamics_wind_turbulence_type']]:
            shp_ctrl.turbulence_type = 'TAB_2'

        # for wind direction
        if not shp_modf[smi['dynamics_wind_effector_type']]:
            shp_ctrl.wind_effector_direction = 'TAB_1'
        elif shp_modf[smi['dynamics_wind_effector_type']]:
            shp_ctrl.wind_effector_direction = 'TAB_2'

        # for a random value per object
        shp_modf[smi['dynamics_random_per_obj']] = hash(obj.name) % 10000
        
        # for generate armature
        shp_ctrl.generate_armature = shp_modf[smi['utils_armature_generate']]
        
        # for custom hair geo deform axis
        if shp_modf[smi['utils_custom_hair_object_axis']] == 1:
            shp_ctrl.custom_geo_deform_axis = 'TAB_1'
        elif shp_modf[smi['utils_custom_hair_object_axis']] == 2:
            shp_ctrl.custom_geo_deform_axis = 'TAB_2'
        elif shp_modf[smi['utils_custom_hair_object_axis']] == 3:
            shp_ctrl.custom_geo_deform_axis = 'TAB_3'

        # for armature type
        if not shp_modf[smi['utils_armature_type']]:
            shp_ctrl.armature_type_selector = 'TAB_1'
        elif shp_modf[smi['utils_armature_type']]:
            shp_ctrl.armature_type_selector = 'TAB_2'


# Refresh Modifier
def refresh_modifier():
    node_group_name = "Stylized Hair PRO"

    for hair_curve in bpy.context.selected_objects:
        if hair_curve and node_group_name in hair_curve.modifiers:
            hair_curve.modifiers[node_group_name].show_viewport = False
            hair_curve.modifiers[node_group_name].show_viewport = True


# Set Active Curve
@persistent
def shp_selection_handler(scene):
    node_group_name = "Stylized Hair PRO"
    global prev_active_object

    # Get the active object from the selected objects (returns None if no active object)
    shp_active_object = bpy.context.active_object

    # Set the scene frame data (for looping wind dynamics)
    if shp_active_object:
        if node_group_name in shp_active_object.modifiers:
            node_group = bpy.data.node_groups[".SHP_dynamics"]
            scene = bpy.context.scene

            node_group.nodes["shp_dynamics_node_frame_rate"].outputs[0].default_value = scene.render.fps
            node_group.nodes["shp_dynamics_node_start_frame"].integer = scene.frame_start
            node_group.nodes["shp_dynamics_node_end_frame"].integer = scene.frame_end
            
    # Check if the active object has changed
    if shp_active_object and shp_active_object != prev_active_object:
        # Check if the active object has the "Stylized Hair PRO" modifier
        if shp_active_object and node_group_name in shp_active_object.modifiers:
            # Run the selection update function
            shp_select_update(shp_active_object)

        # Update the previous active object
        prev_active_object = shp_active_object
    

# Update Profile
def update_profile(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.profile_selector == 'TAB_1':
        shp_modf[smi['profile_type']] = 1
    elif self.profile_selector == 'TAB_2':
        shp_modf[smi['profile_type']] = 2
    elif self.profile_selector == 'TAB_3':
        shp_modf[smi['profile_type']] = 3
    elif self.profile_selector == 'TAB_4':
        shp_modf[smi['profile_type']] = 4
    elif self.profile_selector == 'TAB_5':
        shp_modf[smi['profile_type']] = 5
    elif self.profile_selector == 'TAB_6':
        shp_modf[smi['profile_type']] = 6
    refresh_modifier()


# Update Ornament
def update_ornament(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.ornament_selector == 'TAB_1':
        shp_modf[smi['ornaments_type']] = 1
    elif self.ornament_selector == 'TAB_2':
        shp_modf[smi['ornaments_type']] = 2
    elif self.ornament_selector == 'TAB_3':
        shp_modf[smi['ornaments_type']] = 3
    elif self.ornament_selector == 'TAB_4':
        shp_modf[smi['ornaments_type']] = 4

    refresh_modifier()


# Update Custom Ornament
def update_custom_ornament(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.custom_ornament_tab == 'TAB_1':
        shp_modf[smi['ornaments_custom']] = False
    elif self.custom_ornament_tab == 'TAB_2':
        shp_modf[smi['ornaments_custom']] = True

    refresh_modifier()


# Update Ornament Collection
def update_ornaments_custom_collection(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]
    shp_modf[smi['ornaments_collection']] = context.scene.shp_addon.ornaments_custom_collection
    refresh_modifier()


# Update Ornament Deform Axis
def update_ornament_deform_axis(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.ornament_deform_axis == 'TAB_1':
        shp_modf[smi['ornaments_deform_axis']] = 1
    elif self.ornament_deform_axis == 'TAB_2':
        shp_modf[smi['ornaments_deform_axis']] = 2
    elif self.ornament_deform_axis == 'TAB_3':
        shp_modf[smi['ornaments_deform_axis']] = 3

    refresh_modifier()


# Update Hair Material
def update_hair_material(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]
    shp_modf[smi['material_hair']] = context.scene.shp_addon.hair_material
    refresh_modifier()


# Update Ornament Material
def update_ornament_material(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]
    shp_modf[smi['material_ornament']] = context.scene.shp_addon.ornament_material
    refresh_modifier()


# Update Shading Style Selector
def update_shading_style_selector(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.shading_style_selector == 'TAB_1':
        shp_modf[smi['settings_shading_type']] = 1
    elif self.shading_style_selector == 'TAB_2':
        shp_modf[smi['settings_shading_type']] = 2
    elif self.shading_style_selector == 'TAB_3':
        shp_modf[smi['settings_shading_type']] = 3

    refresh_modifier()


# Update Wind Direction
def update_wind_generation_type(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.wind_generation_type == 'TAB_1':
        shp_modf[smi['dynamics_wind_generation_type']] = False
    elif self.wind_generation_type == 'TAB_2':
        shp_modf[smi['dynamics_wind_generation_type']] = True

    refresh_modifier()


# Update Complex / Simple Turbulence
def update_turbulence_type(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.turbulence_type == 'TAB_1':
        shp_modf[smi['dynamics_wind_turbulence_type']] = False
    elif self.turbulence_type == 'TAB_2':
        shp_modf[smi['dynamics_wind_turbulence_type']] = True

    refresh_modifier()


# Update Wind Direction
def update_wind_effector_direction(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.wind_effector_direction == 'TAB_1':
        shp_modf[smi['dynamics_wind_effector_type']] = False
    elif self.wind_effector_direction == 'TAB_2':
        shp_modf[smi['dynamics_wind_effector_type']] = True

    refresh_modifier()


# Update Generate Armature
def update_generate_armature(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    shp_modf[smi['utils_armature_generate']] = self.generate_armature

    refresh_modifier()


# Update Custom Geometry Deform Axis
def update_custom_geo_deform_axis(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.custom_geo_deform_axis == 'TAB_1':
        shp_modf[smi['utils_custom_hair_object_axis']] = 1
    elif self.custom_geo_deform_axis == 'TAB_2':
        shp_modf[smi['utils_custom_hair_object_axis']] = 2
    elif self.custom_geo_deform_axis == 'TAB_3':
        shp_modf[smi['utils_custom_hair_object_axis']] = 3

    refresh_modifier()


# Update Wind Direction
def update_armature_type_selector(self, context):
    shp_modf = context.object.modifiers["Stylized Hair PRO"]

    if self.armature_type_selector == 'TAB_1':
        shp_modf[smi['utils_armature_type']] = False
    elif self.armature_type_selector == 'TAB_2':
        shp_modf[smi['utils_armature_type']] = True

    refresh_modifier()


################################
#   DRAW FUNCTIONS
################################

# Custom Hair Geometry warning message
custom_hair_geo_message = "⚠ Disabled: Custom Hair Geometry active."


# MAIN
def draw_main(self, context):
    layout = self.layout
    pcoll = preview_collections["main"]

    obj = context.object
    node_group_name = "Stylized Hair PRO"

    if obj and node_group_name not in obj.modifiers and obj.type in {'CURVE', 'CURVES'}:        
        if obj.type == 'CURVE' and obj.data.bevel_object:
            col = layout.column()
            col.scale_y = 1.5
            col.operator("wm.reuse_old_curves", text="Convert curve setup to SHP")
        else:
            col = layout.row()
            col.scale_y = 1.5
            col.operator("wm.append_stylized_hair_pro", text="Add 'Stylized Hair PRO' setup",
                        icon_value=pcoll["shp_icon_setup_add"].icon_id)
        
    elif obj and node_group_name in obj.modifiers and obj.type in {'CURVE', 'CURVES'}:
        row = layout.row()
        row.scale_y = 1.5
        row.alert = True
        row.operator("wm.remove_stylized_hair_pro", text="Remove 'Stylized Hair PRO' setup",
                     icon_value=pcoll["shp_icon_setup_remove"].icon_id)

    elif obj and obj.type == 'MESH':
        col = layout.column()
        row = col.row()
        row.scale_y = 1.5
        # check for a UV map (needs one to add a hair curve)
        if bool(obj.data.uv_layers.active):
            row.enabled = True
            row.operator("wm.add_strand", text="Add Hair Curve to Mesh",
                         icon_value=pcoll["shp_icon_add_new_curve"].icon_id)
        else:
            row.enabled = False
            row.operator("wm.add_strand", text="Mesh doesn't have a UV map!", icon='ERROR')

    else:
        col = layout.column()
        row = col.row()
        row.scale_y = 1.5
        row.enabled = False
        row.operator("wm.add_strand", text="Select Mesh or Curve...")

    box = layout.box()
    col = box.column(align=True)

    if obj and obj.type in {'CURVE', 'CURVES'} and "Stylized Hair PRO" in obj.modifiers:
        col.enabled = True
        col.label(text=f"Editing:  '{obj.name}'")
    elif obj and obj.type in {'CURVE', 'CURVES'} and "Stylized Hair PRO" not in obj.modifiers:
        col.enabled = False
        col.label(text="Add 'Stylized Hair PRO' setup...")
    else:
        col.enabled = False
        col.label(text="Select a Curve...")

    row = col.row(align=False)
    row.operator("wm.duplicate_strand", text="Duplicate Strand", icon_value=pcoll["shp_icon_curve_duplicate"].icon_id)
    row.scale_x = 0.5
    row.operator("wm.reset_all", text="Reset", icon_value=pcoll["shp_icon_curve_refresh"].icon_id)

    col = layout.column(align=True)
    col.operator("wm.shp_call_pie_menu", text="SHP Quick Menu")

    if obj and node_group_name in obj.modifiers:
        shp_modf = obj.modifiers[node_group_name]
        col = layout.column(align=True)

        col.label(text="Main Settings:")

        row = col.row(align=False)
        row.label(text="Mirror:")
        row.prop(shp_modf, shp_inp(smi['x_mirror']), text='X')
        row.prop(shp_modf, shp_inp(smi['y_mirror']), text='Y')
        row.prop(shp_modf, shp_inp(smi['z_mirror']), text='Z')
        
        col.prop(shp_modf, shp_inp(smi['main_thickness']), text='Thickness')
        col.prop(shp_modf, shp_inp(smi['main_rotation']), text='Rotation')


# SHAPE
def draw_shape(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout

        if shp_modf[smi['utils_use_custom_hair_geo']]:
            layout.label(text=custom_hair_geo_message)

        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=False)
        row.label(text="Ends Thickness:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['root_thickness']), text='Root')
        row.prop(shp_modf, shp_inp(smi['tip_thickness']), text='Tip')

        row = col.row(align=False)
        row.label(text="Shape Factor:")
        row.label(text="Contrast:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['thickness_factor']), text='')
        row.prop(shp_modf, shp_inp(smi['thickness_contrast']), text='')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Ends Shape:")
        col.prop(shp_modf, shp_inp(smi['tip_open']), text='Tip Open')
        col.prop(shp_modf, shp_inp(smi['tip_bulge']), text='Tip Bulge')
        col.prop(shp_modf, shp_inp(smi['tip_roundness']), text='Tip Roundness')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['root_open']), text='Root Open')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Flatten Strand:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['flat_root']), text='Flat Root')
        row.prop(shp_modf, shp_inp(smi['flat_tip']), text='Flat Tip')

        row = col.row(align=False)
        row.label(text="Shape Factor:")
        row.label(text="Contrast:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['flatness_factor']), text='')
        row.prop(shp_modf, shp_inp(smi['flatness_contrast']), text='')

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['flip_flatten_axis']), text='Flip Flatten Axis')


# TWIST
def draw_twist(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=False)
        row.label(text="Twist Hair Strand:")

        row = col.row(align=False)
        row.label(text="Root:")
        row.label(text="Mid:")
        row.label(text="Tip:")
        
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['twist_root']), text='')
        row.prop(shp_modf, shp_inp(smi['twist_mid']), text='')
        row.prop(shp_modf, shp_inp(smi['twist_tip']), text='')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Custom Twist:")

        row = col.row(align=True)
        row.prop(shp_controls, "custom_twist_tab", expand=True)
        col.separator(factor=1)

        if shp_controls.custom_twist_tab == 'TAB_1':
            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_1_amount']), text='Amount 1')

            row = col.row(align=True)
            row.label(text="Position 1:")
            row.label(text="Spread 1:")

            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_1_position']), text='')
            row.prop(shp_modf, shp_inp(smi['twist_1_spread']), text='')
        elif shp_controls.custom_twist_tab == 'TAB_2':
            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_2_amount']), text='Amount 2')

            row = col.row(align=True)
            row.label(text="Position 2:")
            row.label(text="Spread 2:")

            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_2_position']), text='')
            row.prop(shp_modf, shp_inp(smi['twist_2_spread']), text='')
        elif shp_controls.custom_twist_tab == 'TAB_3':
            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_3_amount']), text='Amount 3')

            row = col.row(align=True)
            row.label(text="Position 3:")
            row.label(text="Spread 3:")

            row = col.row(align=False)
            row.prop(shp_modf, shp_inp(smi['twist_3_position']), text='')
            row.prop(shp_modf, shp_inp(smi['twist_3_spread']), text='')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Waviness:")
        col.prop(shp_modf, shp_inp(smi['waviness']), text='Waviness')

        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['waviness_scale']), text='Scale')
        row.prop(shp_modf, shp_inp(smi['waviness_seed']), text='Seed')


# BUMPS
def draw_bumps(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        col = layout.column(align=True)
        row = col.row(align=False)
        row.label(text="Shape Factor:")
        row.label(text="Contrast:")
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['bumps_factor']), text='')
        row.prop(shp_modf, shp_inp(smi['bumps_contrast']), text='')

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=False)
        row.label(text="Regular Bumps:")
        col.prop(shp_modf, shp_inp(smi['bumps_regular_strength']), text='Strength')
        col.prop(shp_modf, shp_inp(smi['bumps_regular_count']), text='Count')
        col.prop(shp_modf, shp_inp(smi['bumps_regular_shape']), text='Shape')
        col.prop(shp_modf, shp_inp(smi['bumps_regular_gap_size']), text='Gap Size')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Random Bumps:")
        col.prop(shp_modf, shp_inp(smi['bumps_random_strength']), text='Strength')
        col.prop(shp_modf, shp_inp(smi['bumps_random_contrast']), text='Contrast')
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['bumps_random_scale']), text='Scale')
        row.prop(shp_modf, shp_inp(smi['bumps_random_seed']), text='Seed')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Surface Bumps:")
        col.prop(shp_modf, shp_inp(smi['bumps_surface_strength']), text='Strength')
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['bumps_surface_scale']), text='Scale')
        row.prop(shp_modf, shp_inp(smi['bumps_surface_seed']), text='Seed')


# CURLS
def draw_curls(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        col = layout.column(align=True)
        row = col.row(align=False)
        row.label(text="Shape Factor:")
        row.label(text="Contrast:")
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['curls_factor']), text='')
        row.prop(shp_modf, shp_inp(smi['curls_contrast']), text='')

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=False)
        row.label(text="Curl Shape:")

        col.prop(shp_modf, shp_inp(smi['curls_flip_dir']), text='Flip Direction')
        col.prop(shp_modf, shp_inp(smi['curls_frequency']), text='Frequency')
        col.prop(shp_modf, shp_inp(smi['curls_radius']), text='Radius')
        col.prop(shp_modf, shp_inp(smi['curls_phase']), text='Phase')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Curl Noise:")
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['curls_noise_amount']), text='Amount')
        row.prop(shp_modf, shp_inp(smi['curls_noise_seed']), text='Seed')


# BRAID
def draw_braid(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout

        if shp_modf[smi['utils_use_custom_hair_geo']]:
            layout.label(text=custom_hair_geo_message)
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Braid Body:")
        col.prop(shp_modf, shp_inp(smi['braid_frequency']), text='Frequency')
        col.separator(factor=0.5)
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['braid_width']), text='Width')
        row.prop(shp_modf, shp_inp(smi['braid_depth']), text='Depth')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['braid_taper']), text='Taper')
        col.prop(shp_modf, shp_inp(smi['braid_phase']), text='Phase')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Braid Tip:")
        col.prop(shp_modf, shp_inp(smi['braid_tip']), text='Tip Factor')
        col.prop(shp_modf, shp_inp(smi['braid_tip_thickness']), text='Tip Thickness')
        col.prop(shp_modf, shp_inp(smi['braid_tip_width']), text='Pinch Width')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Braid Strands:")
        col.prop(shp_modf, shp_inp(smi['braid_strand_thickness']), text='Strand Thickness')
        col.separator(factor=0.5)
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['braid_pinch']), text='Pinch')
        row.prop(shp_modf, shp_inp(smi['braid_bulge']), text='Bulge')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['braid_strand_random']), text='Randomize Strand Thickness')
        col.prop(shp_modf, shp_inp(smi['braid_strand_random_seed']), text='Seed')
        row = col.row(align=False)
        row.label(text="")
        row.label(text="Twist:")
        row.label(text="Rotate:")
        row = col.row(align=False)
        row.label(text="Strand 1:")
        row.prop(shp_modf, shp_inp(smi['braid_strand_1_twist']), text='')
        row.prop(shp_modf, shp_inp(smi['braid_strand_1_rotate']), text='')
        row = col.row(align=False)
        row.label(text="Strand 2:")
        row.prop(shp_modf, shp_inp(smi['braid_strand_2_twist']), text='')
        row.prop(shp_modf, shp_inp(smi['braid_strand_2_rotate']), text='')
        row = col.row(align=False)
        row.label(text="Strand 3:")
        row.prop(shp_modf, shp_inp(smi['braid_strand_3_twist']), text='')
        row.prop(shp_modf, shp_inp(smi['braid_strand_3_rotate']), text='')


# PROFILE
def draw_profile(self, context):
    shp_controls = context.scene.shp_addon
    pcoll = preview_collections["main"]
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout

        if shp_modf[smi['utils_use_custom_hair_geo']]:
            layout.label(text=custom_hair_geo_message)

        col = layout.column(align=True)

        # profile select
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Profile Type:")

        row = col.row(align=True)
        # box
        if shp_controls.profile_selector == 'TAB_1':
            row.operator("wm.set_profile_box", depress=True, icon_value=pcoll["shp_icon_profile_box"].icon_id)
        else:
            row.operator("wm.set_profile_box", depress=False, icon_value=pcoll["shp_icon_profile_box"].icon_id)
        # triangle
        if shp_controls.profile_selector == 'TAB_2':
            row.operator("wm.set_profile_triangle", depress=True, icon_value=pcoll["shp_icon_profile_triangle"].icon_id)
        else:
            row.operator("wm.set_profile_triangle", depress=False, icon_value=pcoll["shp_icon_profile_triangle"].icon_id)
        
        row = col.row(align=True)
        # robo
        if shp_controls.profile_selector == 'TAB_3':
            row.operator("wm.set_profile_robo", depress=True, icon_value=pcoll["shp_icon_profile_robo"].icon_id)
        else:
            row.operator("wm.set_profile_robo", depress=False, icon_value=pcoll["shp_icon_profile_robo"].icon_id)
        # islands
        if shp_controls.profile_selector == 'TAB_4':
            row.operator("wm.set_profile_islands", depress=True, icon_value=pcoll["shp_icon_profile_islands"].icon_id)
        else:
            row.operator("wm.set_profile_islands", depress=False, icon_value=pcoll["shp_icon_profile_islands"].icon_id)
        
        row = col.row(align=True)
        # line
        if shp_controls.profile_selector == 'TAB_5':
            row.operator("wm.set_profile_line", depress=True, icon_value=pcoll["shp_icon_profile_linear"].icon_id)
        else:
            row.operator("wm.set_profile_line", depress=False, icon_value=pcoll["shp_icon_profile_linear"].icon_id)
        # crescent
        if shp_controls.profile_selector == 'TAB_6':
            row.operator("wm.set_profile_crescent", depress=True, icon_value=pcoll["shp_icon_profile_crescent"].icon_id)
        else:
            row.operator("wm.set_profile_crescent", depress=False, icon_value=pcoll["shp_icon_profile_crescent"].icon_id)

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Profile Shape:")

        if shp_controls.profile_selector == 'TAB_1':
            col.prop(shp_modf, shp_inp(smi['profile_smooth']), text='Smooth')
            col.prop(shp_modf, shp_inp(smi['profile_preserve_corners']), text='Preserve Corners')
        elif shp_controls.profile_selector == 'TAB_2':
            col.prop(shp_modf, shp_inp(smi['profile_smooth']), text='Smooth')
            col.prop(shp_modf, shp_inp(smi['profile_preserve_corners']), text='Preserve Corners')
        elif shp_controls.profile_selector == 'TAB_3':
            pass
        elif shp_controls.profile_selector == 'TAB_4':
            col.prop(shp_modf, shp_inp(smi['profile_smooth']), text='Smooth')
            col.label(text="Individual Tips:")
            col.prop(shp_modf, shp_inp(smi['profile_islands_open']), text='Open')
            col.prop(shp_modf, shp_inp(smi['profile_islands_bulge']), text='Bulge ')
            col.prop(shp_modf, shp_inp(smi['profile_islands_round']), text='Roundness')
        elif shp_controls.profile_selector == 'TAB_5':
            col.prop(shp_modf, shp_inp(smi['profile_bend']), text='Bend')
        elif shp_controls.profile_selector == 'TAB_6':
            col.prop(shp_modf, shp_inp(smi['profile_bend']), text='Bend')
            col.prop(shp_modf, shp_inp(smi['profile_thickness']), text='Thickness')

        col.separator(factor=0.5)

        if shp_controls.profile_selector == 'TAB_4':
            col.prop(shp_modf, shp_inp(smi['profile_sub_strands']), text='Sub-strands Thickness')
            row = col.row(align=True)
            row.prop(shp_modf, shp_inp(smi['profile_ss_scale']), text='Count')
            row.prop(shp_modf, shp_inp(smi['profile_ss_seed']), text='Seed')
        else:
            col.prop(shp_modf, shp_inp(smi['profile_sub_strands']), text='Sub-strands')
            row = col.row(align=True)
            row.prop(shp_modf, shp_inp(smi['profile_ss_scale']), text='Scale')
            row.prop(shp_modf, shp_inp(smi['profile_ss_seed']), text='Seed')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Custom Profile Curve:")
        col.prop(shp_modf, shp_inp(smi['profile_custom']), text='')


# ORNAMENTS
def draw_ornaments(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        

        box = layout.box()
        col = box.column(align=True)
        col.prop(shp_modf, shp_inp(smi['ornaments_enable']), text='Movable Ornament')

        col = box.column(align=True)
        col.enabled = shp_modf[smi['ornaments_enable']]
        col.prop(shp_modf, shp_inp(smi['ornaments_position']), text='Position')
        col.prop(shp_modf, shp_inp(smi['ornaments_width']), text='Width')
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['ornaments_pinch']), text='Pinch')
        row.prop(shp_modf, shp_inp(smi['ornaments_tightness']), text='Tightness')

        box = layout.box()
        col = box.column(align=True)
        col.prop(shp_modf, shp_inp(smi['ornaments_in_bump_gaps']), text='Ornaments in Bump Gaps')
        
        col = box.column(align=True)
        col.enabled = shp_modf[smi['ornaments_in_bump_gaps']]
        row = col.row(align=False)
        row.label(text="Disable from:")
        row.prop(shp_modf, shp_inp(smi['ornaments_disable_root']), text='Root')
        row.prop(shp_modf, shp_inp(smi['ornaments_disable_tip']), text='Tip')

        box = layout.box()
        col = box.column(align=True)
        col.prop(shp_modf, shp_inp(smi['braid_tip_ornament']), text='Ornament at Braid Tip')

        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['ornaments_enable']] or shp_modf[smi['ornaments_in_bump_gaps']] or shp_modf[smi['braid_tip_ornament']]
        col.label(text="Ornament Type:")

        row = col.row(align=True)
        row.prop(shp_controls, "ornament_selector", expand=True)

        sub = box.box()
        sub.enabled = shp_modf[smi['ornaments_enable']] or shp_modf[smi['ornaments_in_bump_gaps']] or shp_modf[smi['braid_tip_ornament']]
        if shp_controls.ornament_selector == 'TAB_1':
            col = sub.column(align=True)

            col.label(text="Hair Tie/Band:")
            col.prop(shp_modf, shp_inp(smi['ornaments_thickness']), text='Thickness')
            col.prop(shp_modf, shp_inp(smi['ornaments_adjust_range']), text='Range')
        elif shp_controls.ornament_selector == 'TAB_2':
            col = sub.column(align=True)

            col.label(text="Ring/Coil Tie:")
            col.prop(shp_modf, shp_inp(smi['ornaments_thickness']), text='Thickness')
            col.separator(factor=0.5)
            col.prop(shp_modf, shp_inp(smi['ornaments_coil']), text='Coil')
            col.prop(shp_modf, shp_inp(smi['ornaments_coil_radius']), text='Coil Radius')
        elif shp_controls.ornament_selector == 'TAB_3':
            col = sub.column(align=True)

            col.label(text="Scrunchie Tie:")
            col.prop(shp_modf, shp_inp(smi['ornaments_thickness']), text='Thickness')
            col.separator(factor=0.5)
            col.prop(shp_modf, shp_inp(smi['ornaments_scrunch']), text='Scrunch')
            col.prop(shp_modf, shp_inp(smi['ornaments_scrunch_seed']), text='Scrunch Seed')
        elif shp_controls.ornament_selector == 'TAB_4':
            col = sub.column(align=True)

            col.label(text="Custom Ornament:")
            row = col.row(align=True)
            row.prop(shp_controls, "custom_ornament_tab", expand=True)
            if shp_controls.custom_ornament_tab == 'TAB_1':
                col.label(text="Pick Custom Object")
                col.prop(shp_modf, shp_inp(smi['ornaments_object']), text='')
            elif shp_controls.custom_ornament_tab == 'TAB_2':
                col.label(text="Pick Custom Object")

                col.prop_search(shp_controls, "ornaments_custom_collection", bpy.data, "collections")
                col.prop(shp_modf, shp_inp(smi['ornaments_individual_obj']), text='Individual Object from Collection')
                col.prop(shp_modf, shp_inp(smi['ornaments_obj_seed']), text='Object Seed')
            
            col = box.column(align=True)
            col.enabled = shp_modf[smi['ornaments_enable']] or shp_modf[smi['ornaments_in_bump_gaps']] or shp_modf[smi['braid_tip_ornament']]
            col.prop(shp_modf, shp_inp(smi['ornaments_deform']), text='Deform Custom Ornament')
            row = col.row(align=True)
            row.enabled = shp_modf[smi['ornaments_deform']]
            row.label(text="Deform Axis:")
            sub = row.row(align=False)
            sub.scale_x = 0.5
            sub.prop(shp_controls, "ornament_deform_axis", expand=True)
        
        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['ornaments_enable']] or shp_modf[smi['ornaments_in_bump_gaps']] or shp_modf[smi['braid_tip_ornament']]
        col.label(text="Adjustments:")
        col.prop(shp_modf, shp_inp(smi['ornaments_adjust_size']), text='Adjust Size')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['ornaments_rotate']), text='Adjust Rotation')
        col.prop(shp_modf, shp_inp(smi['ornaments_rotate_random']), text='Randomize Rotation')
        

# DYNAMICS
def draw_dynamics(self, context):
    shp_controls = context.scene.shp_addon

    if context.object and context.object.type in {'CURVE', 'CURVES'} and "Stylized Hair PRO" in context.object.modifiers:
        shp_modf = context.object.modifiers["Stylized Hair PRO"]
        layout = self.layout

        if not shp_modf[smi['dynamics_enable']]:
            layout.operator("wm.toggle_dynamics", text="Enable Dynamics", depress=False)
        else:
            layout.operator("wm.toggle_dynamics", text="Disable Dynamics", depress=True)
        
        col = layout.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        row = col.row(align=False)
        row.label(text="Effect Factor:")
        row.label(text="Contrast:")
        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['dynamics_factor']), text='')
        row.prop(shp_modf, shp_inp(smi['dynamics_contrast']), text='')

        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        col.label(text="Strand Settings:")
        col.prop(shp_modf, shp_inp(smi['dynamics_stiffness']), text='Stiffness')
        col.prop(shp_modf, shp_inp(smi['dynamics_elasticity']), text='Elasticity')
        col.prop(shp_modf, shp_inp(smi['dynamics_damping']), text='Damping')
        col.prop(shp_modf, shp_inp(smi['dynamics_liveliness']), text='Liveliness')

        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        col.label(text="Gravity:")
        col.prop(shp_modf, shp_inp(smi['dynamics_gravity_strength']), text='Gravity Strength')
        col.prop(shp_modf, shp_inp(smi['dynamics_gravity_direction']), text='Gravity Direction')

        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        col.label(text="Collisions:")
        col.prop(shp_modf, shp_inp(smi['dynamics_collisions_enable']), text='Enable Collisions')

        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']] and shp_modf[smi['dynamics_collisions_enable']]

        row = col.row(align=True)
        row.label(text="Collider Object:")
        row.prop(shp_modf, shp_inp(smi['dynamics_collisions_object']), text='')

        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['dynamics_collisions_offset']), text='Offset Distance')
        col.prop(shp_modf, shp_inp(smi['dynamics_collisions_repel']), text='Repel Force')
        col.prop(shp_modf, shp_inp(smi['dynamics_collisions_quality']), text='Quality Steps')

        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        col.label(text="Simulation Settings:")
        col.prop(shp_modf, shp_inp(smi['dynamics_sim_points']), text='Simulation Points')
        col.prop(shp_modf, shp_inp(smi['dynamics_sim_smoothing']), text='Post-sim Smoothing')
        col.prop(shp_modf, shp_inp(smi['dynamics_sim_complex_curls']), text='Complex Curls Simulation')


# WIND EFFECTS
def draw_wind_effects(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]

        row = col.row(align=True)
        row.prop(shp_controls, "wind_generation_type", expand=True)
        col.label(text="Wind Settings:")
        col.prop(shp_modf, shp_inp(smi['dynamics_wind_force']), text='Force')
        col.prop(shp_modf, shp_inp(smi['dynamics_wind_speed']), text='Speed')

        col.separator(factor=0.5)

        col.prop(shp_modf, shp_inp(smi['dynamics_wind_turbulence']), text='Turbulence')
        row = col.row(align=True)
        row.prop(shp_controls, "turbulence_type", expand=True)
        
        col.separator(factor=0.5)

        sub = col.column(align=True)
        if shp_controls.turbulence_type == 'TAB_1':
            sub.enabled = False
        else:
            sub.enabled = True
        sub.prop(shp_modf, shp_inp(smi['dynamics_wind_turbulence_orientation']), text='Wave Orientation')
        sub.prop(shp_modf, shp_inp(smi['dynamics_wind_turbulence_scale']), text='Wave Scale')
        
        box = layout.box()
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']]
        col.label(text="Wind Direction:")
        col.prop(shp_modf, shp_inp(smi['dynamics_wind_direction']), text='Direction')
        col.prop(shp_modf, shp_inp(smi['dynamics_wind_use_effector']), text='Use Effector')
        
        col = box.column(align=True)
        col.enabled = shp_modf[smi['dynamics_enable']] and shp_modf[smi['dynamics_wind_use_effector']]

        row = col.row(align=True)
        row.label(text="Effector Object:")
        row.prop(shp_modf, shp_inp(smi['dynamics_wind_effector_object']), text='')
        col.separator(factor=0.5)

        row = col.row(align=True)
        row.prop(shp_controls, "wind_effector_direction", expand=True)


# MATERIALS / UV
def draw_materials(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        
        if shp_modf[smi['utils_use_custom_hair_geo']]:
            layout.label(text=custom_hair_geo_message)

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=False)
        row.label(text="Materials:")

        col.prop_search(shp_controls, "hair_material", bpy.data, "materials")
        col.prop_search(shp_controls, "ornament_material", bpy.data, "materials")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="UV Settings:")
        col.prop(shp_modf, shp_inp(smi['material_uv_switch_order']), text='Switch UV Order')
        col.prop(shp_modf, shp_inp(smi['material_uv_extend']), text='Extend UV')
        col.prop(shp_modf, shp_inp(smi['material_uv_pack']), text='Pack UV Islands')
        col.prop(shp_modf, shp_inp(smi['material_uv_margin']), text='Margin')


# SHADES
def draw_shades(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        col.prop(shp_modf, shp_inp(smi['material_shade_color']), text='Strand Color')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Noise:")
        col.prop(shp_modf, shp_inp(smi['material_shade_noise_scale']), text='Scale')
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_noise_contrast']), text='Contrast')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_noise_seed']), text='Seed')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['material_shade_noise_twist']), text='Twist')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Sub-strands Shade:")
        col.prop(shp_modf, shp_inp(smi['material_shade_ss_blur']), text='Blur')
        col.prop(shp_modf, shp_inp(smi['material_shade_ss_balance']), text='Color Balance')
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_ss_contrast']), text='Contrast')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_ss_seed']), text='Seed')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Random per Strand Shade:")
        col.prop(shp_modf, shp_inp(smi['material_shade_random_seed']), text='Seed')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Ends Shade:")
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_tip']), text='Tip')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_tip_contrast']), text='Contrast')
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_root']), text='Root')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_root_contrast']), text='Contrast')
        col.separator(factor=0.6)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_noise']), text='Noise')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_ends_noise_contrast']), text='Contrast')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Anisotropic Highlight:")
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_anime_move']), text='Move')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_anime_size']), text='Size')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['material_shade_anime_shift']), text='Spot Shift')
        col.prop(shp_modf, shp_inp(smi['material_shade_anime_brightness']), text='Brightness')
        col.prop(shp_modf, shp_inp(smi['material_shade_anime_detail']), text='Detail')
        col.separator(factor=0.6)
        col.prop(shp_modf, shp_inp(smi['material_shade_anime_distortion']), text='Distortion')
        col.separator(factor=0.5)
        row = col.row(align=True)
        row.prop(shp_modf, shp_inp(smi['material_shade_anime_distortion_scale']), text='Scale')
        row.separator(factor=0.6)
        row.prop(shp_modf, shp_inp(smi['material_shade_anime_distortion_seed']), text='Seed')


# SETTINGS
def draw_settings(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
        layout = self.layout
        col = layout.column(align=True)

        row = col.row(align=False)
        row.label(text="Hair Settings:")
        row.prop(hair_curve, "show_wire", text='Show Wireframe')

        col.prop(shp_modf, shp_inp(smi['settings_pre_smooth']), text='Pre-smooth Hair Curve')
        col.prop(shp_modf, shp_inp(smi['use_original_thickness']), text='Use Original Thickness (Radius)')
        col.prop(shp_modf, shp_inp(smi['settings_flip_normals']), text='Flip Normals')
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Resolution:")
        
        row = col.row(align=False)
        row.label(text="Curve:")
        row.label(text="Profile:")
        row.label(text="Ornament:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['settings_resolution_curve']), text='')
        row.prop(shp_modf, shp_inp(smi['settings_resolution_profile']), text='')
        row.prop(shp_modf, shp_inp(smi['settings_resolution_ornament']), text='')

        col.prop(shp_modf, shp_inp(smi['settings_resolution_auto_adjust']), text='Auto-Adjust Resolution')
        col.prop(shp_modf, shp_inp(smi['settings_resolution_taper']), text='Taper Curve Resolution')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Shading Style:")
        row = col.row(align=True)
        row.prop(shp_controls, "shading_style_selector", expand=True)
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['settings_auto_smooth_angle']), text='Auto-Smooth Angle')

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Subdivision Level:")

        row = col.row(align=False)
        row.label(text="Hair Curve:")
        row.label(text="Geometry:")

        row = col.row(align=False)
        row.prop(shp_modf, shp_inp(smi['settings_subd_hair']), text='')
        row.prop(shp_modf, shp_inp(smi['settings_subd_geo']), text='')
        

# MESH CONVERSION
def draw_mesh_conversion(self, context, space):
    # shp_controls = context.scene.shp_addon
    # hair_curve = context.object
    # node_group_name = "Stylized Hair PRO"

    # if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    shp_modf = hair_curve.modifiers["Stylized Hair PRO"]
    
    col = space.column(align=True)
    if hair_curve.type == 'CURVES':
        col.prop(shp_controls, "generate_armature")
    else:
        col.label(text="Armature available only for Hair Curves.")

    col = space.column(align=True)
    col.enabled = shp_controls.generate_armature and hair_curve.type == 'CURVES'
    col.prop(shp_modf, shp_inp(smi['utils_armature_preview']), text='Preview Armature')
    
    row = col.row(align=True)
    row.enabled = shp_modf[smi['utils_armature_preview']]
    row.prop(shp_modf, shp_inp(smi['utils_armature_preview_scale']), text='Preview Scale')

    col.separator(factor=1)
    col.label(text = "Bone Type:")
    row = col.row(align=True)
    row.prop(shp_controls, "armature_type_selector", expand=True)
    col.separator(factor=0.5)

    if shp_controls.armature_type_selector == 'TAB_1':
        col.prop(shp_modf, shp_inp(smi['utils_armature_bones']), text='Bone Count')
        col.prop(shp_modf, shp_inp(smi['utils_armature_taper']), text='Taper Armature')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['utils_armature_use_curl']), text='Use Curled Curve')
    elif shp_controls.armature_type_selector == 'TAB_2':
        col.prop(shp_modf, shp_inp(smi['utils_bbone_armature_handles']), text='Number of Handles')
        col.prop(shp_modf, shp_inp(smi['utils_bbone_armature_handle_size']), text='Handle Size')
        col.separator(factor=0.5)
        col.prop(shp_modf, shp_inp(smi['utils_bbone_armature_segments']), text='B-bone Segments')
    
    col.separator(factor=1)
    col.prop(shp_controls, "parent_to_armature")
    
    col = space.column(align=True)
    col.enabled = shp_controls.parent_to_armature and shp_controls.generate_armature
    col.prop(shp_controls, "parent_type_selector", text='Method')    

    col = space.column(align=True)
    if shp_controls.armature_type_selector == 'TAB_1':
        col.operator("wm.mesh_convert")
    elif shp_controls.armature_type_selector == 'TAB_2':
        col.operator("wm.mesh_convert_b_bone")


# UTILITIES
def draw_utilities(self, context):
    shp_controls = context.scene.shp_addon
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"
    
    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_modf = hair_curve.modifiers[node_group_name]
        layout = self.layout

        # update version sub-panel
        header, panel = layout.panel("shp_ui_panel_update_version", default_closed=True)
        header.label(text="UPDATE TO LATEST VERSION")
        if panel:
            col = panel.column(align=True)
            col.separator(factor=0.5)

            if f"{bl_info['version'][0]}.{bl_info['version'][1]}{bl_info['version'][2]}" in bpy.data.node_groups[node_group_name].nodes["Frame.016"].label:
                col.label(text = "Setup matches installed version!")
                col = panel.column(align=True)
                col.enabled = False
                col.operator("wm.update_shp_version", text="Update to Latest Version")
            else:
                col.label(text = "⚠ Save a BACKUP of your file!")
                col.label(text = "1. Select all curves with older SHP setup.")
                col.label(text = "2. Run the UPDATE with the button bellow.")
                col = panel.column(align=True)
                col.enabled = True
                col.operator("wm.update_shp_version", text="Update to Latest Version")

        # mesh convert sub-panel
        header, panel = layout.panel("shp_ui_panel_mesh_convert", default_closed=True)
        header.label(text="MESH & ARMATURE")
        if panel:
            draw_mesh_conversion(self, context, panel)

        # custom hair geo sub-panel
        header, panel = layout.panel("shp_ui_panel_custom_hair_geo", default_closed=True)
        header.label(text="CUSTOM HAIR GEOMETRY")
        if panel:
            col = panel.column(align=True)
            col.prop(shp_modf, shp_inp(smi['utils_use_custom_hair_geo']), text='Use Custom Hair Geometry')
            col = panel.column(align=True)
            col.enabled = shp_modf[smi['utils_use_custom_hair_geo']]
            col.label(text = "Custom Hair Object:")
            col.prop(shp_modf, shp_inp(smi['utils_custom_hair_object']), text='')
            col.separator(factor=1)
            row = col.row(align=True)
            row.label(text="Deform Axis:")
            sub = row.row(align=False)
            sub.scale_x = 0.5
            sub.prop(shp_controls, "custom_geo_deform_axis", expand=True)


# GLOBAL VALUES
def draw_global_values(self, context):
    hair_curve = context.object
    node_group_name = "Stylized Hair PRO"

    if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
        shp_nodetree = bpy.data.node_groups["Stylized Hair PRO"]
        layout = self.layout

        layout.label(text="Settings Scale Factor:")
        box = layout.box()
        col = box.column(align=True)
        col.prop(shp_nodetree.nodes["SHP_nt_global_settings_scale"].inputs[0], "default_value", text='Scale Factor')

        layout.label(text="Global Materials:")
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=False)
        row.label(text="Hair Material:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_material_1"].inputs[2], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_material_1"].inputs[1], "default_value", text='Set')

        row = col.row(align=False)
        row.label(text="Ornament Material:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_material_2"].inputs[2], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_material_2"].inputs[1], "default_value", text='Set')

        layout.label(text="Global UV Settings:")
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_uv_1"].inputs[2], "default_value", text='Switch UV Order')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_uv_1"].inputs[1], "default_value", text='Set')

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_uv_1"].inputs[5], "default_value", text='Extend UV')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_uv_1"].inputs[4], "default_value", text='Set')

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_uv_2"].inputs[8], "default_value", text='Pack UV Islands')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_uv_2"].inputs[7], "default_value", text='Set')

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_uv_2"].inputs[11], "default_value", text='Margin')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_uv_2"].inputs[10], "default_value", text='Set')

        layout.label(text="Global Hair Dynamics Settings:")
        box = layout.box()
        col = box.column(align=True)

        # Stiffness
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[2], "default_value", text='Stiffness')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[1], "default_value", text='Set')

        # Elasticity
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[5], "default_value", text='Elasticity')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[4], "default_value", text='Set')

        # Damping
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[8], "default_value", text='Damping')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[7], "default_value", text='Set')

        col.separator()

        # Liveliness
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[11], "default_value", text='Liveliness')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[10], "default_value", text='Set')

        col.separator()

        # Effect Factor
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[14], "default_value", text='Effect Factor')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[13], "default_value", text='Set')

        # Contrast
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[17], "default_value", text='Contrast')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[16], "default_value", text='Set')

        col.separator()

        # Gravity Strength
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[20], "default_value", text='Gravity Strength')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[19], "default_value", text='Set')

        # Gravity Direction
        row = col.row(align=False)
        row.label(text="Gravity Direction:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[23], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[22], "default_value", text='Set')

        # Collider Object
        row = col.row(align=False)
        row.label(text="Collider Object:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[26], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[25], "default_value", text='Set')

        col.separator()

        # Distance
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[29], "default_value", text='Offset Distance')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[28], "default_value", text='Set')

        # Repel Force
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[32], "default_value", text='Repel Force')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[31], "default_value", text='Set')

        # Quality Steps
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[35], "default_value", text='Quality Steps')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[34], "default_value", text='Set')

        col.separator()

        row = col.row(align=False)
        row.label(text="Wind Effects:")

        # Wind Force
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[38], "default_value", text='Wind Force')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[37], "default_value", text='Set')

        # Wind Speed
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[41], "default_value", text='Wind Speed')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[40], "default_value", text='Set')

        # Turbulence
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[44], "default_value", text='Turbulence')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[43], "default_value", text='Set')

        # Complex / Simple
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[47], "default_value", text='Complex / Simple')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[46], "default_value", text='Set')

        # Wave Orientation
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[50], "default_value", text='Wave Orientation')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[49], "default_value", text='Set')

        # Wave Scale
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[74], "default_value", text='Wave Orientation')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[73], "default_value", text='Set')

        # Wind Direction
        row = col.row(align=False)
        row.label(text="Wind Direction:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[53], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[52], "default_value", text='Set')

        # Use Effector
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[56], "default_value", text='Use Effector')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[55], "default_value", text='Set')

        # Effector Object
        row = col.row(align=False)
        row.label(text="Effector Object:")

        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[59], "default_value", text='')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[58], "default_value", text='Set')

        # Attract / Repel
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[62], "default_value", text='Attract / Repel')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[61], "default_value", text='Set')

        # Simulation Points
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[65], "default_value", text='Simulation Points')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[64], "default_value", text='Set')

        # Post-sim Smoothing
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[68], "default_value", text='Post-sim Smoothing')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_1"].inputs[67], "default_value", text='Set')

        # Complex Curls Simulation
        row = col.row(align=False)
        row.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_2"].inputs[71], "default_value", text='Complex Curls Simulation')
        sub = row.row(align=False)
        sub.scale_x = 0.5
        sub.prop(shp_nodetree.nodes["SHP_nt_global_dynamics_2"].inputs[70], "default_value", text='Set')


################################
# PROPERTY GROUP (CUSTOM PROPS)
################################

# class SHP_Props(bpy.types.PropertyGroup):
#     # Custom Twist Tab Selector
#     custom_twist_tab: bpy.props.EnumProperty(
#         items=[('TAB_1', "Twist 1", "Custom Twist 1"),
#                ('TAB_2', "Twist 2", "Custom Twist 2"),
#                ('TAB_3', "Twist 3", "Custom Twist 3")],
#         default='TAB_1'
#     )

class SHP_Props(bpy.types.PropertyGroup):
    # Custom Twist Tab Selector
    custom_twist_tab: bpy.props.EnumProperty(
        items=[('TAB_1', "Twist 1", "Custom Twist 1"),
               ('TAB_2', "Twist 2", "Custom Twist 2"),
               ('TAB_3', "Twist 3", "Custom Twist 3")],
        default='TAB_1'
    ) # type: ignore

    # Profile Curve Selector
    profile_selector: bpy.props.EnumProperty(
        items=[('TAB_1', "Box", "Square/Smooth Profile", 'SNAP_FACE', 1),
               ('TAB_2', "Triangle", "Triangular/Smooth Profile", 'PLAY', 2),
               ('TAB_3', "Robo", "Sharp/Angular Profile", 'SELECT_EXTEND', 3),
               ('TAB_4', "Islands", "Multiple Islands Profile", 'OUTLINER_OB_POINTCLOUD', 4),
               ('TAB_5', "Line", "2D Line Profile", 'IPO_LINEAR', 5),
               ('TAB_6', "Crescent", "Crescent Profile", 'SPHERECURVE', 6)],
        default='TAB_1',
        update=update_profile
    ) # type: ignore

    # Ornament Type Selector
    ornament_selector: bpy.props.EnumProperty(
        items=[('TAB_1', "Band", "Simple band, that follows the hair strand"),
               ('TAB_2', "Ring", "Ring/Coil tie"),
               ('TAB_3', "Scrunchie", "Scrunchie Tie"),
               ('TAB_4', "Custom", "Select a custom ornament Object/Collection")],
        default='TAB_1',
        update=update_ornament
    ) # type: ignore

    # Custom Ornament Tab Selector
    custom_ornament_tab: bpy.props.EnumProperty(
        items=[('TAB_1', "Object", "Custom Ornament Object"),
               ('TAB_2', "Collection", "Custom Ornament Collection")],
        default='TAB_1',
        update=update_custom_ornament
    ) # type: ignore

    # Custom Ornament Collection
    ornaments_custom_collection: bpy.props.PointerProperty(type=bpy.types.Collection, name='', update=update_ornaments_custom_collection) # type: ignore

    # Custom Ornament Axis Selector
    ornament_deform_axis: bpy.props.EnumProperty(
        items=[('TAB_1', "X", "Deform along X-axis of ornament object"),
               ('TAB_2', "Y", "Deform along Y-axis of ornament object"),
               ('TAB_3', "Z", "Deform along Z-axis of ornament object"),],
        default='TAB_3',
        update=update_ornament_deform_axis
    ) # type: ignore

    # Hair Material
    hair_material: bpy.props.PointerProperty(type=bpy.types.Material, name='Hair', update=update_hair_material) # type: ignore

    # Ornament Material
    ornament_material: bpy.props.PointerProperty(type=bpy.types.Material, name='Ornament', update=update_ornament_material) # type: ignore

    # Shading Style Selector
    shading_style_selector: bpy.props.EnumProperty(
        items=[('TAB_1', "Flat", "Flat Shading"),
               ('TAB_2', "Smooth", "Smooth Shading"),
               ('TAB_3', "Auto-Smooth", "Auto-Smooth Shading")],
        default='TAB_3',
        update=update_shading_style_selector
    ) # type: ignore

    # Wind Simulation / Generation
    wind_generation_type: bpy.props.EnumProperty(
        items=[('TAB_1', "Simulated", "Run the Wind Effects through the Dynamics simulation. Creates more accurate results, but prevents looping."),
               ('TAB_2', "Generated", "Generate the Wind Effects as a post-effect to the Dynamics simulation. Creates less accurate results, but allows looping. Suitable for static sculptures.")],
        default='TAB_1',
        update=update_wind_generation_type
    ) # type: ignore

    # Complex / Simple Turbulence
    turbulence_type: bpy.props.EnumProperty(
        items=[('TAB_1', "Complex", "Complex wind wave"),
               ('TAB_2', "Simple", "Simple wind wave")],
        default='TAB_1',
        update=update_turbulence_type
    ) # type: ignore

    # Wind Effector Attract / Repel
    wind_effector_direction: bpy.props.EnumProperty(
        items=[('TAB_1', "Attract", "Attract wind towards the Effector Object"),
               ('TAB_2', "Repel", "Repel wind away from the Effector Object")],
        default='TAB_1',
        update=update_wind_effector_direction
    ) # type: ignore

    # for armature generation

    # Generate Armature
    generate_armature: bpy.props.BoolProperty(name='Generate Armature',
                                              description='Automatically generate an armature to the selected hair strand, when converted to mesh',
                                              default=False,
                                              update=update_generate_armature
    ) # type: ignore

    # Parent to Armature
    parent_to_armature: bpy.props.BoolProperty(name='Parent to Armature',
                                               description='Parent the hair mesh to the generated armature',
                                               default=False) # type: ignore

    # Parent Type
    parent_type_selector: bpy.props.EnumProperty(
        items=[('TAB_1', "With Empty Groups", "Armature Deform: With Empty Groups"),
               ('TAB_2', "With Envelope Weights", "Armature Deform: With Envelope Weights"),
               ('TAB_3', "With Automatic Weights", "Armature Deform: With Automatic Weights")
               ],
        default='TAB_3'
    ) # type: ignore


    # Custom Hair Geometry Axis Selector
    custom_geo_deform_axis: bpy.props.EnumProperty(
        items=[('TAB_1', "X", "Deform along X-axis of object"),
               ('TAB_2', "Y", "Deform along Y-axis of object"),
               ('TAB_3', "Z", "Deform along Z-axis of object"),],
        default='TAB_3',
        update=update_custom_geo_deform_axis
    ) # type: ignore


    # Custom Ornament Tab Selector
    armature_type_selector: bpy.props.EnumProperty(
        items=[('TAB_1', "Normal", "Create an armature with normal bones."),
               ('TAB_2', "B-Bone", "Create a Bendy Bone armature.")],
        default='TAB_1',
        update=update_armature_type_selector
    ) # type: ignore


################################
#   OPERATORS
################################

# ADD SHP SETUP
class SHP_OT_AppendStylizedHairPro(bpy.types.Operator):
    bl_idname = "wm.append_stylized_hair_pro"
    bl_label = "Add 'Stylized Hair PRO' setup"
    bl_description = "Add 'Stylized Hair PRO' setup to the selected curve"

    def execute(self, context):
        shp_add_setup()

        return {'FINISHED'}


# REMOVE SHP SETUP
class SHP_OT_RemoveStylizedHairPro(bpy.types.Operator):
    bl_idname = "wm.remove_stylized_hair_pro"
    bl_label = "Remove 'Stylized Hair PRO' setup"
    bl_description = "Remove 'Stylized Hair PRO' setup to the selected curve"

    def execute(self, context):
        
        shp_remove_setup()
        
        return {'FINISHED'}


# RESET ALL
class SHP_OT_ResetAll(bpy.types.Operator):
    bl_idname = "wm.reset_all"
    bl_label = "Reset All"
    bl_description = "Reset all settings to default"

    def execute(self, context):
        node_group_name = "Stylized Hair PRO"

        bpy.ops.object.modifier_remove(modifier=node_group_name)

        bpy.ops.object.modifier_add(type='NODES')
        bpy.context.object.modifiers.active.name = node_group_name
        bpy.context.object.modifiers.active.node_group = bpy.data.node_groups[node_group_name]
        bpy.context.object.modifiers.active.show_group_selector = False

        return {'FINISHED'}


# ADD STRAND
class SHP_OT_AddStrand(bpy.types.Operator):
    bl_idname = "wm.add_strand"
    bl_label = "Add Strand"
    bl_description = "Add a hair curve to the selected mesh"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'MESH'}:
            bpy.ops.object.curves_empty_hair_add(align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.object.name = "Hair Strand"
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Add", space_type='VIEW_3D')
            bpy.context.tool_settings.curves_sculpt.brush.curves_sculpt_settings.points_per_curve = 20
        return {'FINISHED'}


# DUPLICATE STRAND
class SHP_OT_DuplicateStrand(bpy.types.Operator):
    bl_idname = "wm.duplicate_strand"
    bl_label = "Duplicate Strand"
    bl_description = "Duplicate the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVE', 'CURVES'}:
            bpy.ops.object.duplicate(linked=False)
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Slide", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


## for PROFILES
# BOX PROFILE
class SHP_OT_ProfileBox(bpy.types.Operator):
    bl_idname = "wm.set_profile_box"
    bl_label = "Box"
    bl_description = "Square/Smooth Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_1'

        return {'FINISHED'}


# TRIANGLE PROFILE
class SHP_OT_ProfileTriangle(bpy.types.Operator):
    bl_idname = "wm.set_profile_triangle"
    bl_label = "Triangle"
    bl_description = "Triangular/Smooth Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_2'

        return {'FINISHED'}


# ROBO PROFILE
class SHP_OT_ProfileRobo(bpy.types.Operator):
    bl_idname = "wm.set_profile_robo"
    bl_label = "Robo"
    bl_description = "Angular/Sharp Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_3'

        return {'FINISHED'}


# ISLANDS PROFILE
class SHP_OT_ProfileIslands(bpy.types.Operator):
    bl_idname = "wm.set_profile_islands"
    bl_label = "Islands"
    bl_description = "Multiple Curves Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_4'

        return {'FINISHED'}


# LINE PROFILE
class SHP_OT_ProfileLine(bpy.types.Operator):
    bl_idname = "wm.set_profile_line"
    bl_label = "Line"
    bl_description = "2D Line Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_5'

        return {'FINISHED'}


# CRESCENT PROFILE
class SHP_OT_ProfileCrescent(bpy.types.Operator):
    bl_idname = "wm.set_profile_crescent"
    bl_label = "Crescent"
    bl_description = "Crescent Profile"

    def execute(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"
        shp_ctrl = bpy.context.scene.shp_addon

        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            shp_ctrl.profile_selector = 'TAB_6'

        return {'FINISHED'}


# TOGGLE DYNAMICS
class SHP_OT_ToggleDynamics(bpy.types.Operator):
    bl_idname = "wm.toggle_dynamics"
    bl_label = "Toggle Dynamics"
    bl_description = "Enable Dynamics"

    def execute(self, context):
        modifier = context.object.modifiers["Stylized Hair PRO"]

        if not modifier[smi['dynamics_enable']]:
            modifier[smi['dynamics_enable']] = True
        else:
            modifier[smi['dynamics_enable']] = False

        refresh_modifier()

        return {'FINISHED'}


# CONVERT TO MESH
class SHP_OT_MeshConvert(bpy.types.Operator):
    bl_idname = "wm.mesh_convert"
    bl_label = "Convert Hair Curve to Mesh"
    bl_description = "Convert the selected hair curve to mesh and generate the armature if enabled"

    def execute(self, context):
        modf_name = "Stylized Hair PRO"
        hair_curve = context.object
        hair_curve_name = context.object.name
        shp_controls = context.scene.shp_addon
        splines_count = 0
        armature_name = ""
        mirror_axes = 0
       
        hair_curve.modifiers[modf_name]["Socket_70"] = False  # Remove the armature preview

        if hair_curve and hair_curve.type == 'CURVES' and modf_name in hair_curve.modifiers:
            if shp_controls.generate_armature:
                
                hair_curve.modifiers[modf_name]["Socket_74"] = True # Toggle the armature guide curve
                
                refresh_modifier() # Refresh modifier

                # Get the number of mirror axes
                mirror_axes = hair_curve.modifiers[modf_name]["Input_169"] + hair_curve.modifiers[modf_name]["Socket_79"] + hair_curve.modifiers[modf_name]["Socket_80"]
                
                # Set the number of splines (read mirroring)
                if bpy.context.object.type == 'CURVES':
                    splines_count = len(bpy.context.object.data.curves) * (2 ** mirror_axes)
                elif bpy.context.object.type == 'CURVE':
                    splines_count = len(bpy.context.object.data.splines) * (2 ** mirror_axes)
                
                curve_points = bpy.context.object.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.attributes['arm_point_pos'] # Get the position attribute from the evaluated curve

                points_per_spline = int(len(curve_points.data) / splines_count) # Get the number of points in each spline

                start_point = curve_points.data[0].vector # Position of the root point of the curve

                end_point = curve_points.data[1].vector # Position of the second point of the curve
                
                bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(start_point),
                                            scale=(1, 1, 1)) # Add the armature at the location of the root point
                
                armature_name = f"Armature ({hair_curve_name})"
                bpy.context.object.name = armature_name # Set the name of the armature

                tail_loc = end_point - start_point # Calculate the global position vector for the second point

                bpy.ops.object.editmode_toggle() # Enter 'Edit Mode'
                
                bpy.context.edit_object.data.edit_bones[0].tail = (tail_loc) # Set the tail of the first bone to the location of the second curve point
                
                bpy.ops.armature.select_all(action='SELECT') # Select the bone
                
                for i in range(points_per_spline - 2):
                    start_pt = curve_points.data[i + 1].vector
                    end_pt = curve_points.data[i + 2].vector

                    target_loc = end_pt - start_pt
                    bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False},
                                                  TRANSFORM_OT_translate={"value": target_loc}) # Extrude bones
                
                if splines_count > 1: # Add new bone chains if there are more than 1 spline
                    for i in range(1, splines_count):
                        
                        new_start_point = curve_points.data[points_per_spline * i].vector # Position of the root point of the curve
                        
                        new_end_point = curve_points.data[(points_per_spline * i) + 1].vector # Position of the second point of the curve
                        
                        new_head_loc = new_start_point - start_point # Calculate the local position vector for the head
                        
                        new_tail_loc = new_end_point - start_point # Calculate the local position vector for the tail
                        
                        bpy.ops.armature.bone_primitive_add() # Add new bone
                        
                        bpy.context.edit_object.data.edit_bones[(points_per_spline * i) - i].head = (new_head_loc)
                        bpy.context.edit_object.data.edit_bones[(points_per_spline * i) - i].tail = (new_tail_loc) # Set the tail of the first bone to the location of the second curve point
                        
                        for j in range((points_per_spline * i), (points_per_spline * i) + points_per_spline - 2):
                            new_start_pt = curve_points.data[j + 1].vector
                            new_end_pt = curve_points.data[j + 2].vector

                            new_target_loc = new_end_pt - new_start_pt
                            bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False},
                                                          TRANSFORM_OT_translate={"value": new_target_loc}) # Extrude bones
                
                bpy.ops.object.editmode_toggle() # Exit 'Edit Mode'
                
                bpy.ops.object.select_all(action='DESELECT') # Deselect all objects

                if hair_curve_name in bpy.data.objects: # Check if the curve exists in the scene
                    bpy.context.view_layer.objects.active = bpy.data.objects[hair_curve_name] # Set the curve as the active object
                    bpy.data.objects[hair_curve_name].select_set(True) # Select the curve
                
                hair_curve.modifiers[modf_name]["Socket_74"] = False # Toggle the armature guide curve (hide)
                
                refresh_modifier() # Refresh modifier
            else:
                pass
            
            bpy.ops.object.convert(target='MESH') # Convert the hair curve to mesh

            if shp_controls.generate_armature is True and shp_controls.parent_to_armature is True:
                
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM') # Remove the parenting from the base mesh
                
                bpy.data.objects[armature_name].select_set(True) # Add the armature to the selection
                
                bpy.context.view_layer.objects.active = bpy.data.objects[armature_name] # Set the armature as the active object
                
                if shp_controls.parent_type_selector == 'TAB_1': # Parent the hair mesh to the armature
                    bpy.ops.object.parent_set(type='ARMATURE_NAME')
                elif shp_controls.parent_type_selector == 'TAB_2':
                    bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
                elif shp_controls.parent_type_selector == 'TAB_3':
                    bpy.ops.object.parent_set(type='ARMATURE_AUTO') 
        else:
            bpy.ops.object.convert(target='MESH') # Convert the hair curve to mesh

        return {'FINISHED'}


# CONVERT TO MESH (B-bone)
class SHP_OT_MeshConvertBbone(bpy.types.Operator):
    bl_idname = "wm.mesh_convert_b_bone"
    bl_label = "Convert Hair Curve to Mesh"
    bl_description = "Convert the selected hair curve to mesh and generate the armature if enabled"

    def execute(self, context):
        modf_name = "Stylized Hair PRO"
        hair_curve = context.object
        hair_curve_name = context.object.name
        shp_controls = context.scene.shp_addon
        splines_count = 0
        armature_name = ""
        mirror_axes = 0
        bbone_segments = hair_curve.modifiers[modf_name][smi['utils_bbone_armature_segments']]
       
        hair_curve.modifiers[modf_name]["Socket_70"] = False  # Remove the armature preview

        if hair_curve and hair_curve.type == 'CURVES' and modf_name in hair_curve.modifiers:
            if shp_controls.generate_armature:
                
                hair_curve.modifiers[modf_name]["Socket_74"] = True # Toggle the armature guide curve
                
                refresh_modifier() # Refresh modifier

                # Get the number of mirror axes
                mirror_axes = hair_curve.modifiers[modf_name]["Input_169"] + hair_curve.modifiers[modf_name]["Socket_79"] + hair_curve.modifiers[modf_name]["Socket_80"]
                
                # Set the number of splines (read mirroring)
                if bpy.context.object.type == 'CURVES':
                    splines_count = len(bpy.context.object.data.curves) * (2 ** mirror_axes)
                elif bpy.context.object.type == 'CURVE':
                    splines_count = len(bpy.context.object.data.splines) * (2 ** mirror_axes)
                
                curve_points = bpy.context.object.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.attributes['arm_point_pos'] # Get the position attribute from the evaluated curve

                points_per_spline = int(len(curve_points.data) / splines_count) # Get the number of points in each spline

                start_point = curve_points.data[0].vector # Position of the root point of the curve

                end_point = curve_points.data[1].vector # Position of the second point of the curve
                
                bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(start_point),
                                            scale=(1, 1, 1)) # Add the armature at the location of the root point
                
                armature_name = f"Armature ({hair_curve_name})"
                bpy.context.object.name = armature_name # Set the name of the armature object
                bpy.context.object.data.name = armature_name # Set the name of the armature
                bpy.context.object.data.display_type = 'BBONE' # Set the viewport preview as B-Bone

                tail_loc = end_point - start_point # Calculate the global position vector for the second point

                bpy.ops.object.editmode_toggle() # Enter 'Edit Mode'
                
                bpy.context.edit_object.data.edit_bones[0].tail = (tail_loc) # Set the tail of the first bone to the location of the second curve point
                
                bpy.ops.armature.select_all(action='SELECT') # Select the bone
                bpy.context.active_bone.name = "SHP_Root_Handle" # Name the bone
                bpy.context.active_bone.use_deform = False # Set as non-deforming bone
                bpy.context.active_bone.bbone_z = 0.02
                bpy.context.active_bone.bbone_x = 0.02 # Set preview scale
                
                for i in range(points_per_spline - 2):
                    b_bone_name_id = 1
                    handle_name_id = 1

                    start_pt = curve_points.data[i + 1].vector # Get the position of the next point in the guide curve (the tail of the previous bone)
                    end_pt = curve_points.data[i + 2].vector # Get the position of the next point over in the guide curve (the target for the new bone's tail)

                    target_loc = end_pt - start_pt # Create the offset vector for the new bone from the previous

                    bone = bpy.context.view_layer.objects.active.data.edit_bones.active
                    bpy.ops.armature.select_all(action='DESELECT')
                    bone.select_tail = True
                    bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False},
                                                  TRANSFORM_OT_translate={"value": target_loc}) # Extrude new bone
                    
                    # Alternate between handles and b-bones
                    if i % 2 == 0: # B-Bone
                        bpy.context.active_bone.name = f"SHP_B-bone.{b_bone_name_id:0>3}"   # Name the new bone
                        bpy.context.active_bone.use_deform = True                           # Set as deforming bone
                        bpy.context.active_bone.bbone_segments = bbone_segments             # Set the number of segments
                        bpy.context.active_bone.bbone_z = 0.005
                        bpy.context.active_bone.bbone_x = 0.005                             # Set preview scale
                        bpy.context.active_bone.bbone_handle_type_start = 'ABSOLUTE'
                        bpy.context.active_bone.bbone_handle_type_end = 'ABSOLUTE'          # Set b-bone handle types

                    else: # Handle
                        bpy.context.active_bone.name = f"SHP_Handle.{handle_name_id:0>3}"                   # Name the new bone
                        bpy.context.active_bone.use_deform = False                                          # Set as non-deforming bone
                        bpy.context.active_bone.bbone_z = 0.02
                        bpy.context.active_bone.bbone_x = 0.02                                             # Set preview scale
                        
                        b_bone = bpy.context.view_layer.objects.active.data.edit_bones.active.parent
                        bpy.ops.armature.select_all(action='DESELECT')
                        bpy.context.view_layer.objects.active.data.edit_bones.active = b_bone
                        bpy.context.view_layer.objects.active.data.edit_bones.active.select = True              # Select and set active the previous b-bone

                        start_handle = bpy.context.view_layer.objects.active.data.edit_bones.active.parent
                        end_handle = bpy.context.view_layer.objects.active.data.edit_bones.active.children[0]
                        bpy.context.active_bone.bbone_custom_handle_start = start_handle
                        bpy.context.active_bone.bbone_custom_handle_end = end_handle                            # Set the b-bone custom handles

                        bpy.ops.object.posemode_toggle()                                                        # Enter 'Pose Mode'
                        bpy.ops.pose.constraint_add(type='STRETCH_TO')
                        bone_name = bpy.context.view_layer.objects.active.data.bones.active.name
                        armature_object = bpy.context.view_layer.objects.active
                        bone_target = bpy.context.view_layer.objects.active.data.bones.active.children[0].name
                        
                        constraint = bpy.context.object.pose.bones[bone_name].constraints["Stretch To"]
                        constraint.target = armature_object
                        constraint.subtarget = bone_target                                                      # Set the 'Stretch To' constraint

                        bpy.ops.object.editmode_toggle()                                                        # Enter 'Edit Mode'
                        
                        handle_bone = bpy.context.view_layer.objects.active.data.edit_bones.active.children[0]
                        bpy.ops.armature.select_all(action='DESELECT')
                        handle_bone.select = True
                        bpy.context.view_layer.objects.active.data.edit_bones.active = handle_bone              # Select back the handle bone
                        bpy.context.active_bone.parent = None                                                   # Clear its parent

                if splines_count > 1:                                                           # Add new bone chains if there are more than 1 spline
                    for i in range(1, splines_count):
                        
                        new_start_point = curve_points.data[points_per_spline * i].vector       # Position of the root point of the curve
                        
                        new_end_point = curve_points.data[(points_per_spline * i) + 1].vector   # Position of the second point of the curve
                        
                        new_head_loc = new_start_point - start_point                            # Calculate the local position vector for the head
                        
                        new_tail_loc = new_end_point - start_point                              # Calculate the local position vector for the tail
                        
                        new_bone_name = f"SHP_Root_Handle.{i:0>3}"
                        bpy.ops.armature.bone_primitive_add(name=new_bone_name)
                        bpy.context.view_layer.objects.active.data.edit_bones.active = bpy.context.view_layer.objects.active.data.edit_bones[new_bone_name]

                        bpy.context.active_bone.use_deform = False      # Set as non-deforming bone
                        bpy.context.active_bone.bbone_z = 0.02
                        bpy.context.active_bone.bbone_x = 0.02          # Set preview scale
                        
                        bpy.context.edit_object.data.edit_bones[(points_per_spline * i) - i].head = (new_head_loc)
                        bpy.context.edit_object.data.edit_bones[(points_per_spline * i) - i].tail = (new_tail_loc) # Set the tail of the first bone to the location of the second curve point
                        
                        for j in range((points_per_spline * i), (points_per_spline * i) + points_per_spline - 2):
                            new_start_pt = curve_points.data[j + 1].vector
                            new_end_pt = curve_points.data[j + 2].vector

                            new_target_loc = new_end_pt - new_start_pt
                            bone = bpy.context.view_layer.objects.active.data.edit_bones.active
                            bpy.ops.armature.select_all(action='DESELECT')
                            bone.select_tail = True
                            bpy.ops.armature.extrude_move(ARMATURE_OT_extrude={"forked": False},
                                                          TRANSFORM_OT_translate={"value": new_target_loc}) # Extrude bones
                            # Alternate between handles and b-bones
                            if j % 2 == 0: # B-Bone
                                bpy.context.active_bone.name = f"SHP_B-bone.{b_bone_name_id:0>3}"   # Name the new bone
                                bpy.context.active_bone.use_deform = True                           # Set as deforming bone
                                bpy.context.active_bone.bbone_segments = bbone_segments             # Set the number of segments
                                bpy.context.active_bone.bbone_z = 0.005
                                bpy.context.active_bone.bbone_x = 0.005                             # Set preview scale
                                bpy.context.active_bone.bbone_handle_type_start = 'ABSOLUTE'
                                bpy.context.active_bone.bbone_handle_type_end = 'ABSOLUTE'          # Set b-bone handle types

                            else: # Handle
                                bpy.context.active_bone.name = f"SHP_Handle.{handle_name_id:0>3}"               # Name the new bone
                                bpy.context.active_bone.use_deform = False                                      # Set as non-deforming bone
                                bpy.context.active_bone.bbone_z = 0.02
                                bpy.context.active_bone.bbone_x = 0.02                                          # Set preview scale
                                
                                b_bone = bpy.context.view_layer.objects.active.data.edit_bones.active.parent
                                bpy.ops.armature.select_all(action='DESELECT')
                                bpy.context.view_layer.objects.active.data.edit_bones.active = b_bone
                                bpy.context.view_layer.objects.active.data.edit_bones.active.select = True              # Select and set active the previous b-bone

                                start_handle = bpy.context.view_layer.objects.active.data.edit_bones.active.parent
                                end_handle = bpy.context.view_layer.objects.active.data.edit_bones.active.children[0]
                                bpy.context.active_bone.bbone_custom_handle_start = start_handle
                                bpy.context.active_bone.bbone_custom_handle_end = end_handle                            # Set the b-bone custom handles

                                bpy.ops.object.posemode_toggle()                                                        # Enter 'Pose Mode'
                                bpy.ops.pose.constraint_add(type='STRETCH_TO')
                                bone_name = bpy.context.view_layer.objects.active.data.bones.active.name
                                armature_object = bpy.context.view_layer.objects.active
                                bone_target = bpy.context.view_layer.objects.active.data.bones.active.children[0].name
                                
                                constraint = bpy.context.object.pose.bones[bone_name].constraints["Stretch To"]
                                constraint.target = armature_object
                                constraint.subtarget = bone_target                                                      # Set the 'Stretch To' constraint

                                bpy.ops.object.editmode_toggle()                                                        # Enter 'Edit Mode'
                                
                                handle_bone = bpy.context.view_layer.objects.active.data.edit_bones.active.children[0]
                                bpy.ops.armature.select_all(action='DESELECT')
                                handle_bone.select = True
                                bpy.context.view_layer.objects.active.data.edit_bones.active = handle_bone              # Select back the handle bone
                                bpy.context.active_bone.parent = None 
                
                bpy.ops.object.editmode_toggle() # Exit 'Edit Mode'
                
                bpy.ops.object.select_all(action='DESELECT') # Deselect all objects

                if hair_curve_name in bpy.data.objects: # Check if the curve exists in the scene
                    bpy.context.view_layer.objects.active = bpy.data.objects[hair_curve_name] # Set the curve as the active object
                    bpy.data.objects[hair_curve_name].select_set(True) # Select the curve
                
                hair_curve.modifiers[modf_name]["Socket_74"] = False # Toggle the armature guide curve (hide)
                
                refresh_modifier() # Refresh modifier
            else:
                pass
            
            bpy.ops.object.convert(target='MESH') # Convert the hair curve to mesh

            if shp_controls.generate_armature is True and shp_controls.parent_to_armature is True:
                
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM') # Remove the parenting from the base mesh
                
                bpy.data.objects[armature_name].select_set(True) # Add the armature to the selection
                
                bpy.context.view_layer.objects.active = bpy.data.objects[armature_name] # Set the armature as the active object
                
                if shp_controls.parent_type_selector == 'TAB_1': # Parent the hair mesh to the armature
                    bpy.ops.object.parent_set(type='ARMATURE_NAME')
                elif shp_controls.parent_type_selector == 'TAB_2':
                    bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
                elif shp_controls.parent_type_selector == 'TAB_3':
                    bpy.ops.object.parent_set(type='ARMATURE_AUTO') 
        else:
            bpy.ops.object.convert(target='MESH') # Convert the hair curve to mesh

        print("*** STYLIZED HAIR PRO MESSAGE: You can safely ignore dependency cycles error messages! They are caused by temporary code execution. Does not affect the final result. ***")
        return {'FINISHED'}


# UPDATE VERSION
class SHP_OT_UpdateVersion(bpy.types.Operator):
    bl_idname = "wm.update_shp_version"
    bl_label = "Update to Latest Version"
    bl_description = "Update existing hair curves to latest installed version of 'Stylized Hai PRO'"

    def execute(self, context):
        node_group_name = "Stylized Hair PRO"

        shp_temp_values = []            # whole temporary list (all_curves_name, all_settings_tuples) - used to store the modifier data for all curves
        shp_hair_curve_values = []      # list for the curve values (curve_name, settings_tuple)
        shp_modifier_values = []        # list for the modifier settings (socket, value)
        shp_temp_global_values = []     # separate list for the global values

        for item in sgv:
            shp_nodetree = bpy.data.node_groups["Stylized Hair PRO"]
            try:
                if shp_nodetree.nodes[item[1]].inputs[item[2]].type == 'VECTOR':
                    for i in range(3):
                        temp_gl_tuple = (item[1], item[2], shp_nodetree.nodes[item[1]].inputs[item[2]].default_value[i], i)
                        shp_temp_global_values.append(temp_gl_tuple)
                else:
                    temp_gl_tuple = (item[1], item[2], shp_nodetree.nodes[item[1]].inputs[item[2]].default_value, None)
                    shp_temp_global_values.append(temp_gl_tuple)
            except Exception:
                pass

        for hair_curve in bpy.context.selected_objects:
            shp_modifier = hair_curve.modifiers[node_group_name]
            
            shp_hair_curve_values.append(hair_curve.name)

            for control in smi.values():
                try:
                    if str(type(shp_modifier[control])) == "<class 'IDPropertyArray'>":
                        temp_tuple = (control, list(shp_modifier[control]))
                        shp_modifier_values.append(temp_tuple)
                    else:
                        temp_tuple = (control, shp_modifier[control])
                        shp_modifier_values.append(temp_tuple)
                except Exception:
                    pass

            shp_hair_curve_values.append(tuple(shp_modifier_values.copy())) # add the created "modifier_values" list as a tuple to "hair_curve_values"
            shp_temp_values.append(tuple(shp_hair_curve_values.copy())) # add the created "hair_curve_values" list as a tuple to "temp_values"
            
            shp_modifier_values.clear()
            shp_hair_curve_values.clear() # clear the values lists, ready for the next hair curve

        time.sleep(0.5)    
        shp_remove_setup() # Remove SHP from all selected curves
        
        # Remove all of the existing SHP node groups
        for node_group_name in sng:
            try:
                existing_node_group = bpy.data.node_groups[node_group_name]
                bpy.data.node_groups.remove(existing_node_group)
            except Exception:
                pass
        
        time.sleep(0.5)
        shp_add_setup() # Add new SHP to all selected curves

        # Return the modifier values from "shp_temp_values"
        for item in shp_temp_values:
            selected_hair_curve = bpy.data.objects[item[0]]
            
            for socket, value in item[1]:
                selected_hair_curve.modifiers["Stylized Hair PRO"][socket] = value
                # print(f"{selected_hair_curve.name} - {socket} : {value} --> {selected_hair_curve.modifiers['Stylized Hair PRO'][socket]}")

        time.sleep(0.5)
        refresh_modifier()

        # Return the global values from "shp_temp_global_values"
        for item in shp_temp_global_values:
            shp_nodetree = bpy.data.node_groups["Stylized Hair PRO"]
            try:
                if item[3] is None:
                    shp_nodetree.nodes[item[0]].inputs[item[1]].default_value = item[2]
                else:
                    shp_nodetree.nodes[item[0]].inputs[item[1]].default_value[item[3]] = item[2]
            except Exception:
                pass

        shp_temp_values.clear()
        shp_temp_global_values.clear() # clear the temporary lists
        
        return {'FINISHED'}


# RE-USE OLD CURVES
class SHP_OT_ReUseCurves(bpy.types.Operator):
    bl_idname = "wm.reuse_old_curves"
    bl_label = "Reuse Curves From Old Hairstyles."
    bl_description = "Re-use curves from an old hairstyle, updating them with the SHP setup"

    def execute(self, context):
        modf_name = "Stylized Hair PRO"
        hair_curve = context.object

        if hair_curve:
            for curve in bpy.context.selected_objects:
                bpy.context.view_layer.objects.active = curve # Set the curve as the active object
                if curve.type == 'CURVE':
                    profile_curve = curve.data.bevel_object
                    curve.data.bevel_object = None
                    if modf_name not in curve.modifiers:
                        shp_add_setup(all=False)
                        time.sleep(0.2)
                        curve.modifiers[modf_name][smi['use_original_thickness']] = True
                        curve.modifiers[modf_name][smi['profile_custom']] = profile_curve
                        curve.modifiers[modf_name][smi['settings_pre_smooth']] = 0.00
                        curve.modifiers[modf_name][smi['settings_flip_normals']] = True
                        curve.modifiers[modf_name][smi['material_hair']] = hair_curve.active_material
        return {'FINISHED'}

################################
#   PIE MENU BRUSH OPERATORS
################################

# COMB STRAND
class SHP_OT_CombStrand(bpy.types.Operator):
    bl_idname = "wm.comb_strand"
    bl_label = "Comb"
    bl_description = "Comb the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Comb", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


# SMOOTH STRAND
class SHP_OT_SmoothStrand(bpy.types.Operator):
    bl_idname = "wm.smooth_strand"
    bl_label = "Smooth"
    bl_description = "Smooth the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


# SLIDE STRAND
class SHP_OT_SlideStrand(bpy.types.Operator):
    bl_idname = "wm.slide_strand"
    bl_label = "Slide"
    bl_description = "Slide the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Slide", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


# GRAB STRAND
class SHP_OT_GrabStrand(bpy.types.Operator):
    bl_idname = "wm.grab_strand"
    bl_label = "Grab"
    bl_description = "Grab (Snake Hook) the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Snake Hook", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


# LENGTH STRAND
class SHP_OT_LengthStrand(bpy.types.Operator):
    bl_idname = "wm.length_strand"
    bl_label = "Length"
    bl_description = "Adjust the length of the selected strand"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.context.object and bpy.context.object.type in {'CURVES'}:
            bpy.ops.object.mode_set(mode='SCULPT_CURVES')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Grow / Shrink", space_type='VIEW_3D')
            bpy.ops.curves.select_all(action='SELECT')
        return {'FINISHED'}


################################
#   PIE MENU
################################

# Call Pie Menu Operator
class SHP_OT_CallPieMenu(bpy.types.Operator):
    bl_idname = "wm.shp_call_pie_menu"
    bl_label = "SHP Call Pie Menu"
    bl_description = "Open the Stylized Hair PRO Quick Menu"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="SHP_MT_PieMenu")
        return {'FINISHED'}


# Pie Menu
class SHP_MT_PieMenu(Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Stylized Hair PRO"

    def draw(self, context):
        obj = context.object
        node_group_name = "Stylized Hair PRO"
        layout = self.layout
        pcoll = preview_collections["main"]

        pie = layout.menu_pie()
        if obj and obj.type in {'CURVE', 'CURVES'} and "Stylized Hair PRO" in obj.modifiers:
            pie.enabled = True
        else:
            pie.enabled = False

        if obj and obj.type in {'CURVE', 'CURVES'} and "Stylized Hair PRO" in obj.modifiers:
            # Left
            col = pie.column()
            col.scale_x = 1.6
            col.scale_y = 1.5
            col.operator("wm.shape_pie_menu", icon_value=pcoll["shp_icon_curve_shape"].icon_id)
            col.operator("wm.twist_pie_menu", icon_value=pcoll["shp_icon_curve_twist"].icon_id)
            col.operator("wm.bumps_pie_menu", icon_value=pcoll["shp_icon_curve_bumps"].icon_id)
            col.operator("wm.curls_pie_menu", icon_value=pcoll["shp_icon_curve_curls"].icon_id)
            col.operator("wm.braid_pie_menu", icon_value=pcoll["shp_icon_curve_braid"].icon_id)

            # Right
            col = pie.column()
            col.scale_x = 1.0
            col.scale_y = 1.5
            col.operator("wm.profile_pie_menu", icon_value=pcoll["shp_icon_curve_profile"].icon_id)
            col.operator("wm.ornaments_pie_menu", icon_value=pcoll["shp_icon_curve_ornament"].icon_id)

            row = col.row(align=True)
            row.operator("wm.dynamics_pie_menu", icon_value=pcoll["shp_icon_curve_dynamics"].icon_id)
            row.separator(factor=0.3)
            sub = row.row(align=True)
            sub.scale_x = 0.2
            sub.operator("wm.wind_effects_pie_menu", text="                            ",
                         icon_value=pcoll["shp_icon_curve_wind"].icon_id)

            row = col.row(align=True)
            row.operator("wm.materials_pie_menu", icon_value=pcoll["shp_icon_curve_uv"].icon_id)
            row.separator(factor=0.3)
            sub = row.row(align=True)
            sub.scale_x = 0.265
            sub.operator("wm.shades_pie_menu", text="                            ",
                         icon_value=pcoll["shp_icon_curve_shades"].icon_id)

            row = col.row(align=True)
            row.operator("wm.settings_pie_menu", icon_value=pcoll["shp_icon_curve_settings"].icon_id)
            row.separator(factor=0.3)
            sub = row.row(align=True)
            sub.scale_x = 0.195
            sub.operator("wm.mesh_convert_pie_menu", text="                            ",
                         icon_value=pcoll["shp_icon_curve_mesh_convert"].icon_id)

            # Bottom
            col = pie.column()

            row = col.row()
            if obj and obj.type in {'CURVES'} and "Stylized Hair PRO" in obj.modifiers:
                row.enabled = True
            else:
                row.enabled = False
            row.scale_y = 2.0
            row.operator("wm.slide_strand", icon_value=pcoll["shp_icon_edit_slide"].icon_id)
            row.operator("wm.smooth_strand", icon_value=pcoll["shp_icon_edit_smooth"].icon_id)
            row.operator("wm.comb_strand", icon_value=pcoll["shp_icon_edit_comb"].icon_id)
            row.operator("wm.grab_strand", icon_value=pcoll["shp_icon_edit_grab"].icon_id)
            row.operator("wm.length_strand", icon_value=pcoll["shp_icon_edit_length"].icon_id)

            # Top
            col = pie.column()
            col.scale_x = 0.8

            row = col.row()
            row.scale_y = 1.2
            row.prop(obj, "name", text='')
            
            sub = row.row(align=True)
            sub.scale_x = 1.0
            sub.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_169"), text='X')
            sub.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Socket_79"), text='Y')
            sub.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Socket_80"), text='Z')
            
            col.separator(factor=0.5)

            row = col.row(align=False)
            row.scale_y = 1.4
            row.operator("wm.duplicate_strand", text="Duplicate Strand", icon_value=pcoll["shp_icon_curve_duplicate"].icon_id)
            row.operator("wm.reset_all", text="Reset", icon_value=pcoll["shp_icon_curve_refresh"].icon_id)

            col.separator(factor=0.5)

            row = col.row()
            row.scale_y = 1.0
            row.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_10"), text='Thickness')
            row.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_2"), text='Rotation')

            row = col.row(align=True)
            row.scale_y = 1.0
            row.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_161"), text='Root')
            row.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_160"), text='Mid')
            row.prop(obj.modifiers[node_group_name], "[\"%s\"]" % bpy.utils.escape_identifier("Input_159"), text='Tip')
            


################################
#   PIE MENU PANEL OPERATORS
################################

# SHAPE PIE MENU
class SHP_OT_ShapePieMenu(bpy.types.Operator):
    bl_idname = "wm.shape_pie_menu"
    bl_label = "SHAPE"
    bl_description = "Shape Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_shape(self, context)

    def execute(self, context):
        return {'FINISHED'}


# TWIST PIE MENU
class SHP_OT_TwistPieMenu(bpy.types.Operator):
    bl_idname = "wm.twist_pie_menu"
    bl_label = "TWIST"
    bl_description = "Twist Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_twist(self, context)

    def execute(self, context):
        return {'FINISHED'}


# BUMPS PIE MENU
class SHP_OT_BumpsPieMenu(bpy.types.Operator):
    bl_idname = "wm.bumps_pie_menu"
    bl_label = "BUMPS"
    bl_description = "Bumps Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_bumps(self, context)

    def execute(self, context):
        return {'FINISHED'}


# CURLS PIE MENU
class SHP_OT_CurlsPieMenu(bpy.types.Operator):
    bl_idname = "wm.curls_pie_menu"
    bl_label = "CURLS"
    bl_description = "Curls Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_curls(self, context)

    def execute(self, context):
        return {'FINISHED'}


# BRAID PIE MENU
class SHP_OT_BraidPieMenu(bpy.types.Operator):
    bl_idname = "wm.braid_pie_menu"
    bl_label = "BRAID"
    bl_description = "Braid Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_braid(self, context)

    def execute(self, context):
        return {'FINISHED'}


# PROFILE PIE MENU
class SHP_OT_ProfilePieMenu(bpy.types.Operator):
    bl_idname = "wm.profile_pie_menu"
    bl_label = "PROFILE"
    bl_description = "Profile Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_profile(self, context)

    def execute(self, context):
        return {'FINISHED'}


# ORNAMENTS PIE MENU
class SHP_OT_OrnamentsPieMenu(bpy.types.Operator):
    bl_idname = "wm.ornaments_pie_menu"
    bl_label = "ORNAMENTS"
    bl_description = "Ornaments Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_ornaments(self, context)

    def execute(self, context):
        return {'FINISHED'}


# DYNAMICS PIE MENU
class SHP_OT_DynamicsPieMenu(bpy.types.Operator):
    bl_idname = "wm.dynamics_pie_menu"
    bl_label = "DYNAMICS"
    bl_description = "Hair Dynamics Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_dynamics(self, context)

    def execute(self, context):
        return {'FINISHED'}


# WIND EFFECTS PIE MENU
class SHP_OT_WindEffectsPieMenu(bpy.types.Operator):
    bl_idname = "wm.wind_effects_pie_menu"
    bl_label = "WIND EFFECTS"
    bl_description = "Wind Effects Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_wind_effects(self, context)

    def execute(self, context):
        return {'FINISHED'}


# MATERIALS / UV PIE MENU
class SHP_OT_MaterialsPieMenu(bpy.types.Operator):
    bl_idname = "wm.materials_pie_menu"
    bl_label = "MATERIALS / UV"
    bl_description = "Materials/UV Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_materials(self, context)

    def execute(self, context):
        return {'FINISHED'}


# SHADES PIE MENU
class SHP_OT_ShadesPieMenu(bpy.types.Operator):
    bl_idname = "wm.shades_pie_menu"
    bl_label = "SHADE SETTINGS"
    bl_description = "Shade Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        # layout = self.layout
        # layout.label(text="SHADE SETTINGS")

        draw_shades(self, context)

    def execute(self, context):
        return {'FINISHED'}


# SETTINGS PIE MENU
class SHP_OT_SettingsPieMenu(bpy.types.Operator):
    bl_idname = "wm.settings_pie_menu"
    bl_label = "SETTINGS"
    bl_description = "Hair Settings"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        draw_settings(self, context)

    def execute(self, context):
        return {'FINISHED'}


# MESH CONVERSION PIE MENU
class SHP_OT_MeshConvertPieMenu(bpy.types.Operator):
    bl_idname = "wm.mesh_convert_pie_menu"
    bl_label = "MESH & ARMATURE"
    bl_description = "Convert Hair Curve to Mesh / Generate Armature"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        hair_curve = context.object
        node_group_name = "Stylized Hair PRO"

        layout = self.layout
        if hair_curve and hair_curve.type in {'CURVE', 'CURVES'} and node_group_name in hair_curve.modifiers:
            draw_mesh_conversion(self, context, layout)

    def execute(self, context):
        return {'FINISHED'}


################################
#   PANELS
################################

# MAIN
class SHP_PT_MainPanel(bpy.types.Panel):
    bl_label = f"Stylized Hair PRO v{bl_info['version'][0]}.{bl_info['version'][1]}{bl_info['version'][2]}"
    bl_idname = "SHP_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = ""

    def draw(self, context):
        draw_main(self, context)


# SHAPE
class SHP_PT_ShapePanel(bpy.types.Panel):
    bl_label = "SHAPE"
    bl_idname = "SHP_PT_ShapePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_shape(self, context)


# TWIST
class SHP_PT_TwistPanel(bpy.types.Panel):
    bl_label = "TWIST"
    bl_idname = "SHP_PT_TwistPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_twist(self, context)


# BUMPS
class SHP_PT_BumpsPanel(bpy.types.Panel):
    bl_label = "BUMPS"
    bl_idname = "SHP_PT_BumpsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_bumps(self, context)


# CURLS        
class SHP_PT_CurlsPanel(bpy.types.Panel):
    bl_label = "CURLS"
    bl_idname = "SHP_PT_CurlsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_curls(self, context)


# BRAID
class SHP_PT_BraidPanel(bpy.types.Panel):
    bl_label = "BRAID"
    bl_idname = "SHP_PT_BraidPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_braid(self, context)


# PROFILE
class SHP_PT_ProfilePanel(bpy.types.Panel):
    bl_label = "PROFILE"
    bl_idname = "SHP_PT_ProfilePanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_profile(self, context)


# ORNAMENTS
class SHP_PT_OrnamentsPanel(bpy.types.Panel):
    bl_label = "ORNAMENTS"
    bl_idname = "SHP_PT_OrnamentsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_ornaments(self, context)


# DYNAMICS
class SHP_PT_HairDynamicsPanel(bpy.types.Panel):
    bl_label = "DYNAMICS"
    bl_idname = "SHP_PT_HairDynamicsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_dynamics(self, context)


# WIND EFFECTS
class SHP_PT_WindEffectsPanel(bpy.types.Panel):
    bl_label = "WIND EFFECTS"
    bl_idname = "SHP_PT_WindEffectsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_HairDynamicsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_wind_effects(self, context)


# MATERIALS / UV
class SHP_PT_MaterialsPanel(bpy.types.Panel):
    bl_label = "MATERIALS / UV"
    bl_idname = "SHP_PT_MaterialsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_materials(self, context)


# SHADES
class SHP_PT_ShadeSettingsPanel(bpy.types.Panel):
    bl_label = "SHADE SETTINGS"
    bl_idname = "SHP_PT_ShadeSettingsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MaterialsPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_shades(self, context)


# SETTINGS
class SHP_PT_SettingsPanel(bpy.types.Panel):
    bl_label = "SETTINGS"
    bl_idname = "SHP_PT_SettingsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_settings(self, context)


# UTILITIES
class SHP_PT_UtilitiesPanel(bpy.types.Panel):
    bl_label = "UTILITIES"
    bl_idname = "SHP_PT_UtilitiesPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_utilities(self, context)


# MESH CONVERSION
# class SHP_PT_MeshConversionPanel(bpy.types.Panel):
#     bl_label = "MESH CONVERSION"
#     bl_idname = "SHP_PT_MeshConversionPanel"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'Stylized Hair PRO'
#     bl_parent_id = "SHP_PT_UtilitiesPanel"
#     bl_options = {'DEFAULT_CLOSED'}

#     def draw(self, context):
#         draw_mesh_conversion(self, context)


# GLOBAL VALUES
class SHP_PT_GlobalSettingsPanel(bpy.types.Panel):
    bl_label = "GLOBAL VALUES"
    bl_idname = "SHP_PT_GlobalSettingsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Stylized Hair PRO'
    bl_parent_id = "SHP_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_global_values(self, context)


# bpy.data.node_groups["Stylized Hair PRO"].nodes["SHP_nt_global_material_1"].inputs[1]
# row.prop(shp_modf, "[\"%s\"]" % bpy.utils.escape_identifier("Input_"), text='')

################################
#   REGISTER
################################

ICONS_LIST = (
    ("shp_icon_add_new_curve", "shp_icon_add_new_curve.png"),
    ("shp_icon_curve_braid", "shp_icon_curve_braid.png"),
    ("shp_icon_curve_bumps", "shp_icon_curve_bumps.png"),
    ("shp_icon_curve_curls", "shp_icon_curve_curls.png"),
    ("shp_icon_curve_duplicate", "shp_icon_curve_duplicate.png"),
    ("shp_icon_curve_dynamics", "shp_icon_curve_dynamics.png"),
    ("shp_icon_curve_wind", "shp_icon_curve_wind.png"),
    ("shp_icon_curve_ornament", "shp_icon_curve_ornament.png"),
    ("shp_icon_curve_profile", "shp_icon_curve_profile.png"),
    ("shp_icon_curve_refresh", "shp_icon_curve_refresh.png"),
    ("shp_icon_curve_settings", "shp_icon_curve_settings.png"),
    ("shp_icon_curve_mesh_convert", "shp_icon_curve_mesh_convert.png"),
    ("shp_icon_curve_shape", "shp_icon_curve_shape.png"),
    ("shp_icon_curve_twist", "shp_icon_curve_twist.png"),
    ("shp_icon_curve_uv", "shp_icon_curve_uv.png"),
    ("shp_icon_curve_shades", "shp_icon_curve_shades.png"),
    ("shp_icon_edit_comb", "shp_icon_edit_comb.png"),
    ("shp_icon_edit_grab", "shp_icon_edit_grab.png"),
    ("shp_icon_edit_length", "shp_icon_edit_length.png"),
    ("shp_icon_edit_slide", "shp_icon_edit_slide.png"),
    ("shp_icon_edit_smooth", "shp_icon_edit_smooth.png"),
    ("shp_icon_setup_add", "shp_icon_setup_add.png"),
    ("shp_icon_setup_remove", "shp_icon_setup_remove.png"),
    ("shp_icon_profile_box", "shp_icon_profile_box.png"),
    ("shp_icon_profile_crescent", "shp_icon_profile_crescent.png"),
    ("shp_icon_profile_islands", "shp_icon_profile_islands.png"),
    ("shp_icon_profile_linear", "shp_icon_profile_linear.png"),
    ("shp_icon_profile_robo", "shp_icon_profile_robo.png"),
    ("shp_icon_profile_triangle", "shp_icon_profile_triangle.png")
)


CLASSES_LIST = (
    SHP_Props,
    SHP_OT_AppendStylizedHairPro,
    SHP_OT_RemoveStylizedHairPro,
    SHP_OT_AddStrand,
    SHP_OT_DuplicateStrand,
    SHP_OT_ProfileBox,
    SHP_OT_ProfileTriangle,
    SHP_OT_ProfileRobo,
    SHP_OT_ProfileIslands,
    SHP_OT_ProfileLine,
    SHP_OT_ProfileCrescent,
    SHP_OT_ToggleDynamics,
    SHP_OT_MeshConvert,
    SHP_OT_MeshConvertBbone,
    SHP_OT_UpdateVersion,
    SHP_OT_ReUseCurves,
    SHP_OT_CombStrand,
    SHP_OT_SmoothStrand,
    SHP_OT_SlideStrand,
    SHP_OT_GrabStrand,
    SHP_OT_LengthStrand,
    SHP_MT_PieMenu,
    SHP_OT_CallPieMenu,
    SHP_OT_ShapePieMenu,
    SHP_OT_TwistPieMenu,
    SHP_OT_BumpsPieMenu,
    SHP_OT_CurlsPieMenu,
    SHP_OT_BraidPieMenu,
    SHP_OT_ProfilePieMenu,
    SHP_OT_OrnamentsPieMenu,
    SHP_OT_DynamicsPieMenu,
    SHP_OT_WindEffectsPieMenu,
    SHP_OT_MaterialsPieMenu,
    SHP_OT_ShadesPieMenu,
    SHP_OT_SettingsPieMenu,
    SHP_OT_MeshConvertPieMenu,
    SHP_OT_ResetAll,
    SHP_PT_MainPanel,
    SHP_PT_ShapePanel,
    SHP_PT_TwistPanel,
    SHP_PT_BumpsPanel,
    SHP_PT_CurlsPanel,
    SHP_PT_BraidPanel,
    SHP_PT_ProfilePanel,
    SHP_PT_OrnamentsPanel,
    SHP_PT_HairDynamicsPanel,
    SHP_PT_WindEffectsPanel,
    SHP_PT_MaterialsPanel,
    SHP_PT_ShadeSettingsPanel,
    SHP_PT_SettingsPanel,
    SHP_PT_UtilitiesPanel,
    # SHP_PT_MeshConversionPanel,
    SHP_PT_GlobalSettingsPanel
)


def register():
    for cls in CLASSES_LIST:
        bpy.utils.register_class(cls)
    bpy.types.Scene.shp_addon = bpy.props.PointerProperty(type=SHP_Props)
    bpy.app.handlers.depsgraph_update_post.append(shp_selection_handler)

    # FOR ICONS
    pcoll = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # load a preview thumbnail of a file and store in the previews collection
    for icon_name, icon_file in ICONS_LIST:
        pcoll.load(icon_name, os.path.join(icons_dir, icon_file), 'IMAGE')

    preview_collections["main"] = pcoll


def unregister():
    for cls in CLASSES_LIST:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.shp_addon

    if shp_selection_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(shp_selection_handler)

    # FOR ICONS
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


if __name__ == "__main__":
    register()
