# ///////////////////////////////////////////////////////////////
#
# Blender Dome Light
# by: WANDERSON M. PIMENTA
# version: 3.0.0
#
# ///////////////////////////////////////////////////////////////

import bpy
import os
import json

# Import Shared Data
from .shared import (
    preview_collections,
)

def load_icons(preview_collections, icons_info):
    """
    Load icons and register them in the preview collection.
    
    Args:
    - preview_collections: Dictionary containing the preview collections.
    - icons_info: List of tuples containing information about the icons to be loaded.
      Each tuple should contain the icon name, the path to the icon file, and the type of icon.
    """
    for icon_name, icon_path, icon_type in icons_info:
        if 'icons' not in preview_collections:
            preview_collections['icons'] = bpy.utils.previews.new()

        pcoll = preview_collections['icons']
        pcoll.load(icon_name, icon_path, icon_type)

# Generate HDR/EXR Previews HDR 1
def generate_previews(self, context):
    """Callback function for EnumProperty"""
    enum_items = []

    # Check if context is valid
    if context is None:
        return enum_items  # Return an empty list if the context is not valid

    # Get active world and its preview directory
    active_world = context.scene.world
    directory = os.path.abspath(bpy.path.abspath(active_world.my_previews_dir))  # Convert to absolute path

    # Create or retrieve the preview collection
    if 'hdr_thumbnails' not in preview_collections:
        pcoll = bpy.utils.previews.new()
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections["hdr_thumbnails"] = pcoll
    else:
        pcoll = preview_collections["hdr_thumbnails"]

    # If directory hasn't changed, return cached previews
    if directory == pcoll.my_previews_dir:
        return pcoll.my_previews

    # Scan the directory for HDR and EXR files
    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".hdr") or fn.lower().endswith(".exr"):
                image_paths.append(fn)

        # Generate preview thumbnails for each image
        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            enum_items.append((name, name, "", thumb.icon_id, i))

    # Update the preview collection with new previews and directory
    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory

    # Update the actual HDR
    try:
        active_world.actual_hdr = ""
    except:
        pass

    # Set the first item as default
    if not active_world.my_previews and enum_items:
        try:
            active_world.my_previews = enum_items[0][0]  # Attempt to set the first item as default
        except:
            # If setting the default item fails, register the reload_previews_operator to run after 1 second
            bpy.app.timers.register(reload_previews_operator, first_interval=1)

    return pcoll.my_previews

def update_light(self, context):
    # Get scene
    active_world = context.scene.world
    selected_image = active_world.my_previews  # Get the name of the selected image
    selected_image_path = bpy.path.abspath(os.path.join(active_world.my_previews_dir, selected_image))  # Construct the full path of the image
    
    if selected_image and os.path.isfile(selected_image_path):
        nodes = active_world.node_tree.nodes
        images = bpy.data.images

        # Check if node exists
        if 'DOMELIGHT_environment' in nodes:
            env = nodes['DOMELIGHT_environment']
            
            # Remove selected image if it exists and its name is different from actual_hdr and actual_hdr_2
            if (selected_image in images and 
                selected_image != active_world.actual_hdr and 
                selected_image != active_world.actual_hdr_2):
                bpy.data.images.remove(images[selected_image])

            # Load the image
            bpy.data.images.load(selected_image_path)

            if selected_image in bpy.data.images:
                try:
                    env.image = images[selected_image]
                    active_world.actual_hdr = selected_image
                except:
                    pass

# Generate HDR/EXR Previews HDR 2
def generate_previews_2(self, context):
    """Callback function for EnumProperty for 'DOMELIGHT_environment_2'"""
    enum_items = []

    # Check if context is valid
    if context is None:
        return enum_items  # Return an empty list if the context is not valid

    # Get active world and its preview directory
    active_world = context.scene.world
    directory = bpy.path.abspath(active_world.my_previews_dir_2)  # Convert to absolute path

    # Create or retrieve the preview collection
    if 'hdr_thumbnails_2' not in preview_collections:
        pcoll = bpy.utils.previews.new()
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections["hdr_thumbnails_2"] = pcoll
    else:
        pcoll = preview_collections["hdr_thumbnails_2"]

    # If directory hasn't changed, return cached previews
    if directory == pcoll.my_previews_dir:
        return pcoll.my_previews

    # Scan the directory for HDR and EXR files
    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".hdr") or fn.lower().endswith(".exr"):
                image_paths.append(fn)

        # Generate preview thumbnails for each image
        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            enum_items.append((name, name, "", thumb.icon_id, i))

    # Update the preview collection with new previews and directory
    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory

    # Update the actual HDR
    try:
        active_world.actual_hdr_2 = ""
    except:
        pass

    return pcoll.my_previews

def update_light_2(self, context):
    # Get scene
    active_world = context.scene.world
    selected_image = active_world.my_previews_2  # Get the name of the selected image
    selected_image_path = bpy.path.abspath(os.path.join(active_world.my_previews_dir_2, selected_image))  # Construct the full path of the image

    if selected_image and os.path.isfile(selected_image_path):
        nodes = active_world.node_tree.nodes
        images = bpy.data.images

        # Check if node exists
        if 'DOMELIGHT_environment_2' in nodes:
            env = nodes['DOMELIGHT_environment_2']

            # Remove selected image if it exists and its name is different from actual_hdr and actual_hdr_2
            if (selected_image in images and 
                selected_image != active_world.actual_hdr and 
                selected_image != active_world.actual_hdr_2):
                bpy.data.images.remove(images[selected_image])

            # Load the image
            bpy.data.images.load(selected_image_path)

            if selected_image in bpy.data.images:
                try:
                    env.image = images[selected_image]
                    active_world.actual_hdr_2 = selected_image
                except:
                    pass


# Create world nodes
def create_world_nodes():
    # Get the current scene
    scn = bpy.context.scene
    
    # Get the active world in the scene
    world = scn.world  

    # Check if an active world is found
    if world is not None:
        # Enable Use nodes for the active world
        world.use_nodes = True  

        # Get the value of enable_second_light from the scene
        enable_second_light = world.enable_second_light

        # Check if the temporary image is loaded
        temp_light_image = bpy.data.images.get("temp_light.png")
        if temp_light_image is None:
            # Load temporary image
            temp_light_path = os.path.join(os.path.dirname(__file__), "..", "assets", "temp_light.png")
            temp_light_image = bpy.data.images.load(temp_light_path)

        # Call create_nodes function assuming it's defined elsewhere
        create_nodes(world, enable_second_light, temp_light_image)
    else:
        # Print a message if no active world is found
        print("No active world found in the scene.")


# Create nodes inside
def create_nodes(nodes_tree, enable_second_light, temp_light_image):
    # Delete all the nodes
    nodes_tree.node_tree.nodes.clear()

    # Adding new nodes
    tex_coord = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexCoord")   
    mapping = nodes_tree.node_tree.nodes.new(type="ShaderNodeMapping") 
    mapping_2 = nodes_tree.node_tree.nodes.new(type="ShaderNodeMapping")
    env = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env.show_texture = True
    env_2 = nodes_tree.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env_2.show_texture = True
    mix_rgb = nodes_tree.node_tree.nodes.new(type="ShaderNodeMixRGB")
    background = nodes_tree.node_tree.nodes.new(type="ShaderNodeBackground")
    gamma = nodes_tree.node_tree.nodes.new(type="ShaderNodeGamma")
    saturation = nodes_tree.node_tree.nodes.new(type="ShaderNodeHueSaturation")
    color = nodes_tree.node_tree.nodes.new(type="ShaderNodeMixRGB")
    math_multiply = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    math_divide = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    math_add = nodes_tree.node_tree.nodes.new(type="ShaderNodeMath")
    output = nodes_tree.node_tree.nodes.new(type="ShaderNodeOutputWorld")
       
    # Change the parameters
    tex_coord.name = 'DOMELIGHT_texture_coordinate'
    mapping.name = 'DOMELIGHT_mapping'
    mapping_2.name = 'DOMELIGHT_mapping_2'
    env.name = 'DOMELIGHT_environment'
    env_2.name = 'DOMELIGHT_environment_2'
    background.name = 'DOMELIGHT_background'
    mapping.name = 'DOMELIGHT_mapping'
    mix_rgb.name = 'DOMELIGHT_mix_BG_RGB'
    mix_rgb.inputs[0].default_value = 0.5
    if enable_second_light:
        mix_rgb.mute = False
    else:
        mix_rgb.mute = True
    gamma.name = 'DOMELIGHT_gamma'
    saturation.name = 'DOMELIGHT_saturation'
    color.name = 'DOMELIGHT_color'
    math_multiply.name = 'DOMELIGHT_math_multiply'
    math_multiply.operation = 'MULTIPLY'
    math_multiply.inputs[1].default_value = 0.0
    math_divide.name = 'DOMELIGHT_math_divide'
    math_divide.operation = 'DIVIDE'
    math_divide.inputs[1].default_value = 100.0
    math_add.name = 'DOMELIGHT_math_add'   
    math_add.operation = 'ADD'   
    math_add.inputs[1].default_value = 1.0
    color.blend_type = 'MULTIPLY'
    color.inputs[0].default_value = 0.0
    color.inputs[2].default_value = (0.185, 0.266, 0.448, 1)
    output.name = 'DOMELIGHT_world_output'
    
    # Link nodes
    nodes_tree.node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs[0])
    nodes_tree.node_tree.links.new(tex_coord.outputs['Generated'], mapping_2.inputs[0])
    nodes_tree.node_tree.links.new(mapping.outputs[0], env.inputs[0])
    nodes_tree.node_tree.links.new(mapping_2.outputs[0], env_2.inputs[0])
    nodes_tree.node_tree.links.new(env.outputs[0], mix_rgb.inputs[1])
    nodes_tree.node_tree.links.new(env_2.outputs[0], mix_rgb.inputs[2])
    nodes_tree.node_tree.links.new(mix_rgb.outputs['Color'], gamma.inputs[0])
    nodes_tree.node_tree.links.new(mix_rgb.outputs['Color'], math_multiply.inputs[0])
    nodes_tree.node_tree.links.new(gamma.outputs[0], saturation.inputs[4])
    nodes_tree.node_tree.links.new(saturation.outputs[0], color.inputs[1])
    nodes_tree.node_tree.links.new(math_multiply.outputs[0], math_divide.inputs[0])
    nodes_tree.node_tree.links.new(math_divide.outputs[0], math_add.inputs[0])
    nodes_tree.node_tree.links.new(math_add.outputs[0], background.inputs[1])
    nodes_tree.node_tree.links.new(color.outputs[0], background.inputs[0])
    nodes_tree.node_tree.links.new(background.outputs[0], output.inputs[0])    
    
    # Nodes location    
    tex_coord.location = (-90, 200)
    mapping.location = (90, 450)
    mapping_2.location = (90, 0) 
    env.location = (300, 450)
    env_2.location = (300, 0)
    mix_rgb.location = (650, 200)
    gamma.location = (960, 350)
    saturation.location = (1120, 350)
    color.location = (1290, 350)
    math_multiply.location = (960, 100)
    math_divide.location = (1120, 100)
    math_add.location = (1290, 100)
    background.location = (1500, 252)
    output.location = (1660, 252)

    # Set the loaded image as default for env and env_2 nodes
    env.image = temp_light_image
    env_2.image = temp_light_image


# Check environment nodes
def check_environment_nodes():
    # List of nodes to check
    nodes_list = ['DOMELIGHT_texture_coordinate', 'DOMELIGHT_mapping', 'DOMELIGHT_environment', 'DOMELIGHT_environment_2',
                  'DOMELIGHT_gamma', 'DOMELIGHT_saturation', 'DOMELIGHT_math_multiply', 'DOMELIGHT_math_divide',
                  'DOMELIGHT_world_output', 'DOMELIGHT_math_add', 'DOMELIGHT_color', 'DOMELIGHT_mix_BG_RGB',
                  'DOMELIGHT_background']

    # Get the active world
    world = bpy.context.scene.world

    # Check if an active world is found
    if world:
        # Initialize a list to store the names of found nodes
        found_nodes = []

        # Check each node in the nodes list
        for node_name in nodes_list:
            # Check if the node is present in the world
            if any(node.name == node_name for node in world.node_tree.nodes):
                found_nodes.append(node_name)

        # If the list of found nodes is equal to the list of nodes to check, all nodes were found
        if set(found_nodes) == set(nodes_list):
            return 'OK'
        # If there are found nodes but not all, return 'Fix'
        elif found_nodes:
            return 'Fix'
        else:
            return 'Create'
    # If no active world is found, return 'Create'
    else:
        return 'Create'

    
# Update MIX HDR When Change Status        
def update_second_light(self, context):
    # Get the active world
    world = bpy.context.scene.world
    nodes = world.node_tree.nodes
    mix_node = nodes["DOMELIGHT_mix_BG_RGB"]
    enable_second_light = world.enable_second_light
    
    if enable_second_light:
        mix_node.mute = False
    else:
        mix_node.mute = True

# Load favorites
def load_favorites(favorites_file):
    """Load favorites from JSON file"""
    if os.path.exists(favorites_file):
        with open(favorites_file, 'r') as f:
            return json.load(f)
    else:
        return []
    
# Save favorites
def save_favorites(favorites, favorites_file):
    """Save favorites to JSON file"""
    with open(favorites_file, 'w') as f:
        json.dump(favorites, f, indent=4)

# Reload the previews using the operator DOMELIGHT_OT_reload_previews
def reload_previews_operator():
    bpy.ops.domelight.reload_previews()  
    return None