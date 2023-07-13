#pylint: disable=import-error, relative-beyond-top-level, undefined-variable

import bpy
from . smr_pcoll import update_dir
from . update_functions import *
from . smr_pcoll import *
from . SMR_CALLBACK import ui_update
from . SMR_AUTOMATIC import set_custom, preset_update
from . influence_functions import *
from . mat_functions import *

class SMR_SETTINGS(bpy.types.PropertyGroup):
    ####################################
    ########### General ################
        
    #path where the images and .blend files are
    SMR_path: bpy.props.StringProperty(
        name='SMR_path',
        description="file path for SMR",
        default= '',
        subtype = 'DIR_PATH',
        update = update_dir
        )    
 
    #indicates if the if SMR is getting a callback every time the active object changes
    subscribed: bpy.props.BoolProperty(
        name="SMR_subscribed",
        description="Subscribed to active object",
        default=False
        )

    del_confirmation: bpy.props.BoolProperty(
        name="SMR_delete",
        description="Opens a submenu for you to remove part of all of the SMUDGR setup",
        default=False
        )

    diagnostics: bpy.props.BoolProperty(
        name="Error Analysis Mode",
        description="Enables diagnostics",
        default=False
        )

    activation_exception: bpy.props.BoolProperty(
        name="SMR_exception",
        description="",
        default=False
        )
    
    SMR_active_mat: bpy.props.StringProperty(
        name='SMR_activemat',
        description="Active material for SMR",
        default= 'Material',
        )         

    update_exception: bpy.props.BoolProperty(
        name="update_exception",
        description="",
        default=False
        )

    glass_node_choice: bpy.props.BoolProperty(
        name="glass choice",
        description="",
        default=False
        )
    forbidden_node_choice: bpy.props.BoolProperty(
        name="node choice",
        description="",
        default=False
        )
    
    active_smudge_ui: bpy.props.StringProperty(
        name='Active Smudge',
        description="The smudge that is currently on your object",
        default= '',
        )        

    active_scratch_ui: bpy.props.StringProperty(
        name='Active Scratch',
        description="The scratch that is currently on your object",
        default= '',
        )  

    decal_mat: bpy.props.BoolProperty(
        name="Base",
        description="",
        default=True
        )
    decal_sub: bpy.props.BoolProperty(
        name="Subset",
        description="",
        default=False
        )
    ##################################
    ###### Preview collections #######

    #current image in the image selector
    prev_dust: bpy.props.EnumProperty(
        items = dust_previews,
        update = update_dust
        )

    #current image in the image selector
    prev_smudge: bpy.props.EnumProperty(
        items = smudge_previews,
        update = update_smudge
        )
    

    #current image in the image selector
    prev_scratch: bpy.props.EnumProperty(
        items = scratch_previews,
        update = update_scratch
        )
    
    prev_droplets: bpy.props.EnumProperty(
        items = droplets_previews,
        update = update_droplets
        )

    smudge_categ: bpy.props.EnumProperty(
        name="Smudge category",
        description="Categories for smudges",
        items = [
                ("All", "All", "",  0),
                ("Smudges", "Smudges", "",  1),
                ("Stains", "Stains", "",  2),
                ("Wipes", "Wipes", "",  3),
                ("Other", "Other", "",  4),
            ],
        default = "All",
        update = change_smudge_categ
        )
    

    #################################
    ############### UI  #############   
    
    is_SMR_object: bpy.props.BoolProperty(
        name="is_a_SMR_object",
        description="",
        default=False
        )

    pack_ui: bpy.props.BoolProperty(
        name="pack_ui",
        description="",
        default=False
        )
    
    dev_ops: bpy.props.BoolProperty(
        name="Developer Options",
        description="",
        default=False
        )

    has_bake: bpy.props.BoolProperty(
        name="has bake",
        description="",
        default=False
        )
    has_bake2: bpy.props.BoolProperty(
        name="has bake",
        description="",
        default=False
        )    
    wear_cavity_ui: bpy.props.BoolProperty(
        name="Cavity Wear",
        description="",
        default=False
        )
    wear_cavity: bpy.props.BoolProperty(
        name="has cavity",
        description="",
        default=False
        ) 
    wear_edge_ui: bpy.props.BoolProperty(
        name="Edge Wear",
        description="",
        default=False
        )
    wear_edge: bpy.props.BoolProperty(
        name="has cavity",
        description="",
        default=False
        )                
    auto_advanced_ui: bpy.props.BoolProperty(
        name="Advanced Settings",
        description="",
        default=False
        )    
    is_SMR_slot: bpy.props.BoolProperty(
        name="is_a_SMR_slot",
        description="",
        default=False
        )        
    has_smudge: bpy.props.BoolProperty(
        name="has_smudge",
        description="",
        default=False
        )
    has_droplets: bpy.props.BoolProperty(
        name="has_droplets",
        description="",
        default=False
        )    
    has_dust: bpy.props.BoolProperty(
        name="has_dust",
        description="",
        default=False
        )
    
    has_scratch: bpy.props.BoolProperty(
        name="has_scratch",
        description="",
        default=False
        )
        
    forbidden_node_choice: bpy.props.BoolProperty(
        name="has_forbidden_node",
        description="",
        default=False
        )                        
    
    inf_remove_confirmation: bpy.props.BoolProperty(
        name="removal confirmation",
        description="",
        default=False
        )  
        
    pack_confirmation: bpy.props.BoolProperty(
        name="rpackconfirmation",
        description="",
        default=False
        )      
    
    smr_ui_categ: bpy.props.EnumProperty(
        name="Smudge ui category",
        description="UI categories for smudges",
        items = [
                ("Dust", "Dust", "", "OUTLINER_DATA_POINTCLOUD", 0),
                ("Smudge", "Smudge", "", "MOD_DYNAMICPAINT", 1),
                ("Scratch", "Scratch", "", "GPBRUSH_SMOOTH", 2),
                ("Wear", "Wear", "", "MOD_NOISE", 3),
                ("Droplets", "Droplets", "", "MOD_FLUIDSIM", 4),
                ("Utilities", "Utilities", "", "TOOL_SETTINGS", 5),
            ],
        default = "Dust",
        update = ui_update
        )
        
    creation_presets: bpy.props.EnumProperty(
        name="Smudge preset category",
        description="preset categories for smudges",
        items = [
                ("Brand New", "Brand New", "", 0),
                ("Dusty", "Dusty", "",  1),
                ("Well Used", "Well Used", "",  2),
                ("Very Old", "Very Old", "",  3),
                ("Custom", "Custom", "",  4),
            ],
        default = "Brand New",
        update = preset_update
        )    

    preview: bpy.props.BoolProperty(
        name="has_scratch",
        description="",
        default=False
        )
    

    

    ######## smudge ##############
    smudge_at: bpy.props.BoolProperty(
        name="anti tiling smudge",
        description="",
        default=False
        )

    smudge_bcm: bpy.props.BoolProperty(
        name="Base Color Mixing",
        description="",
        default=False
        )

    smudge_at_settings: bpy.props.BoolProperty(
        name="Anti-Tiling settings",
        description="",
        default=False
        )      
    smudge_advanced: bpy.props.BoolProperty(
        name="Advanced settings",
        description="",
        default=False
        )
    inf_smudge_bcm: bpy.props.BoolProperty(
        name="bcm smudge influence",
        description="",
        default=False
        )
    
    inf_smudge_bcm_ui: bpy.props.BoolProperty(
        name="Influence Map: BCM Intensity",
        description="",
        default=False
        )        
    
    inftype_smudge_bcm: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Cavity", "Cavity", "", 1),
                ("Texture Paint", "Texture Paint", "", 2),
                ("Geometry", "Geometry", "", 3),
                ("Gradient", "Gradient", "", 4)
            ],
        default = "Noise",
        update = change_inftype_smudge_bcm
        )                
    
    inf_smudge_int: bpy.props.BoolProperty(
        name="smudge intensity influence",
        description="",
        default=False
        )
    
    inf_smudge_int_ui: bpy.props.BoolProperty(
        name="Influence: Smudge Roughness",
        description="",
        default=False
        )    
        
    inftype_smudge_int: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Cavity", "Cavity", "", 1),
                ("Texture Paint", "Texture Paint", "", 2),
                ("Geometry", "Geometry", "", 3),
                ("Gradient", "Gradient", "", 4)
            ],
        default = "Noise",
        update = change_inftype_smudge_int
        )
              
    smudge_res: bpy.props.EnumProperty(
        name="Active Smudge Resolution",
        description="Smudge Resolution",
        items = [
                ("1K", "1K", "", 0),
                ("2K", "2K", "", 1),
                ("4K", "4K", "", 2),
            ],
        default = "1K",
        update = change_smudge_res
        )
      
    smudge_falloff: bpy.props.FloatProperty(name = "Falloff", description = "Change falloff of the smudge texture", default = 1, step = 1, precision = 1, min = 0, max = 1, update = update_smudge_values)
    smudge_roughness: bpy.props.FloatProperty(name = "Roughness", description = "Change roughness of smudge texture, negative for inverted effect", default = 1, step = 1, precision = 1, min = -1, max = 1, update = update_smudge_values)
    smudge_bcm_falloff: bpy.props.FloatProperty(name = "BCM Falloff", description = "Change falloff of the base color mixing", default = 1, step = 1, precision = 1, min = 0, max = 1, update = update_smudge_values)
    smudge_bcm_intensity: bpy.props.FloatProperty(name = "BCM Intensity", description = "Change intensity of the base color mixing", default = 0, step = 1, precision = 1, min = 0, max = 1, update = update_smudge_values)
    
    smudge_bcm_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the smudges",
        update= update_smudge_values
        )

    smudge_locx: bpy.props.FloatProperty(name = "Loc x", description = "Move texture on X axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_smudge_values)
    smudge_locy: bpy.props.FloatProperty(name = "Loc y", description = "Move texture on y axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_smudge_values)
    smudge_scale: bpy.props.FloatProperty(name = "Scale", description = "Scale texture", default = 5, step = 1, precision = 3, min = 0.001, max = 50, update = update_smudge_values)
    smudge_stretch: bpy.props.FloatProperty(name = "Stretching", description = "Stretch texture", default = 1, step = 1, precision = 2, min = 0.01, max = 10, update = update_smudge_values)
    smudge_rot: bpy.props.FloatProperty(name = "Rotation", description = "Rotate texture", default = 0, step = 1, precision = 2, min = -20, max = 20, update = update_smudge_values)
    smudge_at_rot: bpy.props.FloatProperty(name = "AT rotation", description = "Rotate AT part of texture", default = 5, step = 1, precision = 2, min = -20, max = 20, update = update_smudge_values)
    smudge_at_noise: bpy.props.FloatProperty(name = "AT noise scale", description = "Scale the noise that controls AT", default = 5, step = 1, precision = 2, min = -100, max = 100, update = update_smudge_values)
    smudge_at_scale: bpy.props.FloatProperty(name = "AT scale", description = "Scale AT part of texture", default = 1.2, step = 1, precision = 1, min = 0.1, max = 5, update = update_smudge_values)
    smudge_coord: bpy.props.EnumProperty(
        name="Coordinates",
        description="Change the way smudge textures are applied",
        items = [
                ("Box", "Box", "", 0),
                ("UV", "UV", "", 1),
            ],
        default = "Box",
        update = change_smudge_coord
        )



    ###### scratch #########
    scratch_at: bpy.props.BoolProperty(
        name="anti tiling scratch",
        description="",
        default=False
        )
    scratch_at_settings: bpy.props.BoolProperty(
        name="Anti-Tiling settings",
        description="",
        default=False
        )    
    scratch_advanced: bpy.props.BoolProperty(
        name="Advanced settings",
        description="",
        default=False
        ) 

    scratch_bcm: bpy.props.BoolProperty(
        name="Base Color Mixing",
        description="",
        default=False
        )
    
    inf_scratch_bcm: bpy.props.BoolProperty(
        name="bcm scratch influence",
        description="",
        default=False
        )
    
    inf_scratch_bcm_ui: bpy.props.BoolProperty(
        name="Influence Map: BCM Intensity",
        description="",
        default=False
        )            
    
    inftype_scratch_bcm: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Cavity", "Cavity", "", 1),
                ("Texture Paint", "Texture Paint", "", 2),
                ("Geometry", "Geometry", "", 3),
                ("Gradient", "Gradient", "", 4)
            ],
        default = "Noise",
        update = change_inftype_scratch_bcm
        ) 
        
    inf_scratch_int: bpy.props.BoolProperty(
        name="Influence Map: Scratch Intensity",
        description="",
        default=False
        )
    
    inf_scratch_int_ui: bpy.props.BoolProperty(
        name="Influence Map: Scratch Intensity",
        description="",
        default=False
        )
    
    inftype_scratch_int: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Cavity", "Cavity", "", 1),
                ("Texture Paint", "Texture Paint", "", 2),
                ("Geometry", "Geometry", "", 3),
                ("Gradient", "Gradient", "", 4)
            ],
        default = "Noise",
        update = change_inftype_scratch_int
        )    
         
    scratch_res: bpy.props.EnumProperty(
        name="Active Scratch Resolution",
        description="Scratch Resolution",
        items = [
                ("1K", "1K", "", 0),
                ("2K", "2K", "", 1),
                ("4K", "4K", "", 2),
            ],
        default = "1K",
        update = change_scratch_res
        )

    scratch_intensity: bpy.props.FloatProperty(name = "Depth", description = "Change depth of scratches", default = .2, step = 1, precision = 2, min = 0, max = 1, update = update_scratch_values)
    scratch_bcm_intensity: bpy.props.FloatProperty(name = "BCM Intensity", description = "Change intensity of the base color mixing", default = 0, step = 1, precision = 1, min = 0, max = 1, update = update_scratch_values)
    
    scratch_bcm_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the smudges",
        update= update_scratch_values
        )
        
    scratch_locx: bpy.props.FloatProperty(name = "Loc x", description = "Move texture on X axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_scratch_values)
    scratch_locy: bpy.props.FloatProperty(name = "Loc y", description = "Move texture on y axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_scratch_values)
    scratch_scale: bpy.props.FloatProperty(name = "Scale", description = "Scale texture", default = 15, step = 1, precision = 3, min = 0.001, max = 50, update = update_scratch_values)
    scratch_stretch: bpy.props.FloatProperty(name = "Stretching", description = "Stretch texture", default = 1, step = 1, precision = 2, min = 0.01, max = 10, update = update_scratch_values)
    scratch_rot: bpy.props.FloatProperty(name = "Rotation", description = "Rotate texture", default = 0, step = 1, precision = 2, min = -20, max = 20, update = update_scratch_values)
    scratch_at_rot: bpy.props.FloatProperty(name = "AT rotation", description = "Rotate AT part of texture", default = 5, step = 1, precision = 2, min = -20, max = 20, update = update_scratch_values)
    scratch_at_noise: bpy.props.FloatProperty(name = "AT noise scale", description = "Scale the noise that controls AT", default = 5, step = 1, precision = 2, min = -100, max = 100, update = update_scratch_values)
    scratch_at_scale: bpy.props.FloatProperty(name = "AT scale", description = "Scale AT part of texture", default = 1.2, step = 1, precision = 1, min = 0.1, max = 5, update = update_scratch_values)
    scratch_coord: bpy.props.EnumProperty(
        name="Coordinates",
        description="Change the way scratch textures are applied",
        items = [
                ("Box", "Box", "", 0),
                ("UV", "UV", "", 1),
            ],
        default = "Box",
        update = change_scratch_coord
        )        
        
        
        
    ################# influence values ###################### 
    inf1_black: bpy.props.FloatProperty(name = "Boost Blacks", description = "Make the darkest pixels even daker", default = 0, step = 1, precision = 0, min = 0, soft_max = 100, max = 200, subtype = 'PERCENTAGE', update = update_influence_values)
    inf1_white: bpy.props.FloatProperty(name = "Boost White", description = "Make the brightest pixels even brighter", default = 0, step = 1, precision = 2, min = 0, soft_max = 100, max = 200, subtype = 'PERCENTAGE', update = update_influence_values)
    inf1_mult: bpy.props.FloatProperty(name = "Multiplier", description = "Go past the 0-1 range to make your effects more intense", default = 1, step = 1, precision = 2, min = -10, max = 20, update = update_influence_values)
    inf1_inf: bpy.props.FloatProperty(name = "influence", description = "Determine how much this texture influences your result", default = 1, step = 1, precision = 2, min = 0, max = 1, update = update_influence_values)
    inf1_val1: bpy.props.FloatProperty(name = "val1", description = "val1", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf1_val2: bpy.props.FloatProperty(name = "val2", description = "val2", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf1_val3: bpy.props.FloatProperty(name = "val3", description = "val3", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf1_val4: bpy.props.FloatProperty(name = "val4", description = "val4", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    
    inf2_black: bpy.props.FloatProperty(name = "Boost Blacks", description = "Make the darkest pixels even daker", default = 0, step = 1, precision = 2, min = 0, soft_max = 100, max = 200,subtype = 'PERCENTAGE', update = update_influence_values)
    inf2_white: bpy.props.FloatProperty(name = "Boost White", description = "Make the brightest pixels even brighter", default = 0, step = 1, precision = 2, min = 0, soft_max = 100, max = 200, subtype = 'PERCENTAGE', update = update_influence_values)
    inf2_mult: bpy.props.FloatProperty(name = "Multiplier", description = "Go past the 0-1 range to make your effects more intense", default = 1, step = 1, precision = 2, min = -10, max = 20, update = update_influence_values)
    inf2_inf: bpy.props.FloatProperty(name = "influence", description = "Determine how much this texture influences your result", default = 1, step = 1, precision = 2, min = 0, max = 1, update = update_influence_values)
    inf2_val1: bpy.props.FloatProperty(name = "val1", description = "val1", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf2_val2: bpy.props.FloatProperty(name = "val2", description = "val2", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf2_val3: bpy.props.FloatProperty(name = "val3", description = "val3", default = 0, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)
    inf2_val4: bpy.props.FloatProperty(name = "val4", description = "val4", default = 0.01, step = 1, precision = 2, min = -50, max = 50, update = update_influence_values)  


    ################ Wear ############################

    edge_width: bpy.props.FloatProperty(name = "Edge Width", description = "val4", default = 0.001, step = 1, precision = 3, min = 0.001, max = 1, update = update_wear_values)     
    
    cavity_roughness: bpy.props.FloatProperty(name = "Cavity roughness", description = "Cavity roughness", default = .5, step = 1, precision = 1, min = 0, max = 1, update = update_wear_values)  

    edge_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(0, 0, 0,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the edge",
        update= update_wear_values
        )

    cavity_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(.2, .2, .2,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the cavity",
        update= update_wear_values
        )


    wearmode_bake: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake
        )    
    wearmode_bake2: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake2
        ) 
    wearmode_ScIntensity: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake
        )    
    wearmode_SmIntensity: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake
        ) 
    wearmode_ScBCM: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake2
        )    
    wearmode_SmBCM: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake2
        )   
    wearmode_Dust1: bpy.props.EnumProperty(
        name="Active wear mode",
        description="Active ",
        items = [
                ("Baked", "Baked", "", 0),
                ("Live", "Live", "", 1),
            ],
        default = "Baked",
        update = change_wearmode_bake
        )
    bake1_res: bpy.props.EnumProperty(
        name="Bake resolution",
        description="Resolution for baking",
        items = [
                ("512", "512", "", 0),
                ("1024", "1024", "", 1),
                ("2048", "2048", "", 2),
                ("4096", "4096", "", 3),
            ],
        default = "1024",
        )
    bake2_res: bpy.props.EnumProperty(
        name="Bake resolution",
        description="Resolution for baking",
        items = [
                ("512", "512", "", 0),
                ("1024", "1024", "", 1),
                ("2048", "2048", "", 2),
                ("4096", "4096", "", 3),
            ],
        default = "1024",
        )   
    bake1_samples: bpy.props.EnumProperty(
        name="Samples",
        description="Samples for baking",
        items = [
                ("2", "2", "", 0),
                ("4", "4", "", 1),
                ("8", "8", "", 2),
                ("16", "16", "", 3),
                ("64", "64 ", "", 4),
                ("256", "256 ", "", 5),
                ("1000", "1000 ", "", 6)
            ],
        default = "4",
        ) 
    bake2_samples: bpy.props.EnumProperty(
        name="Bake samples",
        description="Samples for baking",
        items = [
                ("2", "2", "", 0),
                ("4", "4", "", 1),
                ("8", "8", "", 2),
                ("16", "16", "", 3),
                ("64", "64", "", 4),
                ("256", "256 ", "", 5),
                ("1000", "1000 ", "", 6)
            ],
        default = "4",
        )               
    fullbake_res: bpy.props.EnumProperty(
        name="Full Bake resolution",
        description="Resolution for baking",
        items = [
                ("512", "512", "", 0),
                ("1024", "1024", "", 1),
                ("2048", "2048", "", 2),
                ("4096", "4096", "", 3),
                ("8192", "8192 (Not recommended)", "", 3)
            ],
        default = "1024",
        )
    fullbake_samples: bpy.props.EnumProperty(
        name="Full Bake samples",
        description="Samples for baking",
        items = [
                ("2", "2", "", 0),
                ("4", "4", "", 1),
                ("8", "8", "", 2),
                ("16", "16", "", 3),
                ("64", "64", "", 4),
            ],
        default = "2",
        )     
                                                        
    ################# auto smudgr values ######################  
    auto_dust: bpy.props.BoolProperty(
        name="Dust",
        description="",
        default=False,
        update = set_custom
        ) 
    
    auto_dust_strength: bpy.props.FloatProperty(name = "Dust strenght", description = "Multiplies the dust effect", default = 8, step = 1, precision = 1, min = 0, max = 25, update = set_custom)
    auto_dust_side: bpy.props.FloatProperty(name = "Dust side factor", description = "Also puts dust on sides not facing upwards", default = 0, step = 1, precision = 2, min = 0, max = 1, update = set_custom)
    auto_dust_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the dust",
        update = set_custom
        )

    auto_smudge: bpy.props.BoolProperty(
        name="Smudges",
        description="",
        default=True,
        update = set_custom
        ) 
    auto_smudge_strength: bpy.props.FloatProperty(name = "Smudge Strength", description = "Strength of smudge effect", default = .6, step = 1, precision = 2, min = 0, max = 1, update = set_custom)
    auto_smudge_bcm: bpy.props.FloatProperty(name = "Bace color mixing", description = "Adds color to smudges", default = 0, step = 1, precision = 2, min = 0, max = 1, update = set_custom)
    auto_smudge_random: bpy.props.BoolProperty(name="Randomize smudge strength", description="", default=False, update = set_custom) 
    auto_smudge_bcm_random: bpy.props.BoolProperty(name="Randomize smudge BCM strenght", description="", default=False, update = set_custom) 
    auto_smudge_bcm_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the bcm",
        update = set_custom
        )

    auto_scratch: bpy.props.BoolProperty(
        name="Scratch",
        description="",
        default=True,
        update = set_custom
        )       
    auto_scratch_strength: bpy.props.FloatProperty(name = "Scratch Strength", description = "Strength of smudge effect", default = .03, step = 1, precision = 2, min = 0, max = 1, update = set_custom)
    auto_scratch_random: bpy.props.BoolProperty(name="Randomize scratch strength", description="", default=False, update = set_custom)

    auto_cwear: bpy.props.BoolProperty(
        name="Cavity wear",
        description="",
        default=False,
        update = set_custom
        )  
    auto_cwear_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the cavity wear",
        update = set_custom
        )
    auto_cwear_mult: bpy.props.FloatProperty(name = "Cavity multiplier", description = "Multiplies the strength of the cavity effect", default = 1, step = 1, precision = 2, min = 0, max = 50, update = set_custom)


    custom_exception: bpy.props.BoolProperty(name="custom exception", description="", default=False) 

    ############# Dust ####################
    dust_at: bpy.props.BoolProperty(
        name="anti tiling dust",
        description="",
        default=False
        )

    dust_at_settings: bpy.props.BoolProperty(
        name="Anti-Tiling settings",
        description="",
        default=False
        )      
    dust_advanced: bpy.props.BoolProperty(
        name="Advanced settings",
        description="",
        default=False
        )

      
    dust_multiplier: bpy.props.FloatProperty(name = "Multiplier", description = "Multiplies the dust effect", default = 8, step = 1, precision = 1, min = 0, max = 25, update = update_dust_values)
    dust_side: bpy.props.FloatProperty(name = "Side Dust", description = "Also puts dust on the sides of your object", default = 0, step = 1, precision = 1, min = 0, max = 1, update = update_dust_values)
    dust_influence: bpy.props.FloatProperty(name = "Influence map", description = "Decreasing this will make the influence map less prevelent", default = .6, step = 1, precision = 1, min = 0, max = 1, update = update_dust_values)
    
    dust_color: bpy.props.FloatVectorProperty(
        name = "",
        subtype='COLOR',
        default=(1, 1, 1,1),
        min=0.0,
        max=1.0,
        size=4,
        description="Color of the dust",
        update= update_dust_values
        )

    dust_locx: bpy.props.FloatProperty(name = "Loc x", description = "Move texture on X axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_dust_values)
    dust_locy: bpy.props.FloatProperty(name = "Loc y", description = "Move texture on y axis", default = 0, step = 1, precision = 2, min = -100, max = 100, update = update_dust_values)
    dust_scale: bpy.props.FloatProperty(name = "Influence Scale", description = "Scale texture", default = 5, step = 1, precision = 3, min = 0.001, max = 50, update = update_dust_values)
    dust_genscale: bpy.props.FloatProperty(name = "Dust Scale", description = "Scale underlaying dust texture", default = 5, step = 1, precision = 3, min = 0.001, max = 50, update = update_dust_values)
    dust_stretch: bpy.props.FloatProperty(name = "Stretching", description = "Stretch texture", default = 1, step = 1, precision = 2, min = 0.01, max = 10, update = update_dust_values)
    dust_rot: bpy.props.FloatProperty(name = "Rotation", description = "Rotate texture", default = 0, step = 1, precision = 2, min = -20, max = 20, update = update_dust_values)
    dust_at_rot: bpy.props.FloatProperty(name = "AT rotation", description = "Rotate AT part of texture", default = 5, step = 1, precision = 2, min = -20, max = 20, update = update_dust_values)
    dust_at_noise: bpy.props.FloatProperty(name = "AT noise scale", description = "Scale the noise that controls AT", default = 5, step = 1, precision = 2, min = -100, max = 100, update = update_dust_values)
    dust_at_scale: bpy.props.FloatProperty(name = "AT scale", description = "Scale AT part of texture", default = 1.2, step = 1, precision = 1, min = 0.1, max = 5, update = update_dust_values)
    dust_coord: bpy.props.EnumProperty(
        name="Coordinates",
        description="Change the way dust textures are applied",
        items = [
                ("Box", "Box", "", 0),
                ("UV", "UV", "", 1),
            ],
        default = "Box",
        update = change_dust_coord
        )   

    inf_dust1: bpy.props.BoolProperty(
        name="Influence Map",
        description="",
        default=False
        ) 
    inf_dust1_ui: bpy.props.BoolProperty(
        name="Influence Map: Multiplier",
        description="",
        default=False
        )

    inftype_dust1: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Cavity", "Cavity", "", 1),
                ("Texture Paint", "Texture Paint", "", 2),
                ("Gradient", "Gradient", "", 3)
            ],
        default = "Noise",
        update = change_inftype_dust1
        )
    
    inf_dust_inf: bpy.props.BoolProperty(
        name="Influence Map",
        description="",
        default=False
        ) 
    inf_dust_inf_ui: bpy.props.BoolProperty(
        name="Influence Map: Dust Influence Map",
        description="",
        default=False
        )

    inftype_dust_inf: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Texture Paint", "Texture Paint", "", 1),
                ("Gradient", "Gradient", "", 2)
            ],
        default = "Noise",
        update = change_inftype_dust_inf
        )
    ########## droplets ###############

    droplet_strength: bpy.props.FloatProperty(name = "Droplet strength", description = "Sets how strong the droplet effect is", default = .5, step = 1, precision = 2, min = 0, max = 1, update = update_droplets_values)
    droplet_scale: bpy.props.FloatProperty(name = "Droplet scale", description = "Change scale of droplets", default = 5, step = 1, precision = 3, min = 0, max = 999, update = update_droplets_values)
    
    inf_droplets: bpy.props.BoolProperty(
        name="Influence Map",
        description="",
        default=False
        ) 
    inf_droplets_ui: bpy.props.BoolProperty(
        name="Influence Map: Droplet Strength",
        description="",
        default=False
        )

    inftype_droplets: bpy.props.EnumProperty(
        name="Active Influence Map",
        description="Active Influence Map",
        items = [
                ("Noise", "Noise", "", 0),
                ("Texture Paint", "Texture Paint", "", 1),
                ("Gradient", "Gradient", "", 2)
            ],
        default = "Noise",
        update = change_inftype_droplets
        )