#pylint: disable=import-error, relative-beyond-top-level
import bpy
import os
from . smr_common import ShowMessageBox
from pathlib import Path

def add_smr_name():
    mat, nodes, links = get_mat_data()

    if not 'SMR' in mat.name:
        mat.name = mat.name + '_SMR'
        bpy.context.scene.SMR.SMR_active_mat = mat.name

def move_all_nodes(loc_x):
    mat, nodes, links = get_mat_data()

    nodes_to_move = []
    
    for node in nodes:
        if node.location[0] < loc_x:
            nodes_to_move.append(node) 
    
    for node in nodes_to_move:
        node.location[0] = node.location[0] - 1000 


def get_mat_data():
    """
    collects all the required variables and returns them
    """  
    mat = bpy.data.materials.get(bpy.context.scene.SMR.SMR_active_mat)
    nodes= mat.node_tree.nodes
    links = mat.node_tree.links
    return mat, nodes, links   

def check_node(node_name, type):
    """
    checks if a certain node exists, creates a new one if it doesn't exist
    """   
    
    mat, nodes, links = get_mat_data()
    SMR_settings = bpy.context.scene.SMR
    if not mat.use_nodes:
        return
    
    node = nodes.get(node_name, None)
    if node is not None:
        return
    
    
    #procedure for smudgr node group
    if type != 'group':
        node = mat.node_tree.nodes.new(type)
        node.name = node_name
        if type == 'ShaderNodeTexImage' and node_name[:16]!= 'SMR_TexturePaint' and node_name != 'SMR_Bake_Texture' and node_name != 'SMR_Bake2_Texture':
            
            from . smr_pcoll import update_image

            node.projection = 'BOX'
            node.projection_blend = 1

            if 'Dust' in node_name:
                update_image(SMR_settings.prev_dust, 'Dust')
            if 'Smudge' in node_name:
                update_image(SMR_settings.prev_smudge, 'Smudge')                
            if 'Scratch' in node_name:
                update_image(SMR_settings.prev_scratch, 'Scratch')
            if 'Droplets' in node_name:
                update_image(SMR_settings.prev_droplets, 'Droplets')
                node.projection = 'FLAT'                  
        node.hide = True
        if type == 'ShaderNodeTexNoise':
            node.noise_dimensions = '4D'
                
    else:
        try:
            nodes["Group"].name = "Group.1234"
        except:
            pass
        
        found_group = False
        for node_group in  bpy.data.node_groups:
            if node_group.name == node_name:
                found_group = True
        
        #append the node from the .blend file if it doesnt exist in this file
        if found_group == False:
            #append node group
            blendfile = str(os.path.dirname(__file__)) + str(Path('/SMR.blend'))
            section   = str(Path("/NodeTree/"))
            filename    = node_name
            if filename[:6] == 'SMR_AT':
                filename = 'SMR_AT'
            if filename[:13] == "SMR_Influence": 
                filename = "SMR_Influence"
            if filename[:12] == "SMR_Gradient": 
                filename = "SMR_Gradient"
            if filename[:12] == "SMR_Geometry": 
                filename = "SMR_Geometry"                         


            filepath  = blendfile + section + filename
            directory = blendfile + section

            if not SMR_settings.diagnostics:
                try:
                    bpy.ops.wm.append(
                        filepath=filepath, 
                        filename=filename,
                        directory=directory) 
                except:
                    ShowMessageBox("Either the file path is incorrect or your are in edit mode. Please check the install instructions again or contact me on BenderMarket if you need help", "What the smudge!", 'ERROR')
                    return False
                
            else:
                bpy.ops.wm.append(
                    filepath=filepath, 
                    filename=filename,
                    directory=directory)                                 

        #find the node and place it  
        node_tree = bpy.data.materials.get(mat.name).node_tree
        group = node_tree.nodes.new("ShaderNodeGroup")
        
        try:
            group.node_tree = bpy.data.node_groups[filename]
        except:
            group.node_tree = bpy.data.node_groups[node_name]    
        group.name = node_name 
        if group.name != 'SMR':
            group.hide = True 
        return True    

def followLinks(node_in, socket):
    """
    finds out what node is connected to a certain socket
    """    
    input_no=0
    input_source= ''
    input_socket = None
    for n_inputs in node_in.inputs:
        for node_links in n_inputs.links:
            if input_no is socket:
                input_source= node_links.from_node.name
                input_socket = node_links.from_socket.name
                

        input_no += 1

    return input_source, input_socket


def change_smudge_coord(self, context):
    SMR_settings= bpy.context.scene.SMR
    change_coord_general(SMR_settings.smudge_coord, 'Smudge')

def change_scratch_coord(self, context):
    SMR_settings= bpy.context.scene.SMR
    change_coord_general(SMR_settings.scratch_coord, 'Scratch')

def change_dust_coord(self, context):
    SMR_settings= bpy.context.scene.SMR
    change_coord_general(SMR_settings.dust_coord, 'Dust')

def change_coord_general(mapping, categ):
    mat, nodes, links = get_mat_data()
    
    AT_node = nodes['SMR_AT_{}'.format(categ)]
    texture_node = nodes['SMR_{}_Texture'.format(categ)]

    if mapping == 'Box':
        AT_node.inputs[0].default_value = 1
        texture_node.projection_blend = 1
        texture_node.projection = 'BOX'        
    if mapping == 'UV':
        AT_node.inputs[0].default_value = 0
        texture_node.projection_blend = 0
        texture_node.projection = 'FLAT'


def add_smr_uv():    
    obj=bpy.context.active_object
    if not obj:
        print('no active object')
        return
    try:
        obj.data.uv_layers["SMR_UV"]
    except:
        old_name = obj.data.uv_layers.active.name
        obj.data.uv_layers.new(name="temp_name")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(island_margin=0)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.uv_layers[old_name].name = 'SMR_UV'
        obj.data.uv_layers["temp_name"].name = old_name
        obj.data.uv_layers[old_name].active_render = True