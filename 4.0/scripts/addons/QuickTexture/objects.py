import bpy
import bmesh
import random
import mathutils
import numpy
from mathutils import *
from math import *
import numpy
import os

import mathutils
import bpy_extras
from bpy_extras.view3d_utils import region_2d_to_location_3d
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras import view3d_utils

from . import maths
from . import utils

def create_empty(empty_name, empty_type, rotate, context, only_once):

    bpy.ops.object.select_all(action='DESELECT')
    found = empty_name in bpy.data.objects
    if found == 0 or only_once == 0:
        obj = bpy.ops.object.empty_add(
            type=empty_type, location=(0, 0, 0), rotation=rotate)
        obj = context.object
        context.view_layer.objects.active = obj
        obj.name = empty_name
        bpy.ops.object.select_all(action='DESELECT')
        context.object.hide_viewport = True
        context.object.hide_render = True
        context.object.hide_select = True
        return obj
    else:
        obj = bpy.data.objects[empty_name]
        return obj

def empty(empty_name, empty_type, location, rotate, context, only_once):

    bpy.ops.object.select_all(action='DESELECT')
    found = empty_name in bpy.data.objects
    if found == 0 or only_once == 0:
        obj = bpy.ops.object.empty_add(
            type=empty_type, location=location, rotation=rotate)
        obj = context.object
        context.view_layer.objects.active = obj
        obj.name = empty_name
        context.object.hide_viewport = True
        context.object.hide_render = True
        context.object.hide_select = True
        bpy.ops.object.select_all(action='DESELECT')
        return obj
    else:
        obj = bpy.data.objects[empty_name]
        return obj

def add_empty(empty_name, empty_type, location, rotate, context):

    bpy.ops.object.select_all(action='DESELECT')
    obj = bpy.ops.object.empty_add(type=empty_type, location=location, rotation=rotate)
    obj = context.object
    context.view_layer.objects.active = obj
    obj.name = empty_name
    context.object.hide_viewport = True
    context.object.hide_render = True
    context.object.hide_select = True
    bpy.ops.object.select_all(action='DESELECT')
    return obj

def make_collection(name, context):

    if name in bpy.data.collections:
        return bpy.data.collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        context.scene.collection.children.link(new_collection)
        
        return new_collection

def add_to_collection(name, collection, context):

    if name not in collection.objects:
        ob_cm = bpy.data.objects[name]
        col2 = context.scene.collection.children[collection.name]
        for col in ob_cm.users_collection:
            col.objects.unlink(ob_cm)
        col2.objects.link(ob_cm)

def create_image_plane(self, context, name, img_spec):

    # Create new mesh
    bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
    plane = context.active_object
    if plane.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    px, py = img_spec.size
    size = px/py 

    width = 1 * size
    height = 1 

    plane.dimensions = width, height, 0.0
    plane.data.name = plane.name = name

    plane.rotation_euler.x = pi/2
    
    return plane

# MATERIAL
def create_material(self, context, img_spec, ref, mode, proc_uv, files, dirname, decal, selected):

    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None

    if len(files) > 1:
        for f in files:
            if 'albedo' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]     
            if 'diffuse' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'diff' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'color' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                albedo_spec = bpy.data.images[f.name]   
            if 'col' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecolor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecol' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'roughness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'rough' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'glossiness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'gloss' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'spec' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'specular' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'normal' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'norm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'nor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'nrm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'nmap' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'opacity' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'opac' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'alpha' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'ao' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     
            if 'ambientocclusion' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     

    width, height = img_spec.size
    if width == 0:
        width = 1000
    if height == 0:
        height = 1000
    material = bpy.data.materials.new(name=img_spec.name)
    size = width/height

    material.use_nodes = True
    out_material = clean_node_tree(material.node_tree)
    out_material.name = 'QT_Output' 

    groupname = 'QT_Shader_' + img_spec.name
    grp = bpy.data.node_groups.new(groupname, 'ShaderNodeTree')
    group_node = material.node_tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = bpy.data.node_groups[grp.name]
    group_node.name = groupname
    group_node.select = True

    material.node_tree.nodes.active = group_node
    
    nodes = group_node.node_tree.nodes
    node_tree = group_node.node_tree
    
    out_node = node_tree.nodes.new('NodeGroupOutput')
    group_node.outputs.new('NodeSocketShader', 'Output')
    group_node.location = out_material.location
    group_node.location.x -= 500

    core_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    core_shader.name = 'QT_Shader_1'
    core_shader.label = 'QT_Layer_1_' + img_spec.name 
    core_shader.inputs[17].default_value = (1,1,1,1)
    core_shader.inputs[18].default_value = 0
    
    node_tree.links.new(core_shader.outputs[0], out_node.inputs[0])
    material.node_tree.links.new(out_material.inputs['Surface'], group_node.outputs[0])
    
    # mapping
    diffuse_mapping = node_tree.nodes.new('ShaderNodeMapping')
    rough_mapping = node_tree.nodes.new('ShaderNodeMapping')
    bump_mapping = node_tree.nodes.new('ShaderNodeMapping')
    alpha_mapping = node_tree.nodes.new('ShaderNodeMapping')
    
    diffuse_mapping.name = 'QT_Diffuse_Mapping_1'
    rough_mapping.name = 'QT_Rough_Mapping_1'
    bump_mapping.name = 'QT_Bump_Mapping_1'
    alpha_mapping.name = 'QT_Alpha_Mapping_1'

    if decal:
        coord = node_tree.nodes.new('ShaderNodeUVMap')
        coord.name = 'QT_UV_Layer_1'
        coord.uv_map = 'QT_UV_View_Layer_1'
        coord.label = 'Decal'

        node_tree.links.new(coord.outputs[0], diffuse_mapping.inputs[0])
        node_tree.links.new(coord.outputs[0], rough_mapping.inputs[0])
        node_tree.links.new(coord.outputs[0], bump_mapping.inputs[0])    
        node_tree.links.new(coord.outputs[0], alpha_mapping.inputs[0])

        diffuse_mapping.vector_type = 'TEXTURE'
        rough_mapping.vector_type = 'TEXTURE'
        bump_mapping.vector_type = 'TEXTURE'
        alpha_mapping.vector_type = 'TEXTURE'

        diffuse_mapping.inputs[3].default_value[0] = size
        rough_mapping.inputs[3].default_value[0] = size
        bump_mapping.inputs[3].default_value[0] = size
        alpha_mapping.inputs[3].default_value[0] = size

    else:
        if proc_uv:
            if mode == 'view':            
                coord = node_tree.nodes.new('ShaderNodeUVMap')
                coord.name = 'QT_UV_Layer_1'    
                coord.uv_map = 'QT_UV_View_Layer_1'    
                coord.label = 'View'
                
                node_tree.links.new(coord.outputs[0], diffuse_mapping.inputs[0])
                node_tree.links.new(coord.outputs[0], rough_mapping.inputs[0])
                node_tree.links.new(coord.outputs[0], bump_mapping.inputs[0])    
                node_tree.links.new(coord.outputs[0], alpha_mapping.inputs[0])

            else:
                coord = node_tree.nodes.new('ShaderNodeUVMap')
                coord.name = 'QT_UV_Layer_1'    
                coord.uv_map = 'QT_UV_Box_Layer_1'
                coord.label = 'Box'

                node_tree.links.new(coord.outputs[0], diffuse_mapping.inputs[0])
                node_tree.links.new(coord.outputs[0], rough_mapping.inputs[0])
                node_tree.links.new(coord.outputs[0], bump_mapping.inputs[0])    
                node_tree.links.new(coord.outputs[0], alpha_mapping.inputs[0])

        else:            
            coord = node_tree.nodes.new('ShaderNodeTexCoord')
            coord.name = 'QT_UV_Layer_1'    
            coord.label = 'UV'
            
            node_tree.links.new(coord.outputs[2], diffuse_mapping.inputs[0])
            node_tree.links.new(coord.outputs[2], rough_mapping.inputs[0])
            node_tree.links.new(coord.outputs[2], bump_mapping.inputs[0])
            node_tree.links.new(coord.outputs[2], alpha_mapping.inputs[0])
           
        diffuse_mapping.vector_type = 'TEXTURE'
        rough_mapping.vector_type = 'TEXTURE'
        bump_mapping.vector_type = 'TEXTURE'
        alpha_mapping.vector_type = 'TEXTURE'

        test = context.active_object

        if not selected:

            diff = test.scale[1] - test.scale[0]

            diffuse_mapping.inputs[1].default_value[0] = test.scale[0]/2 + diff
            rough_mapping.inputs[1].default_value[0] = test.scale[0]/2 + diff
            bump_mapping.inputs[1].default_value[0] = test.scale[0]/2 + diff
            alpha_mapping.inputs[1].default_value[0] = test.scale[0]/2 + diff

            diffuse_mapping.inputs[1].default_value[1] = .25
            rough_mapping.inputs[1].default_value[1] = .25
            bump_mapping.inputs[1].default_value[1] = .25
            alpha_mapping.inputs[1].default_value[1] = .25

            diffuse_mapping.inputs[3].default_value[0] = test.scale[0]
            rough_mapping.inputs[3].default_value[0] = test.scale[0]
            bump_mapping.inputs[3].default_value[0] = test.scale[0]
            alpha_mapping.inputs[3].default_value[0] = test.scale[0]

            diffuse_mapping.inputs[3].default_value[1] = test.scale[1]
            rough_mapping.inputs[3].default_value[1] = test.scale[1]
            bump_mapping.inputs[3].default_value[1] = test.scale[1]
            alpha_mapping.inputs[3].default_value[1] = test.scale[1]

    # diffuse
    diffuse_tex = node_tree.nodes.new('ShaderNodeTexImage')
    diffuse_tex.image = img_spec
    diffuse_tex.show_texture = True
    diffuse_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    
    diffuse_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")

    if albedo_spec:
        diffuse_tex.image = albedo_spec
    else:
        diffuse_tex.image = img_spec
    
    diffuse_tex.name = 'QT_Diffuse_Tex_1' 
    diffuse_hue_sat.name = 'QT_Diffuse_Hue_Sat_1'
    diffuse_bright_contrast.name = 'QT_Diffuse_Bright_Contrast_1' 
    
    node_tree.links.new(diffuse_mapping.outputs[0], diffuse_tex.inputs[0])
    node_tree.links.new(diffuse_tex.outputs[0], diffuse_hue_sat.inputs[4])
    node_tree.links.new(diffuse_hue_sat.outputs[0], diffuse_bright_contrast.inputs[0])
    node_tree.links.new(diffuse_bright_contrast.outputs[0], core_shader.inputs[0])

    # roughness
    rough_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if roughness_spec:
        rough_tex.image = roughness_spec
    else:
        rough_tex.image = img_spec
        
    rough_tex.show_texture = True

    rough_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    rough_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    rough_invert = node_tree.nodes.new("ShaderNodeInvert")
    rough_invert.inputs[0].default_value = 0
    rough_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    rough_tex.name = 'QT_Rough_Tex_1' 
    rough_color_ramp.name = 'QT_Rough_Color_Ramp_1' 
    rough_bright_contrast.name = 'QT_Rough_Bright_Contrast_1' 
    rough_invert.name = 'QT_Rough_Invert_1' 
    rough_hue_sat.name = 'QT_Rough_Hue_Sat_1' 

    node_tree.links.new(rough_mapping.outputs[0], rough_tex.inputs[0])
    node_tree.links.new(rough_tex.outputs[0], rough_color_ramp.inputs[0])
    node_tree.links.new(rough_color_ramp.outputs[0], rough_hue_sat.inputs[4])
    node_tree.links.new(rough_hue_sat.outputs[0], rough_invert.inputs[1])
    node_tree.links.new(rough_invert.outputs[0], rough_bright_contrast.inputs[0])
    node_tree.links.new(rough_bright_contrast.outputs[0], core_shader.inputs[7])
    
    rough_clamp = node_tree.nodes.new("ShaderNodeClamp")
    rough_clamp.name = 'QT_Roughness_Clamp_1'
    node_tree.links.new(rough_bright_contrast.outputs[0], rough_clamp.inputs[0])
    node_tree.links.new(rough_clamp.outputs[0], core_shader.inputs[7])
        
    # bump
    bump_tex = node_tree.nodes.new('ShaderNodeTexImage')
    bump_tex.show_texture = True
    
    bump_tex.image = img_spec
    bump_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    bump_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    bump_bump = node_tree.nodes.new("ShaderNodeBump")
    bump_bump.inputs[0].default_value = 0.1
    bump_invert = node_tree.nodes.new("ShaderNodeInvert")
    bump_invert.inputs[0].default_value = 0
    bump_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    bump_tex.name = 'QT_Bump_Tex_1' 
    bump_color_ramp.name = 'QT_Bump_Color_Ramp_1' 
    bump_bright_contrast.name = 'QT_Bump_Bright_Contrast_1'
    bump_bump.name = 'QT_Bump_Bump_1'
    bump_invert.name = 'QT_Bump_Invert_1' 
    bump_hue_sat.name = 'QT_Bump_Hue_Sat_1'

    node_tree.links.new(bump_tex.outputs[0], bump_color_ramp.inputs[0])
    node_tree.links.new(bump_color_ramp.outputs[0], bump_hue_sat.inputs[4])
    node_tree.links.new(bump_hue_sat.outputs[0], bump_invert.inputs[1])
    node_tree.links.new(bump_invert.outputs[0], bump_bright_contrast.inputs[0])
    node_tree.links.new(bump_bright_contrast.outputs[0], bump_bump.inputs[2])

    bump_clamp = node_tree.nodes.new("ShaderNodeClamp")
    bump_clamp.name = 'QT_Bump_Clamp_1'

    node_tree.links.new(bump_bright_contrast.outputs[0], bump_clamp.inputs[0])
    node_tree.links.new(bump_clamp.outputs[0], bump_bump.inputs[2])
            
    node_tree.links.new(bump_mapping.outputs[0], bump_tex.inputs[0])
    node_tree.links.new(bump_bump.outputs[0], core_shader.inputs[20])

    # normal
    if normal_spec:
        normal_tex = node_tree.nodes.new('ShaderNodeTexImage')
        normal_tex.show_texture = True
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = 'Non-Color'
        normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")

        normal_tex.name = 'QT_Normal_Tex_1'
        normal_strength.name = 'QT_Normal_Strength_1'

        node_tree.links.new(diffuse_mapping.outputs[0], normal_tex.inputs[0])
        node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
        node_tree.links.new(normal_strength.outputs[0], bump_bump.inputs[5])
    
    # ao
    if ao_spec:
        ao_tex = node_tree.nodes.new('ShaderNodeTexImage')
        ao_tex.image = ao_spec
        ao_tex.show_texture = True
        ao_tex.name = 'QT_AO_Tex_1'

        ao_multiply = node_tree.nodes.new('ShaderNodeMixRGB')
        ao_multiply.blend_type = 'MULTIPLY'
        ao_multiply.name = 'QT_AO_Multiply_1'
        ao_multiply.inputs[0].default_value = 0.5        

        node_tree.links.new(diffuse_mapping.outputs[0], ao_tex.inputs[0])
        node_tree.links.new(ao_tex.outputs[0], ao_multiply.inputs[2])
        node_tree.links.new(diffuse_tex.outputs[0], ao_multiply.inputs[1])

        node_tree.links.new(ao_multiply.outputs[0], diffuse_hue_sat.inputs[4])
        
    # alpha
    alpha_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if alpha_spec:
        alpha_tex.image = alpha_spec
    else:
        alpha_tex.image = img_spec

    alpha_tex.show_texture = True
    alpha_tex.name = 'QT_Alpha_Tex_1' 

    alpha_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    alpha_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    alpha_invert = node_tree.nodes.new("ShaderNodeInvert")
    alpha_invert.inputs[0].default_value = 0
    alpha_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")        
    alpha_clamp = node_tree.nodes.new("ShaderNodeClamp")

    alpha_clamp.name = 'QT_Alpha_Clamp_1'
    alpha_color_ramp.name = 'QT_Alpha_Color_Ramp_1' 
    alpha_bright_contrast.name = 'QT_Alpha_Bright_Contrast_1' 
    alpha_invert.name = 'QT_Alpha_Invert_1' 
    alpha_hue_sat.name = 'QT_Alpha_Hue_Sat_1' 
    
    node_tree.links.new(alpha_mapping.outputs[0], alpha_tex.inputs[0])
    node_tree.links.new(alpha_color_ramp.outputs[0], alpha_hue_sat.inputs[4])
    node_tree.links.new(alpha_hue_sat.outputs[0], alpha_invert.inputs[1])
    node_tree.links.new(alpha_invert.outputs[0], alpha_bright_contrast.inputs[0])    
    node_tree.links.new(alpha_bright_contrast.outputs[0], alpha_clamp.inputs[0])
    node_tree.links.new(alpha_clamp.outputs[0], core_shader.inputs[19])

    if alpha_spec:
        node_tree.links.new(alpha_tex.outputs[0], alpha_color_ramp.inputs[0])
    else:
        node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])
    
    if ref:
        bump_bump.inputs[0].default_value = 0
        core_shader.inputs[5].default_value = 0

        if mode == 'view':
            diffuse_tex.extension = 'CLIP'
            rough_tex.extension = 'CLIP'
            bump_tex.extension = 'CLIP'
            alpha_tex.extension = 'CLIP'
            if ao_spec:
                ao_tex.extension = 'CLIP'
            if normal_spec:
                normal_tex.extension = 'CLIP'
                    
    if decal:
        diffuse_tex.extension = 'CLIP'
        rough_tex.extension = 'CLIP'
        bump_tex.extension = 'CLIP'
        alpha_tex.extension = 'CLIP'
        if ao_spec:
            ao_tex.extension = 'CLIP'
        if normal_spec:
            normal_tex.extension = 'CLIP'
                
    auto_align_nodes(node_tree) 

    for n in nodes:
        if n.name.startswith('QT_Bump'):
            n.location.y -= 150   

        if n.name.startswith('QT_AO_Tex'):
            n.location.y += 150   

    return material

def box_layer(self, context, img_spec, material, activelayer, files, dirname, decal, selected):

    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None

    if len(files) > 1:
        for f in files:
            if 'albedo' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]     
            if 'diffuse' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'diff' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'color' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'col' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecolor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecol' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'roughness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'rough' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'glossiness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'gloss' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'spec' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'specular' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'normal' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'norm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]    
            if 'nmap' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name] 
            if 'nor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'nrm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'opacity' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'opac' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'alpha' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'ao' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     
            if 'ambientocclusion' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     

    width, height = img_spec.size
    size = width/height

    for n in material.node_tree.nodes:
        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        n.select = False
        if n.name == 'Group Output':
            out_node = n

    layer1 = None
    layer2 = None
    layer3 = None
    layer4 = None
    layer5 = None

    blend1 = None
    blend2 = None
    blend3 = None
    blend4 = None
    blend5 = None

    fixalign = 0

    for n in nodes:
        if n.name.startswith('QT_Shader_1'):
            layer1 = n

        if n.name.startswith('QT_Layer_2'):
            layer2 = n

        if n.name.startswith('QT_Layer_3'):
            layer3 = n
        
        if n.name.startswith('QT_Layer_4'):
            layer4 = n

    if activelayer == 2 and layer2: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('_4'):                 
                    n.name = n.name.replace("_4", "_5")   
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   
        if layer3:
            for n in nodes:
                if n.name.endswith('_3'):                 
                    n.name = n.name.replace("_3", "_4")   
                    n.label = n.label.replace("_3", "_4")   
                    n.location.y -= 2000   
        if layer2:       
            for n in nodes:
                if n.name.endswith('_2'):                 
                    n.name = n.name.replace("_2", "_3")   
                    n.label = n.label.replace("_2", "_3")   
                    n.location.y -= 2000       

    if activelayer == 3 and layer3: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('_4'):                 
                    n.name = n.name.replace("_4", "_5")   
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   
        if layer3:
            for n in nodes:
                if n.name.endswith('_3'):                 
                    n.name = n.name.replace("_3", "_4")   
                    n.label = n.label.replace("_3", "_4")   
                    n.location.y -= 2000   

    if activelayer == 4 and layer4: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('_4'):                 
                    n.name = n.name.replace("_4", "_5")   
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   

    for n in nodes:                                
        if n.name.startswith('QT_Shader_1'):
            prev_shader = n

        if n.name.startswith('QT_Layer_' + str(activelayer-1)):
            prev_shader = n

        if n.name.startswith('QT_Layer_' + str(activelayer)):
            next_shader = n

    new_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    new_shader.name = 'QT_Shader_' + str(activelayer) 
    new_shader.label = 'QT_Layer_' + str(activelayer) + '_' + img_spec.name
    new_shader.inputs[17].default_value = (1,1,1,1)
    new_shader.inputs[18].default_value = 0
                
    coord = node_tree.nodes.new('ShaderNodeUVMap')
    coord.uv_map = 'QT_UV_Box_Layer_1'
    coord.name = 'QT_UV_Layer_' + str(activelayer)
    coord.label = 'Box'
    
    # mapping
    diffuse_mapping = node_tree.nodes.new('ShaderNodeMapping')
    rough_mapping = node_tree.nodes.new('ShaderNodeMapping')
    bump_mapping = node_tree.nodes.new('ShaderNodeMapping')
    alpha_mapping = node_tree.nodes.new('ShaderNodeMapping')
    
    diffuse_mapping.name = 'QT_Diffuse_Mapping_' + str(activelayer)
    rough_mapping.name = 'QT_Rough_Mapping_' + str(activelayer) 
    bump_mapping.name = 'QT_Bump_Mapping_' + str(activelayer)
    alpha_mapping.name = 'QT_Alpha_Mapping_' + str(activelayer)

    node_tree.links.new(coord.outputs[0], diffuse_mapping.inputs[0])
    node_tree.links.new(coord.outputs[0], rough_mapping.inputs[0])
    node_tree.links.new(coord.outputs[0], bump_mapping.inputs[0]) 
    node_tree.links.new(coord.outputs[0], alpha_mapping.inputs[0])   

    diffuse_mapping.inputs[3].default_value[0] = size/2
    diffuse_mapping.inputs[3].default_value[1] = 0.5
    diffuse_mapping.inputs[1].default_value[0] = 0.5 + (diffuse_mapping.inputs[3].default_value[0] / 2)
    diffuse_mapping.inputs[1].default_value[1] = 0.25
    rough_mapping.inputs[3].default_value[0] = size/2
    rough_mapping.inputs[3].default_value[1] = 0.5
    rough_mapping.inputs[1].default_value[0] = 0.5 + (rough_mapping.inputs[3].default_value[0] / 2)
    rough_mapping.inputs[1].default_value[1] = 0.25
    bump_mapping.inputs[3].default_value[0] = size/2
    bump_mapping.inputs[3].default_value[1] = 0.5
    bump_mapping.inputs[1].default_value[0] = 0.5 + (bump_mapping.inputs[3].default_value[0] / 2)
    bump_mapping.inputs[1].default_value[1] = 0.25
    alpha_mapping.inputs[3].default_value[0] = size/2
    alpha_mapping.inputs[3].default_value[1] = 0.5
    alpha_mapping.inputs[1].default_value[0] = 0.5 + (alpha_mapping.inputs[3].default_value[0] / 2)
    alpha_mapping.inputs[1].default_value[1] = 0.25

    diffuse_mapping.vector_type = 'TEXTURE'
    rough_mapping.vector_type = 'TEXTURE'        
    bump_mapping.vector_type = 'TEXTURE'        
    alpha_mapping.vector_type = 'TEXTURE'

    # diffuse
    diffuse_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if albedo_spec:
        diffuse_tex.image = albedo_spec
    else:
        diffuse_tex.image = img_spec

    diffuse_tex.show_texture = True
    diffuse_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    
    diffuse_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    
    diffuse_tex.name = 'QT_Diffuse_Tex_' + str(activelayer)
    diffuse_hue_sat.name = 'QT_Diffuse_Hue_Sat_' + str(activelayer) 
    diffuse_bright_contrast.name = 'QT_Diffuse_Bright_Contrast_' + str(activelayer) 
    
    node_tree.links.new(diffuse_mapping.outputs[0], diffuse_tex.inputs[0])
    node_tree.links.new(diffuse_tex.outputs[0], diffuse_hue_sat.inputs[4])
    node_tree.links.new(diffuse_hue_sat.outputs[0], diffuse_bright_contrast.inputs[0])
    node_tree.links.new(diffuse_bright_contrast.outputs[0], new_shader.inputs[0])

    # roughness
    rough_tex = node_tree.nodes.new('ShaderNodeTexImage')
    
    if roughness_spec:
        rough_tex.image = roughness_spec
    else:
        rough_tex.image = img_spec

    rough_tex.show_texture = True

    rough_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    rough_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    rough_invert = node_tree.nodes.new("ShaderNodeInvert")
    rough_invert.inputs[0].default_value = 0
    rough_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    rough_tex.name = 'QT_Rough_Tex_' + str(activelayer)
    rough_color_ramp.name = 'QT_Rough_Color_Ramp_' + str(activelayer)
    rough_bright_contrast.name = 'QT_Rough_Bright_Contrast_' + str(activelayer)
    rough_invert.name = 'QT_Rough_Invert_' + str(activelayer)
    rough_hue_sat.name = 'QT_Rough_Hue_Sat_' + str(activelayer)

    node_tree.links.new(rough_mapping.outputs[0], rough_tex.inputs[0])
    node_tree.links.new(rough_tex.outputs[0], rough_color_ramp.inputs[0])
    node_tree.links.new(rough_color_ramp.outputs[0], rough_hue_sat.inputs[4])
    node_tree.links.new(rough_hue_sat.outputs[0], rough_invert.inputs[1])
    node_tree.links.new(rough_invert.outputs[0], rough_bright_contrast.inputs[0])
    node_tree.links.new(rough_bright_contrast.outputs[0], new_shader.inputs[7])
    
    rough_clamp = node_tree.nodes.new("ShaderNodeClamp")
    rough_clamp.name = 'QT_Roughness_Clamp_' + str(activelayer)
    node_tree.links.new(rough_bright_contrast.outputs[0], rough_clamp.inputs[0])
    node_tree.links.new(rough_clamp.outputs[0], new_shader.inputs[7])
        
    # bump
    bump_tex = node_tree.nodes.new('ShaderNodeTexImage')
    bump_tex.show_texture = True
    
    bump_tex.image = img_spec    
    bump_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    bump_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    bump_bump = node_tree.nodes.new("ShaderNodeBump")
    bump_bump.inputs[0].default_value = 0.1
    bump_invert = node_tree.nodes.new("ShaderNodeInvert")
    bump_invert.inputs[0].default_value = 0
    bump_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    bump_tex.name = 'QT_Bump_Tex_' + str(activelayer)
    bump_color_ramp.name = 'QT_Bump_Color_Ramp_' + str(activelayer)
    bump_bright_contrast.name = 'QT_Bump_Bright_Contrast_' + str(activelayer)
    bump_bump.name = 'QT_Bump_Bump_' + str(activelayer)
    bump_invert.name = 'QT_Bump_Invert_' + str(activelayer)
    bump_hue_sat.name = 'QT_Bump_Hue_Sat_' + str(activelayer)

    node_tree.links.new(bump_tex.outputs[0], bump_color_ramp.inputs[0])
    node_tree.links.new(bump_color_ramp.outputs[0], bump_hue_sat.inputs[4])
    node_tree.links.new(bump_hue_sat.outputs[0], bump_invert.inputs[1])
    node_tree.links.new(bump_invert.outputs[0], bump_bright_contrast.inputs[0])
    node_tree.links.new(bump_bright_contrast.outputs[0], bump_bump.inputs[2])

    bump_clamp = node_tree.nodes.new("ShaderNodeClamp")
    bump_clamp.name = 'QT_Bump_Clamp_' + str(activelayer)

    node_tree.links.new(bump_bright_contrast.outputs[0], bump_clamp.inputs[0])
    node_tree.links.new(bump_clamp.outputs[0], bump_bump.inputs[2])
    
    node_tree.links.new(bump_mapping.outputs[0], bump_tex.inputs[0])
    node_tree.links.new(bump_bump.outputs[0], new_shader.inputs[20])

    # normal
    if normal_spec:
        normal_tex = node_tree.nodes.new('ShaderNodeTexImage')
        normal_tex.show_texture = True
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = 'Non-Color'
        normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")

        normal_tex.name = 'QT_Normal_Tex_' + str(activelayer)
        normal_strength.name = 'QT_Normal_Strength_' + str(activelayer)

        node_tree.links.new(diffuse_mapping.outputs[0], normal_tex.inputs[0])
        node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
        node_tree.links.new(normal_strength.outputs[0], bump_bump.inputs[5])
    
    # ao
    if ao_spec:
        ao_tex = node_tree.nodes.new('ShaderNodeTexImage')
        ao_tex.image = ao_spec
        ao_tex.show_texture = True
        ao_tex.name = 'QT_AO_Tex_' + str(activelayer)

        ao_multiply = node_tree.nodes.new('ShaderNodeMixRGB')
        ao_multiply.blend_type = 'MULTIPLY'
        ao_multiply.name = 'QT_AO_Multiply_' + str(activelayer)
        ao_multiply.inputs[0].default_value = 0.5        

        node_tree.links.new(diffuse_mapping.outputs[0], ao_tex.inputs[0])
        node_tree.links.new(ao_tex.outputs[0], ao_multiply.inputs[2])
        node_tree.links.new(diffuse_tex.outputs[0], ao_multiply.inputs[1])

        node_tree.links.new(ao_multiply.outputs[0], diffuse_hue_sat.inputs[4])
        
    # alpha
    alpha_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if alpha_spec:
        alpha_tex.image = alpha_spec
    else:
        alpha_tex.image = img_spec

    alpha_tex.show_texture = True
    alpha_tex.name = 'QT_Alpha_Tex_' + str(activelayer)

    alpha_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    alpha_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    alpha_invert = node_tree.nodes.new("ShaderNodeInvert")
    alpha_invert.inputs[0].default_value = 0
    alpha_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")        
    alpha_clamp = node_tree.nodes.new("ShaderNodeClamp")

    alpha_clamp.name = 'QT_Alpha_Clamp_' + str(activelayer)
    alpha_color_ramp.name = 'QT_Alpha_Color_Ramp_' + str(activelayer) 
    alpha_bright_contrast.name = 'QT_Alpha_Bright_Contrast_' + str(activelayer) 
    alpha_invert.name = 'QT_Alpha_Invert_' + str(activelayer) 
    alpha_hue_sat.name = 'QT_Alpha_Hue_Sat_' + str(activelayer) 
    
    node_tree.links.new(alpha_mapping.outputs[0], alpha_tex.inputs[0])
    node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])
    node_tree.links.new(alpha_color_ramp.outputs[0], alpha_hue_sat.inputs[4])
    node_tree.links.new(alpha_hue_sat.outputs[0], alpha_invert.inputs[1])
    node_tree.links.new(alpha_invert.outputs[0], alpha_bright_contrast.inputs[0])    
    node_tree.links.new(alpha_bright_contrast.outputs[0], alpha_clamp.inputs[0])
    node_tree.links.new(alpha_clamp.outputs[0], new_shader.inputs[19])

    if alpha_spec:
        node_tree.links.new(alpha_tex.outputs[0], alpha_color_ramp.inputs[0])
    else:
        node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])

    blend_node = node_tree.nodes.new('ShaderNodeMixShader')
    blend_node.name = 'QT_Layer_' + str(activelayer)
    blend_node.inputs[0].default_value = 1

    node_tree.links.new(prev_shader.outputs[0], blend_node.inputs[1])
    node_tree.links.new(new_shader.outputs[0], blend_node.inputs[2])
    node_tree.links.new(blend_node.outputs[0], out_node.inputs[0])
                        
    auto_align_nodes(node_tree)

    for n in nodes:
        if n.select:
            n.location.y -= 2000

    for n in nodes:
        if n.name.startswith('QT_Shader_1'):
            layer1 = n

        if n.name.startswith('QT_Layer_2'):
            layer2 = n

        if n.name.startswith('QT_Layer_3'):
            layer3 = n
        
        if n.name.startswith('QT_Layer_4'):
            layer4 = n

        if n.name.startswith('QT_Layer_5'):
            layer5 = n

        if n.name.startswith('QT_Blend_1'):
            blend1 = n

        if n.name.startswith('QT_Blend_2'):
            blend2 = n

        if n.name.startswith('QT_Blend_3'):
            blend3 = n
        
        if n.name.startswith('QT_Blend_4'):
            blend4 = n

        if n.name.startswith('QT_Blend_5'):
            blend5 = n

    if layer2:
        node_tree.links.new(layer1.outputs[0], layer2.inputs[1])

    if layer3:
        node_tree.links.new(layer2.outputs[0], layer3.inputs[1])

    if layer4:
        node_tree.links.new(layer3.outputs[0], layer4.inputs[1])

    if layer5:
        node_tree.links.new(layer4.outputs[0], layer5.inputs[1])

    if blend2:
        node_tree.links.new(layer1.outputs[0], blend2.inputs[1])

    if blend3:
        node_tree.links.new(layer2.outputs[0], blend3.inputs[1])

    if blend4:
        node_tree.links.new(layer3.outputs[0], blend4.inputs[1])

    if blend5:
        node_tree.links.new(layer4.outputs[0], blend5.inputs[1])
        
    out_node.location.y = blend_node.location.y
    out_node.location.x = blend_node.location.x + 300  

    for n in nodes:
        if n.name.startswith('QT_Bump') and n.name.endswith(str(activelayer)):
            n.location.y -= 150   

        if n.name.startswith('QT_AO_Tex') and n.name.endswith(str(activelayer)):
            n.location.y += 150   

def view_layer(self, context, img_spec, material, activelayer, files, dirname, decal, selected):

    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None

    if len(files) > 1:
        for f in files:
            if 'albedo' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]     
            if 'diffuse' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'diff' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]    
            if 'color' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'col' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecolor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'basecol' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                albedo_spec = bpy.data.images[f.name]   
            if 'roughness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'rough' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'glossiness' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'gloss' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]    
            if 'spec' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'specular' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                roughness_spec = bpy.data.images[f.name]     
            if 'normal' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]   
            if 'nmap' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name] 
            if 'nor' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]    
            if 'norm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'nrm' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                normal_spec = bpy.data.images[f.name]     
            if 'opacity' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'opac' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'alpha' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                alpha_spec = bpy.data.images[f.name]     
            if 'ao' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     
            if 'ambientocclusion' in str(f.name).lower():
                img_path = (os.path.join(dirname, f.name))
                bpy.ops.image.open( filepath = img_path )
                ao_spec = bpy.data.images[f.name]     

    width, height = img_spec.size
    size = width/height

    for n in material.node_tree.nodes:
        if n.name == 'QT_Output':
            out_material = n

        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        if n.name == 'Group Output':
            out_node = n

    layer1 = None
    layer2 = None
    layer3 = None
    layer4 = None
    layer5 = None

    blend1 = None
    blend2 = None
    blend3 = None
    blend4 = None
    blend5 = None
    
    coord2 = None
    coord3 = None
    coord4 = None

    fixalign = 0

    for n in nodes:
        if n.name.startswith('QT_Shader_1'):
            layer1 = n

        if n.name.startswith('QT_Layer_2'):
            layer2 = n

        if n.name.startswith('QT_Layer_3'):
            layer3 = n
        
        if n.name.startswith('QT_Layer_4'):
            layer4 = n

        if n.name == 'QT_UV_Layer_2':
            coord2 = n

        if n.name == 'QT_UV_Layer_3':
            coord3 = n

        if n.name == 'QT_UV_Layer_4':
            coord4 = n

    if activelayer == 2 and layer2: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('4'):                 
                    if coord4:
                        coord4.uv_map = 'QT_UV_View_Layer_5'  
                    n.name = n.name.replace("_4", "_5")   
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   
        if layer3:
            for n in nodes:
                if n.name.endswith('3'):    
                    if coord3:
                        coord3.uv_map = 'QT_UV_View_Layer_4'               
                    n.name = n.name.replace("_3", "_4")   
                    n.label = n.label.replace("_3", "_4")   
                    n.location.y -= 2000   
        if layer2:       
            for n in nodes:
                if n.name.endswith('2'):      
                    if coord2:
                        coord2.uv_map = 'QT_UV_View_Layer_3'           
                    n.name = n.name.replace("_2", "_3")   
                    n.label = n.label.replace("_2", "_3")   
                    n.location.y -= 2000     

    if activelayer == 3 and layer3: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('4'):    
                    if coord4:
                        coord4.uv_map = 'QT_UV_View_Layer_5'               
                    n.name = n.name.replace("_4", "_5")     
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   
        if layer3:
            for n in nodes:
                if n.name.endswith('3'):     
                    if coord3:
                        coord3.uv_map = 'QT_UV_View_Layer_4'               
                    n.name = n.name.replace("_3", "_4")   
                    n.label = n.label.replace("_3", "_4")   
                    n.location.y -= 2000   

    if activelayer == 4 and layer4: 
        fixalign = 1
        if layer4:
            for n in nodes:
                if n.name.endswith('4'):  
                    if coord4:
                        coord4.uv_map = 'QT_UV_View_Layer_5'                 
                    n.name = n.name.replace("_4", "_5")   
                    n.label = n.label.replace("_4", "_5")   
                    n.location.y -= 2000   

    for n in nodes:
        n.select = False
                                
        if n.name.startswith('QT_Shader_1'):
            prev_shader = n

        if n.name.startswith('QT_Layer_' + str(activelayer-1)):
            prev_shader = n

    new_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    new_shader.name = 'QT_Shader_' + str(activelayer) 
    new_shader.label = 'QT_Layer_' + str(activelayer) + '_' + img_spec.name
    new_shader.inputs[17].default_value = (1,1,1,1)
    new_shader.inputs[18].default_value = 0
    
    coord = node_tree.nodes.new('ShaderNodeUVMap')
    coord.uv_map = 'QT_UV_View_Layer_' + str(activelayer)
    coord.name = 'QT_UV_Layer_' + str(activelayer)
    coord.label = 'View'

    # mapping
    diffuse_mapping = node_tree.nodes.new('ShaderNodeMapping')
    rough_mapping = node_tree.nodes.new('ShaderNodeMapping')
    bump_mapping = node_tree.nodes.new('ShaderNodeMapping')
    alpha_mapping = node_tree.nodes.new('ShaderNodeMapping')
    
    diffuse_mapping.name = 'QT_Diffuse_Mapping_' + str(activelayer)
    rough_mapping.name = 'QT_Rough_Mapping_' + str(activelayer)
    bump_mapping.name = 'QT_Bump_Mapping_' + str(activelayer)
    alpha_mapping.name = 'QT_Alpha_Mapping_' + str(activelayer)

    node_tree.links.new(coord.outputs[0], diffuse_mapping.inputs[0])
    node_tree.links.new(coord.outputs[0], rough_mapping.inputs[0])
    node_tree.links.new(coord.outputs[0], bump_mapping.inputs[0])
    node_tree.links.new(coord.outputs[0], alpha_mapping.inputs[0])

    diffuse_mapping.vector_type = 'TEXTURE'
    rough_mapping.vector_type = 'TEXTURE'
    bump_mapping.vector_type = 'TEXTURE'
    alpha_mapping.vector_type = 'TEXTURE'

    if selected:
        diffuse_mapping.inputs[3].default_value[0] = size/2
        diffuse_mapping.inputs[3].default_value[1] = 0.5
        diffuse_mapping.inputs[1].default_value[0] = 0.25
        diffuse_mapping.inputs[1].default_value[1] = 0.25

        rough_mapping.inputs[3].default_value[0] = size/2
        rough_mapping.inputs[3].default_value[1] = 0.5
        rough_mapping.inputs[1].default_value[0] = 0.25
        rough_mapping.inputs[1].default_value[1] = 0.25

        bump_mapping.inputs[3].default_value[0] = size/2
        bump_mapping.inputs[3].default_value[1] = 0.5
        bump_mapping.inputs[1].default_value[0] = 0.25
        bump_mapping.inputs[1].default_value[1] = 0.25

        alpha_mapping.inputs[3].default_value[0] = size/2
        alpha_mapping.inputs[3].default_value[1] = 0.5
        alpha_mapping.inputs[1].default_value[0] = 0.25
        alpha_mapping.inputs[1].default_value[1] = 0.25

    # diffuse
    diffuse_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if albedo_spec:
        diffuse_tex.image = albedo_spec
    else:
        diffuse_tex.image = img_spec

    diffuse_tex.show_texture = True
    diffuse_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    
    diffuse_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    
    diffuse_tex.name = 'QT_Diffuse_Tex_' + str(activelayer)
    diffuse_hue_sat.name = 'QT_Diffuse_Hue_Sat_' + str(activelayer)
    diffuse_bright_contrast.name = 'QT_Diffuse_Bright_Contrast_' + str(activelayer)
    
    node_tree.links.new(diffuse_mapping.outputs[0], diffuse_tex.inputs[0])
    node_tree.links.new(diffuse_tex.outputs[0], diffuse_hue_sat.inputs[4])
    node_tree.links.new(diffuse_hue_sat.outputs[0], diffuse_bright_contrast.inputs[0])
    node_tree.links.new(diffuse_bright_contrast.outputs[0], new_shader.inputs[0])

    # roughness
    rough_tex = node_tree.nodes.new('ShaderNodeTexImage')
    
    if roughness_spec:
        rough_tex.image = roughness_spec
    else:
        rough_tex.image = img_spec

    rough_tex.show_texture = True

    rough_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    rough_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    rough_invert = node_tree.nodes.new("ShaderNodeInvert")
    rough_invert.inputs[0].default_value = 0
    rough_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    rough_tex.name = 'QT_Rough_Tex_' + str(activelayer)
    rough_color_ramp.name = 'QT_Rough_Color_Ramp_' + str(activelayer)
    rough_bright_contrast.name = 'QT_Rough_Bright_Contrast_' + str(activelayer)
    rough_invert.name = 'QT_Rough_Invert_' + str(activelayer)
    rough_hue_sat.name = 'QT_Rough_Hue_Sat_' + str(activelayer)

    node_tree.links.new(rough_mapping.outputs[0], rough_tex.inputs[0])
    node_tree.links.new(rough_tex.outputs[0], rough_color_ramp.inputs[0])
    node_tree.links.new(rough_color_ramp.outputs[0], rough_hue_sat.inputs[4])
    node_tree.links.new(rough_hue_sat.outputs[0], rough_invert.inputs[1])
    node_tree.links.new(rough_invert.outputs[0], rough_bright_contrast.inputs[0])
    node_tree.links.new(rough_bright_contrast.outputs[0], new_shader.inputs[7])

    rough_clamp = node_tree.nodes.new("ShaderNodeClamp")
    rough_clamp.name = 'QT_Roughness_Clamp_' + str(activelayer)
    node_tree.links.new(rough_bright_contrast.outputs[0], rough_clamp.inputs[0])
    node_tree.links.new(rough_clamp.outputs[0], new_shader.inputs[7])
        
    # bump
    bump_tex = node_tree.nodes.new('ShaderNodeTexImage')
    bump_tex.show_texture = True

    bump_tex.image = img_spec       
    bump_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    bump_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    bump_bump = node_tree.nodes.new("ShaderNodeBump")
    bump_bump.inputs[0].default_value = 0.1
    bump_invert = node_tree.nodes.new("ShaderNodeInvert")
    bump_invert.inputs[0].default_value = 0
    bump_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    bump_tex.name = 'QT_Bump_Tex_' + str(activelayer)
    bump_color_ramp.name = 'QT_Bump_Color_Ramp_' + str(activelayer) 
    bump_bright_contrast.name = 'QT_Bump_Bright_Contrast_' + str(activelayer) 
    bump_bump.name = 'QT_Bump_Bump_' + str(activelayer) 
    bump_invert.name = 'QT_Bump_Invert_' + str(activelayer)
    bump_hue_sat.name = 'QT_Bump_Hue_Sat_' + str(activelayer) 

    node_tree.links.new(bump_tex.outputs[0], bump_color_ramp.inputs[0])
    node_tree.links.new(bump_color_ramp.outputs[0], bump_hue_sat.inputs[4])
    node_tree.links.new(bump_hue_sat.outputs[0], bump_invert.inputs[1])
    node_tree.links.new(bump_invert.outputs[0], bump_bright_contrast.inputs[0])
    node_tree.links.new(bump_bright_contrast.outputs[0], bump_bump.inputs[2])

    bump_clamp = node_tree.nodes.new("ShaderNodeClamp")
    bump_clamp.name = 'QT_Bump_Clamp_' + str(activelayer)

    node_tree.links.new(bump_bright_contrast.outputs[0], bump_clamp.inputs[0])
    node_tree.links.new(bump_clamp.outputs[0], bump_bump.inputs[2])
    
    node_tree.links.new(bump_mapping.outputs[0], bump_tex.inputs[0])
    node_tree.links.new(bump_bump.outputs[0], new_shader.inputs[20])

    # normal
    if normal_spec:
        normal_tex = node_tree.nodes.new('ShaderNodeTexImage')
        normal_tex.show_texture = True
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = 'Non-Color'
        normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")

        normal_tex.name = 'QT_Normal_Tex_' + str(activelayer)
        normal_strength.name = 'QT_Normal_Strength_' + str(activelayer)

        node_tree.links.new(diffuse_mapping.outputs[0], normal_tex.inputs[0])
        node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
        node_tree.links.new(normal_strength.outputs[0], bump_bump.inputs[5])
    
    # ao
    if ao_spec:
        ao_tex = node_tree.nodes.new('ShaderNodeTexImage')
        ao_tex.image = ao_spec
        ao_tex.show_texture = True
        ao_tex.name = 'QT_AO_Tex_' + str(activelayer)

        ao_multiply = node_tree.nodes.new('ShaderNodeMixRGB')
        ao_multiply.blend_type = 'MULTIPLY'
        ao_multiply.name = 'QT_AO_Multiply_' + str(activelayer)
        ao_multiply.inputs[0].default_value = 0.5        

        node_tree.links.new(diffuse_mapping.outputs[0], ao_tex.inputs[0])
        node_tree.links.new(ao_tex.outputs[0], ao_multiply.inputs[2])
        node_tree.links.new(diffuse_tex.outputs[0], ao_multiply.inputs[1])

        node_tree.links.new(ao_multiply.outputs[0], diffuse_hue_sat.inputs[4])
        
    # alpha
    alpha_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if alpha_spec:
        alpha_tex.image = alpha_spec
    else:
        alpha_tex.image = img_spec

    alpha_tex.show_texture = True
    alpha_tex.name = 'QT_Alpha_Tex_' + str(activelayer)

    alpha_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    alpha_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    alpha_invert = node_tree.nodes.new("ShaderNodeInvert")
    alpha_invert.inputs[0].default_value = 0
    alpha_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")        
    alpha_clamp = node_tree.nodes.new("ShaderNodeClamp")

    alpha_clamp.name = 'QT_Alpha_Clamp_' + str(activelayer)
    alpha_color_ramp.name = 'QT_Alpha_Color_Ramp_' + str(activelayer) 
    alpha_bright_contrast.name = 'QT_Alpha_Bright_Contrast_' + str(activelayer) 
    alpha_invert.name = 'QT_Alpha_Invert_' + str(activelayer) 
    alpha_hue_sat.name = 'QT_Alpha_Hue_Sat_' + str(activelayer) 
    
    node_tree.links.new(alpha_mapping.outputs[0], alpha_tex.inputs[0])
    node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])
    node_tree.links.new(alpha_color_ramp.outputs[0], alpha_hue_sat.inputs[4])
    node_tree.links.new(alpha_hue_sat.outputs[0], alpha_invert.inputs[1])
    node_tree.links.new(alpha_invert.outputs[0], alpha_bright_contrast.inputs[0])    
    node_tree.links.new(alpha_bright_contrast.outputs[0], alpha_clamp.inputs[0])
    node_tree.links.new(alpha_clamp.outputs[0], new_shader.inputs[19])

    if alpha_spec:
        node_tree.links.new(alpha_tex.outputs[0], alpha_color_ramp.inputs[0])
    else:
        node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])

    blend_node = node_tree.nodes.new('ShaderNodeMixShader')
    blend_node.name = 'QT_Blend_' + str(activelayer)
    
    blend_node2 = node_tree.nodes.new('ShaderNodeMixShader')
    blend_node2.name = 'QT_Layer_' + str(activelayer)
    blend_node2.inputs[0].default_value = 1

    node_tree.links.new(prev_shader.outputs[0], blend_node.inputs[1])
    node_tree.links.new(new_shader.outputs[0], blend_node.inputs[2])
    node_tree.links.new(prev_shader.outputs[0], blend_node2.inputs[1])
    node_tree.links.new(blend_node.outputs[0], blend_node2.inputs[2])
    node_tree.links.new(blend_node2.outputs[0], out_node.inputs[0])

    # mask
    mask_range = node_tree.nodes.new("ShaderNodeMapRange")
    node_tree.links.new(diffuse_tex.outputs[1], mask_range.inputs[0])
    node_tree.links.new(mask_range.outputs[0], blend_node.inputs[0])
    mask_range.name = 'QT_Range_' + str(activelayer)
    
    auto_align_nodes(node_tree)

    mask_range.location.y -= 300
    blend_node.location.y -= 300
    blend_node2.location.y -= 300
    
    for n in nodes:
        if n.select:
            n.location.y -= 2000

    for n in nodes:
        if n.name.startswith('QT_Shader_1'):
            layer1 = n

        if n.name.startswith('QT_Layer_2'):
            layer2 = n

        if n.name.startswith('QT_Layer_3'):
            layer3 = n
        
        if n.name.startswith('QT_Layer_4'):
            layer4 = n

        if n.name.startswith('QT_Layer_5'):
            layer5 = n

        if n.name.startswith('QT_Blend_1'):
            blend1 = n

        if n.name.startswith('QT_Blend_2'):
            blend2 = n

        if n.name.startswith('QT_Blend_3'):
            blend3 = n
        
        if n.name.startswith('QT_Blend_4'):
            blend4 = n

        if n.name.startswith('QT_Blend_5'):
            blend5 = n

    if layer2:
        node_tree.links.new(layer1.outputs[0], layer2.inputs[1])

    if layer3:
        node_tree.links.new(layer2.outputs[0], layer3.inputs[1])

    if layer4:
        node_tree.links.new(layer3.outputs[0], layer4.inputs[1])

    if layer5:
        node_tree.links.new(layer4.outputs[0], layer5.inputs[1])

    if blend2:
        node_tree.links.new(layer1.outputs[0], blend2.inputs[1])

    if blend3:
        node_tree.links.new(layer2.outputs[0], blend3.inputs[1])

    if blend4:
        node_tree.links.new(layer3.outputs[0], blend4.inputs[1])

    if blend5:
        node_tree.links.new(layer4.outputs[0], blend5.inputs[1])

    out_node.location.y = blend_node2.location.y
    out_node.location.x = blend_node2.location.x + 300  

    for n in nodes:
        if n.name.startswith('QT_Bump') and n.name.endswith(str(activelayer)):
            n.location.y -= 150   

        if n.name.startswith('QT_AO_Tex') and n.name.endswith(str(activelayer)):
            n.location.y += 150   

def remake_material(ob, albedo_spec, roughness_spec, normal_spec, alpha_spec, ao_spec):

    material = ob.data.materials[0]
    
    # material settings
    material.blend_method = 'HASHED'
    material.shadow_method = 'HASHED'
    material.use_screen_refraction = True
    material.show_transparent_back = False

    material.name = 'QT_' + albedo_spec.name    
    material.use_nodes = True
    out_material = clean_node_tree(material.node_tree)
    out_material.name = 'QT_Output' 

    groupname = 'QT_Shader_' + albedo_spec.name
    grp = bpy.data.node_groups.new(groupname, 'ShaderNodeTree')
    group_node = material.node_tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = bpy.data.node_groups[grp.name]
    group_node.name = groupname
    group_node.select = True

    material.node_tree.nodes.active = group_node
    
    nodes = group_node.node_tree.nodes
    node_tree = group_node.node_tree
    
    out_node = node_tree.nodes.new('NodeGroupOutput')
    group_node.outputs.new('NodeSocketShader', 'Output')
    group_node.location = out_material.location
    group_node.location.x -= 500

    core_shader = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    core_shader.name = 'QT_Shader_1'
    core_shader.label = 'QT_Layer_1_' + albedo_spec.name 
    core_shader.inputs[17].default_value = (1,1,1,1)
    core_shader.inputs[18].default_value = 0
    
    node_tree.links.new(core_shader.outputs[0], out_node.inputs[0])
    material.node_tree.links.new(out_material.inputs['Surface'], group_node.outputs[0])
    
    # mapping
    diffuse_mapping = node_tree.nodes.new('ShaderNodeMapping')
    rough_mapping = node_tree.nodes.new('ShaderNodeMapping')
    bump_mapping = node_tree.nodes.new('ShaderNodeMapping')
    alpha_mapping = node_tree.nodes.new('ShaderNodeMapping')
    
    diffuse_mapping.name = 'QT_Diffuse_Mapping_1'
    rough_mapping.name = 'QT_Rough_Mapping_1'
    bump_mapping.name = 'QT_Bump_Mapping_1'
    alpha_mapping.name = 'QT_Alpha_Mapping_1'

    coord = node_tree.nodes.new('ShaderNodeTexCoord')
    coord.name = 'QT_UV_Layer_1'    
    coord.label = 'UV'

    node_tree.links.new(coord.outputs[2], diffuse_mapping.inputs[0])
    node_tree.links.new(coord.outputs[2], rough_mapping.inputs[0])
    node_tree.links.new(coord.outputs[2], bump_mapping.inputs[0])
    node_tree.links.new(coord.outputs[2], alpha_mapping.inputs[0])

    diffuse_mapping.vector_type = 'TEXTURE'
    rough_mapping.vector_type = 'TEXTURE'
    bump_mapping.vector_type = 'TEXTURE'
    alpha_mapping.vector_type = 'TEXTURE'

    # diffuse
    diffuse_tex = node_tree.nodes.new('ShaderNodeTexImage')
    diffuse_tex.image = albedo_spec
    diffuse_tex.show_texture = True
    diffuse_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    
    diffuse_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    
    diffuse_tex.name = 'QT_Diffuse_Tex_1' 
    diffuse_hue_sat.name = 'QT_Diffuse_Hue_Sat_1'
    diffuse_bright_contrast.name = 'QT_Diffuse_Bright_Contrast_1' 
    
    node_tree.links.new(diffuse_mapping.outputs[0], diffuse_tex.inputs[0])
    node_tree.links.new(diffuse_tex.outputs[0], diffuse_hue_sat.inputs[4])
    node_tree.links.new(diffuse_hue_sat.outputs[0], diffuse_bright_contrast.inputs[0])
    node_tree.links.new(diffuse_bright_contrast.outputs[0], core_shader.inputs[0])

    # roughness
    rough_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if roughness_spec:
        rough_tex.image = roughness_spec
    else:
        rough_tex.image = albedo_spec
        
    rough_tex.show_texture = True

    rough_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    rough_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    rough_invert = node_tree.nodes.new("ShaderNodeInvert")
    rough_invert.inputs[0].default_value = 0
    rough_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    rough_tex.name = 'QT_Rough_Tex_1' 
    rough_color_ramp.name = 'QT_Rough_Color_Ramp_1' 
    rough_bright_contrast.name = 'QT_Rough_Bright_Contrast_1' 
    rough_invert.name = 'QT_Rough_Invert_1' 
    rough_hue_sat.name = 'QT_Rough_Hue_Sat_1' 

    node_tree.links.new(rough_mapping.outputs[0], rough_tex.inputs[0])
    node_tree.links.new(rough_tex.outputs[0], rough_color_ramp.inputs[0])
    node_tree.links.new(rough_color_ramp.outputs[0], rough_hue_sat.inputs[4])
    node_tree.links.new(rough_hue_sat.outputs[0], rough_invert.inputs[1])
    node_tree.links.new(rough_invert.outputs[0], rough_bright_contrast.inputs[0])
    node_tree.links.new(rough_bright_contrast.outputs[0], core_shader.inputs[7])
    
    rough_clamp = node_tree.nodes.new("ShaderNodeClamp")
    rough_clamp.name = 'QT_Roughness_Clamp_1'
    node_tree.links.new(rough_bright_contrast.outputs[0], rough_clamp.inputs[0])
    node_tree.links.new(rough_clamp.outputs[0], core_shader.inputs[7])
        
    # bump
    bump_tex = node_tree.nodes.new('ShaderNodeTexImage')
    bump_tex.show_texture = True
    
    bump_tex.image = albedo_spec
    bump_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    bump_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    bump_bump = node_tree.nodes.new("ShaderNodeBump")
    bump_bump.inputs[0].default_value = 0.1
    bump_invert = node_tree.nodes.new("ShaderNodeInvert")
    bump_invert.inputs[0].default_value = 0
    bump_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    bump_tex.name = 'QT_Bump_Tex_1' 
    bump_color_ramp.name = 'QT_Bump_Color_Ramp_1' 
    bump_bright_contrast.name = 'QT_Bump_Bright_Contrast_1'
    bump_bump.name = 'QT_Bump_Bump_1'
    bump_invert.name = 'QT_Bump_Invert_1' 
    bump_hue_sat.name = 'QT_Bump_Hue_Sat_1'

    node_tree.links.new(bump_tex.outputs[0], bump_color_ramp.inputs[0])
    node_tree.links.new(bump_color_ramp.outputs[0], bump_hue_sat.inputs[4])
    node_tree.links.new(bump_hue_sat.outputs[0], bump_invert.inputs[1])
    node_tree.links.new(bump_invert.outputs[0], bump_bright_contrast.inputs[0])
    node_tree.links.new(bump_bright_contrast.outputs[0], bump_bump.inputs[2])

    bump_clamp = node_tree.nodes.new("ShaderNodeClamp")
    bump_clamp.name = 'QT_Bump_Clamp_1'

    node_tree.links.new(bump_bright_contrast.outputs[0], bump_clamp.inputs[0])
    node_tree.links.new(bump_clamp.outputs[0], bump_bump.inputs[2])
            
    node_tree.links.new(bump_mapping.outputs[0], bump_tex.inputs[0])
    node_tree.links.new(bump_bump.outputs[0], core_shader.inputs[20])

    # normal
    if normal_spec:
        normal_tex = node_tree.nodes.new('ShaderNodeTexImage')
        normal_tex.show_texture = True
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = 'Non-Color'
        normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")

        normal_tex.name = 'QT_Normal_Tex_1'
        normal_strength.name = 'QT_Normal_Strength_1'

        node_tree.links.new(diffuse_mapping.outputs[0], normal_tex.inputs[0])
        node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
        node_tree.links.new(normal_strength.outputs[0], bump_bump.inputs[5])
    
    # ao
    if ao_spec:
        ao_tex = node_tree.nodes.new('ShaderNodeTexImage')
        ao_tex.image = ao_spec
        ao_tex.show_texture = True
        ao_tex.name = 'QT_AO_Tex_1'

        ao_multiply = node_tree.nodes.new('ShaderNodeMixRGB')
        ao_multiply.blend_type = 'MULTIPLY'
        ao_multiply.name = 'QT_AO_Multiply_1'
        ao_multiply.inputs[0].default_value = 0.5        

        node_tree.links.new(diffuse_mapping.outputs[0], ao_tex.inputs[0])
        node_tree.links.new(ao_tex.outputs[0], ao_multiply.inputs[2])
        node_tree.links.new(diffuse_tex.outputs[0], ao_multiply.inputs[1])

        node_tree.links.new(ao_multiply.outputs[0], diffuse_hue_sat.inputs[4])
        
    # alpha
    alpha_tex = node_tree.nodes.new('ShaderNodeTexImage')

    if alpha_spec:
        alpha_tex.image = alpha_spec
    else:
        alpha_tex.image = albedo_spec

    alpha_tex.show_texture = True
    alpha_tex.name = 'QT_Alpha_Tex_1' 

    alpha_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    alpha_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    alpha_invert = node_tree.nodes.new("ShaderNodeInvert")
    alpha_invert.inputs[0].default_value = 0
    alpha_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")        
    alpha_clamp = node_tree.nodes.new("ShaderNodeClamp")

    alpha_clamp.name = 'QT_Alpha_Clamp_1'
    alpha_color_ramp.name = 'QT_Alpha_Color_Ramp_1' 
    alpha_bright_contrast.name = 'QT_Alpha_Bright_Contrast_1' 
    alpha_invert.name = 'QT_Alpha_Invert_1' 
    alpha_hue_sat.name = 'QT_Alpha_Hue_Sat_1' 
    
    node_tree.links.new(alpha_mapping.outputs[0], alpha_tex.inputs[0])
    node_tree.links.new(alpha_color_ramp.outputs[0], alpha_hue_sat.inputs[4])
    node_tree.links.new(alpha_hue_sat.outputs[0], alpha_invert.inputs[1])
    node_tree.links.new(alpha_invert.outputs[0], alpha_bright_contrast.inputs[0])    
    node_tree.links.new(alpha_bright_contrast.outputs[0], alpha_clamp.inputs[0])
    node_tree.links.new(alpha_clamp.outputs[0], core_shader.inputs[19])

    if alpha_spec:
        node_tree.links.new(alpha_tex.outputs[0], alpha_color_ramp.inputs[0])
    else:
        node_tree.links.new(alpha_tex.outputs[1], alpha_color_ramp.inputs[0])
                        
    auto_align_nodes(node_tree) 

    for n in nodes:
        if n.name.startswith('QT_Bump'):
            n.location.y -= 150   

        if n.name.startswith('QT_AO_Tex'):
            n.location.y += 150   

    return material

# MASKS

def texture_mask(self, context, img_spec, material, activelayer, proc_uv):

    width, height = img_spec.size
    size = width/height

    for n in material.node_tree.nodes:
        if n.name == 'QT_Output':
            out_material = n

        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        if n.name == 'Group Output':
            out_node = n

    for n in nodes:
        n.select = False
        
        if n.name.startswith('QT_Layer_' + str(activelayer)):
            blend_node = n

        if n.name.startswith('QT_UV_Layer_' + str(activelayer)):
            coord = n
    
    # mapping
    mask_mapping = node_tree.nodes.new('ShaderNodeMapping')
    mask_mapping.name = 'QT_Mapping_Mask_' + str(activelayer) 

    # align image
    if coord.label == 'Decal' or coord.label == 'View' or coord.label == 'Box':
        node_tree.links.new(coord.outputs[0], mask_mapping.inputs[0])

    if proc_uv:        
        # procedural UVs
        mask_mapping.vector_type = 'TEXTURE'
        mask_mapping.inputs[3].default_value[0] = size/2
        mask_mapping.inputs[3].default_value[1] = 0.5
        mask_mapping.inputs[1].default_value[0] = 0.5 + (mask_mapping.inputs[3].default_value[0] / 2)
        mask_mapping.inputs[1].default_value[1] = 0.25

    # mask
    mask_tex = node_tree.nodes.new('ShaderNodeTexImage')
    mask_tex.image = img_spec
    mask_tex.show_texture = True

    mask_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    mask_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    mask_invert = node_tree.nodes.new("ShaderNodeInvert")
    mask_invert.inputs[0].default_value = 0
    mask_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    mask_tex.name = 'QT_Tex_Mask_' + str(activelayer) 
    mask_color_ramp.name = 'QT_Color_Ramp_Mask_' + str(activelayer) 
    mask_bright_contrast.name = 'QT_Bright_Contrast_Mask_' + str(activelayer) 
    mask_invert.name = 'QT_Invert_Mask_' + str(activelayer)
    mask_hue_sat.name = 'QT_Hue_Sat_Mask_' + str(activelayer) 

    node_tree.links.new(mask_mapping.outputs[0], mask_tex.inputs[0])
    node_tree.links.new(mask_tex.outputs[0], mask_color_ramp.inputs[0])
    node_tree.links.new(mask_color_ramp.outputs[0], mask_hue_sat.inputs[4])
    node_tree.links.new(mask_hue_sat.outputs[0], mask_invert.inputs[1])
    node_tree.links.new(mask_invert.outputs[0], mask_bright_contrast.inputs[0])
    node_tree.links.new(mask_bright_contrast.outputs[0], blend_node.inputs[0])

    # clamps
    mask_clamp = node_tree.nodes.new("ShaderNodeClamp")
    mask_clamp.name = 'QT_Clamp_Mask_' + str(activelayer)   
    
    node_tree.links.new(out_node.inputs[0], mask_clamp.outputs[0])

    node_tree.links.new(mask_bright_contrast.outputs[0], mask_clamp.inputs[0])
    node_tree.links.new(mask_clamp.outputs[0], blend_node.inputs[0])
    
    auto_align_nodes(node_tree)
            
    for n in nodes:
        if n.select:
            n.location.y = 0
            if activelayer == 2:
                n.location.y -= 1500
            elif activelayer == 3:
                n.location.y -= 3500
            elif activelayer == 4:
                n.location.y -= 5500
            elif activelayer == 5:
                n.location.y -= 7500

def depth_mask(self, context, img_spec, material, activelayer, proc_uv):

    width, height = img_spec.size
    size = width/height

    for n in material.node_tree.nodes:
        if n.name == 'QT_Output':
            out_material = n

        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        if n.name == 'Group Output':
            out_node = n

    for n in nodes:
        n.select = False
        
        if n.name.startswith('QT_Layer_' + str(activelayer)):
            blend_node = n

        if n.name.startswith('QT_Diffuse_Mapping_' + str(activelayer-1)):
            mask_mapping = n
    
    # mask
    mask_tex = node_tree.nodes.new('ShaderNodeTexImage')
    mask_tex.image = img_spec
    mask_tex.show_texture = True

    mask_color_ramp = node_tree.nodes.new("ShaderNodeValToRGB")
    mask_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    mask_invert = node_tree.nodes.new("ShaderNodeInvert")
    mask_invert.inputs[0].default_value = 0
    mask_hue_sat = node_tree.nodes.new("ShaderNodeHueSaturation")    

    mask_tex.name = 'QT_Tex_Mask_' + str(activelayer) 
    mask_color_ramp.name = 'QT_Color_Ramp_Mask_' + str(activelayer) 
    mask_bright_contrast.name = 'QT_Bright_Contrast_Mask_' + str(activelayer) 
    mask_invert.name = 'QT_Invert_Mask_' + str(activelayer)
    mask_hue_sat.name = 'QT_Hue_Sat_Mask_' + str(activelayer) 

    node_tree.links.new(mask_mapping.outputs[0], mask_tex.inputs[0])
    node_tree.links.new(mask_tex.outputs[0], mask_color_ramp.inputs[0])
    node_tree.links.new(mask_color_ramp.outputs[0], mask_hue_sat.inputs[4])
    node_tree.links.new(mask_hue_sat.outputs[0], mask_invert.inputs[1])
    node_tree.links.new(mask_invert.outputs[0], mask_bright_contrast.inputs[0])
    node_tree.links.new(mask_bright_contrast.outputs[0], blend_node.inputs[0])

    # clamps
    mask_clamp = node_tree.nodes.new("ShaderNodeClamp")
    mask_clamp.name = 'QT_Clamp_Mask_' + str(activelayer)   
    
    node_tree.links.new(out_node.inputs[0], mask_clamp.outputs[0])

    node_tree.links.new(mask_bright_contrast.outputs[0], mask_clamp.inputs[0])
    node_tree.links.new(mask_clamp.outputs[0], blend_node.inputs[0])
    
    auto_align_nodes(node_tree)
            
    for n in nodes:
        if n.select:
            n.location.y = 0
            if activelayer == 2:
                n.location.y -= 1500
            elif activelayer == 3:
                n.location.y -= 3500
            elif activelayer == 4:
                n.location.y -= 5500
            elif activelayer == 5:
                n.location.y -= 7500

def height_mask(self, context, material, activelayer):

    for n in material.node_tree.nodes:
        if n.name == 'QT_Output':
            out_material = n

        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        if n.name == 'Group Output':
            out_node = n

    for n in nodes:
        n.select = False
        
        if n.name.startswith('QT_Layer_' + str(activelayer)):
            blend_node = n
        
    coord = node_tree.nodes.new('ShaderNodeTexCoord')
    mask_add = node_tree.nodes.new('ShaderNodeVectorMath')
    mask_xyz = node_tree.nodes.new('ShaderNodeSeparateXYZ')
    mask_math = node_tree.nodes.new('ShaderNodeMath')
    mask_power = node_tree.nodes.new('ShaderNodeMath')    
    mask_noise = node_tree.nodes.new('ShaderNodeTexNoise')
    mask_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    mask_invert = node_tree.nodes.new("ShaderNodeInvert")
    mask_clamp = node_tree.nodes.new("ShaderNodeClamp")
    
    # names
    coord.name = 'QT_UV_Layer_Mask_' + str(activelayer)
    mask_add.name = 'QT_Mapping_Mask_' + str(activelayer)
    mask_xyz.name = 'QT_Xyz_Mask_' + str(activelayer)    
    mask_math.name = 'QT_Math_Mask_' + str(activelayer)    
    mask_power.name = 'QT_Power_Mask_' + str(activelayer)  
    mask_noise.name = 'QT_Noise_Mask_' + str(activelayer)      
    mask_bright_contrast.name = 'QT_Bright_Contrast_Mask_' + str(activelayer)
    mask_invert.name = 'QT_Invert_Mask_' + str(activelayer)
    mask_clamp.name = 'QT_Clamp_Mask_' + str(activelayer)
    
    # links    
    node_tree.links.new(coord.outputs[3], mask_add.inputs[0])
    node_tree.links.new(mask_add.outputs[0], mask_xyz.inputs[0])
    node_tree.links.new(mask_xyz.outputs[2], mask_invert.inputs[1])

    node_tree.links.new(mask_invert.outputs[0], mask_math.inputs[0])
    node_tree.links.new(mask_math.outputs[0], mask_power.inputs[0])
    node_tree.links.new(mask_power.outputs[0], mask_clamp.inputs[0])

    node_tree.links.new(mask_noise.outputs[0], mask_bright_contrast.inputs[0])
    node_tree.links.new(mask_bright_contrast.outputs[0], mask_math.inputs[1])
    
    node_tree.links.new(mask_clamp.outputs[0], out_node.inputs[0])
    node_tree.links.new(mask_clamp.outputs[0], blend_node.inputs[0])
    
    # settings
    mask_invert.inputs[0].default_value = 1
    mask_noise.inputs[2].default_value = 0
    mask_math.operation = 'SUBTRACT'
    mask_power.operation = 'POWER'
    mask_power.inputs[1].default_value = 0.001

    auto_align_nodes(node_tree)
            
    for n in nodes:
        if n.select:
            n.location.y = 0
            if activelayer == 2:
                n.location.y -= 1700
            elif activelayer == 3:
                n.location.y -= 3700
            elif activelayer == 4:
                n.location.y -= 5700
            elif activelayer == 5:
                n.location.y -= 7700

    mask_noise.location.y += 200
    mask_bright_contrast.location.y += 200

def normal_mask(self, context, material, activelayer):

    for n in material.node_tree.nodes:
        if n.name == 'QT_Output':
            out_material = n

        if n.name.startswith('QT_Shader'):
            nodes = n.node_tree.nodes
            node_tree = n.node_tree
            
    for n in nodes:
        if n.name == 'Group Output':
            out_node = n

    for n in nodes:
        n.select = False
        
        if n.name.startswith('QT_Layer_' + str(activelayer)):
            blend_node = n
        
    coord = node_tree.nodes.new('ShaderNodeTexCoord')
    mask_xyz = node_tree.nodes.new('ShaderNodeSeparateXYZ')
    mask_math = node_tree.nodes.new('ShaderNodeMath')
    mask_noise = node_tree.nodes.new('ShaderNodeTexNoise')
    mask_bright_contrast = node_tree.nodes.new("ShaderNodeBrightContrast")
    mask_invert = node_tree.nodes.new("ShaderNodeInvert")
    mask_clamp = node_tree.nodes.new("ShaderNodeClamp")

    # names
    coord.name = 'QT_UV_Layer_Mask_' + str(activelayer)
    mask_xyz.name = 'QT_Xyz_Mask_' + str(activelayer)    
    mask_math.name = 'QT_Math_Mask_' + str(activelayer)    
    mask_noise.name = 'QT_Noise_Mask_' + str(activelayer)      
    mask_bright_contrast.name = 'QT_Bright_Contrast_Mask_' + str(activelayer)
    mask_invert.name = 'QT_Invert_Mask_' + str(activelayer)
    mask_clamp.name = 'QT_Clamp_Mask_' + str(activelayer)

    # links    
    node_tree.links.new(coord.outputs[1], mask_xyz.inputs[0])
    node_tree.links.new(mask_xyz.outputs[2], mask_invert.inputs[1])
    node_tree.links.new(mask_invert.outputs[0], mask_math.inputs[0])
    node_tree.links.new(mask_math.outputs[0], mask_clamp.inputs[0])

    node_tree.links.new(mask_noise.outputs[0], mask_bright_contrast.inputs[0])
    node_tree.links.new(mask_bright_contrast.outputs[0], mask_math.inputs[1])
    
    node_tree.links.new(mask_clamp.outputs[0], out_node.inputs[0])
    node_tree.links.new(mask_clamp.outputs[0], blend_node.inputs[0])

    # settings
    mask_invert.inputs[0].default_value = 0
    mask_noise.inputs[2].default_value = 0
    mask_bright_contrast.inputs[1].default_value = -1
    mask_bright_contrast.inputs[2].default_value = 10
    mask_math.operation = 'SUBTRACT'

    coord.location.x -= 700
    mask_xyz.location.x -= 500
    mask_clamp.location.x -= 300
    
    auto_align_nodes(node_tree)
            
    for n in nodes:
        if n.select:
            n.location.y = 0
            if activelayer == 2:
                n.location.y -= 1700
            elif activelayer == 3:
                n.location.y -= 3700
            elif activelayer == 4:
                n.location.y -= 5700
            elif activelayer == 5:
                n.location.y -= 7700

    mask_noise.location.y += 200
    mask_bright_contrast.location.y += 200

# BLEND

def blend(self, context, material, shader_node, out_mat, node_group_name):

    # create the blend group in the material
    groupname = 'QT_Blend'
    grp = bpy.data.node_groups.new(groupname, 'ShaderNodeTree')
    blend_node = material.node_tree.nodes.new('ShaderNodeGroup')
    blend_node.node_tree = bpy.data.node_groups[grp.name]
    blend_node.name = groupname

    # this is inside the blend group
    nodes = blend_node.node_tree.nodes
    node_tree = blend_node.node_tree
    out_node = node_tree.nodes.new('NodeGroupOutput')
    in_node = node_tree.nodes.new('NodeGroupInput')
    blend_node.outputs.new('NodeSocketShader', 'Output')
    blend_node.inputs.new('NodeSocketShader', 'Input')
    blend_node.location = shader_node.location
    blend_node.location.x += 250
    # creating the instanced group from the other material
    group_node = nodes.new("ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[node_group_name]

    # nodes
    blend_coord = node_tree.nodes.new('ShaderNodeTexCoord')
    blend_add = node_tree.nodes.new('ShaderNodeVectorMath')
    blend_xyz = node_tree.nodes.new('ShaderNodeSeparateXYZ')
    blend_math = node_tree.nodes.new('ShaderNodeMath')
    blend_power = node_tree.nodes.new('ShaderNodeMath')
    blend_clamp = node_tree.nodes.new("ShaderNodeClamp")
    blend_mix = node_tree.nodes.new('ShaderNodeMixShader')
    blend_noise = node_tree.nodes.new('ShaderNodeTexNoise')
    blend_bright_contrast = node_tree.nodes.new('ShaderNodeBrightContrast')
    # names
    blend_coord.name = 'QT_Blend_Coord'
    blend_add.name = 'QT_Blend_Add'
    blend_xyz.name = 'QT_Blend_XYZ'
    blend_math.name = 'QT_Blend_Math'
    blend_power.name = 'QT_Blend_Power'
    blend_clamp.name = 'QT_Blend_Clamp'
    blend_noise.name = 'QT_Blend_Noise'
    blend_bright_contrast.name = 'QT_Blend_Bright_Contrast'
    blend_mix.name = 'QT_Blend_Mix'
    blend_mix.label = 'QT_Blend_Material'
    # links        
    node_tree.links.new(blend_coord.outputs[3], blend_add.inputs[0])
    node_tree.links.new(blend_add.outputs[0], blend_xyz.inputs[0])
    node_tree.links.new(blend_xyz.outputs[2], blend_math.inputs[1])
    node_tree.links.new(blend_noise.outputs[0], blend_bright_contrast.inputs[0])
    node_tree.links.new(blend_bright_contrast.outputs[0], blend_math.inputs[0])
    node_tree.links.new(blend_math.outputs[0], blend_power.inputs[0])
    node_tree.links.new(blend_power.outputs[0], blend_clamp.inputs[0])
    node_tree.links.new(blend_clamp.outputs[0], blend_mix.inputs[0])
    
    node_tree.links.new(in_node.outputs[0], blend_mix.inputs[1])
    node_tree.links.new(group_node.outputs[0], blend_mix.inputs[2])
    node_tree.links.new(blend_mix.outputs[0], out_node.inputs[0])

    # settings            
    blend_noise.inputs[2].default_value = 0
    blend_math.operation = 'SUBTRACT'
    blend_power.operation = 'POWER'
    blend_power.inputs[1].default_value = 0.001

    # link material nodes
    material.node_tree.links.new(shader_node.outputs[0], blend_node.inputs[0])
    material.node_tree.links.new(blend_node.outputs[0], out_mat.inputs[0])

    auto_align_nodes(node_tree)

# DECAL

def create_decal(self, context, name, sel, rv3d, region, res, padding):

    if len(sel) > 0:
        bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
    else:
        bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN', align = 'VIEW')

    # Create new mesh
    plane = context.active_object

    bpy.ops.object.mode_set(mode='OBJECT')
    
    if len(sel) > 0:
        col = sel[0].users_collection[0]
        add_to_collection(plane.name, col, context)

        plane.location = Vector((0,0,0))
        # displace
        displace = plane.modifiers.new(name="QT_Displace", type="DISPLACE")
        displace.strength = padding
        displace.mid_level = 0.5
        displace.show_in_editmode = True
        displace.show_on_cage = True
        displace.show_expanded = False

        ob = sel[0]
        bb = ob.bound_box

        centers = []

        bb = []

        x_2d = []
        y_2d = []

        for obj in sel:
            for v in obj.bound_box:
                pos = obj.matrix_world @ Vector(v) 
                x = view3d_utils.location_3d_to_region_2d(region, rv3d, pos)            
                x_2d.append(x[0])
                y_2d.append(x[1])

        regX = context.region.width
        regY = context.region.height

        minx = min(x_2d) - 100
        miny = min(y_2d) - 100
        maxx = max(x_2d) + 100
        maxy = max(y_2d) + 100

        if minx < 0:
            minx = 0
        if miny < 0:
            miny = 0
        if maxx > regX:
            maxx = regX
        if maxy > regY:
            maxy = regY
        
        cloc = Vector((0,0,0))

        v0 = ((minx,miny))
        v1 = ((maxx,maxy))
        v2 = ((minx,maxy))
        v3 = ((maxx,miny))

        pt0 = region_2d_to_location_3d(region, rv3d, (v0), (cloc)) 
        pt1 = region_2d_to_location_3d(region, rv3d, (v1), (cloc)) 
        pt2 = region_2d_to_location_3d(region, rv3d, (v2), (cloc)) 
        pt3 = region_2d_to_location_3d(region, rv3d, (v3), (cloc)) 
        
        plane.data.vertices[0].co = pt0
        plane.data.vertices[1].co = pt2
        plane.data.vertices[2].co = pt3
        plane.data.vertices[3].co = pt1
    
        plane.data.name = plane.name = name

        bpy.context.view_layer.objects.active = plane
        bpy.data.objects[plane.name].select_set(True)

        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.subdivide(number_cuts=8)

        if res == 2:
            bpy.ops.mesh.subdivide(number_cuts=7)

        elif res == 3:
            bpy.ops.mesh.subdivide(number_cuts=8)

        elif res == 4:
            bpy.ops.mesh.subdivide(number_cuts=8)
            bpy.ops.mesh.subdivide(number_cuts=1)
        
        bpy.ops.object.editmode_toggle()

    bpy.ops.object.shade_smooth()
    
    return plane

# NODES
def get_input_nodes(node, links):
    """Get nodes that are a inputs to the given node"""
    # Get all links going to node.
    input_links = {lnk for lnk in links if lnk.to_node == node}
    # Sort those links, get their input nodes (and avoid doubles!).
    sorted_nodes = []
    done_nodes = set()
    for socket in node.inputs:
        done_links = set()
        for link in input_links:
            nd = link.from_node
            if nd in done_nodes:
                # Node already treated!
                done_links.add(link)
            elif link.to_socket == socket:
                sorted_nodes.append(nd)
                done_links.add(link)
                done_nodes.add(nd)
        input_links -= done_links
    return sorted_nodes

def auto_align_nodes(node_tree):
    
    """Given a shader node tree, arrange nodes neatly relative to the output node."""
    x_gap = 400
    y_gap = 400
    nodes = node_tree.nodes
    links = node_tree.links
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL' or node.type == 'GROUP_OUTPUT':
            output_node = node
            break

    else:  # Just in case there is no output
        return

    def align(to_node):
        from_nodes = get_input_nodes(to_node, links)
        for i, node in enumerate(from_nodes):
            if node.select:
                node.location.x = min(node.location.x, to_node.location.x - x_gap)
                node.location.y = to_node.location.y
                node.location.y -= i * y_gap
                node.location.y += (len(from_nodes) - 1) * y_gap / (len(from_nodes))
                align(node)

    align(output_node)

def clean_node_tree(node_tree):
    """Clear all nodes in a shader node tree except the output.

    Returns the output node
    """
    nodes = node_tree.nodes
    for node in list(nodes):  # copy to avoid altering the loop's data source
        if not node.type == 'OUTPUT_MATERIAL':
            nodes.remove(node)

    return node_tree.nodes[0]

    """copies all links between the nodes in the list to the nodes in the group"""

    for node in nodes:
        #find the corresponding node in the created group
        new_node = group.nodes[ node.name ]

        #enumerate over every link in the nodes inputs
        for i, inp in enumerate( node.inputs ):
            for link in inp.links:
                #find the connected node for the link in the group
                connected_node = group.nodes[ link.from_node.name ]
                #connect the group nodes
                group.links.new( connected_node.outputs[ link.from_socket.name ], new_node.inputs[i] )