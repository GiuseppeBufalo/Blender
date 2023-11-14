import bpy
from ..functions import show_message
from re import findall

def color_socket_info(mat,node):
    links =  mat.node_tree.links                    
    if node.bl_idname == 'ShaderNodeBsdfPrincipled':
        input_name = 'Emission'
    elif node.bl_idname == 'ShaderNodeEmission':
        input_name = 'Color'
    socket = node.inputs[input_name]
    value = node.inputs[input_name].default_value[:]
    link = [l for l in links if l.to_node == node and l.to_socket == socket]
    if link:
        link_socket = link[0].from_socket.name
        link = link[0].from_node
    else:
        link_socket = ''
        link = ''
    return (input_name,link_socket,link,value)
    
def socket_info(mat,node):
    links =  mat.node_tree.links
    if node.bl_idname == 'ShaderNodeBsdfPrincipled':
        input_name = 'Emission Strength'
    elif node.bl_idname == 'ShaderNodeEmission':
        input_name = 'Strength'
    socket = node.inputs[input_name]
    value = node.inputs[input_name].default_value
    link = [l for l in links if l.to_node == node and l.to_socket == socket]
    if link:
        link_socket = link[0].from_socket.name
        link = link[0].from_node
    else:
        link_socket = ''
        link = ''
    return (input_name,link_socket,link,value)

class LIGHTMIXER_OT_ScanEmissive(bpy.types.Operator):
    bl_idname = "lightmixer.scan_emissive"
    bl_label = "Scan"
    bl_description = "Scan all materials to find Emission nodes that are not muted"

    def execute(self, context):
        for mat in bpy.data.materials:
            
            # Reset
            for prop in {'is_emissive', 'em_node'}:
                if mat.get(prop, False):
                    mat[prop] = False

            if mat.use_nodes and mat.users:
                nodes = mat.node_tree.nodes
                links =  mat.node_tree.links                 
                em_nodes = []
                for node in nodes:
                    # Reset
                    for prop in {'em_color', 'em_strength', 'connected'}:
                        if node.get(prop, False):
                            node[prop] = False
                    engine = context.scene.render.engine
                    if engine != 'LUXCORE' or (engine=='LUXCORE' and mat.luxcore.use_cycles_nodes):
                        types = ['ShaderNodeEmission']
                        if bpy.app.version >= (2,91,2):
                            types.append('ShaderNodeBsdfPrincipled')
                        if node.bl_idname in types:
                            link = [l for l in links if l.from_node == node]
                            if not node.mute and link:
                                em_nodes.append(node.name)
        
                                # Get information about Color and Strength
                                input_color_name, em_color_link_socket, em_color_link, color_value = color_socket_info(mat,node)
                                input_strength_name, em_strength_link_socket, em_strength_link, strength_value = socket_info(mat,node)
                            
                                if em_color_link:
                                    node['connected'] = True  
                                    if em_color_link.get('is_em_controls',False):
                                        node['em_color'] = [em_color_link.name,'Color Multiplier']
                                else:
                                    node['em_color'] = [node.name,input_color_name]
                                    
                                if em_strength_link:
                                    node['connected'] = True  
                                    if em_strength_link.get('is_em_controls',False):                                
                                        node['em_strength'] = [em_strength_link.name,'Strength Multiplier']
                                else:
                                    node['em_strength'] = [node.name,input_strength_name]
                                
                                # Remove BSDF if Emission is 0:
                                if node.bl_idname == 'ShaderNodeBsdfPrincipled' and not em_color_link:
                                    if (color_value == (0,0,0,color_value[3]) or strength_value == 0):
                                        em_nodes.remove(node.name)
                                        
                                # Remove Focus Plane material
                                if "_FocusPlane_Mat" in mat.name:
                                    em_nodes.remove(node.name)
                
                mat['em_nodes'] = em_nodes
                
                if mat['em_nodes']:
                    mat['is_emissive']= True
                    if len(mat['em_nodes'])>1:
                        mat.lightmixer.show_more = True

        return {'FINISHED'}
        
class LIGHTMIXER_OT_CreateEmissive(bpy.types.Operator):
    bl_idname = "lightmixer.create_emissive"
    bl_label = "Create"
    bl_description = ("Create new Emissive Material and Assign to active slot. \n"
                    "Shift-Click to Replace all material slots")
    bl_options = {'REGISTER', 'UNDO'}

    mat_name: bpy.props.StringProperty(
        name="Name",
        description="Name of the material",
        default="Emissive",
    )
    type: bpy.props.EnumProperty(
        name="Shader Type",
        items=[('EMISSION', 'Emission', 'Simple Emission Shader',0),
        ('BSDF', 'Principled BSDF', 'Principled BSDF with Emission',1)]
    )
    color: bpy.props.FloatVectorProperty(
        name="Color", description="Emissive Color",
        subtype='COLOR',
        min=0.0, max=1.0, size=4,
        default=(1.0,1.0,1.0,1.0),
    )
    strength: bpy.props.FloatProperty(
        name='Strength',
        precision=3,
        default=1.0
    )
    shift: bpy.props.BoolProperty(
        name='Replace all material slots',
        description="Only in Object Mode")

    def execute(self, context):
        # Increment name if material with same name already exists
        mats = [m.name for m in bpy.data.materials if m.name.startswith(self.mat_name)]
        highest = 0
        if mats:
            for m in mats:
                #find last numbers in the filename after the camera name
                suffix = findall('\d+', m.split(self.mat_name)[-1])
                if suffix:
                    if int(suffix[-1]) > highest:
                        highest = int(suffix[-1])    
        
            mat_name = self.mat_name + "." + str(highest+1).zfill(3)
        else:
            mat_name = self.mat_name
        
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Shader
        if self.type == 'EMISSION':
            for node in nodes:
                if node.type != 'OUTPUT_MATERIAL':
                    nodes.remove(node) 
            sh = nodes.new('ShaderNodeEmission')
            sh.inputs['Color'].default_value = self.color         
            sh.inputs['Strength'].default_value = self.strength         
            # Output
            output = nodes['Material Output']
            output.location = (200,0)
            # Connect them
            links.new(sh.outputs[0], output.inputs['Surface'])
        elif self.type == 'BSDF':
            if bpy.app.version >= (2,91,2):
                sh = output = nodes['Principled BSDF']
                sh.inputs['Emission'].default_value = self.color
                sh.inputs['Emission Strength'].default_value = self.strength
            else:
                show_message("Principled BSDF is not supported for versions below 2.91.2.")
                return {'CANCELLED'}
        
        active = context.active_object
        if active and active.type == 'MESH' and (context.mode == 'EDIT_MESH' or active.select_get()):
            bpy.ops.lightmixer.assign_emissive(mat_name=mat_name,shift=self.shift)
        else:
            mat.use_fake_user = True
        bpy.ops.lightmixer.scan_emissive()

        return {'FINISHED'}
        
    def invoke(self, context, event):
        self.shift = event.shift
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
class LIGHTMIXER_OT_AssignEmissive(bpy.types.Operator):
    bl_idname = "lightmixer.assign_emissive"
    bl_label = "Assign Emissive Material to active Material Slot"
    bl_description = "Shift-Click to replace all material slots"
    bl_options = {'UNDO'}

    mat_name: bpy.props.StringProperty()
    # replaced_mat: bpy.props.PointerProperty()
    shift: bpy.props.BoolProperty()

    @classmethod
    def poll(cls,context):
        active = context.active_object
        return active is not None and active.type == 'MESH' and (context.mode == 'EDIT_MESH' or active.select_get())

    def execute(self, context):
        obj = context.active_object
        em_mat = bpy.data.materials[self.mat_name]
        
        if context.object.mode == 'EDIT':
            if not em_mat.name in obj.data.materials:
                obj.data.materials.append(em_mat)
            mat_index = {mat.name: i for i, mat in enumerate(obj.data.materials)}
            obj.active_material_index = mat_index[em_mat.name]
            bpy.ops.object.material_slot_assign()
        else:
            if context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            if self.shift:
                for slot in obj.material_slots:
                    bpy.ops.object.material_slot_remove()
                obj.data.materials.append(em_mat)
            else:
                if not obj.data.materials:
                    obj.data.materials.append(em_mat)
                else:
                    index = obj.active_material_index
                    obj.data.materials[index] = em_mat        
        obj.data.update()

        return {'FINISHED'}
        
    def invoke(self, context, event):
        self.shift = event.shift
        return self.execute(context)

class LIGHTMIXER_OT_AddEmissiveControls(bpy.types.Operator):
    bl_idname = "lightmixer.add_emissive_controls"
    bl_label = "Add Emissive Controls"
    bl_description = "Inserts Value and RGB multiplier into the Emissive shader"
    bl_options = {'UNDO'}

    mat_name: bpy.props.StringProperty()
    
    def execute(self, context):
        if self.mat_name:
            mat = bpy.data.materials[self.mat_name]
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            if not mat.get('em_nodes',False):
                show_message("Couldn't find Emissive node, please Scan Emissive materials again.")
                return {'CANCELLED'}           
            
            else:
                for em_node in mat['em_nodes']:
                    em_node = nodes[em_node]
                    input_color_name, output_socket, em_color_link, color_value = color_socket_info(mat,em_node)
                    input_strength_name, em_strength_link_socket, em_strength_link, strength_value = socket_info(mat,em_node)
                    
                    # Check if Node Group already exists in Scene
                    em_controls_grp = [g for g in bpy.data.node_groups if g.name == 'EmissiveMixer Controls']
                    if em_controls_grp:
                        em_controls_grp = em_controls_grp[0]                    
                    else:
                        # Create Node Group
                        em_controls_grp = bpy.data.node_groups.new('EmissiveMixer Controls', 'ShaderNodeTree')

                        # Create group inputs
                        group_inputs = em_controls_grp.nodes.new('NodeGroupInput')
                        group_inputs.location = (-300,200)
                        col = em_controls_grp.inputs.new('NodeSocketColor','Color Input')
                        col.default_value = (1.0,1.0,1.0,1.0)
                        str = em_controls_grp.inputs.new('NodeSocketFloat','Strength Input')
                        str.default_value = 1
                        str.min_value = 0
                        rgb = em_controls_grp.inputs.new('NodeSocketColor','Color Multiplier')
                        rgb.default_value = (1.0,1.0,1.0,1.0)
                        float = em_controls_grp.inputs.new('NodeSocketFloat','Strength Multiplier')
                        float.default_value = 1
                        float.min_value = 0

                        # Create group outputs
                        group_outputs = em_controls_grp.nodes.new('NodeGroupOutput')
                        group_outputs.location = (300,0)
                        em_controls_grp.outputs.new('NodeSocketColor','Color')
                        em_controls_grp.outputs.new('NodeSocketFloat','Strength')

                        mix = em_controls_grp.nodes.new('ShaderNodeMixRGB')
                        mix.blend_type = 'MULTIPLY'
                        mix.inputs[0].default_value = 1.0
                        mix.location = (0,200)

                        mul = em_controls_grp.nodes.new('ShaderNodeMath')
                        mul.operation = 'MULTIPLY'
                        mul.location = (0,-20)

                        # Connect Nodes together
                        em_controls_grp.links.new(group_inputs.outputs[0], mix.inputs[1])
                        em_controls_grp.links.new(group_inputs.outputs[1], mul.inputs[0])
                        em_controls_grp.links.new(group_inputs.outputs[2], mix.inputs[2])
                        em_controls_grp.links.new(group_inputs.outputs[3], mul.inputs[1])
                        em_controls_grp.links.new(group_outputs.inputs[0], mix.outputs[0])
                        em_controls_grp.links.new(group_outputs.inputs[1], mul.outputs[0])
                    
                    # Check if Group node already in material
                    em_controls_nodes=[n for n in nodes if n.bl_idname=='ShaderNodeGroup' and n.get('is_em_controls', False) and n.get('em_node', '')==em_node.name]
                    if em_controls_nodes:
                        em_controls = em_controls_nodes[0]
                    # Create otherwise
                    else:                    
                        em_controls = nodes.new('ShaderNodeGroup')
                        em_controls.node_tree = em_controls_grp
                        em_controls['is_em_controls'] = True
                        em_controls['em_node'] = em_node.name
                        if em_node.bl_idname == 'ShaderNodeBsdfPrincipled':
                            em_controls.location = (em_node.location[0],em_node.location[1]-420)
                        else:
                            em_controls.location = em_node.location
                        
                        # Move nodes after the emission node to the right
                        for node in nodes:
                            if node.location[0] > em_controls.location[0]:
                                node.location[0] += 200
                        em_node.location[0] += 200
                    
                    # Insert in existing material
                    if em_color_link and em_color_link != em_controls:
                        links.new(em_color_link.outputs[output_socket], em_controls.inputs[0])
                    if em_strength_link and em_strength_link != em_controls:
                        links.new(em_strength_link.outputs[em_strength_link_socket], em_controls.inputs[1])
                    links.new(em_controls.outputs[0],em_node.inputs[input_color_name])
                    links.new(em_controls.outputs[1],em_node.inputs[input_strength_name])
                    
                    # Copy Emissive node default values to Emissive controls if not connected
                    if not em_color_link:
                        em_controls.inputs[2].default_value = em_node.inputs[input_color_name].default_value
                    if not em_strength_link:
                        em_controls.inputs[3].default_value = em_node.inputs[input_strength_name].default_value
                
                bpy.ops.lightmixer.scan_emissive()

        return {'FINISHED'}

class LIGHTMIXER_OT_EmissiveEnable(bpy.types.Operator):
    bl_idname = "lightmixer.emissive_enable"
    bl_label = "Enable Emissive"
    bl_description = "Shift-Click to Solo this Emissive"
    bl_options = {'UNDO'}
    
    mat_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()
    shift: bpy.props.BoolProperty()
    
    def execute(self, context):
        mat = bpy.data.materials[self.mat_name]
        nodes = mat.node_tree.nodes
        node = nodes.get(self.node_name)
    
        if self.shift:
            if context.scene.lightmixer.solo_active:
                # Find solo_node if it exists
                for mat in bpy.data.materials:
                    for em_node in mat.get('em_nodes',''):
                        nodes = mat.node_tree.nodes
                        em_node = nodes[em_node]
                        if em_node.lightmixer.solo:
                            solo_node = em_node
                            break
                    else:
                        continue
                    break        
                # Find solo_light if it exists
                solo_light=[o for o in context.scene.collection.all_objects if o.type=='LIGHT' and o.lightmixer.solo]
                if solo_light:
                    solo_light[0].lightmixer.solo = False
                    node.lightmixer.solo = True
                elif context.scene.world.solo:
                    context.scene.world.solo = False
                    node.lightmixer.solo = True
                elif solo_node:
                    if solo_node == node:
                        node.lightmixer.solo = False  
                    else:
                        solo_node.lightmixer.solo = False
                        node.lightmixer.solo = True
            else:
                node.lightmixer.solo = not node.lightmixer.solo
        else:
            if not context.scene.lightmixer.solo_active:
                node.lightmixer.enabled = not node.lightmixer.enabled
    
        return{'FINISHED'}
                    
    def invoke(self, context, event):
        self.shift = event.shift
        return self.execute(context)
        
class LIGHTMIXER_OT_MaterialEnable(bpy.types.Operator):
    bl_idname = "lightmixer.material_enable"
    bl_label = "Enable all Emissives in Material"
    bl_description = "Shift-Click to Solo this Emissive"
    bl_options = {'UNDO'}
    
    mat_name: bpy.props.StringProperty()
    shift: bpy.props.BoolProperty()
    
    def execute(self, context):
        mat = bpy.data.materials[self.mat_name]
        # if self.mat_name:
        #     mat = bpy.data.materials[self.mat_name]
        #     emissive_mats=[mat for mat in bpy.data.materials if mat.get('is_emissive', False)]
        # 
        #     if self.shift:
        #         # Control other Solo settings from World and Lights
        #         if context.scene.lightmixer.solo_active:
        #             solo_mat=[mat for mat in emissive_mats if mat.lightmixer.solo]
        #             solo_light=[o for o in context.scene.collection.all_objects if o.type=='LIGHT' and o.lightmixer.solo]
        #             if solo_light:
        #                 solo_light[0].lightmixer.solo = False
        #                 mat.lightmixer.solo = True
        #             elif context.scene.world.solo:
        #                 context.scene.world.solo = False
        #                 mat.lightmixer.solo = True
        #             elif solo_mat:
        #                 if solo_mat[0] == mat:
        #                     mat.lightmixer.solo = False  
        #                 else:
        #                     solo_mat[0].lightmixer.solo = False
        #                     mat.lightmixer.solo = True
        #         else:
        #             mat.lightmixer.solo = not mat.lightmixer.solo
        #     else:
        if not context.scene.lightmixer.solo_active:
            mat.lightmixer.enabled = not mat.lightmixer.enabled
        
        return{'FINISHED'}
    # 
    # def invoke(self, context, event):
    #     self.shift = event.shift
    #     return self.execute(context)
        
class LIGHTMIXER_OT_AddBackfaceCullingNodes(bpy.types.Operator):
    bl_idname = "lightmixer.add_backface_culling_nodes"
    bl_label = "Add Backface Culling Nodes"
    bl_options = {'UNDO'}
    
    mat_name: bpy.props.StringProperty()
    
    def execute(self, context):
        mat = bpy.data.materials[self.mat_name]
        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            bfc = [n for n in nodes if n.name=="BackfaceCulling" and n.bl_idname=='ShaderNodeMixShader']
            
            if mat.lightmixer.backface_culling:
                links = mat.node_tree.links
                
                if not mat.get('em_nodes',''):
                    show_message("Couldn't find any Emissive node, please Scan Emissive materials again.")
                    return {'CANCELLED'}           
                
                output = [n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial' and n.target!='EEVEE']
                if output:
                    output = output[0]
                else:
                    show_message("Couldn't find any Output node, can't insert Backface Culling nodes.")
                    return {'CANCELLED'}
                    
                link = [l for l in links if l.to_socket==output.inputs[0]]
                if not link:
                    show_message("Couldn't find any link to the Output node, can't insert Backface Culling nodes.")
                    return {'CANCELLED'}     
                       
                if bfc:
                    bfc = bfc[0]
                    bfc.mute=False
                else:
                    bfc = nodes.new('ShaderNodeMixShader')
                    bfc.location = (output.location[0]+200, output.location[1])
                    bfc.name = "BackfaceCulling"

                    transp = nodes.new('ShaderNodeBsdfTransparent')
                    transp.location = (output.location[0], output.location[1]-70)
                    
                    geo = [n for n in nodes if n.bl_idname=='ShaderNodeNewGeometry']
                    if not geo:
                        geo = nodes.new('ShaderNodeNewGeometry')
                        geo.location = (output.location[0], output.location[1]+220)
                    else:
                        geo = geo[0]

                    # Connect Nodes together
                    links.new(geo.outputs['Backfacing'], bfc.inputs[0])
                    links.new(transp.outputs[0], bfc.inputs[2])
                    
                    # Move Output node
                    output.location[0] += 400
                
                    # Insert into node tree    
                    from_socket = link[0].from_socket.name
                    from_node = link[0].from_node
                    links.new(from_node.outputs[from_socket],bfc.inputs[1])
                    links.new(bfc.outputs[0],output.inputs[0])
            else:
                if bfc:
                    bfc[0].mute = True

        return{'FINISHED'}