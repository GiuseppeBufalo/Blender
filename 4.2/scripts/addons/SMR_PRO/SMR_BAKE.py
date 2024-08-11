#pylint: disable=import-error, relative-beyond-top-level
import bpy
import os
from . mat_functions import get_mat_data, add_smr_uv, check_node, followLinks
from . smr_common import ShowMessageBox
from . influence_functions import stop_preview
from . SMR_CALLBACK import SMR_callback
from pathlib import Path

import threading

# exclusion_list = []

# class StoppableThread(threading.Thread):
#     """Thread class with a stop() method. The thread itself has to check
#     regularly for the stopped() condition."""
#     def __init__(self):
#         super(StoppableThread, self).__init__()
#         self._stop = threading.Event()
#     def stop(self):
#         self._stop.set()
#     def stopped(self):
#         return self._stop.isSet()

# class RenderStop(bpy.types.Operator):
#     """Stop the rendering"""
#     bl_idname = "render.stop"
#     bl_label = "Stop the rendering"

#     def execute(self, context):
#         threads = threading.enumerate()
#         for th in threads:
#             if th.name == 'render':
#                 th.stop()

#         def draw(self, context):
#             self.layout.label("Render will be stop after the current frame finishes")
#         context.window_manager.popup_menu(draw, title="Stop Render", icon='ERROR')
#         return {'FINISHED'}

class SMR_OT_FULLBAKE(bpy.types.Operator):

    bl_idname = "smr.fullbake"
    bl_label = "Full Bake"
    bl_description = "Starts the bake operation, this might take some time"
    bl_options = {"REGISTER", "UNDO"}

    name: bpy.props.StringProperty(name = 'Texture Prefix', default = 'SMR_Obj')
    fullbake_colorspace: bpy.props.EnumProperty(
        name="Full Bake Color Space",
        description="Normal Map Color Space for baking",
        items = [
                ("srgb", "sRGB", "", 0),
                ("noncolor", "Non-Color", "", 1),
            ],
        default = "srgb",
        ) 
    fullbake_uv: bpy.props.EnumProperty(
        name="Full Bake UVs",
        description="Decide if you want auto generated UV's (SMR_UV) or use the UV's you already have",
        items = [
                ("auto", "Auto UV", "", 0),
                ("current", "Current UV", "", 1),
            ],
        default = "auto",
        )         
    def invoke(self,context,event):
        if len(bpy.context.selected_objects) == 0:
            ShowMessageBox("Please select the object you want to bake", "What the smudge!", 'INFO')
            return {'FINISHED'}


        
        self.old_scene = bpy.context.window.scene
        active_object = context.active_object

        if 'SMR_Simple' in active_object.active_material or 'SMR_Subset' in active_object.active_material:
            ShowMessageBox("Baking decal setups is currently not supported, message me if you'd like to see this added", "What the smudge!", 'INFO')
            return {'FINISHED'}

        self.old_uv = active_object.data.uv_layers.active.name
        wm = context.window_manager
        if self.name == 'SMR_Obj':
            self.name = 'SMR_{}'.format(context.active_object.name)
        bake(self, context, context.active_object, context.selected_objects, 'Full')
        
        scene = bpy.data.scenes['SMR_Bake']
        for obj in scene.objects:
            stop = False
            if obj.name == active_object.name:
                stop = True
            for s_obj in context.selected_objects:
                if obj.name == s_obj.name:
                    stop = True
            if not stop:
                scene.collection.objects.unlink(obj)
        return wm.invoke_props_dialog(self)

    def draw(self,context):
        layout = self.layout
        #t
        settings= context.scene.SMR
        col=layout.column()
        col.separator()
        box = col.box()
        box.label(text='You are in a seperate scene', icon = 'INFO')
        box.operator('smr.info', text = 'How to cancel?', icon = 'QUESTION').info = 'bake_cancel'
        col.separator()
        box = col.box()
        box.label(text = 'Texture Naming Prefix')
        box.prop(self, 'name', text = '')
        box.label(text='Overwrites images with same name', icon = 'ERROR')
        box.label(text='Change export path in preferences', icon = 'INFO')
        col.separator()
        box = col.box()
        box.label(text='Normal Map Color Space:')
        row=box.row(align=True)
        row.prop(self, 'fullbake_colorspace', expand= True)
        col.separator()
        box = col.box()
        box.label(text='UV Mapping:')
        row=box.row(align=True)
        row.prop(self, 'fullbake_uv', expand= True)   
        col.separator()
        box=col.box()
        box.label(text='Bake Settings:')
        row=box.row(align=True)
        row.prop(settings, 'fullbake_res', text = 'Resolution:')
        row=box.row(align=True)
        row.prop(settings, 'fullbake_samples', text = 'Samples:')
        col.separator()
        col2= col.column()
        col2.scale_y = 1.5
        col2.label(text = 'UI freezes during bake, may take minutes', icon='INFO')


    def execute(self,context):
        settings = context.scene.SMR
        SMR_settings = settings
        pref = bpy.context.preferences.addons['SMR_PRO'].preferences
        bakepath = pref.SMR_bakepath
        
        naming = self.name
        mat, nodes, links = get_mat_data()
        mat_copy = mat.copy()
        mat_copy.name = 'BAKED_' + mat.name 
        nodes = mat_copy.node_tree.nodes
        links = mat_copy.node_tree.links
        context.active_object.active_material = mat_copy

        res = int(SMR_settings.fullbake_res)
        emit = nodes.new('ShaderNodeEmission')
        emit.name = 'Bake_EMIT'
        wm = bpy.context.window_manager

        
        if settings.has_scratch or settings.has_droplets:
            type_list = ('Normal', 'Diffuse', 'Roughness')
        else:
            type_list = ('Diffuse', 'Roughness')

        if self.fullbake_uv == 'auto':
            auto = True
        else: 
            auto = False


        principled = None
        glass = None
        for node in nodes:
            if node.name == 'SMR_Principled' or node.name == 'Extreme PBR BSDF':
                principled = node
            if node.name == 'SMR Glass':
                glass = node
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                output = node
        remove_list = []
        # global exclusion_list  
        # exclusion_list.clear()
        # if principled:
        #     follow_all_links(principled)

        # progress from [0 - 1000]
        tot = len(type_list)
        for i in range(len(type_list)):  
            if type_list[i] == 'Normal':
                image_n =  bpy.data.images.new(naming + '_Normal', width=res, height=res)
                fullbake('Normal', image_n, mat_copy, self.fullbake_colorspace, auto, self.old_uv)
            elif type_list[i] == 'Roughness':
                image_r = image = bpy.data.images.new(naming + '_Roughness', width=res, height=res)
                fullbake('Roughness', image_r, mat_copy, self.fullbake_colorspace, auto, self.old_uv)                
            elif type_list[i] == 'Diffuse':
                image_d = image = bpy.data.images.new(naming + '_Diffuse', width=res, height=res)        
                fullbake('Diffuse', image_d, mat_copy, self.fullbake_colorspace, auto, self.old_uv)            
        image_m = None
        if followLinks(principled, 4)[0]:
            image_m = bpy.data.images.new(naming + '_Metallic', width=res, height=res)
            fullbake('Metallic', image_m, mat_copy, self.fullbake_colorspace, auto, self.old_uv, principled)
        image_s = None
        if followLinks(principled, 5)[0]:
            image_s = bpy.data.images.new(naming + '_Specular', width=res, height=res)
            fullbake('Specular', image_s, mat_copy, self.fullbake_colorspace, auto, self.old_uv, principled)


        # if 'error' in (image_normal, image_dif, image_roughness):
        #     ShowMessageBox('Something went wrong, contact me if this happens often', 'What the Smudge!', 'INFO')
        #     return {'FINISHED'}


        
        for node in nodes:
            if node == principled or node == glass or node == output:
                continue
            remove_list.append(node)
        for node in remove_list:
            nodes.remove(node)
        
        if principled:
            links.new(principled.outputs[0], output.inputs[0])
        elif glass:
            links.new(glass.outputs[0], output.inputs[0])
        else:
            ShowMessageBox('Something went wrong, contact me if this happens often', 'What the Smudge!', 'INFO')
            return {'FINISHED'}


        if settings.has_scratch or settings.has_droplets:
            img_node = add_image_node(image_n, 'Normal', principled, glass, nodes, links)
            nor_node = nodes.new('ShaderNodeNormalMap')
            nor_node.location = (-200, -200)
            links.new(img_node.outputs[0], nor_node.inputs[1])
            if principled:
                links.new(nor_node.outputs[0], principled.inputs['Normal'])
            elif glass:
                links.new(nor_node.outputs[0], glass.inputs[3])
        add_image_node(image_d, 'Diffuse', principled, glass, nodes, links)   
        add_image_node(image_r, 'Roughness', principled, glass, nodes, links)

        if image_m:
            add_image_node(image_m, 'Metallic', principled, glass, nodes, links)
        if image_s:
            add_image_node(image_s, 'Specular', principled, glass, nodes, links)

        map_node = nodes.new('ShaderNodeMapping')
        map_node.location = (-1200, 200)
        coord_node = nodes.new('ShaderNodeTexCoord')
        coord_node.location = (-1400, 200)

        links.new(coord_node.outputs[2], map_node.inputs[0])
        for node in nodes:
            if node.bl_idname == 'ShaderNodeTexImage':
                links.new(map_node.outputs[0], node.inputs[0])

        obj = context.active_object
        if self.fullbake_uv == 'auto':
            obj.data.uv_layers['SMR_UV'].active_render = True
            remove_layers = []
            for layer in obj.data.uv_layers:
                if layer.name == 'SMR_UV':
                    pass
                else:
                    remove_layers.append(layer)
            for layer in remove_layers:
                obj.data.uv_layers.remove(layer)     
        else:
            layer = obj.data.uv_layers['SMR_UV']
            obj.data.uv_layers.remove(layer)  
        bpy.context.window.scene = self.old_scene
    
        if not bakepath:
            bakepath2 = pref.SMR_path2  
        elif not os.path.isdir(bakepath):
            bakepath2 = pref.SMR_path2 
        else:
            bakepath2= bakepath
        
       

        if type_list[0] == 'Normal':
            save_image(image_n, bakepath2)
            if self.fullbake_colorspace == 'noncolor':
                image_n.colorspace_settings.name = 'Non-Color'

        save_image(image_r, bakepath2)
        save_image(image_d, bakepath2)
        m=0
        s=0
        if image_m:
            save_image(image_m, bakepath2)
            m=1
        if image_s:
            save_image(image_s, bakepath2)
            s=1

        mat_copy['SMR_BAKE'] = 1
        
        SMR_callback(self)
        amount = len(type_list) + m + s
        ShowMessageBox('Exported {} images to {} '.format(amount, bakepath2), 'Bake Export [Ctrl + Z to revert material]', 'INFO')
        return {'FINISHED'}
def add_image_node(image, image_name, principled, glass, nodes, links):
    img_node = nodes.new('ShaderNodeTexImage')
    img_node.image = image
    img_node.name = image_name
    
    loc = {'Diffuse': (-600, 400), 'Normal': (-600, -200), 'Roughness': (-600, 100), 'Metallic': (-1000, 300), 'Specular': (-1000, -100)}
    img_node.location = loc[image_name]
    if principled:
        socket = {'Diffuse': 0, 'Normal': 'Normal', 'Roughness': 7, 'Metallic': 4, 'Specular': 5}
        links.new(img_node.outputs[0], principled.inputs[socket[image_name]])
    elif glass:
        socket = {'Diffuse': 0, 'Normal': 3, 'Roughness': 1, 'Metallic': 2, 'Specular': 2}
        links.new(img_node.outputs[0], glass.inputs[socket[image_name]]) 
    return img_node

def save_image(image, bakepath2):
    image.filepath_raw = bakepath2 + str(Path("/{}.png".format(image.name)))
    image.file_format = 'PNG'
    image.save()

# def follow_all_links(node_in):
#     for n_inputs in node_in.inputs:
#         for node_links in n_inputs.links:
#             global exclusion_list
#             name = node_links.from_node.name
#             if 'SMR' not in name:
#                 exclusion_list.append(name)
#                 follow_all_links(node_links.from_node)    

class SMR_OT_BAKE(bpy.types.Operator):

    bl_idname = "smr.bake"
    bl_label = "Bake"
    bl_description = "Starts the bake operation, this might take some time"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    
    def invoke(self,context,event):
        wm = context.window_manager
        categ = self.categ
        mat, nodes, links = get_mat_data()
        
        if len(bpy.context.selected_objects) == 0:
            ShowMessageBox("Please select the object you want to bake", "What the smudge!", 'INFO')
            return {'FINISHED'}

        active_obj = context.active_object
        context_objs = context.selected_objects
        
        self.old_scene = bake(self, context, active_obj, context_objs, categ)
        scene = bpy.data.scenes['SMR_Bake']
        for obj in scene.objects:
            stop = False
            if obj.name == active_obj.name:
                stop = True
            for s_obj in context.selected_objects:
                if obj.name == s_obj.name:
                    stop = True
            if not stop:
                scene.collection.objects.unlink(obj)


        return wm.invoke_props_dialog(self)


    def draw(self,context):
        type = self.categ
        if type == 'EWear':
            bakemat = 'Bake2'
            txt1= 'Edge Width'
        else:
            bakemat = 'Bake'
            txt1 = 'Boost Blacks'
            txt2 = 'Boost Whites'
        nodes = bpy.data.materials['SMR_{}'.format(bakemat)].node_tree.nodes
        node = nodes['Bake_Control']
        layout= self.layout
        
        layout.label(text='You are in a seperate scene', icon = 'INFO')
        layout.operator('smr.info', text = 'How to cancel?', icon = 'QUESTION').info = 'bake_cancel'
        
        col = layout.column()
        col.scale_y = 1.5

        col.prop(node.inputs[1], 'default_value', text = txt1)
        if type != 'EWear':
            col.prop(node.inputs[2], 'default_value', text = txt2)
        col = layout.column()
        layout.label(text = 'Press OK to Bake, see progress bar below') 

    def execute(self,context):
        if not self.old_scene:
            return {'FINISHED'}
        mat, nodes, links = get_mat_data()

        categ = self.categ
        bpy.ops.object.bake('INVOKE_DEFAULT')
        bpy.context.window.scene = self.old_scene 
        
        #here
        context.scene.SMR.has_bake = True
        if categ == 'EWear':
            image_node = nodes['SMR_Bake2_Texture']
        else:
            image_node = nodes['SMR_Bake_Texture']

        inf_node = nodes['SMR_Influence_{}'.format(categ)]
        links.new(image_node.outputs[0], inf_node.inputs[0])
        for area in bpy.context.screen.areas: # iterate through areas in current screen
            if area.type == 'VIEW_3D':
                for space in area.spaces: # iterate through spaces in current VIEW_3D area
                    if space.type == 'VIEW_3D': # check if space is a 3D view
                        space.shading.type = 'MATERIAL'
        return {'FINISHED'}


def bake (self, context, active_object, context_objects, type):
    mat, nodes, links = get_mat_data()
    #here
    SMR_settings = context.scene.SMR
    
    if type == 'Full':
        res = int(SMR_settings.fullbake_res)
        bake_samples = int(SMR_settings.fullbake_samples)
    elif type == 'EWear':
        res = int(SMR_settings.bake2_res)
        bake_samples =  int(SMR_settings.bake2_samples)
    else: 
        if type == 'SmBCM' or type == 'ScBCM':
            res = int(SMR_settings.bake2_res)
            bake_samples=int(SMR_settings.bake2_samples)
        else:
            res = int(SMR_settings.bake1_res)
            bake_samples=int(SMR_settings.bake1_samples)

    for area in bpy.context.screen.areas: # iterate through areas in current screen
        if type == 'Full':
            break
        if area.type == 'VIEW_3D':
            for space in area.spaces: # iterate through spaces in current VIEW_3D area
                if space.type == 'VIEW_3D': # check if space is a 3D view
                    space.shading.type = 'RENDERED'


    obj=bpy.context.active_object
    #mesh = bpy.data.meshes[obj.name]
    mesh = obj.data

    old_scene = bpy.context.window.scene 
    active_object = active_object
    selected_objects = context_objects


    if not active_object:
        self.report({'WARNING'}, "No object selected")
        return None
    
    #check if scene exists, otherwise create it

    try:
        smr_scene = bpy.data.scenes['SMR_Bake']
        remove_list = []
        for obj in smr_scene.objects:
            remove_list.append(obj)
        for obj in remove_list:
            smr_scene.collection.objects.unlink(obj)
        smr_scene.view_layers['View Layer'].material_override = None
        smr_scene = bpy.data.scenes['SMR_Bake']

    except:
        smr_scene = bpy.data.scenes.new(name='SMR_Bake')

    bpy.context.window.scene = smr_scene    
    
        
    #set some render settings
    smr_scene.render.engine = "CYCLES"
    smr_scene.cycles.samples = bake_samples
    smr_scene.cycles.bake_type = "EMIT"
    smr_scene.render.bake.margin = 2
    
    uv_exists = False
    original_uv = None

    for obj in selected_objects:
        try:
            smr_scene.collection.objects.link(obj)
        except:
            pass    
    smr_scene.view_layers['View Layer'].objects.active = active_object
    
    add_smr_uv()
    
    check_node('SMR_UV2', 'ShaderNodeUVMap')
    uv_node =  nodes['SMR_UV2']
    uv_node.uv_map = 'SMR_UV'
    loc = nodes['SMR'].location  
    uv_node.location = loc[0] -203, loc[1] - 39
 
    
    #check if the baking material exists, otherwise append it
    if type == 'Full':
        bakemat = 'FullBake'
    else:
        if type == 'EWear':
            bakemat = 'Bake2'
        else:
            bakemat = 'Bake'
        try:
            bpy.data.materials['SMR_{}'.format(bakemat)]
            if SMR_settings.diagnostics:	
                print('already found SMR_{}'.format(bakemat))         
        
        except:    
            #here
            blendfile = str(os.path.dirname(__file__)) + str(Path('/SMR.blend'))
            section   = str(Path("/Material/"))
            filename    = 'SMR_{}'.format(bakemat)                
            filepath  = blendfile + section + filename
            directory = blendfile + section

            bpy.ops.wm.append(
                filepath=filepath, 
                filename=filename,
                directory=directory)
            if SMR_settings.diagnostics:
                print('appending SMR_{}'.format(bakemat))             

        #set the baking material as override

        smr_scene.view_layers['View Layer'].material_override = bpy.data.materials['SMR_{}'.format(bakemat)]


                

    #deselect all, this also doesn
    deselect_list=[]
    for obj in bpy.context.selected_objects:
        deselect_list.append(obj)
    for obj in deselect_list:
        obj.select_set(state = False)    

    active_object.select_set(state=True)
    smr_scene.view_layers['View Layer'].objects.active = active_object


    #this are external functions returning material data and creating nodes in the right places
    
    node_name = "SMR_{}_Texture".format(bakemat)
    check_node(node_name, 'ShaderNodeTexImage')
    node=nodes[node_name]
    node.location = nodes['SMR'].location[0] - 700, nodes['SMR'].location[1] - 570
    
    #checking if the bake image exists, otherwise create it

    if type == 'Full':
        return old_scene


    image_name = "SMR_{}_{}".format(bakemat, active_object.name)
    
    try:
        image = bpy.data.images[image_name]
        if image.size[0] != res:
            bpy.data.images.remove(image)
            image = bpy.data.images.new(image_name, width=res, height=res)
            SMR_settings.pack_confirmation = True            
    except:
        image = bpy.data.images.new(image_name, width=res, height=res)
        SMR_settings.pack_confirmation = True
    
    for s_node in nodes:
        s_node.select = False

    node.image = image
    node.select = True
    nodes.active = node
    
    try:
        l = node.outputs[0].links[0]
        mat.node_tree.links.remove(l)
    except:
        pass

    
    links.new(uv_node.outputs[0], node.inputs[0])

    active_object.select_set(state=True)
    

    return old_scene

def fullbake(texture_type, image, mat, fullbake_colorspace, auto_uv, old_uv, principled = None):
    active_object = bpy.context.active_object
    SMR_settings = bpy.context.scene.SMR
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    
    
    SMR_settings.pack_confirmation = True

    node = nodes.new('ShaderNodeTexImage')
    node.image = image
    for node2 in nodes:
        node2.select=False
    node.select = True
    nodes.active = node

    uv_node = nodes['SMR_UV2']

    try:
        l = node.outputs[0].links[0]
        mat.node_tree.links.remove(l)
    except:
        pass

    if auto_uv:
        links.new(uv_node.outputs[0], node.inputs[0])


    emission = nodes['Bake_EMIT']
    smr_node = nodes['SMR']
    mat_ouput = None
    main = None
    for node in nodes:
        if node.bl_idname == 'ShaderNodeOutputMaterial':
            mat_output = node
        elif node.bl_idname == 'ShaderNodeBsdfPrincipled' or node.bl_idname == 'ShaderNodeBsdfGlass':
            main = node
        
    if not mat_output:
        print('error')
        return 'error'
    if not main:
        print('error')
        return 'error'
    if fullbake_colorspace == 'srgb':
        normal_output = 1
    else:
        normal_output = 0
    smr_scene = bpy.data.scenes['SMR_Bake']
    SMR_settings.SMR_active_mat = mat.name
    if texture_type == 'Diffuse':
        links.new(smr_node.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], mat_output.inputs[0])
    if texture_type == 'Metallic':
        metal_node = nodes[followLinks(principled, 4)[0]]
        links.new(metal_node.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], mat_output.inputs[0])
    if texture_type == 'Specular':
        spec_node = nodes[followLinks(principled, 5)[0]]
        links.new(spec_node.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], mat_output.inputs[0])          
    if texture_type == 'Normal':
        check_node('SMR_Normal_Bake', 'group')
        normal_bake = nodes['SMR_Normal_Bake']
        links.new(normal_bake.outputs[normal_output], emission.inputs[0])
        links.new(smr_node.outputs[2], normal_bake.inputs[0])
        links.new(emission.outputs[0], mat_output.inputs[0])
    if texture_type == 'Roughness':
        links.new(smr_node.outputs[1], emission.inputs[0])
        links.new(emission.outputs[0], mat_output.inputs[0])
    
    for node2 in nodes:
        node2.select=False
    node.select = True
    nodes.active = node

    active_object.data.uv_layers.active = active_object.data.uv_layers[old_uv]
    if auto_uv:
        search_name = 'SMR_UV'
    else:
        search_name = old_uv

    i=0
    for layer in active_object.data.uv_layers:
        if layer.name == search_name:
            index = i
            break
        i+=1

    active_object.data.uv_layers.active_index = index

    
    # if not auto_uv:
    #     uv_node = nodes.new('ShaderNodeUVMap')
    #     uv_node.uv_map = old_uv
    #     links.new(uv_node.outputs[0], node.inputs[0])

    active_object.select_set(state=True)
    smr_scene.view_layers['View Layer'].objects.active = active_object
    bpy.ops.object.bake()
