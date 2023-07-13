import bpy   

class LIGHTMIXER_PT_EmissiveViewPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Photographer'
    bl_label = "Emissive Mixer"
    bl_order = 13

    def draw(self,context):
        layout = self.layout
        layout.use_property_split = False
        solo_active = context.scene.lightmixer.solo_active
        
        row = layout.row(align=True)
        # row.operator("lightmixer.add_emissive", text="Add Emissive", icon='LIGHT_AREA')                    
        row.operator("lightmixer.scan_emissive", icon='VIEWZOOM')
        row.operator("lightmixer.create_emissive", icon='MATERIAL_DATA')
        
        emissive_mats = [mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
        if not emissive_mats:
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.label(text="No Emissive material in the Scene", icon='INFO')
        
        else:
            for mat in emissive_mats:
                lightmixer = mat.lightmixer
                nodes = mat.node_tree.nodes
                
                if len(mat.get('em_nodes', ''))>1:
                    mat_box = layout.box()
                    mat_row = mat_box.row(align=True)
                        
                    mat_row.operator("lightmixer.show_more", text="",
                                    icon='TRIA_DOWN' if lightmixer.show_more else 'TRIA_RIGHT',
                                    emboss=False).mat=mat.name

                    if not solo_active and lightmixer.enabled:
                        icn = 'MATERIAL_DATA'    
                    else:
                        icn = 'MESH_CIRCLE'
                    mat_en = mat_row.operator("lightmixer.material_enable", text="",
                                        icon=icn, emboss=False)
                    mat_en.mat_name=mat.name
                    
                    emissive_obj_list = []
                    if mat.users:
                        for obj in bpy.context.scene.objects:
                            for m in obj.material_slots:
                                if m.name == mat.name:
                                    emissive_obj_list.append(obj)
                    all_selected = all(obj.select_get() for obj in emissive_obj_list)
                    if all_selected and not (mat.users==1 and mat.use_fake_user):
                        icn = 'RESTRICT_SELECT_OFF'
                    else:
                        icn = 'RESTRICT_SELECT_ON'
                    mat_row.operator("photographer.select_emissive", text="",
                                    icon=icn).mat_name=mat.name
                    mat_row.operator("lightmixer.assign_emissive", text="", icon='PLUS').mat_name=mat.name
                    
                    mat_row.prop(mat, "name", text='')
                    
                    if lightmixer.show_more:                         
                        for em_node in mat.get('em_nodes', ''):
                            
                            em_node = nodes.get(em_node,False)
                            if not em_node:
                                col = mat_box.column(align=True)
                                col.label(text='Emissive Node has been deleted.')
                                col.operator('lightmixer.scan_emissive',
                                                    text='Please Scan again',
                                                    icon='VIEWZOOM')
                            else:                          
                                em_color = em_node.get('em_color', '')                
                                em_strength = em_node.get('em_strength', '')
                                connected = em_node.get('connected', '')
                                node_lm = em_node.lightmixer
                                
                                # box = mat_box.box()
                                row = mat_box.row(align=True)
                                row.enabled = lightmixer.enabled
                                    
                                main_col = row.column(align=True)
                                
                                if solo_active and node_lm.solo:
                                    icn = 'EVENT_S'
                                    row.alert=True
                                elif not solo_active and node_lm.enabled:
                                    icn = 'OUTLINER_OB_LIGHT'    
                                else:
                                    icn = 'LIGHT'
                                    
                                en = main_col.operator("lightmixer.emissive_enable", text="",
                                                    icon=icn, emboss=False)
                                en.node_name=em_node.name
                                en.mat_name=mat.name
                                
                                col = row.column(align=True)
                                name_row = col.row(align=True)
                                
                                name_row.prop(em_node, "name", text='')
                                
                                # Color Row
                                color_row = name_row.row(align=True)
                                # Make sure Nodes still exists since last scan
                                if em_color and nodes.get(em_color[0], None):
                                    if node_lm.use_light_temperature:
                                        color_row.prop(node_lm, "light_temperature", text='')
                                        row=color_row.row(align=True)
                                        row.ui_units_x = 1
                                        row.prop(node_lm, "preview_color_temp", text='')

                                    else:
                                        color_row.ui_units_x = 3
                                        color_row.prop(nodes[em_color[0]].inputs[em_color[1]], "default_value", text='')
                                    icn = 'EVENT_K' if node_lm.use_light_temperature else 'EVENT_C'
                                    name_row.prop(node_lm, 'use_light_temperature',
                                                    icon=icn, text='', toggle=True)                                

                                # Second Row
                                intensity_row = col.row(align=True)

                                # Disable UI if not Emissive enabled        
                                if solo_active or not node_lm.enabled:
                                    if not node_lm.solo:
                                        name_row.enabled = False
                                        intensity_row.enabled = False
                                        
                                # Disable name_row if no Emissive controls
                                if connected and (not em_color or not em_strength):
                                    color_row.enabled = False
                                    name_row.enabled = False
                                    main_col.enabled = False
                                    intensity_row.operator('lightmixer.add_emissive_controls', icon='ERROR').mat_name=mat.name
                                else:
                                    # Check if Node hasn't been deleted since last Scan
                                    if not nodes.get(em_strength[0], None):
                                        color_row.enabled = False
                                        intensity_row.operator('lightmixer.scan_emissive',
                                                            text='Missing Node, please Scan again',
                                                            icon='VIEWZOOM')
                                    else:
                                        sub = intensity_row.row(align=True)
                                        if intensity_row.enabled:
                                            sub.prop(nodes[em_strength[0]].inputs[em_strength[1]], "default_value", text='Strength')
                                        else:
                                            sub.prop(node_lm, "strength")
                                        minus = sub.operator("lightmixer.emissive_stop", text='', icon='REMOVE')
                                        minus.factor = -0.5
                                        minus.mat_name = mat.name
                                        minus.node_name = em_node.name
                                        plus = sub.operator("lightmixer.emissive_stop", text='', icon='ADD')
                                        plus.factor = 0.5
                                        plus.mat_name = mat.name
                                        plus.node_name = em_node.name
                    
                        row = mat_box.row(align=True)
                        row.enabled = lightmixer.enabled
                        row.prop(lightmixer,'backface_culling', toggle=True)

                else:
                    for em_node in mat.get('em_nodes', ''):
                        box = layout.box()    
                        
                        em_node = nodes.get(em_node,False)
                        if not em_node:
                            col = box.column(align=True)
                            col.label(text='Emissive Node has been deleted.')
                            col.operator('lightmixer.scan_emissive',
                                                text='Please Scan again',
                                                icon='VIEWZOOM')
                        
                        else: 
                            em_color = em_node.get('em_color','')     
                            em_strength = em_node.get('em_strength', '')
                            connected = em_node.get('connected', '')
                            node_lm = em_node.lightmixer
                    
                            row = box.row(align=True)
                            main_col = row.column(align=True)
                            
                            if solo_active and node_lm.solo:
                                icn = 'EVENT_S'
                                row.alert=True
                            elif not solo_active and node_lm.enabled:
                                icn = 'OUTLINER_OB_LIGHT'    
                            else:
                                icn = 'LIGHT'
                                
                            en = main_col.operator("lightmixer.emissive_enable", text="",
                                                icon=icn, emboss=False)
                            en.node_name=em_node.name
                            en.mat_name=mat.name
                                                
                            col = row.column(align=True)
                            name_row = col.row(align=True)
                            
                            emissive_obj_list = []
                            if mat.users:
                                for obj in bpy.context.scene.objects:
                                    for m in obj.material_slots:
                                        if m.name == mat.name:
                                            emissive_obj_list.append(obj)
                            all_selected = all(obj.select_get() for obj in emissive_obj_list)
                            if all_selected and not (mat.users==1 and mat.use_fake_user):
                                icn = 'RESTRICT_SELECT_OFF'
                            else:
                                icn = 'RESTRICT_SELECT_ON'
                            name_row.operator("photographer.select_emissive", text="",
                                            # icon = 'RESTRICT_SELECT_OFF',).mat_name=mat.name
                                            icon=icn).mat_name=mat.name
                            name_row.operator("lightmixer.assign_emissive", text="", icon='PLUS').mat_name=mat.name
                            if len(mat.get('em_nodes', ''))>1:
                                name_row.prop(em_node, "name", text='')
                            else:
                                name_row.prop(mat, "name", text='')
                            
                            # Color Row
                            color_row = name_row.row(align=True)
                            # Make sure Nodes still exists since last scan
                            if em_color and nodes.get(em_color[0], None):
                                if node_lm.use_light_temperature:
                                    color_row.prop(node_lm, "light_temperature", text='')
                                    row=color_row.row(align=True)
                                    row.ui_units_x = 1
                                    row.prop(node_lm, "preview_color_temp", text='')

                                else:
                                    color_row.ui_units_x = 3
                                    # color_row.prop(node_lm, "color", text='')
                                    color_row.prop(nodes[em_color[0]].inputs[em_color[1]], "default_value", text='')
                                icn = 'EVENT_K' if node_lm.use_light_temperature else 'EVENT_C'
                                name_row.prop(node_lm, 'use_light_temperature',
                                                icon=icn, text='', toggle=True)


                            # Second Row
                            intensity_row = col.row(align=True) 
                            
                            # Disable UI if not Emissive enabled        
                            if solo_active or not node_lm.enabled:
                                if not node_lm.solo:
                                    name_row.enabled = False
                                    intensity_row.enabled = False  
                                                           
                            # Disable name_row if no Emissive controls
                            if connected and (not em_color or not em_strength):
                                color_row.enabled = False
                                name_row.enabled = False
                                main_col.enabled = False
                                intensity_row.operator('lightmixer.add_emissive_controls', icon='ERROR').mat_name=mat.name
                            else:
                                # Check if Node hasn't been deleted since last Scan
                                if not nodes.get(em_strength[0], None):
                                    color_row.enabled = False
                                    intensity_row.operator('lightmixer.scan_emissive',
                                                        text='Missing Node, please Scan again',
                                                        icon='VIEWZOOM')
                                else:
                                    sub = intensity_row.row(align=True)
                                    if intensity_row.enabled:
                                        sub.prop(nodes[em_strength[0]].inputs[em_strength[1]], "default_value", text='Strength')
                                    else:
                                        sub.prop(node_lm, "strength")
                                    minus = sub.operator("lightmixer.emissive_stop", text='', icon='REMOVE')
                                    minus.factor = -0.5
                                    minus.mat_name = mat.name
                                    minus.node_name = em_node.name
                                    plus = sub.operator("lightmixer.emissive_stop", text='', icon='ADD')
                                    plus.factor = 0.5
                                    plus.mat_name = mat.name
                                    plus.node_name = em_node.name
                                
                            main_col.operator("lightmixer.show_more", text="",
                                            icon='TRIA_DOWN' if lightmixer.show_more else 'TRIA_RIGHT',
                                            emboss=False).mat=mat.name

                            if lightmixer.show_more:
                                more_col = box.column(align=False)
                                more_col.enabled = lightmixer.enabled
                                col = more_col.column(align=True)
                                col.prop(lightmixer,'backface_culling', toggle=True)
                                if solo_active or not node_lm.enabled:
                                    more_col.enabled = False
                            
   
                                    
                            # if context.scene.render.engine == "CYCLES":
                            #     row = col.row(align=True)
                                # row.prop(world.cycles_visibility, "diffuse", toggle=True)
                                # row.prop(world.cycles_visibility, "glossy", toggle=True)
                                # row.prop(world.cycles_visibility, "camera", toggle=True)
            
