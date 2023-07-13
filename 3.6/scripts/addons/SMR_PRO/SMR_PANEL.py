#pylint: disable=import-error, relative-beyond-top-level
import bpy

class SMR_PANEL(bpy.types.Panel):
    """
    Main panel, can be found in properties>material
    """  

    bl_idname = "SMR_PT_Panel"
    bl_label = "SMUDGR Pro"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    COMPAT_ENGINES = {'CYCLES'}

    def draw(self, context):
        settings = bpy.context.scene.SMR
        layout = self.layout
        pref = bpy.context.preferences.addons['SMR_PRO'].preferences

        if settings.SMR_path == '':
            try:
                if context.window.scene ==bpy.data.scenes['SMR_Bake']:
                    col=layout.column()
                    col.scale_y = 2.5
                    col.label(text='You are in the SMR_Bake scene', icon='INFO')
                    col.operator('smr.getback', text='Take Me Back!')
                    return
                else:
                    col=layout.column()
                    col.scale_y = 3
                    col.label(text = 'Please update the path in the addon preferences')
                    return                    
            except:
                col=layout.column()
                col.scale_y = 3
                col.label(text = 'Please update the path in the addon preferences')
                return

        #activate button
        if not settings.subscribed:
            col = layout.column()    
            col.operator("smr.activate", text="Activate")
            return




        obj = context.object
        layout.template_list("SMR_UL_SLOTS_UI", "", obj, "material_slots", obj, "active_material_index")
        col = layout.column() 
        col.operator("smr.slot", text="Make this slot active", icon= "MOUSE_LMB")

        try:
            mat = bpy.data.materials[settings.SMR_active_mat]
        except:
            col.label(text = 'The active material changed names')
            col.label(text= 'Please press "Make this slot active"')
            return

        if 'SMR_BAKE' in mat:
            col = layout.column()
            col.scale_y = 2
            col.label(text = 'This is a baked Smudgr material', icon = 'INFO')
            col.label(text='Press Ctrl+Z/Undo to revert to the unbaked material', icon = 'INFO')
            col.operator('smr.applydecal', text = 'Apply material to DM decals', icon = 'INFO')
            return

        if settings.pack_ui:
            col = layout.column() 
            col.label(text = 'You still have an image you have to pack', icon = 'ERROR')
            col.operator("smr.pack", text="Pack Image")
            col.operator("smr.nopack", text="Don't Pack")
            return   
        
        box = layout.box()
        boxbox = box.box().box().box() if not pref.small_ui else box.box()

        
        row=boxbox.row()
        row.alignment = 'CENTER'
        row.scale_y = 2 if not pref.small_ui else 1
        row.label(text="SMUDGR Pro", icon ='EVENT_S')         
        
        if settings.glass_node_choice:
            col = layout.column() 
            col.label(text = "SMUDGR found a glass node, but also other shader nodes", icon = 'INFO')
            col.label(text = "What do you want to do?")
            col.operator('smr.forcechoice', text = 'Connect to glass node')
            col.operator('smr.manualchoice', text = 'Connect nodes myself')
            col.operator('smr.nochoice', text = 'Cancel')
            return           

        if settings.forbidden_node_choice:
            col = layout.column() 
            col.label(text = "SMUDGR found a Principled BSDF, but also other shader nodes", icon = 'INFO')
            col.label(text = "What do you want to do?")
            col.operator('smr.forcechoice', text = 'Connect to Principled BSDF')
            col.operator('smr.manualchoice', text = 'Connect nodes myself')
            col.operator('smr.nochoice', text = 'Cancel')
            return 

        if not settings.is_SMR_slot:
            col = layout.column() 
            col.label(text = "This material does not yet contain a SMUDGR setup")
            
            try:
                if context.active_object.DM.isdecal:
                    col.separator()
                    col.label(text = 'Decal: Apply Smudgr to:')
                    row = col.row(align = True)
                    row.scale_y = 1.5
                    row.prop(settings, 'decal_mat', toggle = 1)
                    row.prop(settings, 'decal_sub', toggle = 1)
            except:
                pass

            box, col, row = get_box(layout)
            
            col_high = col.column()
            col_high.scale_y =2
            if not pref.small_ui:
                col_high.label(text = 'Manual setup', icon = 'MATERIAL')
            col_high.operator("smr.addmain", text="Add SMUDGR setup")
            
            box, col, row = get_box(layout)
            
            col_high = col.column()
            col_high.scale_y =2
            if not pref.small_ui:
                col_high.label(text = 'Automatic Setup ', icon = 'TIME')
            col_high.operator("smr.automatic", text="Add Automatic Setup")
            row = col_high.row(align = True)
            row.label(text='Presets:')
            row.prop(settings, 'creation_presets', expand=True)
            if settings.auto_cwear:
                col_high = col_high.column()
                row = col_high.row()
                row.label(text='This preset includes cavity', icon='ERROR')
                row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_cavity_choice'
            
                     
            box = box.box()
            col = box.column()
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(settings, 'auto_advanced_ui',
                icon="TRIA_DOWN" if settings.auto_advanced_ui else "TRIA_RIGHT",
                emboss=False,
                toggle=True)
            if settings.auto_advanced_ui:
                presets_ui(settings, col,layout)
            
            col=layout.column()        
            col.label(text = 'Note: Textures are applied using real scale', icon= 'INFO')      
            col.prop(settings, 'diagnostics')
            return
        
       

        # UI categories buttons, switches between panels for each category
        row = layout.row()
        row.scale_y = 3
        row.prop(settings, 'smr_ui_categ', expand=True)
        

        ######## Scratch menu #########

        if settings.smr_ui_categ == 'Scratch':        
            box = layout.box()
            boxbox = box.box().row()
            boxbox.label(text="Scratches") 
            boxbox.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_scratch'
            boxbox.prop(settings, 'del_confirmation', text = '', icon = 'TRASH', emboss=True,toggle=True)

            if settings.del_confirmation:
                col=layout.column()
                col.scale_y = 2
                if settings.has_scratch:
                    col.operator("smr.cdelete", text =  'Remove SCRATCHES from this material', icon = "TRASH")
                col.operator("smr.adelete", text =  'Remove ALL SMUDGR setups from this material', icon = "TRASH")             
            
            if not settings.has_scratch:
                col = layout.column()    
                col.label(text = "You have not yet added scratches")
                col.operator("smr.addpart", text="Add scratches").categ = 'Scratch'
                return 
            
            scratch_menu(self, context, layout, settings)
        


        ############ droplets #############
        if settings.smr_ui_categ == 'Droplets': 
            box = layout.box()
            boxbox = box.box().row()
            boxbox.label(text="Water droplets") 
            boxbox.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_droplets'
            boxbox.prop(settings, 'del_confirmation', text = '', icon = 'TRASH', emboss=True,toggle=True)

            if settings.del_confirmation:
                col=layout.column()
                col.scale_y = 2
                if settings.has_droplets:
                    col.operator("smr.cdelete", text =  'Remove DROPLETS from this material', icon = "TRASH")
                col.operator("smr.adelete", text =  'Remove ALL SMUDGR setups from this material', icon = "TRASH")               
            
            col = layout.column()
            if not settings.has_droplets:    
                col.label(text = "You have not yet added droplets")
                col.operator("smr.addpart", text="Add droplets").categ = 'Droplets'
                col.label(text = "Looks best on glass, since it uses a normal map", icon='INFO')
                return
            
            col.template_icon_view(context.scene.SMR, "prev_droplets", show_labels=True, scale=11)
            col = layout.column()
            row = col.row(align=True)
            row.operator("smr.previous", text="Previous", icon='TRIA_LEFT')
            row.operator("smr.next", text="Next", icon='TRIA_RIGHT')

            col = layout.column()
            row = col.row(align=True)
            if not settings.inf_droplets:
                row_left = row.row(align=True)
                row_right = row.column(align=True)
                row_right.scale_x = 1.5
                row_left.prop(settings, 'droplet_strength' , slider = True)
                row_right.operator("smr.influence", text="", icon = "BRUSH_DATA" ).type = 'Droplets'
            else:
                row.label(text= 'Droplet Strength: Influence Map') 
            
            col.prop(settings, 'droplet_scale')
            col2 = col.column()
            col2.scale_y = 2
            col2.label(text="Droplets need a UV map, otherwise you can't see them", icon = 'INFO')
            
            if settings.inf_droplets:
                box, col, row = get_box(layout)
                row.prop(settings, 'inf_droplets_ui',
                    icon="TRIA_DOWN" if settings.inf_droplets_ui else "BRUSH_DATA",
                    emboss=False,
                    toggle=True)
                if settings.inf_droplets_ui:
                    row= col.row()
                    row.scale_y=2
                    row.prop(settings, 'inftype_droplets', expand=True)
                    influence_ui(settings, box, row, col, 'Droplets', settings.inftype_droplets)

        ########## wear menu ###############

        if settings.smr_ui_categ == 'Wear':        
            box = layout.box()
            boxbox = box.box().row()
            boxbox.label(text="Wear & Tear") 
            boxbox.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_wear'
            boxbox.prop(settings, 'del_confirmation', text = '', icon = 'TRASH', emboss=True,toggle=True)

            if settings.del_confirmation:
                col=layout.column()
                col.scale_y = 2
                if settings.wear_edge or settings.wear_cavity:
                    col.operator("smr.cdelete", text =  'Remove WEAR effects from this material', icon = "TRASH")
                col.operator("smr.adelete", text =  'Remove ALL SMUDGR setups from this material', icon = "TRASH")   
            
            if not settings.wear_cavity:
                col = layout.column()
                col.scale_y = 2
                col.operator("smr.addpart", text="Add cavity wear").categ = 'Cavity'   
            else:
                box, col, row = get_box(layout)
                row.prop(settings, 'wear_cavity_ui',
                    icon="TRIA_DOWN" if settings.wear_cavity_ui else "TRIA_RIGHT",
                    emboss=False,
                    toggle=True)
                if settings.wear_cavity_ui:                
                    wear_menu (box, settings, 'CWear')

            if not settings.wear_edge:
                col = layout.column()
                col.scale_y = 2
                col.operator("smr.addpart", text="Add edge wear").categ = 'Edge'   
            else:
                box, col, row = get_box(layout)

                
                row.prop(settings, 'wear_edge_ui',
                    icon="TRIA_DOWN" if settings.wear_edge_ui else "TRIA_RIGHT",
                    emboss=False,
                    toggle=True)
                if settings.wear_edge_ui:
                    wear_menu (box, settings, 'EWear')                         
        
        ########## Dust menu ##########
                
        if settings.smr_ui_categ == 'Dust':
            box = layout.box()
            boxbox = box.box().row()
            boxbox.label(text="Dust") 
            boxbox.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_dust'
            boxbox.prop(settings, 'del_confirmation', text = '', icon = 'TRASH', emboss=True,toggle=True)

            if settings.del_confirmation:
                col=layout.column()
                col.scale_y = 2
                if settings.has_dust:
                    col.operator("smr.cdelete", text =  'Remove DUST from this material', icon = "TRASH")
                col.operator("smr.adelete", text =  'Remove ALL SMUDGR setups from this material', icon = "TRASH")   

            if not settings.has_dust:
                col = layout.column()    
                col.label(text = "You have not yet added dust")
                col.operator("smr.addpart", text="Add dust").categ = 'Dust' 
                return
            
            dust_menu(self, context, layout, settings)
        
        ######### Smudge menu #########

        if settings.smr_ui_categ == 'Smudge':
            box = layout.box()
            boxbox = box.box().row()
            boxbox.label(text="Smudges and Stains") 
            boxbox.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_smudge'
            boxbox.prop(settings, 'del_confirmation', text = '', icon = 'TRASH', emboss=True,toggle=True)

            if settings.del_confirmation:
                col=layout.column()
                col.scale_y = 2
                if settings.has_smudge:
                    col.operator("smr.cdelete", text =  'Remove SMUDGES from this material', icon = "TRASH")
                col.operator("smr.adelete", text =  'Remove ALL SMUDGR setups from this material', icon = "TRASH")   

            if not settings.has_smudge:
                col = layout.column()    
                col.label(text = "You have not yet added smudges")
                col.operator("smr.addpart", text="Add smudges").categ = 'Smudge' 
                return
            
            smudge_ui (self, context, layout, settings)
            
        ##utilities ##################
        if settings.smr_ui_categ == 'Utilities':        
            
            col= layout.column()
            row=col.row()
            row.label(text = 'Bake all Smudgr Effects to textures:')
            row.operator('smr.info', text = '', icon = 'QUESTION').info = 'fullbake'

            col.scale_y =2            
            col.operator('smr.fullbake', text = 'Bake', icon = 'RENDER_RESULT')
            row=col.row()
            row.label(text = 'Copy to DecalMachine:')
            row.operator('smr.info', text = '', icon = 'QUESTION').info = 'decalmachine'
            col.operator('smr.applydecal', text = 'Copy Smudgr material to DM decals', icon = 'OVERLAY')


            box, col, row = get_box(layout)
            #row.alignment = 'LEFT'
            row.prop(settings, 'dev_ops',
                icon="TRIA_DOWN" if settings.dev_ops else "TRIA_RIGHT",
                emboss=False,
                toggle=True)
            if settings.dev_ops:
                col.scale_y=1.5
                col.operator("smr.reset", text="Reset pcoll")
                col.prop(settings, 'diagnostics')


def dust_menu(self, context, layout, settings):
    """
    UI for adding dust, in main panel
    """  
    
    #template icon view
    col = layout.column()
    col.label(text = 'Dust influence maps:')
    col.template_icon_view(context.scene.SMR, "prev_dust", show_labels=True, scale=11)
    
    #next and previous buttons
    col = layout.column()
    row = col.row(align=True)
    row.operator("smr.previous", text="Previous", icon='TRIA_LEFT')
    row.operator("smr.next", text="Next", icon='TRIA_RIGHT')
    
    col = layout.column()
    row = col.row(align=True)
    if not settings.inf_dust1:
        row_left = row.row(align=True)
        row_right = row.column(align=True)
        row_right.scale_x = 1.5
        row_left.prop(settings, 'dust_multiplier')
        row_right.operator("smr.influence", text="", icon = "BRUSH_DATA" ).type = 'Dust1'
    else:
        row.label(text= 'Multiplier: Influence Map') 
    
    col.prop(settings, 'dust_side')
    row = col.row(align=True)
    if not settings.inf_dust_inf:
        row_left = row.row(align=True)
        row_right = row.column(align=True)
        row_right.scale_x = 1.5
        row_left.prop(settings, 'dust_influence', slider = True)
        row_right.operator("smr.influence", text="", icon = "BRUSH_DATA" ).type = 'Dust_Inf'
    else:
        row.label(text= 'Dust Influence: Influence Map') 
    row = col.row()
    row.label(text = 'Dust color:')
    row.prop(settings, 'dust_color')
    
    box, col, row = get_box(layout)
    #row.alignment = 'LEFT'
    row.prop(settings, 'dust_advanced',
        icon="TRIA_DOWN" if settings.dust_advanced else "TRIA_RIGHT",
        emboss=False,
        toggle=True)
    if settings.dust_advanced:
        col = box.column()
        col.prop(settings, 'dust_locx')
        col.prop(settings, 'dust_locy')
        col.prop(settings, 'dust_scale')
        col.prop(settings, 'dust_genscale')
        col.prop(settings, 'dust_stretch')
        col.prop(settings, 'dust_rot')
        col.label(text = "")
        row = col.row()
        row.label(text="Texture mapping:") 
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_mapping'
        
        row = col.row()
        row.prop(settings, 'dust_coord', expand=True)

    if settings.dust_at:
        box, col, row = get_box(layout)
        #row.alignment = 'LEFT'
        row.prop(settings, 'dust_at_settings',
            icon="TRIA_DOWN" if settings.dust_at_settings else "TRIA_RIGHT",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_at'    
        if settings.dust_at_settings:
            col = box.column()
            col.prop(settings, 'dust_at_scale')           
            col.prop(settings, 'dust_at_rot')
            col.prop(settings, 'dust_at_noise')
            if settings.preview:
                col.operator("smr.stoppreview", text="Stop previewing")
            else:    
                col.operator("smr.preview", text="Preview noise texture").categ = 'AT_Noise'
            col.operator("smr.atremove", text="Remove Anti-Tiling").categ = "Dust"
    else:         
        col = layout.column()
        col.operator("smr.at", text="Anti-Tile Influence Map").categ = "Dust"

    if settings.inf_dust_inf:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_dust_inf_ui',
            icon="TRIA_DOWN" if settings.inf_dust_inf_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf'    
        if settings.inf_dust_inf_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_dust_inf', expand=True)
            influence_ui(settings, box, row, col, 'Dust_Inf', settings.inftype_dust_inf)

    if settings.inf_dust1:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_dust1_ui',
            icon="TRIA_DOWN" if settings.inf_dust1_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf'            
        if settings.inf_dust1_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_dust1', expand=True)
            influence_ui(settings, box, row, col, 'Dust1', settings.inftype_dust1)


def wear_menu (box, settings, type):
    """
    UI for adding wear, in main panel
    """ 

    if type == 'EWear':
        infnumber = 2
        sign = 'bake2'
        has_bake = settings.has_bake2
        wearmode = settings.wearmode_bake2        
    else: 
        if type == 'SmBCM' or type == 'ScBCM':
            infnumber = 2
        else:
            infnumber = 1  
        if type == 'CWear':
            sign = 'bake'
        else:    
            sign = type
        has_bake = settings.has_bake
        
        if type == 'SmBCM':
            wearmode = settings.wearmode_SmBCM
        elif type == 'ScBCM':
            wearmode = settings.wearmode_ScBCM
        elif type == 'SmIntensity':
            wearmode = settings.wearmode_SmIntensity
        elif type == 'ScIntensity':
            wearmode = settings.wearmode_ScIntensity 
        elif type == 'Dust1':
            wearmode = settings.wearmode_Dust1
        else:
            wearmode = settings.wearmode_bake                                            

    col = box.column()
    col_high = col.column()
    col_high.scale_y = 2

    if settings.preview:
        if type == 'CWear' or type == 'EWear':
            col_high.operator("smr.stoppreview", text="Stop previewing", icon="PANEL_CLOSE" )
    else: 
        if type == 'CWear' or type == 'EWear':
            col_high.operator("smr.preview", text="Preview Influence Map", icon="TEXTURE").categ = type
    if type == 'EWear':
        col_high.prop(settings, 'edge_width')
    row = col_high.row()
    row.prop(settings, 'wearmode_{}'.format(sign), expand = True)
    if has_bake == True and wearmode == 'Baked':
        col = col.column()                   
        col_high.operator("smr.bake", text="Rebake").categ= type
        col_high.label(text = 'Baking may take a long time, especially in complex scenes', icon = 'ERROR')
        col_high.prop(settings, 'bake{}_res'.format(infnumber)) 
        col_high.prop(settings, 'bake{}_samples'.format(infnumber))

    elif has_bake == False and wearmode == 'Baked':
        col_high.operator("smr.bake", text="Bake").categ= type
        col_high.label(text = 'Baking may take a long time, especially in complex scenes', icon = 'ERROR')  
        col_high.prop(settings, 'bake{}_res'.format(infnumber))
        col_high.prop(settings, 'bake{}_samples'.format(infnumber))
    else:
        col_high.label(text='Live mode is only visible in Cycles rendered mode', icon='INFO')     
    col = col.column()
    col.prop(settings, 'inf{}_black'.format(infnumber), slider = True)
    col.prop(settings, 'inf{}_white'.format(infnumber), slider = True)
    col.prop(settings, 'inf{}_mult'.format(infnumber))
    col.prop(settings, 'inf{}_inf'.format(infnumber))
    if type == 'CWear':
        col.prop(settings, 'cavity_color')
        col.prop(settings, 'cavity_roughness') 
    if type == 'EWear': 
        col.prop(settings, 'edge_color')       
    
def scratch_menu (self, context, layout, settings):
    """
    UI for adding scratches, in main panel
    """ 

   #template icon view
    col = layout.column()
    col.template_icon_view(context.scene.SMR, "prev_scratch", show_labels=True, scale=11)
    
    #next and previous buttons
    col = layout.column()
    row = col.row(align=True)
    row.operator("smr.previous", text="Previous", icon='TRIA_LEFT')
    row.operator("smr.next", text="Next", icon='TRIA_RIGHT')
    

    col = layout.column()
    row= col.row()
    row.prop(settings, 'scratch_res', expand=True) 
    col.label(text= 'Active Scratch: {}'.format(settings.active_scratch_ui))

    if not settings.inf_scratch_int:
        row= col.row()
        row_left = row.row(align=True)
        row_right = row.column(align=True)
        row_right.scale_x = 1.5
        row_left.prop(settings, 'scratch_intensity', slider = True)
        row_right.operator("smr.influence", text="", icon = "BRUSH_DATA").type = 'ScIntensity'
    else:
        col.label(text = "Scratch Intensity: Influence Map")

        
    box, col, row = get_box(layout)
    row.prop(settings, 'scratch_bcm',
        icon="TRIA_DOWN" if settings.scratch_bcm else "TRIA_RIGHT",
        emboss=False,
        toggle=True)
    row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_bcm'    
    if settings.scratch_bcm:
        col = box.column()
        if not settings.inf_scratch_bcm:    
            row = col.row()
            row_left = row.row(align=True)
            row_right = row.column(align=True)
            row_right.scale_x = 1.5
            row_left.prop(settings, 'scratch_bcm_intensity')
            row_right.operator("smr.influence", text="", icon = "BRUSH_DATA").type = 'ScBCM'
        else:
            col.label(text = "BCM Intensity: Influence Map")
            
        col.prop(settings, 'scratch_bcm_color')
    
    box, col, row = get_box(layout)
    #row.alignment = 'LEFT'
    row.prop(settings, 'scratch_advanced',
        icon="TRIA_DOWN" if settings.scratch_advanced else "TRIA_RIGHT",
        emboss=False,
        toggle=True)
    if settings.scratch_advanced:
        col = box.column()
        col.prop(settings, 'scratch_locx')
        col.prop(settings, 'scratch_locy')
        col.prop(settings, 'scratch_scale')
        col.prop(settings, 'scratch_stretch')
        col.prop(settings, 'scratch_rot')
        col.label(text = "")
        row = col.row()
        row.label(text="Texture mapping:") 
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_mapping'
        
        row = col.row()
        row.prop(settings, 'scratch_coord', expand=True)

    if settings.scratch_at:
        box, col, row = get_box(layout)
        #row.alignment = 'LEFT'
        row.prop(settings, 'scratch_at_settings',
            icon="TRIA_DOWN" if settings.scratch_at_settings else "TRIA_RIGHT",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_at'    
        if settings.scratch_at_settings:
            col = box.column()
            col.prop(settings, 'scratch_at_scale')           
            col.prop(settings, 'scratch_at_rot')
            col.prop(settings, 'scratch_at_noise')
            if settings.preview:
                col.operator("smr.stoppreview", text="Stop previewing")
            else:    
                col.operator("smr.preview", text="Preview noise texture").categ = 'AT_Noise'
            col.operator("smr.atremove", text="Remove Anti-Tiling").categ = "Scratch"
    else:         
        col = layout.column()
        col.operator("smr.at", text="Anti-Tile").categ = "Scratch"

    if settings.inf_scratch_bcm:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_scratch_bcm_ui',
            icon="TRIA_DOWN" if settings.inf_scratch_bcm_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf'            
        if settings.inf_scratch_bcm_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_scratch_bcm', expand=True)
            influence_ui(settings, box, row, col, 'ScBCM', settings.inftype_scratch_bcm)
            
    if settings.inf_scratch_int:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_scratch_int_ui',
            icon="TRIA_DOWN" if settings.inf_scratch_int_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf'            
        if settings.inf_scratch_int_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_scratch_int', expand=True)
            influence_ui(settings, box, row, col, 'ScIntensity', settings.inftype_scratch_int)





def get_box(layout):
    """
    called by other UI elements for getting a box
    """ 
    col = layout.column()
    box = col.box()
    col = box.column(align=True)
    row = col.row(align=True)
    row.scale_y= 2
    row.alignment = 'LEFT'
    return box, col, row




def smudge_ui (self, context, layout, settings):
    """
    UI for adding smudges, in main panel
    """ 
    #template icon view with category buttons on the right side
    col = layout.column(align=True)
    row = col.row(align=True)
    row_left = row.row(align=True)
    row_right = row.column(align=True)
    row_right.scale_y = 11/5
    row_right.scale_x = 1/4
    row_right.prop(settings, 'smudge_categ', expand=True)  
    row_left.template_icon_view(context.scene.SMR, "prev_smudge", show_labels=True, scale=11)
    
    #next and previous buttons
    col = layout.column()
    row = col.row(align=True)
    row.operator("smr.previous", text="Previous", icon='TRIA_LEFT')
    row.operator("smr.next", text="Next", icon='TRIA_RIGHT')
    
    col = layout.column()
    row= col.row()
    row.prop(settings, 'smudge_res', expand=True) 
    col.label(text= 'Active Smudge: {}'.format(settings.active_smudge_ui))

    col.prop(settings, 'smudge_falloff', slider = True)
    row= col.row()
    if not settings.inf_smudge_int:
        row_left = row.row(align=True)
        row_right = row.column(align=True)
        row_right.scale_x = 1.5
        row_left.prop(settings, 'smudge_roughness', slider = True)
        row_right.operator("smr.influence", text="", icon = "BRUSH_DATA" ).type = 'SmIntensity'
    else:
        row.label(text= 'Roughness: Influence Map') 
        
    box, col, row = get_box(layout)
    row.prop(settings, 'smudge_bcm',
        icon="TRIA_DOWN" if settings.smudge_bcm else "TRIA_RIGHT",
        emboss=False,
        toggle=True)
    row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_bcm'        
    if settings.smudge_bcm:
        col = box.column()
        row= col.row()
        row_left = row.row(align=True)
        row_right = row.column(align=True)
        row_right.scale_x = 1.5
        if not settings.inf_smudge_bcm:
            row_left.prop(settings, 'smudge_bcm_intensity')
            row_right.operator("smr.influence", text="", icon = "BRUSH_DATA" ).type = 'SmBCM'
        else:
            row.label(text= 'BCM Intensity: Influence Map')    
        col.prop(settings, 'smudge_bcm_falloff')
        col.prop(settings, 'smudge_bcm_color')
    
    box, col, row = get_box(layout)
    row.alignment = 'LEFT'
    row.prop(settings, 'smudge_advanced',
        icon="TRIA_DOWN" if settings.smudge_advanced else "TRIA_RIGHT",
        emboss=False,
        toggle=True)
    if settings.smudge_advanced:
        col = box.column()
        col.prop(settings, 'smudge_locx')
        col.prop(settings, 'smudge_locy')
        col.prop(settings, 'smudge_scale')
        col.prop(settings, 'smudge_stretch')
        col.prop(settings, 'smudge_rot')
        
        col.label(text = "")
        row = col.row()
        row.label(text="Texture mapping:") 
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_mapping'
        
        row.prop(settings, 'smudge_coord', expand=True)
    
    if settings.smudge_at:
        box, col, row = get_box(layout)
        #row.alignment = 'LEFT'
        row.prop(settings, 'smudge_at_settings',
            icon="TRIA_DOWN" if settings.smudge_at_settings else "TRIA_RIGHT",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_at'    
        if settings.smudge_at_settings:
            col = box.column()
            col.prop(settings, 'smudge_at_scale')
            col.prop(settings, 'smudge_at_rot')
            col.prop(settings, 'smudge_at_noise')
            if settings.preview:
                col.operator("smr.stoppreview", text="Stop previewing")
            else:    
                col.operator("smr.preview", text="Preview noise texture").categ = 'AT_Noise'
            col.operator("smr.atremove", text="Remove Anti-Tiling").categ = "Smudge"
    else:         
        col = layout.column()
        col.operator("smr.at", text="Anti-Tile").categ = "Smudge"
    
    if settings.inf_smudge_bcm:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_smudge_bcm_ui',
            icon="TRIA_DOWN" if settings.inf_smudge_bcm_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf'         
        if settings.inf_smudge_bcm_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_smudge_bcm', expand=True)
            influence_ui(settings, box, row, col, 'SmBCM', settings.inftype_smudge_bcm)
            
    if settings.inf_smudge_int:
        box, col, row = get_box(layout)
        row.prop(settings, 'inf_smudge_int_ui',
            icon="TRIA_DOWN" if settings.inf_smudge_int_ui else "BRUSH_DATA",
            emboss=False,
            toggle=True)
        row.operator("smr.info", text =  '', icon = "QUESTION").info = 'info_inf' 
        if settings.inf_smudge_int_ui:
            row= col.row()
            row.scale_y=2
            row.prop(settings, 'inftype_smudge_int', expand=True)
            influence_ui(settings, box, row, col, 'SmIntensity', settings.inftype_smudge_int)

def influence_ui(settings, box, row, col, categsign, inftype):        
    """
    UI for adding influence maps, in main panel
    """ 

    col_high = col.column()
    col_high.scale_y = 2
    if settings.preview:
        col_high.operator("smr.stoppreview", text="Stop previewing", icon="PANEL_CLOSE" )
    else:  
        col_high.operator("smr.preview", text="Preview Influence Map", icon="TEXTURE").categ = categsign

    if categsign[2:] == "BCM":
        infnumber = 2
        wearmode = 'bake2'
        wearmode_sign = settings.wearmode_bake2
    if categsign[2:] == "Intensity":
        infnumber = 1           
        wearmode = 'bake'
        wearmode_sign = settings.wearmode_bake
    if categsign == 'Dust1':
        infnumber = 1   
        wearmode = 'bake'
        wearmode_sign = settings.wearmode_bake
    if categsign == 'Dust_Inf':
        infnumber = 2   
        wearmode = 'bake2'
        wearmode_sign = settings.wearmode_bake2    
    if categsign == 'Droplets':
        infnumber = 1   
        wearmode = 'bake'
        wearmode_sign = settings.wearmode_bake


    if inftype == "Texture Paint":
        if not settings.preview:
            col_high.operator("smr.texpaint", text="Start Painting", icon="BRUSH_DATA").categ= categsign
        if settings.pack_confirmation:
            col_high.operator("smr.pack", text="PACK IMAGE", icon="ERROR")
        col_high.label(text='')
    if inftype == "Cavity":
        wear_menu (box, settings, categsign)
    else:        
        col = col.column(align = True)
        col.prop(settings, 'inf{}_black'.format(infnumber), slider = True)
        col.prop(settings, 'inf{}_white'.format(infnumber), slider = True)
        col.prop(settings, 'inf{}_mult'.format(infnumber))
        col.prop(settings, 'inf{}_inf'.format(infnumber))
    col = box.column()
    row=col.row(align=True)
    row.label(text='Presets:')
    row.operator("smr.infpreset", text="Contrast").categ = '2{}'.format(infnumber)
    row.operator("smr.infpreset", text="Hotspots").categ = '3{}'.format(infnumber)
    row.operator("smr.infpreset", text="Invert").categ = '4{}'.format(infnumber)
    row.operator("smr.infpreset", text="Reset").categ = '1{}'.format(infnumber)

    if inftype == "Gradient" or inftype == 'Noise':
        col = col.column(align = True)
        col.label(text= '{} Settings'.format(inftype))
        col.prop(settings, 'inf{}_val1'.format(infnumber), text = 'Move' if inftype == 'Gradient' else 'Seed')
        col.prop(settings, 'inf{}_val2'.format(infnumber), text = 'Rotate X' if inftype == 'Gradient' else 'Scale')
        col.prop(settings, 'inf{}_val3'.format(infnumber), text = 'Rotate Y' if inftype == 'Gradient' else 'Detail')
        col.prop(settings, 'inf{}_val4'.format(infnumber), text = 'Rotate Z' if inftype == 'Gradient' else 'Distortion')            
    
    if categsign == 'Droplets':
        col.label(text='Droplets look best at low multiplier values', icon = 'INFO')

    col = col.column()
    col.label(text='')
    col.prop(settings, 'inf_remove_confirmation', text = 'Remove Influence [confirmation]' if not settings.inf_remove_confirmation else "Cancel removal",
        emboss=True,toggle=True)
    if settings.inf_remove_confirmation:
        col.operator("smr.removeinfluence", text="Remove Influence", icon = "ERROR").type = categsign       

def presets_ui(settings, col2, layout):
    """
    UI for automatic mode for adding smudgr setups
    """ 
    col= col2.box() 
    col.prop(settings, 'auto_dust')
    if settings.auto_dust:
        col.prop(settings,'auto_dust_strength')
        col.prop(settings,'auto_dust_side')
        col.prop(settings,'auto_dust_color')
    col2.label(text='')

    col= col2.box()   
    col.prop(settings, 'auto_smudge')
    if settings.auto_smudge:
        col.prop(settings,'auto_smudge_strength')
        col.prop(settings,'auto_smudge_random')
        col.prop(settings,'auto_smudge_bcm')
        col.prop(settings,'auto_smudge_bcm_color')
        col.prop(settings,'auto_smudge_bcm_random')   
    col2.label(text='')
    
    col= col2.box() 
    col.prop(settings, 'auto_scratch')
    if settings.auto_scratch:
        col.prop(settings,'auto_scratch_strength')
        col.prop(settings,'auto_scratch_random')
    col2.label(text='')

    col= col2.box() 
    col.prop(settings, 'auto_cwear')
    if settings.auto_cwear:
        col.prop(settings,'auto_cwear_color')
        col.prop(settings,'auto_cwear_mult')
