import bpy
import os
import mathutils
from . import utils

def clean_node_tree(node_tree):
    nodes = node_tree.nodes
    for node in list(nodes):
        if not node.type == "OUTPUT_MATERIAL":
            nodes.remove(node)
    return node_tree.nodes[0]

def create_material(ob, img_spec, files, dirname, fullpath, photomodeling, decal):
    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None
    disp_spec = None
    metal_spec = None

    diffuse_keywords = bpy.context.preferences.addons[__package__].preferences.diffuse.split(" ")
    roughness_keywords = bpy.context.preferences.addons[__package__].preferences.roughness.split(" ")
    normal_keywords = bpy.context.preferences.addons[__package__].preferences.normal.split(" ")
    opacity_keywords = bpy.context.preferences.addons[__package__].preferences.opacity.split(" ")
    ao_keywords = bpy.context.preferences.addons[__package__].preferences.ao.split(" ")
    displacement_keywords = bpy.context.preferences.addons[__package__].preferences.displacement.split(" ")
    metal_keywords = bpy.context.preferences.addons[__package__].preferences.metal.split(" ")

    # create
    if dirname:
        uv_mode = bpy.context.window_manager.my_toolqt.uv_mode
        if len(files) > 1:
            for f in files:
                for kw in diffuse_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        albedo_spec = bpy.data.images[f.name]
                        img_spec = albedo_spec
                for kw in roughness_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        roughness_spec = bpy.data.images[f.name]
                for kw in normal_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        normal_spec = bpy.data.images[f.name]
                for kw in opacity_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        alpha_spec = bpy.data.images[f.name]
                for kw in ao_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        ao_spec = bpy.data.images[f.name]
                for kw in displacement_keywords:
                    if kw in str(f.name).lower():
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        disp_spec = bpy.data.images[f.name]
                for kw in metal_keywords:
                    if kw in str(f.name).lower():
                        print (f.name)
                        img_path = os.path.join(dirname, f.name)
                        bpy.ops.image.open(filepath=img_path)
                        metal_spec = bpy.data.images[f.name]

    # remake
    else:
        if bpy.context.window_manager.my_toolqt.uv_mode == 'Triplanar':
            uv_mode = 'Triplanar'
        else:
            uv_mode = 'UV'
        img_spec = bpy.data.images[img_spec]
        
        if len(files) > 1:
            for f in files:
                for kw in diffuse_keywords:
                    if kw in str(f).lower():
                        albedo_spec = bpy.data.images[f]
                        img_spec = albedo_spec
                for kw in roughness_keywords:
                    if kw in str(f).lower():
                        roughness_spec = bpy.data.images[f]
                for kw in normal_keywords:
                    if kw in str(f).lower():
                        normal_spec = bpy.data.images[f]
                for kw in opacity_keywords:
                    if kw in str(f).lower():
                        alpha_spec = bpy.data.images[f]
                for kw in ao_keywords:
                    if kw in str(f).lower():
                        ao_spec = bpy.data.images[f]
                for kw in displacement_keywords:
                    if kw in str(f).lower():
                        disp_spec = bpy.data.images[f]
                for kw in metal_keywords:
                    if kw in str(f).lower():
                        metal_spec = bpy.data.images[f]

    material = None
    for mat in ob.data.materials:
        if mat:
            if mat.name == 'TEMP_QT':
                material = mat
                material.name = img_spec.name
    if not material:
        material = bpy.data.materials.new(name=img_spec.name)

    # material settings
    material.blend_method = "HASHED"
    material.shadow_method = "HASHED"
    material.use_screen_refraction = True
    material.show_transparent_back = False
    material.use_nodes = True

    out = clean_node_tree(material.node_tree)
    out.name = "QT_Output"
            
    original_group = bpy.data.node_groups.get("QT_Layer")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Layer")
            ]
        original_group = bpy.data.node_groups["QT_Layer"]

    group = original_group.copy()
    group.name = "QT_Layer_1_" + img_spec.name
    group_node = material.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    
    material.node_tree.links.new(group_node.outputs[0], out.inputs[0])
    material.node_tree.links.new(group_node.outputs[1], out.inputs[2])

    group_node.name = "QT_Layer_1"
    nodes = group_node.node_tree.nodes
    node_tree = group_node.node_tree

    group_node.location = out.location
    group_node.location.x += -500
    
    # diffuse
    diffuse_tex = nodes.get("QT_Diffuse_Tex")
    diffuse_tex.image = img_spec
    if albedo_spec:
        diffuse_tex.image = albedo_spec
    else:
        diffuse_tex.image = img_spec
    diffuse_tex.image.colorspace_settings.name = "sRGB"
        
    # roughness
    rough_tex = nodes.get("QT_Rough_Tex")
    if roughness_spec:
        rough_tex.image = roughness_spec
        rough_tex.image.colorspace_settings.name = "Non-Color"
    else:
        rough_tex.image = img_spec

    # metal
    metal_tex = nodes.get("QT_Metal_Tex")
    if metal_spec:
        metal_tex.image = metal_spec
        metal_tex.image.colorspace_settings.name = "Non-Color"
    
    # bump
    bump_tex = nodes.get("QT_Bump_Tex")
    bump_tex.image = img_spec
    
    # normal
    normal_tex = nodes.get("QT_Normal_Tex")
    normal_strength = nodes.get("QT_Normal_Strength")
    if normal_spec:
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = "Non-Color"
    else:
        normal_strength.inputs[0].default_value = 0

    # ao
    ao_tex = nodes.get("QT_AO_Tex")
    if ao_spec:
        ao_tex.image = ao_spec
        ao_tex.image.colorspace_settings.name = "Non-Color"

    # alpha
    alpha_tex = nodes.get("QT_Alpha_Tex")
    if alpha_spec:
        alpha_tex.image = alpha_spec
        alpha_tex.image.colorspace_settings.name = "Non-Color"
    else:
        alpha_tex.image = img_spec

    # displacement
    disp_tex = nodes.get("QT_Disp_Tex")
    if disp_spec:
        disp_tex.image = disp_spec
        disp_tex.image.colorspace_settings.name = "Non-Color"        

    # mapping
    width, height = img_spec.size
    if width == 0:
        width = 1000
    if height == 0:
        height = 1000
    size = width / height

    diffuse_mapping = nodes.get("QT_Diffuse_Mapping")
    rough_mapping = nodes.get("QT_Rough_Mapping")
    bump_mapping = nodes.get("QT_Bump_Mapping")
    alpha_mapping = nodes.get("QT_Alpha_Mapping")
    disp_mapping = nodes.get("QT_Disp_Mapping")

    core_shader = nodes.get("QT_Shader")

    if photomodeling:
        bump = nodes.get("QT_Bump")
        bump.inputs[0].default_value = 0
        core_shader.inputs[7].default_value = 0

        engine = bpy.context.scene.render.engine
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        material.shadow_method = "NONE"
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.object.visible_shadow = 0
        bpy.context.scene.render.engine = engine
        
        # mapping
        diff = ob.scale[1] - ob.scale[0]

        diffuse_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff
        rough_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff
        bump_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff
        alpha_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff

        diffuse_mapping.inputs[1].default_value[1] = 0.25
        rough_mapping.inputs[1].default_value[1] = 0.25
        bump_mapping.inputs[1].default_value[1] = 0.25
        alpha_mapping.inputs[1].default_value[1] = 0.25

        diffuse_mapping.inputs[3].default_value[0] = ob.scale[0]
        rough_mapping.inputs[3].default_value[0] = ob.scale[0]
        bump_mapping.inputs[3].default_value[0] = ob.scale[0]
        alpha_mapping.inputs[3].default_value[0] = ob.scale[0]

        diffuse_mapping.inputs[3].default_value[1] = ob.scale[1]
        rough_mapping.inputs[3].default_value[1] = ob.scale[1]
        bump_mapping.inputs[3].default_value[1] = ob.scale[1]
        alpha_mapping.inputs[3].default_value[1] = ob.scale[1]

        if disp_spec:
            disp_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff
            disp_mapping.inputs[1].default_value[1] = 0.25
            disp_mapping.inputs[3].default_value[0] = ob.scale[0]
            disp_mapping.inputs[3].default_value[1] = ob.scale[1]

    elif decal:
        bump = nodes.get("QT_Bump")
        bump.inputs[0].default_value = 0
        core_shader.inputs[7].default_value = 0

        engine = bpy.context.scene.render.engine
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        material.shadow_method = "NONE"
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.object.visible_shadow = 0
        bpy.context.scene.render.engine = engine

        if disp_spec:
            disp_mapping.inputs[1].default_value[0] = ob.scale[0] / 2 + diff
            disp_mapping.inputs[1].default_value[1] = 0.25
            disp_mapping.inputs[3].default_value[0] = ob.scale[0]
            disp_mapping.inputs[3].default_value[1] = ob.scale[1]

        if not ob.name.startswith("QT_Ref"):
            diffuse_tex.extension = "CLIP"
            rough_tex.extension = "CLIP"
            bump_tex.extension = "CLIP"
            alpha_tex.extension = "CLIP"
            if ao_spec:
                ao_tex.extension = "CLIP"
            if normal_spec:
                normal_tex.extension = "CLIP"

            # import alpha border
            with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
                data_to.node_groups = [
                    name for name in data_from.node_groups if name.startswith("QT_AlphaBorder")
                ]
            original_group_alpha = bpy.data.node_groups["QT_AlphaBorder"]
            alphaborder = original_group_alpha.copy()
            alphaborder_node = nodes.new(type="ShaderNodeGroup")
            alphaborder_node.node_tree = bpy.data.node_groups[alphaborder.name]

            alpha_clamp = nodes.get("QT_Alpha_Clamp")
            alpha_bright_contrast = nodes.get("QT_Alpha_Bright_Contrast")

            alphaborder_node.location.x = alpha_clamp.location.x - 200
            alphaborder_node.location.y = alpha_clamp.location.y
            alphaborder_node.name = "QT_AlphaBorder"

            node_tree.links.new(alpha_bright_contrast.outputs[0], alphaborder_node.inputs[0])
            node_tree.links.new(alphaborder_node.outputs[0], alpha_clamp.inputs[0])

            alpha_color = alphaborder_node.node_tree.nodes.get("QT_Color")
            alpha_color.layer_name = "QT_Decal_Alpha"

    else:
        diffuse_mapping.inputs[3].default_value[1] = 1 / size
        rough_mapping.inputs[3].default_value[1] = 1 / size
        bump_mapping.inputs[3].default_value[1] = 1 / size
        alpha_mapping.inputs[3].default_value[1] = 1 / size
        if disp_spec:
            disp_mapping.inputs[3].default_value[1] = 1 / size
            
    # UV setup
    coord = nodes.get("QT_Coord")
    uv = nodes.get("QT_UV")
    uv_add = nodes.get("QT_UV_Add")
    if decal:
        coord.label = "UV"
        node_tree.links.new(coord.outputs[2], uv_add.inputs[0])
    elif uv_mode == "Procedural Box" or photomodeling:
        uv.uv_map = "QT_UV_Box_Layer"
        coord.label = "Procedural Box"
    elif uv_mode == "View":
        uv.uv_map = "QT_UV_View_Layer_1"
        coord.label = "View"
    elif uv_mode == "UV":
        coord.label = "UV"
        node_tree.links.new(coord.outputs[2], uv_add.inputs[0])
    elif uv_mode == "Triplanar":
        coord.label = "Triplanar"
        node_tree.links.new(coord.outputs[0], uv_add.inputs[0])
        diffuse_tex.projection = "BOX"
        diffuse_tex.projection_blend = 0.3
        rough_tex.projection = "BOX"
        rough_tex.projection_blend = 0.3
        alpha_tex.projection = "BOX"
        alpha_tex.projection_blend = 0.3
        if bump_tex:
            bump_tex.projection = "BOX"
            bump_tex.projection_blend = 0.3
        if normal_tex:
            normal_tex.projection = "BOX"
            normal_tex.projection_blend = 0.3
        if ao_tex:
            ao_tex.projection = "BOX"
            ao_tex.projection_blend = 0.3
        if disp_tex:
            disp_tex.projection = "BOX"
            disp_tex.projection_blend = 0.3
                        
    render = bpy.context.scene.render.engine
    if render != "CYCLES":
        bpy.context.scene.render.engine = "CYCLES"
    material.cycles.displacement_method = 'BOTH'
    bpy.context.scene.render.engine = render

    material.name = "QT_" + material.name
    if ob.data.materials:
        ob.data.materials[-1] = material
    else:
        ob.data.materials.append(material)
    bpy.ops.object.make_links_data(type="MATERIAL")
    px, py = img_spec.size
    if px == 0:
        px = 1000
    if py == 0:
        py = 1000
    bpy.context.window_manager.my_toolqt.active_layer = 1
    bpy.context.window_manager.my_toolqt.active_map = 1
    bpy.context.window_manager.my_toolqt.total_materials = len(ob.data.materials)
    return material

def new_layer(ob, img_spec, files, dirname, fullpath, layer_type):
    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None
    disp_spec = None
    metal_spec = None

    diffuse_keywords = bpy.context.preferences.addons[__package__].preferences.diffuse.split(" ")
    roughness_keywords = bpy.context.preferences.addons[__package__].preferences.roughness.split(" ")
    normal_keywords = bpy.context.preferences.addons[__package__].preferences.normal.split(" ")
    opacity_keywords = bpy.context.preferences.addons[__package__].preferences.opacity.split(" ")
    ao_keywords = bpy.context.preferences.addons[__package__].preferences.ao.split(" ")
    displacement_keywords = bpy.context.preferences.addons[__package__].preferences.displacement.split(" ")
    metal_keywords = bpy.context.preferences.addons[__package__].preferences.metal.split(" ")

    if len(files) > 1:
        for f in files:
            for kw in diffuse_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    albedo_spec = bpy.data.images[f.name]
                    img_spec = albedo_spec
            for kw in roughness_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    roughness_spec = bpy.data.images[f.name]
            for kw in normal_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    normal_spec = bpy.data.images[f.name]
            for kw in opacity_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    alpha_spec = bpy.data.images[f.name]
            for kw in ao_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    ao_spec = bpy.data.images[f.name]
            for kw in displacement_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]
            for kw in metal_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    metal_spec = bpy.data.images[f.name]

    for m in ob.data.materials:
        if m:
            if m.name.startswith("QT_"):
                material = m
                
    bpy.context.window_manager.my_toolqt.active_layer += 1
    bpy.context.window_manager.my_toolqt.total_layers += 1
    bpy.context.window_manager.my_toolqt.active_map = 1
                
    original_group = bpy.data.node_groups.get("QT_NewLayer")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_NewLayer")
            ]
        original_group = bpy.data.node_groups["QT_NewLayer"]

    group = original_group.copy()
    group_node = material.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
        
    out = material.node_tree.nodes.get("QT_Output")
    material.node_tree.links.new(group_node.outputs[0], out.inputs[0])
    material.node_tree.links.new(group_node.outputs[1], out.inputs[2])

    nodes = group_node.node_tree.nodes
    node_tree = group_node.node_tree

    # layers
    layer1 = material.node_tree.nodes.get("QT_Layer_1")
    layer2 = material.node_tree.nodes.get("QT_Layer_2")
    layer3 = material.node_tree.nodes.get("QT_Layer_3")
    layer4 = material.node_tree.nodes.get("QT_Layer_4")
    layer5 = material.node_tree.nodes.get("QT_Layer_5")

    if layer1:
        if layer1 != group_node:
            material.node_tree.links.new(layer1.outputs[0], group_node.inputs[0])
            material.node_tree.links.new(layer1.outputs[1], group_node.inputs[1])
            
    if layer2:
        if layer2 != group_node:
            material.node_tree.links.new(layer2.outputs[0], group_node.inputs[0])
            material.node_tree.links.new(layer2.outputs[1], group_node.inputs[1])
    if layer3:
        if layer3 != group_node:
            material.node_tree.links.new(layer3.outputs[0], group_node.inputs[0])
            material.node_tree.links.new(layer3.outputs[1], group_node.inputs[1])
    if layer4:
        if layer4 != group_node:
            material.node_tree.links.new(layer4.outputs[0], group_node.inputs[0])
            material.node_tree.links.new(layer4.outputs[1], group_node.inputs[1])
    if layer5:
        if layer5 != group_node:
            material.node_tree.links.new(layer5.outputs[0], group_node.inputs[0])
            material.node_tree.links.new(layer5.outputs[1], group_node.inputs[1])

    if bpy.context.window_manager.my_toolqt.active_layer == 2:
        if layer2:
            layer2.name = "QT_Layer_3"
        if layer3:
            layer3.name = "QT_Layer_4"
        if layer4:
            layer3.name = "QT_Layer_5"
    if bpy.context.window_manager.my_toolqt.active_layer == 3:
        if layer3:
            layer3.name = "QT_Layer_4"
        if layer4:
            layer3.name = "QT_Layer_5"
    if bpy.context.window_manager.my_toolqt.active_layer == 4:
        if layer4:
            layer4.name = "QT_Layer_5"
            
    group.name = "QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer)

    # diffuse
    diffuse_tex = nodes.get("QT_Diffuse_Tex")
    diffuse_tex.image = img_spec
    if albedo_spec:
        diffuse_tex.image = albedo_spec
    else:
        diffuse_tex.image = img_spec
    diffuse_tex.image.colorspace_settings.name = "sRGB"
        
    # roughness
    rough_tex = nodes.get("QT_Rough_Tex")
    if roughness_spec:
        rough_tex.image = roughness_spec
        rough_tex.image.colorspace_settings.name = "Non-Color"
    else:
        rough_tex.image = img_spec
    
    # bump
    bump_tex = nodes.get("QT_Bump_Tex")
    bump_tex.image = img_spec
    
    # normal
    normal_tex = nodes.get("QT_Normal_Tex")
    normal_strength = nodes.get("QT_Normal_Strength")
    if normal_spec:
        normal_tex.image = normal_spec
        normal_tex.image.colorspace_settings.name = "Non-Color"
    else:
        normal_strength.inputs[0].default_value = 0

    # metal
    metal_tex = nodes.get("QT_Metal_Tex")
    if metal_spec:
        metal_tex.image = metal_spec
        metal_tex.image.colorspace_settings.name = "Non-Color"

    # ao
    ao_tex = nodes.get("QT_AO_Tex")
    if ao_spec:
        ao_tex.image = ao_spec
        ao_tex.image.colorspace_settings.name = "Non-Color"

    # alpha
    alpha_tex = nodes.get("QT_Alpha_Tex")
    if alpha_spec:
        alpha_tex.image = alpha_spec
        alpha_tex.image.colorspace_settings.name = "Non-Color"
    else:
        alpha_tex.image = img_spec

    # displacement
    disp_tex = nodes.get("QT_Disp_Tex")
    if disp_spec:
        disp_tex.image = disp_spec
        disp_tex.image.colorspace_settings.name = "Non-Color"        
            
    # mapping
    width, height = img_spec.size
    if width == 0:
        width = 1000
    if height == 0:
        height = 1000
    size = width / height
    
    # mapping
    diffuse_mapping = nodes.get("QT_Diffuse_Mapping")
    rough_mapping = nodes.get("QT_Rough_Mapping")
    bump_mapping = nodes.get("QT_Bump_Mapping")
    alpha_mapping = nodes.get("QT_Alpha_Mapping")
    diffuse_mapping.inputs[3].default_value[1] = 1 / size
    rough_mapping.inputs[3].default_value[1] = 1 / size
    bump_mapping.inputs[3].default_value[1] = 1 / size
    alpha_mapping.inputs[3].default_value[1] = 1 / size
    if disp_spec:
        disp_mapping = nodes.get("QT_Disp_Mapping")
        disp_mapping.inputs[3].default_value[1] = 1 / size

    core_shader = nodes.get("QT_Shader")

    # UV setup
    uv_add = nodes.get("QT_UV_Add")
    coord = nodes.get("QT_Coord")
    uv = nodes.get("QT_UV")

    if layer_type == 'Procedural Box':
        uv.uv_map = "QT_UV_Box_Layer"
        coord.label = "Procedural Box"
    elif layer_type == "View":
        uv.uv_map = "QT_UV_View_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer)
        coord.label = "View"
    elif layer_type == "UV":
        coord.label = "UV"
        node_tree.links.new(coord.outputs[2], uv_add.inputs[0])
    elif layer_type == "Triplanar":
        coord.label = "Triplanar"
        node_tree.links.new(coord.outputs[0], uv_add.inputs[0])
        diffuse_tex.projection = "BOX"
        diffuse_tex.projection_blend = 0.3
        rough_tex.projection = "BOX"
        rough_tex.projection_blend = 0.3
        alpha_tex.projection = "BOX"
        alpha_tex.projection_blend = 0.3
        if bump_tex:
            bump_tex.projection = "BOX"
            bump_tex.projection_blend = 0.3
        if normal_tex:
            normal_tex.projection = "BOX"
            normal_tex.projection_blend = 0.3
        if ao_tex:
            ao_tex.projection = "BOX"
            ao_tex.projection_blend = 0.3
        if disp_tex:
            disp_tex.projection = "BOX"
            disp_tex.projection_blend = 0.3
            
    # align
    utils.auto_align_nodes(material.node_tree)
    return material

def replace(ob, img_spec, files, dirname):
    albedo_spec = None
    roughness_spec = None
    normal_spec = None
    ao_spec = None
    alpha_spec = None
    disp_spec = None
    metal_spec = None

    diffuse_keywords = bpy.context.preferences.addons[__package__].preferences.diffuse.split(" ")
    roughness_keywords = bpy.context.preferences.addons[__package__].preferences.roughness.split(" ")
    normal_keywords = bpy.context.preferences.addons[__package__].preferences.normal.split(" ")
    opacity_keywords = bpy.context.preferences.addons[__package__].preferences.opacity.split(" ")
    ao_keywords = bpy.context.preferences.addons[__package__].preferences.ao.split(" ")
    displacement_keywords = bpy.context.preferences.addons[__package__].preferences.displacement.split(" ")
    metal_keywords = bpy.context.preferences.addons[__package__].preferences.metal.split(" ")

    if len(files) > 1:
        for f in files:
            for kw in diffuse_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    albedo_spec = bpy.data.images[f.name]
                    img_spec = albedo_spec
            for kw in roughness_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    roughness_spec = bpy.data.images[f.name]
            for kw in normal_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    normal_spec = bpy.data.images[f.name]
            for kw in opacity_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    alpha_spec = bpy.data.images[f.name]
            for kw in ao_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    ao_spec = bpy.data.images[f.name]
            for kw in displacement_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    disp_spec = bpy.data.images[f.name]
            for kw in metal_keywords:
                if kw in str(f.name).lower():
                    img_path = os.path.join(dirname, f.name)
                    bpy.ops.image.open(filepath=img_path)
                    metal_spec = bpy.data.images[f.name]

    mat = ob.material_slots[bpy.context.window_manager.my_toolqt.active_material].material
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))

    if bpy.context.window_manager.my_toolqt.active_map == 1:
        diffuse_tex = layer.node_tree.nodes.get("QT_Diffuse_Tex")
        if albedo_spec:
            diffuse_tex.image = albedo_spec
        else:
            diffuse_tex.image = img_spec

        rough_tex = layer.node_tree.nodes.get("QT_Rough_Tex")
        if roughness_spec:
            rough_tex.image = roughness_spec
        else:
            rough_tex.image = img_spec

        bump_tex = layer.node_tree.nodes.get("QT_Bump_Tex")
        if albedo_spec:
            bump_tex.image = albedo_spec
        else:
            bump_tex.image = img_spec

        alpha_tex = layer.node_tree.nodes.get("QT_Alpha_Tex")
        if alpha_tex.image:
            if alpha_spec:
                alpha_tex.image = alpha_spec
            else:
                if albedo_spec:
                    alpha_tex.image = albedo_spec
                else:
                    alpha_tex.image = img_spec

        normal_tex = layer.node_tree.nodes.get("QT_Normal_Tex")
        if normal_tex.image:
            if normal_spec:
                normal_tex.image = normal_spec

        ao_tex = layer.node_tree.nodes.get("QT_AO_Tex")
        if ao_tex.image:
            if ao_spec:
                ao_tex.image = ao_spec

        disp_tex = layer.node_tree.nodes.get("QT_Disp_Tex")
        if disp_tex.image:
            if disp_spec:
                disp_tex.image = disp_spec
            else:
                disp_tex.image = img_spec

        metal_tex = layer.node_tree.nodes.get("QT_Metal_Tex")
        if metal_spec:
            metal_tex.image = metal_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 2:
        rough_tex = layer.node_tree.nodes.get("QT_Rough_Tex")
        if roughness_spec:
            rough_tex.image = roughness_spec
        else:
            rough_tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 3:
        bump_tex = layer.node_tree.nodes.get("QT_Bump_Tex")
        if albedo_spec:
            bump_tex.image = albedo_spec
        else:
            bump_tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 4:
        mask = layer.node_tree.nodes.get("QT_Texture_Mask")
        if mask:
            tex = mask.node_tree.nodes.get("QT_Tex")
            tex.image = img_spec
        mask = layer.node_tree.nodes.get("QT_Depth_Mask")
        if mask:
            tex = mask.node_tree.nodes.get("QT_Tex")
            tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 5:
        alpha_tex = layer.node_tree.nodes.get("QT_Alpha_Tex")
        if alpha_spec:
            alpha_tex.image = alpha_spec
        else:
            alpha_tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 6:
        mask = layer.node_tree.nodes.get("QT_Smudge")
        if mask:
            tex = mask.node_tree.nodes.get("QT_Tex")
            tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 7:
        mask = layer.node_tree.nodes.get("QT_Variation")
        if mask:
            tex = mask.node_tree.nodes.get("QT_Tex")
            tex.image = img_spec

    elif bpy.context.window_manager.my_toolqt.active_map == 0:
        disp_tex = layer.node_tree.nodes.get("QT_Disp_Tex")
        if disp_tex.image:
            if disp_spec:
                disp_tex.image = disp_spec
            else:
                disp_tex.image = img_spec
    
def texture_mask(ob, img_spec, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Texture_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Texture_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Texture_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    coord = layer.node_tree.nodes.get("QT_Coord")
    mapping = layer.node_tree.nodes.get("QT_UV_Add")
    mix = layer.node_tree.nodes.get("QT_Mix")
    
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Texture_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    mask_tex = mask.node_tree.nodes.get("QT_Tex")
    mask_tex.image = img_spec
    mask_tex.image.colorspace_settings.name = "sRGB"
    if coord.label == "Triplanar":
        mask_tex.projection = "BOX"
            
    layer.node_tree.links.new(mapping.outputs[0], mask.inputs[0])
    layer.node_tree.links.new(mask.outputs[0], mix.inputs[0])
    
    out = layer.node_tree.nodes.get("OUT")
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])

def edges_mask(ob, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Edge_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Edge_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Edge_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    coord = layer.node_tree.nodes.get("QT_Coord")
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    mix = layer.node_tree.nodes.get("QT_Mix")
    out = layer.node_tree.nodes.get("OUT")
    img_spec = diffuse.image
         
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Edge_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    layer.node_tree.links.new(mix.inputs[0], mask.outputs[0])
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])
    
def dirt_mask(ob, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Dirt_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Dirt_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Dirt_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    coord = layer.node_tree.nodes.get("QT_Coord")
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    mix = layer.node_tree.nodes.get("QT_Mix")
    out = layer.node_tree.nodes.get("OUT")
    img_spec = diffuse.image
         
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Dirt_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    layer.node_tree.links.new(mix.inputs[0], mask.outputs[0])
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])
    
def depth_mask(ob, img_spec, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Depth_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Depth_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Depth_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    coord = layer.node_tree.nodes.get("QT_Coord")
    mapping = layer.node_tree.nodes.get("QT_UV_Add")
    mix = layer.node_tree.nodes.get("QT_Mix")
    
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Depth_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    mask_tex = mask.node_tree.nodes.get("QT_Tex")
    mask_tex.image = img_spec
    mask_tex.image.colorspace_settings.name = "sRGB"
    if coord.label == "Triplanar":
        mask_tex.projection = "BOX"
            
    layer.node_tree.links.new(mapping.outputs[0], mask.inputs[0])
    layer.node_tree.links.new(mask.outputs[0], mix.inputs[0])
    
    out = layer.node_tree.nodes.get("OUT")
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])

def vertex_mask(ob, mat, vertex):
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    color = layer.node_tree.nodes.new("ShaderNodeVertexColor")
    color.name = "QT_Color_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer)
    color.layer_name = vertex
    out = layer.node_tree.nodes.get("OUT")
    mix = layer.node_tree.nodes.get("QT_Mix")
    layer.node_tree.links.new(color.outputs[0], out.inputs[0])    
    layer.node_tree.links.new(mix.inputs[0], color.outputs[0])
    color.location = mix.location
    color.location.x -= 300
    color.location.y -= 300
    
def height_mask(ob, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Height_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Height_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Height_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    mix = layer.node_tree.nodes.get("QT_Mix")
    out = layer.node_tree.nodes.get("OUT")
    coord = layer.node_tree.nodes.get("QT_Coord")        
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    img_spec = diffuse.image
    
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Height_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    layer.node_tree.links.new(mix.inputs[0], mask.outputs[0])
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])
    
def normal_mask(ob, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 4
    
    original_group = bpy.data.node_groups.get("QT_Normal_Mask")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Normal_Mask")
            ]
        original_group = bpy.data.node_groups["QT_Normal_Mask"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    coord = layer.node_tree.nodes.get("QT_Coord")
    mix = layer.node_tree.nodes.get("QT_Mix")
    out = layer.node_tree.nodes.get("OUT")
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    img_spec = diffuse.image
         
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Mask_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Normal_Mask"
    
    mask = group_node
    mask.location = coord.location
    mask.location.x += 300
    
    layer.node_tree.links.new(mix.inputs[0], mask.outputs[0])
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])

def randomize_per_object(ob, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 8
    original_group = bpy.data.node_groups.get("QT_RandColor")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_RandColor")
            ]
        original_group = bpy.data.node_groups["QT_RandColor"]
    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    rough_bright_contrast = layer.node_tree.nodes.get("QT_Rough_Bright_Contrast")
    diffuse_hue_sat = layer.node_tree.nodes.get("QT_Diffuse_Hue_Sat")
    roughness = layer.node_tree.nodes.get("QT_Rough_Clamp")
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    img_spec = diffuse.image
        
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_RandColor_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_RandColor"
    
    mask = group_node
    mask.location = diffuse.location
    mask.location.x += 300
    mask.location.y += 300

    variation = layer.node_tree.nodes.get("QT_Variation")
    if variation:
        diffuse = variation
    
    layer.node_tree.links.new(mask.inputs[0], diffuse.outputs[0])
    layer.node_tree.links.new(diffuse_hue_sat.inputs[4], mask.outputs[0])

    original_group = bpy.data.node_groups.get("QT_RandRough")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_RandRough")
            ]
        original_group = bpy.data.node_groups["QT_RandRough"]
    group = original_group.copy()

    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_RandRough_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_RandRough"
    
    mask = group_node
    mask.location = roughness.location
    mask.location.y += 300
    
    layer.node_tree.links.new(mask.inputs[0], rough_bright_contrast.outputs[0])
    layer.node_tree.links.new(roughness.inputs[0], mask.outputs[0])

def variation(ob, img_spec, fullpath, mat):
    bpy.context.window_manager.my_toolqt.active_map = 7
    
    original_group = bpy.data.node_groups.get("QT_Variation")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Variation")
            ]
        original_group = bpy.data.node_groups["QT_Variation"]

    group = original_group.copy()
    
    layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))
    diffuse = layer.node_tree.nodes.get("QT_Diffuse_Tex")
    diffuse_hue_sat = layer.node_tree.nodes.get("QT_Diffuse_Hue_Sat")
    coord = layer.node_tree.nodes.get("QT_Coord")
    mapping = layer.node_tree.nodes.get("QT_UV_Add")
    
    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    group.name = "QT_Variation_" + str(bpy.context.window_manager.my_toolqt.active_layer) + "_" + img_spec.name
    group_node.name = "QT_Variation"
    
    mask = group_node
    mask.location = diffuse.location
    mask.location.x += 300
    
    mask_tex = mask.node_tree.nodes.get("QT_Tex")
    mask_tex.image = img_spec
    mask_tex.image.colorspace_settings.name = "sRGB"
    if coord.label == "Triplanar":
        mask_tex.projection = "BOX"

    randomization = layer.node_tree.nodes.get("QT_Randomization")
    if randomization:
        diffuse = randomization
            
    layer.node_tree.links.new(mapping.outputs[0], mask.inputs[0])
    layer.node_tree.links.new(diffuse.outputs[0], mask.inputs[9])
    layer.node_tree.links.new(mask.outputs[0], diffuse_hue_sat.inputs[4])

    out = layer.node_tree.nodes.get("OUT")
    layer.node_tree.links.new(out.inputs[0], mask.outputs[0])

def detiling(ob, fullpath, mat):
        bpy.context.window_manager.my_toolqt.active_map = 6
        layer = mat.node_tree.nodes.get("QT_Layer_" + str(bpy.context.window_manager.my_toolqt.active_layer))

        # get all mapping and texture nodes
        diffuse_mapping = layer.node_tree.nodes.get("QT_Diffuse_Mapping")
        ao_mapping = layer.node_tree.nodes.get("QT_Diffuse_Mapping")
        rough_mapping = layer.node_tree.nodes.get("QT_Rough_Mapping")
        normal_mapping = layer.node_tree.nodes.get("QT_Normal_Mapping")
        bump_mapping = layer.node_tree.nodes.get("QT_Bump_Mapping")
        disp_mapping = layer.node_tree.nodes.get("QT_Disp_Mapping")

        diffuse_tex = layer.node_tree.nodes.get("QT_Diffuse_Tex")
        ao_tex = layer.node_tree.nodes.get("QT_AO_Tex")
        rough_tex = layer.node_tree.nodes.get("QT_Rough_Tex")
        normal_tex = layer.node_tree.nodes.get("QT_Normal_Tex")
        bump_tex = layer.node_tree.nodes.get("QT_Bump_Tex")
        disp_tex = layer.node_tree.nodes.get("QT_Disp_Tex")
            
        mappings = [
            diffuse_mapping,
            ao_mapping,
            rough_mapping,
            normal_mapping,
            bump_mapping,
            disp_mapping,
        ]
        diffuses = [
            diffuse_tex,
            ao_tex,
            rough_tex,
            normal_tex,
            bump_tex,
            disp_tex,
        ]

        node = None
        for n in layer.node_tree.nodes:
            if n.name.startswith("QT_Detiling"):
                node = n
                break

        if node:
            for n in layer.node_tree.nodes:
                if n.name.startswith("QT_Detiling"):
                    layer.node_tree.nodes.remove(n)
            for mapping, diffuse in zip(mappings, diffuses):
                if mapping:
                    layer.node_tree.links.new(mapping.outputs[0], diffuse.inputs[0])
        else:
            for mapping, diffuse in zip(mappings, diffuses):
                if mapping:
                    with bpy.data.libraries.load(fullpath, link=False) as (
                        data_from,
                        data_to,
                    ):
                        data_to.node_groups = [
                            name
                            for name in data_from.node_groups
                            if name.startswith("QT_Detiling")
                        ]
                    original_group = bpy.data.node_groups["QT_Detiling"]
                    group = original_group.copy()
                    group_node = layer.node_tree.nodes.new(type="ShaderNodeGroup")
                    group_node.node_tree = bpy.data.node_groups[group.name]
                    group.name = "QT_Detiling_" + str(bpy.context.window_manager.my_toolqt.active_layer)
                    group_node.name = "QT_Detiling"
                    detiling = group_node
                    detiling.location = mapping.location
                    detiling.location.x += 300

                    layer.node_tree.links.new(mapping.outputs[0], detiling.inputs[0])
                    layer.node_tree.links.new(detiling.outputs[0], diffuse.inputs[0])

def duplicate(mat, out):
    layer1 = mat.node_tree.nodes.get("QT_Layer_1")
    layer2 = mat.node_tree.nodes.get("QT_Layer_2")
    layer3 = mat.node_tree.nodes.get("QT_Layer_3")
    layer4 = mat.node_tree.nodes.get("QT_Layer_4")

    if bpy.context.window_manager.my_toolqt.active_layer == 1:
        group = layer1.node_tree.copy()
        group_node = mat.node_tree.nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = bpy.data.node_groups[group.name]

        group_node.location.x += 100
        out.location.x += 100

        if layer4:
            layer4.name = 'QT_Layer_5'
            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_5", 1)
            layer4.node_tree.name = new_name
        if layer3:
            layer3.name = 'QT_Layer_4'
            new_name = layer3.node_tree.name.replace("QT_Layer_3", "QT_Layer_4", 1)
            layer3.node_tree.name = new_name
        if layer2:
            layer2.name = 'QT_Layer_3'
            new_name = layer2.node_tree.name.replace("QT_Layer_2", "QT_Layer_3", 1)
            layer2.node_tree.name = new_name
        new_name = group.name.replace("QT_Layer_1", "QT_Layer_2", 1)
        group.name = new_name
        new_name = group.name.replace(".001", "", 1)
        group.name = new_name
        group_node.name = "QT_Layer_2"

        # create inputs
        group_node.node_tree.interface.new_socket(name="NodeSocketShader", description="Shader", in_out='INPUT', socket_type="NodeSocketShader")
        group_node.node_tree.interface.new_socket(name="NodeSocketVector", description="Vector", in_out='INPUT', socket_type="NodeSocketVector")

        # get nodes I need
        shader = group_node.node_tree.nodes.get("QT_Shader")
        group_out = group_node.node_tree.nodes.get("OUT")
        disp = group_node.node_tree.nodes.get("QT_Disp")

        # create necessary nodes for the new layer
        group_input = group_node.node_tree.nodes.new(type="NodeGroupInput")
        group_input.name = 'IN'
        group_input.location = shader.location - mathutils.Vector((0,1200))
        mix = group_node.node_tree.nodes.new(type="ShaderNodeMixShader")
        mix.name = 'QT_Mix'
        mix.inputs[0].default_value = 1
        mix.location = shader.location + mathutils.Vector((400,0))
        disp_mix = group_node.node_tree.nodes.new(type="ShaderNodeMix")
        disp_mix.name = 'QT_Disp_Mix'
        disp_mix.data_type = 'VECTOR'
        disp_mix.location = mix.location - mathutils.Vector((0,800))

        # connect
        group_node.node_tree.links.new(shader.outputs[0], mix.inputs[2])
        group_node.node_tree.links.new(group_input.outputs[0], mix.inputs[1])
        group_node.node_tree.links.new(mix.outputs[0], group_out.inputs[0])

        group_node.node_tree.links.new(group_input.outputs[1], disp_mix.inputs[4])
        group_node.node_tree.links.new(disp.outputs[0], disp_mix.inputs[5])
        group_node.node_tree.links.new(disp_mix.outputs[1], group_out.inputs[1])

    if bpy.context.window_manager.my_toolqt.active_layer == 2:
        group = layer2.node_tree.copy()
        group_node = mat.node_tree.nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = bpy.data.node_groups[group.name]

        group_node.location.x += 100
        out.location.x += 100

        if layer4:
            layer4.name = 'QT_Layer_5'
            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_5", 1)
            layer4.node_tree.name = new_name
        if layer3:
            layer3.name = 'QT_Layer_4'
            new_name = layer3.node_tree.name.replace("QT_Layer_3", "QT_Layer_4", 1)
            layer3.node_tree.name = new_name

        new_name = group.name.replace("QT_Layer_2", "QT_Layer_3", 1)
        group.name = new_name
        new_name = group.name.replace(".001", "", 1)
        group.name = new_name
        group_node.name = "QT_Layer_3"

    if bpy.context.window_manager.my_toolqt.active_layer == 3:
        group = layer3.node_tree.copy()
        group_node = mat.node_tree.nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = bpy.data.node_groups[group.name]

        group_node.location.x += 100
        out.location.x += 100

        if layer4:
            layer4.name = 'QT_Layer_5'
            new_name = layer4.node_tree.name.replace("QT_Layer_4", "QT_Layer_5", 1)
            layer4.node_tree.name = new_name

        new_name = group.name.replace("QT_Layer_3", "QT_Layer_4", 1)
        group.name = new_name
        new_name = group.name.replace(".001", "", 1)
        group.name = new_name
        group_node.name = "QT_Layer_4"

    if bpy.context.window_manager.my_toolqt.active_layer == 4:
        group = layer4.node_tree.copy()
        group_node = mat.node_tree.nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = bpy.data.node_groups[group.name]

        group_node.location.x += 100
        out.location.x += 100

        new_name = group.name.replace("QT_Layer_4", "QT_Layer_5", 1)
        group.name = new_name
        new_name = group.name.replace(".001", "", 1)
        group.name = new_name
        group_node.name = "QT_Layer_5"

    bpy.context.window_manager.my_toolqt.total_layers += 1
    bpy.context.window_manager.my_toolqt.active_layer += 1

    layer1 = mat.node_tree.nodes.get("QT_Layer_1")
    layer2 = mat.node_tree.nodes.get("QT_Layer_2")
    layer3 = mat.node_tree.nodes.get("QT_Layer_3")
    layer4 = mat.node_tree.nodes.get("QT_Layer_4")
    layer5 = mat.node_tree.nodes.get("QT_Layer_5")

    mat.node_tree.links.new(layer1.outputs[0], layer2.inputs[0])
    mat.node_tree.links.new(layer1.outputs[1], layer2.inputs[1])
    mat.node_tree.links.new(layer2.outputs[0], out.inputs[0])
    mat.node_tree.links.new(layer2.outputs[1], out.inputs[2])

    if layer3:
        mat.node_tree.links.new(layer2.outputs[0], layer3.inputs[0])
        mat.node_tree.links.new(layer2.outputs[1], layer3.inputs[1])
        mat.node_tree.links.new(layer3.outputs[0], out.inputs[0])
        mat.node_tree.links.new(layer3.outputs[1], out.inputs[2])
    if layer4:
        mat.node_tree.links.new(layer3.outputs[0], layer4.inputs[0])
        mat.node_tree.links.new(layer3.outputs[1], layer4.inputs[1])
        mat.node_tree.links.new(layer4.outputs[0], out.inputs[0])
        mat.node_tree.links.new(layer4.outputs[1], out.inputs[2])
    if layer5:
        mat.node_tree.links.new(layer5.outputs[0], out.inputs[0])
        mat.node_tree.links.new(layer5.outputs[1], out.inputs[2])

def create_paintover(ob, fullpath, width, height):
    material = bpy.data.materials.new(name="QT_Paintover")
    material.blend_method = "HASHED"
    engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    material.shadow_method = "NONE"
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.object.visible_shadow = 0
    bpy.context.scene.render.engine = engine
    material.use_screen_refraction = True
    material.show_transparent_back = False
    material.use_nodes = True
    out = clean_node_tree(material.node_tree)
    out.name = "QT_Output"
    ob.data.materials.append(material)

    original_group = bpy.data.node_groups.get("QT_Paintover")
    if not original_group:
        with bpy.data.libraries.load(fullpath, link=False) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups if name == ("QT_Paintover")
            ]
        original_group = bpy.data.node_groups["QT_Paintover"]

    group = original_group.copy()
    group.name = "QT_Paintover"
    group_node = material.node_tree.nodes.new(type="ShaderNodeGroup")
    group_node.node_tree = bpy.data.node_groups[group.name]
    material.node_tree.links.new(group_node.outputs[0], out.inputs[0])

    image = group_node.node_tree.nodes.get("Image")
    res = bpy.context.window_manager.my_toolqt.paintover
    x = res * width
    y = res * height
    tex = bpy.data.images.new("QT_Paintover", width=x, height=y)
    image.image = tex
    image.image.colorspace_settings.name = 'sRGB'

def baked_material(node_tree):
    out_node = clean_node_tree(node_tree)

    # recreate node setup with baked textures
    shader = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    node_tree.links.new(shader.outputs[0], out_node.inputs[0])

    # diffuse
    bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + "DIFFUSE" + ".png" )
    bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )

    bpy.ops.image.open(filepath=bake_path)
    bpy.data.images[bake_spec].filepath = bake_path
    diffuse_spec = bpy.data.images[bake_spec]

    diffuse_tex = node_tree.nodes.new("ShaderNodeTexImage")
    diffuse_tex.image = diffuse_spec
    diffuse_tex.show_texture = True

    node_tree.links.new(diffuse_tex.outputs[0], shader.inputs[0])

    # roughness
    bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + "ROUGHNESS" + ".png" )
    bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )

    bpy.ops.image.open(filepath=bake_path)
    bpy.data.images[bake_spec].filepath = bake_path
    rough_spec = bpy.data.images[bake_spec]

    rough_tex = node_tree.nodes.new("ShaderNodeTexImage")
    rough_tex.image = rough_spec
    rough_tex.show_texture = True

    rough_tex.image.colorspace_settings.name = "Non-Color"

    node_tree.links.new(rough_tex.outputs[0], shader.inputs[2])

    # normal
    bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + "NORMAL" + ".png" )
    bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )

    bpy.ops.image.open(filepath=bake_path)
    bpy.data.images[bake_spec].filepath = bake_path
    normal_spec = bpy.data.images[bake_spec]

    normal_tex = node_tree.nodes.new("ShaderNodeTexImage")
    normal_tex.image = normal_spec
    normal_tex.show_texture = True

    normal_tex.image.colorspace_settings.name = "Non-Color"

    normal_strength = node_tree.nodes.new("ShaderNodeNormalMap")
    node_tree.links.new(normal_tex.outputs[0], normal_strength.inputs[1])
    node_tree.links.new(normal_strength.outputs[0], shader.inputs[22])

    # metal
    bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + "METAL" + ".png" )
    bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )

    try:
        bpy.ops.image.open(filepath=bake_path)
        bpy.data.images[bake_spec].filepath = bake_path
        metal_spec = bpy.data.images[bake_spec]

        metal_tex = node_tree.nodes.new("ShaderNodeTexImage")
        metal_tex.image = metal_spec
        metal_tex.show_texture = True
        metal_tex.image.colorspace_settings.name = "Non-Color"

        node_tree.links.new(metal_tex.outputs[0], shader.inputs[1])
    except Exception:
        pass

    # alpha
    bake_spec = ( bpy.context.window_manager.my_toolqt.bakename + "_" + "ALPHA" + ".png" )
    bake_path = os.path.join( bpy.context.window_manager.my_toolqt.bakepath, bake_spec )

    bpy.ops.image.open(filepath=bake_path)
    bpy.data.images[bake_spec].filepath = bake_path
    alpha_spec = bpy.data.images[bake_spec]

    alpha_tex = node_tree.nodes.new("ShaderNodeTexImage")
    alpha_tex.image = alpha_spec
    alpha_tex.show_texture = True
    alpha_tex.image.colorspace_settings.name = "Non-Color"

    node_tree.links.new(alpha_tex.outputs[1], shader.inputs[4])

    utils.auto_align_nodes(node_tree)