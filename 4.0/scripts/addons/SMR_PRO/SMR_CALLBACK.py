#pylint: disable=import-error, relative-beyond-top-level
import bpy
import os
from . update_functions import update_dust_sliders, update_smudge_sliders, update_droplets_sliders, update_scratch_sliders, update_influence_sliders, update_wear_sliders
from . mat_functions import get_mat_data,  followLinks


class SMR_ACTIVATE(bpy.types.Operator):
    """
    activates the SMR msgbus 
    """
    bl_idname = "smr.activate"
    bl_label = "Activate"
    bl_description = "Activate SMR"
    
    def execute(self, context):    
        SMR_Settings = bpy.context.scene.SMR
        
        #call msgbus
        SMR_Settings.subscribed = False
        msgbus(self, context)

        #update file path
        SMR_Settings.activation_exception = True
        bpy.context.scene.SMR.SMR_path = bpy.context.preferences.addons['SMR_PRO'].preferences.SMR_path2
        SMR_Settings.activation_exception = False
        return {'FINISHED'} 


def msgbus(self, context):
    """
    activates the subscribtion to the active object
    """ 
    SMR_Settings = bpy.context.scene.SMR

    if SMR_Settings.subscribed == True:
        return

    subscribe_to = bpy.types.LayerObjects, "active"
    bpy.msgbus.subscribe_rna(
        key = subscribe_to,
        owner = self,
        args = (self,),
        notify = SMR_callback,
        )
    SMR_Settings.subscribed = True    

def SMR_callback(self):
    """
    runs every time the active object changes or when this function is called in a class
    """    
    SMR_SETTINGS = bpy.context.scene.SMR
    ob = bpy.context.active_object


    SMR_SETTINGS.is_SMR_slot=False
    SMR_SETTINGS.has_dust=False
    SMR_SETTINGS.has_smudge=False
    SMR_SETTINGS.has_droplets=False
    SMR_SETTINGS.has_scratch=False
    SMR_SETTINGS.has_bake = False 
    SMR_SETTINGS.inf_smudge_int = False
    SMR_SETTINGS.inf_smudge_bcm = False
    SMR_SETTINGS.inf_scratch_int = False
    SMR_SETTINGS.inf_scratch_bcm = False
    SMR_SETTINGS.wear_cavity = False
    SMR_SETTINGS.wear_edge = False
    SMR_SETTINGS.dust_at = False
    SMR_SETTINGS.smudge_at = False
    SMR_SETTINGS.scratch_at = False
    SMR_SETTINGS.inf_dust1 = False
    SMR_SETTINGS.inf_dust_inf = False
    SMR_SETTINGS.inf_droplets = False

    
    if ob.type != 'MESH':
        return
    try:
        bpy.context.active_object.active_material.name == ''
    except:
        return

    SMR_SETTINGS.SMR_active_mat = bpy.context.active_object.active_material.name
    
    #introducing some variables and setting them at their base value
    SMR_SETTINGS.is_SMR_object = False

    #check if this object has a SMR material in any of its slots
    for slot in ob.material_slots:
        try:
            if 'SMR' in slot.material.node_tree.nodes:
                SMR_SETTINGS.is_SMR_object = True
        except:
            pass

    if SMR_SETTINGS.is_SMR_object == False:
        SMR_SETTINGS.is_SMR_slot=False
        return

    mat, nodes, links = get_mat_data()
    #checking if the active slot has a smudgr node

    SMR_SETTINGS.update_exception = True   
    for node in nodes:
        if node.name[:3] == 'SMR':
            if node.name == "SMR":
                SMR_SETTINGS.is_SMR_slot=True
            elif node.name == "SMR_Dust":
                SMR_SETTINGS.has_dust= True
                update_dust_sliders()
            elif node.name == "SMR_Smudge":
                SMR_SETTINGS.has_smudge= True
                update_smudge_sliders()
                active_image = nodes['SMR_Smudge_Texture'].image.name
                SMR_SETTINGS.active_smudge_ui = active_image
                filename, file_extension  = os.path.splitext(active_image)
                SMR_SETTINGS.smudge_res = filename[-2:]
                SMR_SETTINGS.smudge_res = filename[-2:]
            elif node.name == 'SMR_Droplets_Texture':
                SMR_SETTINGS.has_droplets = True
                update_droplets_sliders()
            elif node.name == 'SMR_Dust_Texture_AT':
                SMR_SETTINGS.dust_at = True
            elif node.name == 'SMR_Smudge_Texture_AT':
                SMR_SETTINGS.smudge_at = True
            elif node.name == 'SMR_Scratch_Texture_AT':
                SMR_SETTINGS.scratch_at = True                                      
            elif node.name == "SMR_Scratch":
                SMR_SETTINGS.has_scratch = True
                update_scratch_sliders()
                active_image = nodes['SMR_Scratch_Texture'].image.name
                SMR_SETTINGS.active_scratch_ui = active_image
                filename, file_extension  = os.path.splitext(active_image)
                SMR_SETTINGS.scratch_res = filename[-2:]
            elif node.name == "SMR_Bake_Texture":
                if node.image != None:
                    SMR_SETTINGS.has_bake = True 
            elif node.name == "SMR_Bake2_Texture":
                if node.image != None:
                    SMR_SETTINGS.has_bake2 = True 
            elif node.name == 'SMR_Influence_SmBCM':
                SMR_SETTINGS.inf_smudge_bcm = True
                SMR_SETTINGS.inftype_smudge_bcm = find_inftype('SmBCM', nodes, 1)
            elif node.name == 'SMR_Influence_SmIntensity':
                SMR_SETTINGS.inf_smudge_int = True
                SMR_SETTINGS.inftype_smudge_int = find_inftype('SmIntensity', nodes, 1)
            elif node.name == 'SMR_Influence_ScBCM':
                SMR_SETTINGS.inf_scratch_bcm = True
                SMR_SETTINGS.inftype_scratch_bcm = find_inftype('ScBCM', nodes, 1)
                if SMR_SETTINGS.inftype_scratch_bcm == 'Cavity':
                    SMR_SETTINGS.wearmode_ScBCM = find_inftype('ScBCM', nodes, 2)                
            elif node.name == 'SMR_Influence_ScIntensity':
                SMR_SETTINGS.inf_scratch_int = True
                SMR_SETTINGS.inftype_scratch_int = find_inftype('ScIntensity', nodes, 1)
                if SMR_SETTINGS.inftype_scratch_int == 'Cavity':
                    SMR_SETTINGS.wearmode_ScIntensity = find_inftype('ScIntensity', nodes, 2)
            elif node.name == 'SMR_Influence_CWear':
                SMR_SETTINGS.wear_cavity = True
                SMR_SETTINGS.wearmode_bake = find_inftype('CWear', nodes, 2)    
            elif node.name == 'SMR_Influence_EWear':
                SMR_SETTINGS.wear_edge = True
                SMR_SETTINGS.wearmode_bake2 = find_inftype('EWear', nodes, 2)
            elif node.name == 'SMR_Influence_Dust1':
                SMR_SETTINGS.inf_dust1 = True
                SMR_SETTINGS.inftype_dust1 = find_inftype('Dust1', nodes, 1)
            elif node.name == 'SMR_Influence_Dust_Inf':
                SMR_SETTINGS.inf_dust_inf = True
                SMR_SETTINGS.inftype_dust_inf = find_inftype('Dust_Inf', nodes, 1)                                                               
            elif node.name == 'SMR_Influence_Droplets':
                SMR_SETTINGS.inf_droplets = True
                SMR_SETTINGS.inftype_droplets = find_inftype('Droplets', nodes, 1)
            else:
                pass
        else:
            pass                    

    SMR_SETTINGS.update_exception = False
    
    if not SMR_SETTINGS.is_SMR_slot:
        return

    update_influence_sliders()    
    update_wear_sliders()
    #stop_preview()
    
def find_inftype(categ, nodes, num):     
    """
    finds what inftype is selected in this influence menu
    """ 
    inf_node = nodes['SMR_Influence_{}'.format(categ)]
    inftype_name, socket = followLinks(inf_node, 0)
    if 'Noise' in inftype_name:
        x = 'Noise'
    elif 'TexturePaint' in inftype_name:   
        x = 'Texture Paint'
    elif 'Geometry' in inftype_name:
        x = 'Geometry'
    elif 'Gradient' in inftype_name:
        x = 'Gradient'
    elif 'Cavity' in inftype_name:
        x = 'Cavity'
    elif 'Bake' in inftype_name:
        if num == 1:
            x= 'Cavity'        
        else:
            x= 'Baked'
    elif 'Wear' in inftype_name:  
        if num == 1:
            x= 'Cavity'    
        else:    
            x = 'Live'      
    else:
        if num == 1:
            x= 'Cavity'        
        else:
            x= 'Baked'
    return x 


def ui_update(self,context):
    """
    called when switching between smudge, dust, scratch etc. menu's so the influence sliders get update accordingly
    """ 
    SMR_settings= bpy.context.scene.SMR
    update_influence_sliders()
    
    if SMR_settings.pack_confirmation:
        SMR_settings.pack_ui = True