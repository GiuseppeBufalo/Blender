#pylint: disable=import-error, relative-beyond-top-level

import bpy
from . mat_functions import get_mat_data, followLinks

def update_influence_sliders():
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    if SMR_settings.smr_ui_categ == 'Scratch':
        categ = 'ScIntensity'
        categbool = SMR_settings.inf_scratch_int
        categtype = SMR_settings.inftype_scratch_int
        categ2 = 'ScBCM'
        categ2bool = SMR_settings.inf_scratch_bcm
        categ2type = SMR_settings.inftype_scratch_bcm
    elif SMR_settings.smr_ui_categ == 'Smudge':
        categ = 'SmIntensity'
        categbool = SMR_settings.inf_smudge_int
        categtype = SMR_settings.inftype_smudge_int
        categ2 = 'SmBCM'        
        categ2bool = SMR_settings.inf_smudge_bcm
        categ2type = SMR_settings.inftype_smudge_bcm
    elif SMR_settings.smr_ui_categ == 'Wear':
        categ = 'CWear'
        categbool = SMR_settings.wear_cavity
        categtype = None
        categ2 = 'EWear'        
        categ2bool = SMR_settings.wear_edge
        categ2type = None
    elif SMR_settings.smr_ui_categ == 'Dust':
        categ = 'Dust1'
        categbool = SMR_settings.inf_dust1
        categtype = SMR_settings.inftype_dust1
        categ2 = 'Dust_Inf'
        categ2bool = SMR_settings.inf_dust_inf
        categ2type = SMR_settings.inftype_dust_inf
    elif SMR_settings.smr_ui_categ == 'Droplets':
        categ = 'Droplets'
        categbool = SMR_settings.inf_droplets
        categtype = SMR_settings.inftype_droplets
        categ2bool = False    
    else:
        return
    
    SMR_settings.update_exception = True
        
    if categbool:
        inf_node = nodes['SMR_Influence_{}'.format(categ)]   
        SMR_settings.inf1_black = inf_node.inputs[1].default_value*200
        SMR_settings.inf1_white = inf_node.inputs[2].default_value*200
        SMR_settings.inf1_mult = inf_node.inputs[3].default_value
        SMR_settings.inf1_inf = inf_node.inputs[4].default_value
        
        if categtype == 'Gradient' or categtype == 'Noise':
            if categtype == 'Gradient':
                slots = (0,1,2,3)
            else:
                if (2, 83, 0) > bpy.app.version:
                    slots = (1,2,3,4)
                else:
                    slots = (1,2,3,5)

            source_node = nodes['SMR_{}_{}'.format(categtype, categ)]
            
            SMR_settings.inf1_val1 = source_node.inputs[slots[0]].default_value   
            SMR_settings.inf1_val2 = source_node.inputs[slots[1]].default_value
            SMR_settings.inf1_val3 = source_node.inputs[slots[2]].default_value
            SMR_settings.inf1_val4 = source_node.inputs[slots[3]].default_value
        if followLinks(inf_node, 0)[0] == 'SMR_CWear' or followLinks(inf_node, 0)[0] == 'SMR_EWear':
            if SMR_settings.smr_ui_categ == 'Scratch':
                SMR_settings.wearmode_ScIntensity = 'Live'
            elif SMR_settings.smr_ui_categ == 'Smudge':
                SMR_settings.wearmode_SmIntensity = 'Live'
            elif SMR_settings.smr_ui_categ == 'Dust':
                SMR_settings.wearmode_Dust1 = 'Live'
            elif SMR_settings.smr_ui_categ == 'Wear':
                SMR_settings.wearmode_bake = 'Live'                                                
        else: 
            if SMR_settings.smr_ui_categ == 'Scratch':
                SMR_settings.wearmode_ScIntensity = 'Baked'
            elif SMR_settings.smr_ui_categ == 'Smudge':
                SMR_settings.wearmode_SmIntensity = 'Baked'
            elif SMR_settings.smr_ui_categ == 'Dust':
                SMR_settings.wearmode_Dust1 = 'Baked'
            elif SMR_settings.smr_ui_categ == 'Wear':
                SMR_settings.wearmode_bake = 'Baked'
    
    if categ2bool:
        inf_node2 = nodes['SMR_Influence_{}'.format(categ2)]
        SMR_settings.inf2_black = inf_node2.inputs[1].default_value*200
        SMR_settings.inf2_white = inf_node2.inputs[2].default_value*200
        SMR_settings.inf2_mult = inf_node2.inputs[3].default_value
        SMR_settings.inf2_inf= inf_node2.inputs[4].default_value

        
        if categ2type == 'Gradient' or categ2type == 'Noise':
            if categ2type == 'Gradient':
                slots = (0,1,2,3)
            else:
                if (2, 83, 0) > bpy.app.version:
                    slots = (1,2,3,4)
                else:
                    slots = (1,2,3,5)
                
            source_node = nodes['SMR_{}_{}'.format(categ2type, categ2)]

            SMR_settings.inf2_val1 = source_node.inputs[slots[0]].default_value   
            SMR_settings.inf2_val2 = source_node.inputs[slots[1]].default_value
            SMR_settings.inf2_val3 = source_node.inputs[slots[2]].default_value
            SMR_settings.inf2_val4 = source_node.inputs[slots[3]].default_value
    
        if followLinks(inf_node2,0)[0] == 'SMR_CWear' or followLinks(inf_node2,0)[0] == 'SMR_EWear':
            if SMR_settings.smr_ui_categ == 'Scratch':
                SMR_settings.wearmode_ScBCM = 'Live'
            elif SMR_settings.smr_ui_categ == 'Smudge':
                SMR_settings.wearmode_SmBCM = 'Live'
            elif SMR_settings.smr_ui_categ == 'Wear':
                SMR_settings.wearmode_bake2 = 'Live'  
        else: 
            if SMR_settings.smr_ui_categ == 'Scratch':
                SMR_settings.wearmode_ScBCM = 'Baked'
            elif SMR_settings.smr_ui_categ == 'Smudge':
                SMR_settings.wearmode_SmBCM = 'Baked'
            elif SMR_settings.smr_ui_categ == 'Wear':
                SMR_settings.wearmode_bake2 = 'Baked'  
    
    SMR_settings.update_exception = False
    
def update_influence_values(self, context):
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    if SMR_settings.update_exception:
        return
        
    if SMR_settings.smr_ui_categ == 'Scratch':
        categ = 'ScIntensity'
        categbool = SMR_settings.inf_scratch_int
        categtype = SMR_settings.inftype_scratch_int
        categ2 = 'ScBCM'
        categ2bool = SMR_settings.inf_scratch_bcm
        categ2type = SMR_settings.inftype_scratch_bcm
    elif SMR_settings.smr_ui_categ == 'Smudge':
        categ = 'SmIntensity'
        categbool = SMR_settings.inf_smudge_int
        categtype = SMR_settings.inftype_smudge_int
        categ2 = 'SmBCM'        
        categ2bool = SMR_settings.inf_smudge_bcm
        categ2type = SMR_settings.inftype_smudge_bcm
    elif SMR_settings.smr_ui_categ == 'Wear':
        categ = 'CWear'
        categbool = SMR_settings.wear_cavity
        categtype = None
        categ2 = 'EWear'        
        categ2bool = SMR_settings.wear_edge
        categ2type = None
    elif SMR_settings.smr_ui_categ == 'Dust':
        categ = 'Dust1'
        categbool = SMR_settings.inf_dust1
        categtype = SMR_settings.inftype_dust1
        categ2 = 'Dust_Inf'
        categ2bool = SMR_settings.inf_dust_inf
        categ2type = SMR_settings.inftype_dust_inf
    elif SMR_settings.smr_ui_categ == 'Droplets':
        categ = 'Droplets'
        categbool = SMR_settings.inf_droplets
        categtype = SMR_settings.inftype_droplets
        categ2bool = False    
    else:
        return
    
    if categbool:
        inf_node = nodes['SMR_Influence_{}'.format(categ)]
        inf_node.inputs[1].default_value  = SMR_settings.inf1_black / 200
        inf_node.inputs[2].default_value  = SMR_settings.inf1_white / 200
        inf_node.inputs[3].default_value = SMR_settings.inf1_mult 
        inf_node.inputs[4].default_value = SMR_settings.inf1_inf 
        
        if categtype == 'Gradient' or categtype == 'Noise':
            if categtype == 'Gradient':
                slots = (0,1,2,3)
            else:
                if (2, 83, 0) > bpy.app.version:
                    slots = (1,2,3,4)
                else:
                    slots = (1,2,3,5)
                
            source_node = nodes['SMR_{}_{}'.format(categtype, categ)]
            source_node.inputs[slots[0]].default_value = SMR_settings.inf1_val1    
            source_node.inputs[slots[1]].default_value = SMR_settings.inf1_val2  
            source_node.inputs[slots[2]].default_value = SMR_settings.inf1_val3  
            source_node.inputs[slots[3]].default_value = SMR_settings.inf1_val4  

    if categ2bool:
        inf_node2 = nodes['SMR_Influence_{}'.format(categ2)]
        inf_node2.inputs[1].default_value  = SMR_settings.inf2_black / 200
        inf_node2.inputs[2].default_value  = SMR_settings.inf2_white  / 200
        inf_node2.inputs[3].default_value = SMR_settings.inf2_mult  
        inf_node2.inputs[4].default_value = SMR_settings.inf2_inf         
        
        if categ2type == 'Gradient' or categ2type == 'Noise':
            if categ2type == 'Gradient':
                slots = (0,1,2,3)
            else:
                if (2, 83, 0) > bpy.app.version:
                    slots = (1,2,3,4)
                else:
                    slots = (1,2,3,5)
            
            source_node = nodes['SMR_{}_{}'.format(categ2type, categ2)]
            source_node.inputs[slots[0]].default_value = SMR_settings.inf2_val1    
            source_node.inputs[slots[1]].default_value = SMR_settings.inf2_val2 
            source_node.inputs[slots[2]].default_value = SMR_settings.inf2_val3  
            source_node.inputs[slots[3]].default_value = SMR_settings.inf2_val4 

def update_dust_sliders():
    
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    dust_node = nodes['SMR_Dust']
    dust_AT_node = nodes ['SMR_AT_Dust']
    main_node = nodes['SMR']

    SMR_settings.dust_multiplier = dust_node.inputs[2].default_value
    SMR_settings.dust_side = dust_node.inputs[3].default_value
    SMR_settings.dust_influence = dust_node.inputs[5].default_value
    SMR_settings.dust_color = main_node.inputs[13].default_value 
    SMR_settings.dust_locx = dust_AT_node.inputs[1].default_value
    SMR_settings.dust_locy = dust_AT_node.inputs[2].default_value
    SMR_settings.dust_scale = dust_AT_node.inputs[4].default_value
    SMR_settings.dust_genscale = dust_node.inputs[6].default_value
    SMR_settings.dust_stretch = dust_AT_node.inputs[5].default_value
    SMR_settings.dust_rot = dust_AT_node.inputs[3].default_value
    
    if dust_AT_node.inputs[0].default_value == 1:
        SMR_settings.dust_coord = 'Box'
    else:    
        SMR_settings.dust_coord = 'UV'
    
    if SMR_settings.dust_at:
        SMR_settings.dust_at_scale = dust_AT_node.inputs[6].default_value
        SMR_settings.dust_at_rot = dust_AT_node.inputs[7].default_value
        SMR_settings.dust_at_noise = dust_AT_node.inputs[8].default_value   

def update_dust_values (self, context):
    
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR

    if SMR_settings.update_exception:
        return

    dust_node = nodes['SMR_Dust']
    dust_AT_node = nodes ['SMR_AT_Dust']
    main_node = nodes['SMR']

    dust_node.inputs[2].default_value = SMR_settings.dust_multiplier 
    dust_node.inputs[3].default_value = SMR_settings.dust_side 
    dust_node.inputs[5].default_value = SMR_settings.dust_influence 
    main_node.inputs[13].default_value = SMR_settings.dust_color 
    dust_AT_node.inputs[1].default_value = SMR_settings.dust_locx 
    dust_AT_node.inputs[2].default_value = SMR_settings.dust_locy 
    dust_AT_node.inputs[4].default_value = SMR_settings.dust_scale 
    dust_node.inputs[6].default_value = SMR_settings.dust_genscale 
    dust_AT_node.inputs[5].default_value = SMR_settings.dust_stretch 
    dust_AT_node.inputs[3].default_value = SMR_settings.dust_rot 
    
    
    if SMR_settings.dust_at:
        dust_AT_node.inputs[6].default_value = SMR_settings.dust_at_scale 
        dust_AT_node.inputs[7].default_value = SMR_settings.dust_at_rot 
        dust_AT_node.inputs[8].default_value = SMR_settings.dust_at_noise    


def update_smudge_sliders ():
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR

    smudge_node = nodes['SMR_Smudge']
    smudge_AT_node = nodes ['SMR_AT_Smudge']
    main_node = nodes['SMR']

    SMR_settings.smudge_falloff = smudge_node.inputs[2].default_value
    SMR_settings.smudge_roughness = smudge_node.inputs[3].default_value
    SMR_settings.smudge_bcm_falloff = main_node.inputs[3].default_value
    SMR_settings.smudge_bcm_intensity = main_node.inputs[4].default_value 
    SMR_settings.smudge_bcm_color = main_node.inputs[5].default_value 
    SMR_settings.smudge_locx = smudge_AT_node.inputs[1].default_value
    SMR_settings.smudge_locy = smudge_AT_node.inputs[2].default_value
    SMR_settings.smudge_scale = smudge_AT_node.inputs[4].default_value
    SMR_settings.smudge_stretch = smudge_AT_node.inputs[5].default_value
    SMR_settings.smudge_rot = smudge_AT_node.inputs[3].default_value
    
    if smudge_AT_node.inputs[0].default_value == 1:
        SMR_settings.smudge_coord = 'Box'
    else:    
        SMR_settings.smudge_coord = 'UV'
    
    if SMR_settings.smudge_at:
        SMR_settings.smudge_at_scale = smudge_AT_node.inputs[6].default_value
        SMR_settings.smudge_at_rot = smudge_AT_node.inputs[7].default_value
        SMR_settings.smudge_at_noise = smudge_AT_node.inputs[8].default_value    

def update_smudge_values (self, context):        
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    if SMR_settings.update_exception:
        return


    smudge_node = nodes['SMR_Smudge']
    smudge_AT_node = nodes ['SMR_AT_Smudge']
    main_node = nodes['SMR']

    smudge_node.inputs[2].default_value = SMR_settings.smudge_falloff 
    smudge_node.inputs[3].default_value = SMR_settings.smudge_roughness
    main_node.inputs[3].default_value = SMR_settings.smudge_bcm_falloff
    main_node.inputs[4].default_value = SMR_settings.smudge_bcm_intensity
    main_node.inputs[5].default_value = SMR_settings.smudge_bcm_color
    smudge_AT_node.inputs[1].default_value = SMR_settings.smudge_locx 
    smudge_AT_node.inputs[2].default_value = SMR_settings.smudge_locy
    smudge_AT_node.inputs[4].default_value = SMR_settings.smudge_scale
    smudge_AT_node.inputs[5].default_value = SMR_settings.smudge_stretch 
    smudge_AT_node.inputs[3].default_value = SMR_settings.smudge_rot
    
    if SMR_settings.smudge_at:
        smudge_AT_node.inputs[6].default_value = SMR_settings.smudge_at_scale 
        smudge_AT_node.inputs[7].default_value = SMR_settings.smudge_at_rot
        smudge_AT_node.inputs[8].default_value = SMR_settings.smudge_at_noise


def update_wear_values (self, context):        
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    if SMR_settings.update_exception:
        return

    try:
        EWear_node = nodes ['SMR_EWear']
        ewear = True
    except:
        ewear = False    
    main_node = nodes['SMR']

    if ewear:
        EWear_node.inputs[0].default_value = SMR_settings.edge_width
    
    main_node.inputs[16].default_value = SMR_settings.edge_color
    main_node.inputs[18].default_value = SMR_settings.cavity_color
    main_node.inputs[19].default_value = SMR_settings.cavity_roughness

def update_wear_sliders():
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR

    try:
        EWear_node = nodes ['SMR_EWear']
        ewear = True
    except:
        ewear = False    
    main_node = nodes['SMR']

    if ewear:
        SMR_settings.edge_width = EWear_node.inputs[0].default_value
    
    SMR_settings.edge_color = main_node.inputs[16].default_value  
    SMR_settings.cavity_color = main_node.inputs[18].default_value 
    SMR_settings.cavity_roughness = main_node.inputs[19].default_value

def update_scratch_values (self, context):        
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    if SMR_settings.update_exception:
        return
        
    scratch_node = nodes['SMR_Scratch']
    scratch_AT_node = nodes ['SMR_AT_Scratch']
    main_node = nodes['SMR']

    scratch_node.inputs[3].default_value = SMR_settings.scratch_intensity
    main_node.inputs[8].default_value = SMR_settings.scratch_bcm_intensity
    main_node.inputs[9].default_value = SMR_settings.scratch_bcm_color 
    scratch_AT_node.inputs[1].default_value = SMR_settings.scratch_locx 
    scratch_AT_node.inputs[2].default_value = SMR_settings.scratch_locy
    scratch_AT_node.inputs[4].default_value = SMR_settings.scratch_scale
    scratch_AT_node.inputs[5].default_value = SMR_settings.scratch_stretch 
    scratch_AT_node.inputs[3].default_value = SMR_settings.scratch_rot
    
    if SMR_settings.scratch_at:
        scratch_AT_node.inputs[6].default_value = SMR_settings.scratch_at_scale 
        scratch_AT_node.inputs[7].default_value = SMR_settings.scratch_at_rot
        scratch_AT_node.inputs[8].default_value = SMR_settings.scratch_at_noise

def update_scratch_sliders ():
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    scratch_node = nodes['SMR_Scratch']
    scratch_AT_node = nodes ['SMR_AT_Scratch']
    main_node = nodes['SMR']

    SMR_settings.scratch_intensity = scratch_node.inputs[3].default_value
    SMR_settings.scratch_bcm_intensity = main_node.inputs[8].default_value
    SMR_settings.scratch_bcm_color = main_node.inputs[9].default_value 
    SMR_settings.scratch_locx = scratch_AT_node.inputs[1].default_value
    SMR_settings.scratch_locy = scratch_AT_node.inputs[2].default_value
    SMR_settings.scratch_scale = scratch_AT_node.inputs[4].default_value
    SMR_settings.scratch_stretch = scratch_AT_node.inputs[5].default_value
    SMR_settings.scratch_rot = scratch_AT_node.inputs[3].default_value
    
    if scratch_AT_node.inputs[0].default_value == 1:
        SMR_settings.scratch_coord = 'Box'
    else:    
        SMR_settings.scratch_coord = 'UV'
    
    if SMR_settings.scratch_at:
        SMR_settings.scratch_at_scale = scratch_AT_node.inputs[6].default_value
        SMR_settings.scratch_at_rot = scratch_AT_node.inputs[7].default_value
        SMR_settings.scratch_at_noise = scratch_AT_node.inputs[8].default_value          

def update_droplets_sliders():
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    main_node = nodes['SMR']
    mapping_node = nodes['SMR_Droplets_Mapping']

    SMR_settings.droplet_scale = mapping_node.inputs[3].default_value[0]
    SMR_settings.droplet_strength = main_node.inputs[10].default_value


def update_droplets_values(self,context):
    mat, nodes, links = get_mat_data()
    SMR_settings= bpy.context.scene.SMR
    
    if SMR_settings.update_exception:
        return

    main_node = nodes['SMR']
    mapping_node = nodes['SMR_Droplets_Mapping']

    mapping_node.inputs[3].default_value = SMR_settings.droplet_scale, SMR_settings.droplet_scale, SMR_settings.droplet_scale
    main_node.inputs[10].default_value = SMR_settings.droplet_strength    