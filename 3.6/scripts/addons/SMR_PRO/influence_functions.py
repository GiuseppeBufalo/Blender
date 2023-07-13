#pylint: disable=import-error, relative-beyond-top-level
import bpy

from .smr_common import ShowMessageBox
from . mat_functions import get_mat_data, check_node, followLinks
from . update_functions import update_influence_sliders
from . mat_functions import add_smr_uv


def SMR_preview(type):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    categ = SMR_settings.smr_ui_categ
    
    check_node('SMR_Preview', 'ShaderNodeEmission')
    check_node('SMR_Temp', 'ShaderNodeEmission')
    preview_node = nodes['SMR_Preview']
    preview_node.hide = True

    temp_node = nodes['SMR_Temp']
    temp_node.hide = True
    

    for node in nodes:
        if node.type == "OUTPUT_MATERIAL":
            scene_output_node = node
            output_loc = node.location
            break
    
    full_mat_name = followLinks(scene_output_node, 0)[0]
    full_mat = nodes [full_mat_name]
    
    links.new(preview_node.outputs[0], scene_output_node.inputs[0])
    
    preview_node.location = output_loc[0], output_loc[1] + 50
    temp_node.location = output_loc[0], output_loc[1] + 85
    
    if full_mat_name != 'SMR_Preview':
        links.new(full_mat.outputs[0], temp_node.inputs[0])
    
    if type == 'AT_Noise':
        AT_node= nodes['SMR_AT_{}'.format(categ)]
        links.new(AT_node.outputs[2], preview_node.inputs[0])    
    else:
        node_to_preview= nodes['SMR_Influence_{}'.format(type)]
        links.new(node_to_preview.outputs[0], preview_node.inputs[0])

    SMR_settings.preview = True
    
def stop_preview():
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    
    try:
        temp_node = nodes['SMR_Temp']
        full_mat_name = followLinks(temp_node, 0)[0]
        if full_mat_name == 'SMR_Preview' or full_mat_name == 'Emission viewer':
            full_mat = nodes['SMR']
        else:
            full_mat = nodes[full_mat_name]
    except:
        try:
            full_mat = nodes['SMR_Principled']
        except:
            ShowMessageBox("Error connecting your original material, please connect it yourself", "What the smudge!", 'ERROR')
            SMR_settings.preview = False
            return
    
    for node in nodes:
        if node.type == "OUTPUT_MATERIAL":
            scene_output_node = node
            break
        
    links.new(full_mat.outputs[0], scene_output_node.inputs[0])
        
    SMR_settings.preview = False    
           
    

def add_influence(type):
    SMR_settings = bpy.context.scene.SMR
    if SMR_settings.update_exception:
        return
    
    mat, nodes, links = get_mat_data()  
    check_node('SMR_Influence_{}'.format(type), 'group')
    influence_node = nodes['SMR_Influence_{}'.format(type)]
    
    
    if type[:2] == "Sm":
        categ = "Smudge"
        target_node= nodes['SMR_{}'.format(categ)]
        if type[2:] == "BCM":
            target_socket = 4
            target_node= nodes['SMR']
            SMR_settings.inf_smudge_bcm = True
            SMR_settings.inftype_smudge_bcm = 'Noise'
        elif type[2:] == "Intensity": 
            target_socket = 2
            SMR_settings.inf_smudge_int = True
            SMR_settings.inftype_smudge_int = 'Noise' 
    elif type[:2] == "Sc":
        categ = "Scratch"
        target_node= nodes['SMR_{}'.format(categ)]
        if type[2:] == "BCM":
            target_socket = 8
            target_node= nodes['SMR']
            SMR_settings.inf_scratch_bcm = True
            SMR_settings.inftype_scratch_bcm = 'Noise'
        elif type[2:] == "Intensity": 
            target_socket = 3
            SMR_settings.inf_scratch_int = True 
            SMR_settings.inftype_scratch_int = 'Noise'
    elif type == 'Dust1':
        categ = 'Dust1'
        target_node= nodes['SMR_Dust']
        target_socket = 2
        SMR_settings.inf_dust1 = True
        SMR_settings.inftype_dust1 = 'Noise'
    elif type == 'Dust_Inf':
        categ = 'Dust_Inf'
        target_node= nodes['SMR_Dust']
        target_socket = 5
        SMR_settings.inf_dust_inf = True
        SMR_settings.inftype_dust_inf = 'Noise'
    elif type == 'Droplets':
        categ = 'Droplets'
        target_node= nodes['SMR']
        target_socket = 10
        SMR_settings.inf_droplets = True
        SMR_settings.inftype_droplets = 'Noise'

    links.new(influence_node.outputs[0], target_node.inputs[target_socket])
    
    check_node('SMR_Noise_{}'.format(type), 'ShaderNodeTexNoise')
    influence_map = nodes['SMR_Noise_{}'.format(type)]
    
    links.new(influence_map.outputs[0], influence_node.inputs[0])

    node_locs = []
    for node in nodes:
        if node.name[:13] == 'SMR_Influence':
            node_locs.append(node.location[1])
    node_locs.sort()
    
    if len(node_locs) == 0:
        node_locs.append(nodes['SMR'].location[1] - 400)
    
    influence_node.location = nodes['SMR'].location[0] - 700, node_locs[0] - 60
    influence_map.location = influence_node.location[0] - 200, influence_node.location[1]
            

def change_inftype_smudge_bcm(self,context):
    type = bpy.context.scene.SMR.inftype_smudge_bcm
    change_inftype_general(self,context,'SmBCM',type)

def change_inftype_smudge_int(self,context):
    type = bpy.context.scene.SMR.inftype_smudge_int
    change_inftype_general(self,context,'SmIntensity',type)

def change_inftype_scratch_bcm(self,context):
    type = bpy.context.scene.SMR.inftype_scratch_bcm
    change_inftype_general(self,context,'ScBCM',type)

def change_inftype_scratch_int(self,context):
    type = bpy.context.scene.SMR.inftype_scratch_int
    change_inftype_general(self,context,'ScIntensity',type)

def change_inftype_dust1(self,context):
    type = bpy.context.scene.SMR.inftype_dust1
    change_inftype_general(self,context,'Dust1',type)

def change_inftype_dust_inf(self,context):
    type = bpy.context.scene.SMR.inftype_dust_inf
    change_inftype_general(self,context,'Dust_Inf',type)

def change_inftype_droplets(self,context):
    type = bpy.context.scene.SMR.inftype_droplets
    change_inftype_general(self,context,'Droplets',type)

def change_inftype_general(self,context,categ, type):
    
    SMR_settings = bpy.context.scene.SMR
    if SMR_settings.update_exception:
        return

    mat, nodes, links = get_mat_data()

    influence_node=nodes['SMR_Influence_{}'.format(categ)]
    old_node_name=followLinks(influence_node, 0)[0]
    if old_node_name:
        old_node = nodes[old_node_name]
        nodes.remove(old_node)

    if type == 'Noise':
        check_node('SMR_Noise_{}'.format(categ), 'ShaderNodeTexNoise')
        new_node = nodes['SMR_Noise_{}'.format(categ)]
    elif type =='Cavity':
        try:
            bake = nodes['SMR_Bake_Texture']
            links.new(bake.outputs[0], influence_node.inputs[0])
        except:
            pass
    elif type =='Texture Paint':
        check_node('SMR_TexturePaint_{}'.format(categ), 'ShaderNodeTexImage')
        new_node = nodes['SMR_TexturePaint_{}'.format(categ)]
    else:        
        check_node('SMR_{}_{}'.format(type, categ), 'group')
        new_node = nodes['SMR_{}_{}'.format(type, categ)]

    update_influence_sliders()
    links.new(new_node.outputs[0], influence_node.inputs[0])
    new_node.location = influence_node.location[0] - 200, influence_node.location[1]

def start_texture_paint(categ):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    
    obj=bpy.context.active_object
    #mesh = bpy.data.meshes[obj.name]
    mesh = obj.data

    if len(bpy.context.selected_objects) == 0:
        ShowMessageBox("Please select the object you want to texture paint on", "What the smudge!", 'INFO')
        return
    
    check_node('SMR_UV2', 'ShaderNodeUVMap')
    uv_node =  nodes['SMR_UV2']
    loc = nodes['SMR'].location  
    uv_node.location = loc[0] -203, loc[1] - 39
 
    infl_node = nodes['SMR_Influence_{}'.format(categ)]
    image_node_name = followLinks(infl_node, 0)[0]
    image_node = nodes[image_node_name]
    uv_node.location = infl_node.location[0] - 400, infl_node.location[1]

    
    add_smr_uv()
    
    uv_node.uv_map = 'SMR_UV'
    links.new(uv_node.outputs[0], image_node.inputs[0])

    namekey = "{}_{}".format(categ, bpy.context.active_object.name)

    try:
        image = bpy.data.images['SMR_Paint_{}'.format(namekey)]
    except:
        res = 1024
        image = bpy.data.images.new("SMR_Paint_{}".format(namekey), width=res, height=res)
        SMR_settings.pack_confirmation = True
            
    image_node.image = image
        



    SMR_preview(categ)
    
    paint_index = 99
    bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
    
    checkname = 'SMR_Paint_{}'.format(namekey)
    for idx, img in enumerate(mat.texture_paint_images):
        if checkname in img.name:
            paint_index = idx
    
    if paint_index != 99:
        mat.paint_active_slot = paint_index
        
def change_wearmode_bake(self, context):
    if context.scene.SMR.update_exception:
        return
    change_wearmode_general(1)
def change_wearmode_bake2(self, context):
    if context.scene.SMR.update_exception:
        return
    change_wearmode_general(2)


def change_wearmode_general(num):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    if SMR_settings.smr_ui_categ == 'Smudge':
        if num == 1:
            inf_name = 'SmIntensity'
            switch = SMR_settings.wearmode_SmIntensity
        elif num == 2:
            inf_name = 'SmBCM'
            switch = SMR_settings.wearmode_SmBCM
    elif SMR_settings.smr_ui_categ == 'Scratch':
        if num == 1:
            inf_name = 'ScIntensity'
            switch = SMR_settings.wearmode_ScIntensity
        elif num == 2:
            inf_name = 'ScBCM'
            switch = SMR_settings.wearmode_ScBCM         
    elif SMR_settings.smr_ui_categ == 'Wear':
        if num == 1:
            inf_name = 'CWear'
            switch = SMR_settings.wearmode_bake
        elif num == 2:
            inf_name = 'EWear'
            switch = SMR_settings.wearmode_bake2
    elif SMR_settings.smr_ui_categ == 'Dust':
        if num == 1:
            inf_name = 'Dust1'
            switch = SMR_settings.wearmode_Dust1
        elif num == 2:
            inf_name = 'Dust_inf'
            switch = SMR_settings.wearmode_Dust_Inf     

    inf_node = nodes['SMR_Influence_{}'.format(inf_name)]    

    if switch == 'Live':
        if inf_name == 'EWear':
            check_node('SMR_EWear', 'group')
            live_node = nodes['SMR_EWear']
        else:
            check_node('SMR_CWear', 'group')
            live_node = nodes['SMR_CWear']
        live_node.location = inf_node.location[0] -275, inf_node.location[1]

        links.new(live_node.outputs[0], inf_node.inputs[0])
    else:
        if inf_name == 'EWear':
            check_node('SMR_Bake2_Texture', 'ShaderNodeTexImage')
            tex_node = nodes ['SMR_Bake2_Texture']
        else:    
            check_node('SMR_Bake_Texture', 'ShaderNodeTexImage')
            tex_node = nodes ['SMR_Bake_Texture']
        tex_node.location = inf_node.location[0] -275, inf_node.location[1]
        links.new(tex_node.outputs[0], inf_node.inputs[0])

def make_singe_user():
    SMR_settings = bpy.context.scene.SMR
    if bpy.data.materials[SMR_settings.SMR_active_mat].users > 1:
        obj = bpy.context.active_object
        new_mat = bpy.data.materials[SMR_settings.SMR_active_mat].copy()
        SMR_settings.SMR_active_mat = new_mat.name
        idx = obj.active_material_index
        obj.material_slots[idx].material = new_mat

    mat, nodes, links = get_mat_data()
    return mat, nodes, links

def remove_influence(type):
    mat, nodes, links = get_mat_data()
    SMR_settings = bpy.context.scene.SMR
    remove_list = []
    for node in nodes:
        if type in node.name:
            remove_list.append(node.name) 
    for node_name in remove_list:
        node=nodes[node_name]
        nodes.remove(node)
        
    #remove ui boolean
    if type == 'ScIntensity':
        SMR_settings.inf_scratch_int = False
    if type == 'ScBCM':
        SMR_settings.inf_scratch_bcm = False
    if type == 'SmBCM':
        SMR_settings.inf_smudge_bcm = False
    if type == 'SmIntensity':
        SMR_settings.inf_smudge_int = False
    if type == 'Dust1':
        SMR_settings.inf_dust1 = False
    if type == 'Dust_Inf':
        SMR_settings.inf_dust_inf = False
    if type == 'Droplets':
        SMR_settings.inf_droplets = False

    stop_preview()
        