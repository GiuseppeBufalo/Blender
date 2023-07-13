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
import os
from . variables import *


def get_previous_node(node):
    for in_socket in node.inputs:
        if in_socket.is_linked:
            for link in in_socket.links:
                if link.is_valid:
                    return link.from_node


def create_atmosphere_node(mat_nodes):
    if ATMOSPHERE_MATERIAL_NODE_NAME in bpy.data.node_groups:
        group = bpy.data.node_groups[ATMOSPHERE_MATERIAL_NODE_NAME]  # fetch already existing group
        # create and add the new node to the tree
        atmosphere_node = mat_nodes.new(type='ShaderNodeGroup')
        atmosphere_node.name = ATMOSPHERE_MATERIAL_NODE_NAME
        atmosphere_node.node_tree = group  # assign the existing group
        return atmosphere_node


# pass True to add fog and False to remove it
def toggle_fog(is_on):
    # get all materials
    for material in bpy.data.materials:
        material.use_nodes = True  # enable 'Use nodes' if not enabled already
        node_tree = material.node_tree
        material_output = node_tree.get_output_node('ALL')  # get the output node

        if material_output is None:
            # print('Case 1: No output - in any case do nothing')
            continue  # jump to next material

        previous_node = get_previous_node(material_output)  # last node to connect to output node
        if psa_node_setup_modified(material, previous_node):  # set flag if user has modified node setup
            material['psa_user_modified'] = 1

        if is_on:
            add_fog(material, previous_node)
        else:
            remove_fog(material, previous_node)
    gsettings = bpy.context.scene.world.psa_general_settings
    gsettings.material_with_fog_count = len(list(filter(lambda material: 'psa_user_modified' in material, bpy.data.materials)))


def move_node_in_between(node_before, the_node, node_after):
    node_padding = 40
    if node_before is None:
        the_node.location.xy = (node_after.location.x - node_after.width - node_padding, node_after.location.y)
    else:
        the_node_xpos = node_before.location.x + node_padding + node_before.width
        node_after_xpos = the_node_xpos + node_padding + node_after.width
        the_node.location.xy = (the_node_xpos, node_before.location.y)
        node_after.location.xy = (node_after_xpos, node_before.location.y)


def add_fog(material, previous_node):
    node_tree = material.node_tree
    nodes = node_tree.nodes
    material_output = node_tree.get_output_node('ALL')

    if 'psa_user_modified' in material and material['psa_user_modified'] == 1:
        return  # user has modified it (deleted, unlinked, etc.). Don't touch it!

    if ATMOSPHERE_MATERIAL_NODE_NAME in nodes:  # and node setup has not been modified
        return  # everything is awesome - jump to next material
    else:
        # first run for the material (by default not modified by user)
        material['psa_user_modified'] = 0

    starlight_node = create_atmosphere_node(nodes)

    if previous_node is None:
        # print('Case 3: [+] Only output - add and link Atmosphere')
        node_tree.links.new(starlight_node.outputs[0], material_output.inputs[0])
        move_node_in_between(None, starlight_node, material_output)
    else:
        # print('Case 4: [+] Has output & node before - link Atmosphere in between')
        node_tree.links.new(previous_node.outputs[0], starlight_node.inputs[0])
        node_tree.links.new(starlight_node.outputs[0], material_output.inputs[0])
        move_node_in_between(previous_node, starlight_node, material_output)


def remove_fog(material, previous_node):
    node_tree = material.node_tree
    nodes = node_tree.nodes
    material_output = node_tree.get_output_node('ALL')

    if 'psa_user_modified' in material:  # cleanup custom properties
        del(material['psa_user_modified'])

    material_node = nodes.get(ATMOSPHERE_MATERIAL_NODE_NAME) or nodes.get('StarlightAtmosphereMaterial') # StarlightAtmosphereMaterial is a deprecated name of the node
    if not material_node:  # only in case material contains this node
        return  # if there is no Atmosphere node - jump to next material

    if previous_node is None:
        # here should be StarlightAtmosphere, but it's not (it has been disconnected from the output)
        nodes.remove(material_node)  # find node and remove it
        return

    previous_previous_node = get_previous_node(previous_node)

    if previous_previous_node is None:
        # print('Case 5: [-] Atmosphere exists & nothing before - remove Atmosphere')
        nodes.remove(material_node)
    else:
        # print('Case 6: [-] Atmosphere exists & something before - Link nodes and remove Atmosphere')
        node_tree.links.new(previous_previous_node.outputs[0], material_output.inputs[0])
        nodes.remove(material_node)


def psa_node_setup_modified(material, previous_node):
    nodes = material.node_tree.nodes
    if 'psa_user_modified' in material:
        if material['psa_user_modified'] == 1:  # already marked
            return True
        if material['psa_user_modified'] == 0 and ATMOSPHERE_MATERIAL_NODE_NAME not in nodes:  # StarlightAtmosphere deleted
            return True
        if previous_node != nodes.get(ATMOSPHERE_MATERIAL_NODE_NAME):  # Node before output is not StarlightAtmosphere
            return True
    return False