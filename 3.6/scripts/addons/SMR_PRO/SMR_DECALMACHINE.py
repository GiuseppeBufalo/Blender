#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . smr_common import ShowMessageBox #specific to SMR
import random

class SMR_APPLYDECAL(bpy.types.Operator):
    """
    applies the active material to all selected decals from DecalMachine
    """
    bl_idname = "smr.applydecal"
    bl_label = "Apply to Decals"
    bl_description = "Goes over all selected decals and applies your active Smudgr material to them" #description specific to SMR
    bl_options = {"REGISTER", "UNDO"}

    #booleans for the user to select what material properties will be connected to the decal
    mat_col : bpy.props.BoolProperty(name="Material Base Color", description="", default=True)
    mat_r : bpy.props.BoolProperty(name="Material Roughness", description="", default=True)
    mat_n : bpy.props.BoolProperty(name="Material Normal", description="", default=True)

    #same as above, but for subsets
    sub_col : bpy.props.BoolProperty(name="Subset Base Color", description="", default=True)
    sub_r : bpy.props.BoolProperty(name="Subset Roughness", description="", default=True)
    sub_n : bpy.props.BoolProperty(name="Subset Normal", description="", default=True)

    def invoke(self,context,event):
        """
        checks if the selection is as expected, otherwise cancels operation and tells user. Also initializes some often used variables and calls the popup window
        """
        wm = context.window_manager

        self.selected = context.selected_objects
        self.active_object = context.active_object
        try:
            self.active_mat = context.active_object.active_material   
        except AttributeError:
            ShowMessageBox('Please select a Mesh object', 'What the Smudge!', 'ERROR') #specific SMR function
            return {'FINISHED'}    
        except:
            raise

        if self.active_object.DM.isdecal:
            ShowMessageBox('Select the material you wish to copy from as active object, this is a decal', 'What the Smudge!', 'ERROR') #specific SMR function
            return {'FINISHED'}                        

        found_decal = False
        for obj in self.selected:
            if obj.DM.isdecal:
                found_decal = True
                break
        
        if not found_decal:
            ShowMessageBox('No decals found in your selection', 'What the Smudge!', 'ERROR') #specific SMR function
            return {'FINISHED'}   

        found_principled = self.find_principled()[0]
        if not found_principled:
            ShowMessageBox('Your active material is not Principled Bsdf based', 'What the Smudge!', 'ERROR') #specific SMR function
            return {'FINISHED'}
        
        return wm.invoke_props_dialog(self)
    
    def draw(self,context):
        """
        shows a popup window for the user to select which material properties will be connected to the decal
        """
        layout=self.layout

        layout.label(text='Material attributes to apply:')
        col = layout.column(align = True)
        col.prop(self, 'mat_col')
        col.prop(self, 'mat_r')
        col.prop(self, 'mat_n')
        col.separator()
        col.label(text='Subset attributes to apply:')
        col.prop(self, 'sub_col')
        col.prop(self, 'sub_r')
        col.prop(self, 'sub_n')
        col.separator()
        row=col.row()
        row.label(text='May slow down parallax', icon = 'INFO') #specific to SMR
        row.operator('smr.info', text = '', icon = 'QUESTION').info = 'parallax' #info box operator, specific to SMR

    def find_principled(self):
        """
        checks the material of the active object to find a principled bsdf node, returns boolean and the principled node if it found one
        """
        mat = self.active_mat
        nodes = mat.node_tree.nodes
        for node in nodes:
            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                principled = node
                return True, principled
        return False, None

    def nodes_to_copy(self,active_mat):
        """
        returns all nodes in the active material except the principled bsdf and the material output
        """
        nodes = []
        for node in active_mat.node_tree.nodes:
            if node.bl_idname != 'ShaderNodeBsdfPrincipled' and node.bl_idname != 'ShaderNodeOutputMaterial':
                nodes.append(node)
        return nodes


    def copy_attributes(self, attributes, old_prop, new_prop): 
        for attr in attributes:
            if hasattr( new_prop, attr ):
                try:
                    setattr( new_prop, attr, getattr( old_prop, attr ) )
                except AttributeError:
                    pass
                except:
                    raise

    def get_node_attributes(self, node):
        """
        returns a list of all property identifiers of the node, excludes certain readonly attributes
        """

        #all attributes that shouldn't be copied
        ignore_attributes = ( "rna_type", "type", "dimensions", "inputs", "outputs", "internal_links", "select", 'interface', 'texture_mapping')

        attributes = []
        for attr in node.bl_rna.properties:
            if not attr.identifier in ignore_attributes and not attr.identifier.split("_")[0] == "bl":
                attributes.append(attr.identifier)

        return attributes


    def copy_nodes(self, nodes, group_n):
        """
        copies all nodes from the list into the group with their attributes
        """
        group = bpy.data.node_groups[group_n]
        
        #the attributes that should be copied for every link
        input_attributes = ( "default_value", "name" )
        output_attributes = ( "default_value", "name" )

        for node in nodes:
            #create a new node in the group and find and copy its attributes
            new_node = group.nodes.new( node.bl_idname )
            node_attributes = self.get_node_attributes( node )
            self.copy_attributes( node_attributes, node, new_node )

            #copy the attributes for all inputs
            for i, inp in enumerate(node.inputs):
                self.copy_attributes( input_attributes, inp, new_node.inputs[i] )

            #copy the attributes for all outputs
            for i, out in enumerate(node.outputs):
                self.copy_attributes( output_attributes, out, new_node.outputs[i] )


    def copy_links(self, context, nodes, group_n):
        """
        copies all links between the nodes in the list to the nodes in the group
        """
        group = bpy.data.node_groups[group_n]

        for node in nodes:
            #find the corresponding node in the created group
            new_node = group.nodes[ node.name ]
            
            for i, inp in enumerate( node.inputs ):
                for link in inp.links:
                    try:
                        #find the connected node for the link in the group
                        connected_node = group.nodes[ link.from_node.name ]
                        #connect the group nodes
                        group.links.new( connected_node.outputs[ link.from_socket.name ], new_node.inputs[i] )
                    except:
                        pass


    def add_group_nodes(self, group_n):
        """
        adds the group input and output node and positions them correctly
        """
        group = bpy.data.node_groups[group_n]
        group_input = group.nodes.new("NodeGroupInput")
        group_output = group.nodes.new("NodeGroupOutput")
        group_output.name = 'Output'
        group_input.name = 'Input'

        #if there are any nodes in the group, find the mini and maxi x position of all nodes and position the group nodes
        if len(group.nodes) == 0:
            return
        
        min_pos = 9999999
        max_pos = -9999999

        for node in group.nodes:
            if node.location[0] < min_pos:
                min_pos = node.location[0]
            elif node.location[0] + node.width > max_pos:
                max_pos = node.location[0]

        group_input.location = (min_pos - 250, 0)
        group_output.location = (max_pos + 250, 0)


    def connect_outputs(self, group_n):
        """
        checks in the old copy of the material what nodes were connected to the principled bsdf and then connects the corresponding node in the new group to the outputs of the group
        """
        group = bpy.data.node_groups[group_n]
        group_links = group.links
        group_nodes = group.nodes
        output_node = group_nodes['Output']
        principled = self.find_principled()[1]
        
        output_socket = 0
        #iterate over all inputs of the original principled bsdf
        for i, inp in enumerate(principled.inputs):
            for node_links in inp.links:
                source= node_links.from_node.name
                socket = node_links.from_socket.name
                principled_socket_name = inp.name
                
                corresponding_node = group_nodes[source]
                
                #connect to output
                found_output = False
                for output in group.outputs:
                    if output.name == inp.name:
                        found_output = True
                if not found_output:
                    group.outputs.new('NodeSocketColor', inp.name)
                socket_out = group.path_resolve('nodes["Output"].inputs[{}]'.format(output_socket))
                group.links.new(corresponding_node.outputs[socket], socket_out)

                #give the group output the same name as the principled Bsdf socket name
                group.outputs[output_socket].name = principled_socket_name
                output_socket += 1 

    def apply_mat_to_decal(self, decal_mat, group_n, skip_list):
        """
        adds the created nodegroup to the decal material, connecting it to the decal group. Returns the newly created group node in the decal material
        """
        decal_nodes = decal_mat.node_tree.nodes
        decal_links = decal_mat.node_tree.links
        
        try: 
            #checks if the group already exists, clearing all links if it did
            group = decal_nodes[group_n]
        except:
            #creates the group if it didn't exist yet
            group = decal_nodes.new("ShaderNodeGroup")
            group.name = group_n

        link_remove_list = [] #use list to prevent gotcha
        for output in group.outputs:
            for link in output.links:
                link_remove_list.append(link)
        for link in link_remove_list:
            decal_mat.node_tree.links.remove(link)

        group.node_tree = bpy.data.node_groups[group_n]
        random_offset = random.randint(0, 200)
        group.location = (-600, 800 - random_offset) #use random position offset to prevent node stacking. Not the best way, I know, but the other function I wrote didn't work as well

        group_type = None
        for node in decal_nodes:
            if node.name.lower().startswith('subset.'): # Does this always work? Are there other naming conventions?
                decal_group = node
                group_type = 'subset'
            elif node.name.lower().startswith('simple.'):
                decal_group = node
                group_type = 'simple'
            elif node.name.lower().startswith('panel.'):
                decal_group = node
                group_type = 'panel'

        if not group_type:
            ShowMessageBox('Something went wrong, could not find decal nodegroup', 'What the Smudge!', 'ERROR') #specific SMR function

        if 'Material Base Color' in skip_list and 'Material Roughness' in skip_list and 'Material Normal' in skip_list:
            skip_material = True
        else:
            skip_material = False
        if 'Subset Base Color' in skip_list and 'Subset Roughness' in skip_list and 'Subset Normal' in skip_list:
            skip_subset = True
        else:
            skip_subset = False

        #iterate over all outputs of the node group
        for i, output in enumerate(group.outputs):
            #adapting decalmachine node naming convention for materials: Material + same name as principled bsdf socket
            mat_input = 'Material ' + output.name
            #skips over sockets added to the skip list by user deselecting them in the popup menu

            if mat_input in decal_group.inputs and mat_input not in skip_list and not skip_material:
                decal_mat.node_tree.links.new(group.outputs[i], decal_group.inputs[mat_input])
            #continue if the decal is not a subset decal
            if group_type == 'simple':
                continue
            #adapting decalmachine node naming convention for subsets: Subset + same name as principled bsdf socket
            sub_input = 'Subset ' + output.name
            #skips over sockets added to the skip list by user deselecting them in the popup menu
            if sub_input in decal_group.inputs and sub_input not in skip_list and not skip_subset:
                decal_mat.node_tree.links.new(group.outputs[i], decal_group.inputs[sub_input])

        old_principled = self.find_principled()[1]
        #get old specular default value and set it in decalgroup
        if 'Specular' not in group.outputs:
            if not skip_material:
                decal_group.inputs['Material Specular'].default_value = old_principled.inputs['Specular'].default_value
            if 'Subset Specular' in decal_group.inputs and not skip_subset:
                decal_group.inputs['Subset Specular'].default_value = old_principled.inputs['Specular'].default_value

        #get old metallic default value and set it in decalgroup
        if 'Metallic' not in group.outputs:
            if not skip_material:
                decal_group.inputs['Material Metallic'].default_value = old_principled.inputs['Metallic'].default_value
            if 'Subset Metallic' in decal_group.inputs and not skip_subset:
                decal_group.inputs['Subset Metallic'].default_value = old_principled.inputs['Metallic'].default_value

        return group

    def reroute_group_uvs(self, group_n):
        """
        looks for nodes that were previously connected to UV coordinates, connecting them to the input of the node group so a seperate UV channel can be used on the decal
        """
        group = bpy.data.node_groups[group_n]
        nodes = group.nodes
        links = group.links
        group_input= nodes['Input']

        coord_nodes = []
        tex_nodes = []
        #searches for texture coordinate nodes and image nodes
        for node in nodes:
            if node.bl_idname == 'ShaderNodeTexCoord':
                coord_nodes.append(node)
            elif node.bl_idname == 'ShaderNodeTexImage':
                tex_nodes.append(node)

        #creates the new input as vector
        found_input = False
        for input in group.inputs:
            if input.name == 'Original UVs':
                found_input = True
        if not found_input:
            group.inputs.new('VECTOR', 'Original UVs')

        #iterates trough coordinate nodes, looking for nodes that were linked to the UV output of this node and linking them to the group input
        for c_node in coord_nodes:
            for node_links in c_node.outputs['UV'].links:
                destination= node_links.to_node
                destination_socket = node_links.to_socket.name   
                group.links.new(group_input.outputs[0], destination.inputs[destination_socket])




        


    def add_custom_uv(self, obj, group, source_uv):
        """
        adds a datatransfer modifier and a new uv channel called Source_UVs. Uses datatransfer to transfer the UVs of the target object to the decal. Then creates a UVmap node with this new UV channel and connects it to the material group
        """
     
        #look if modifier exists, otherwise creates it and sets it settings
        uv_mod = obj.modifiers.get("SMR_UVTransfer")
        if not uv_mod:
            uv_mod = obj.modifiers.new("SMR_UVTransfer", 'DATA_TRANSFER')
        uv_mod.object = self.active_object
        uv_mod.use_loop_data = True
        uv_mod.data_types_loops = {'UV'}
        uv_mod.loop_mapping =  'POLYINTERP_NEAREST'
        uv_mod.layers_uv_select_src = source_uv 
        #check if the source uvs layer already exists, otherwise creates it
        try:
            new_layer = obj.data.uv_layers["Source_UVs"]
        except:
            new_layer = obj.data.uv_layers.new(name="Source_UVs")
        bpy.context.view_layer.objects.active = obj #really weird stuff, but the next line only works if the object is active, otherwise it can't find the just created UV-layer
        uv_mod.layers_uv_select_dst = new_layer.name

        #return if the material group does not have a vector input, indicating that it does't have images that use the UV channel
        if 'Vector' not in group.inputs:
            return

        nodes = obj.active_material.node_tree.nodes
        links = obj.active_material.node_tree.links

        #create the UVMap node and connect it to the group
        try:
            uv_node = nodes['Source Object UV Map']
        except:
            uv_node = nodes.new('ShaderNodeUVMap')
        uv_node.uv_map = 'Source_UVs'
        uv_node.name = 'Source Object UV Map'
        
        uv_node.location = (group.location[0] -300, group.location[1])
        
        links.new(uv_node.outputs[0], group.inputs['Vector'])

    def remove_unused_groups(self):
        """
        removes any unused nodegroups that have _Copy in their name, meaning they were created by this script
        """
        remove_list = [] #use a list to prevent deleting things while iterating trough them
        for node_group in bpy.data.node_groups:
            if node_group.users == 0 and '_Copy' in node_group.name:
                remove_list.append(node_group)
        for node_group in remove_list:
            bpy.data.node_groups.remove(node_group)

    def remove_unconnected_nodes(self, decal_mat):
        """
        removes any unused nodegroups in the material, indicated by having no output links. 
        """
        remove_list = [] #use list to prevent gotcha
        nodes = decal_mat.node_tree.nodes
        links = decal_mat.node_tree.links
        #iterates over all nodes in material, first checking if it was created by this script and then deletes it if it has no links from its outputs
        for node in nodes:
            if '_Copy' in node.name:
                connected = False
                for output in node.outputs:
                    if output.is_linked:
                        connected = True
                if not connected:
                    remove_list.append(node)
        for node in remove_list:
            decal_mat.node_tree.nodes.remove(node)

    def clear_group(self, group):
        remove_list = [] #use list to prevent deleting items while iterating trough the same items
        for node in group.nodes:
            remove_list.append(node)
        for node in remove_list:
            group.nodes.remove(node)      


    def execute(self, context):    
        """
        execute
        """
        # dictionary of the booleans the user selected for which material channels should be copied
        toggles = {'Material Base Color': self.mat_col, 'Material Roughness' : self.mat_r, 'Material Normal': self.mat_n, 'Subset Base Color': self.sub_col, 'Subset Roughness': self.sub_r, 'Subset Normal': self.sub_n}
        
        #add the channels to the skip_list if their booleans in the dict are false
        skip_list = []
        for socket_name in toggles:
            if not toggles[socket_name]:
                skip_list.append(socket_name)

        #remove unused node groups created previously by this operator
        self.remove_unused_groups()

        group_name = self.active_mat.name + '_Copy'
        #check if group exists, clears it if it does
        

        group = bpy.data.node_groups.new( name=group_name, type="ShaderNodeTree" )
        
        group_n = group.name

        
        #run trough the functions for creating the actual group, all in bpy.data not in an actual material
        nodes = self.nodes_to_copy(self.active_mat)
        self.copy_nodes( nodes, group_n ) 
        self.copy_links( context, nodes, group_n )        
        
        self.add_group_nodes(group_n)
        self.reroute_group_uvs(group_n)
        self.connect_outputs(group_n)        

        #needs to be checked here, since the decals will become the active object during iterating
        try:
            source_uv = context.active_object.data.uv_layers.active.name
        except:
            new_uv = context.active_object.data.uv_layers.new()
            source_uv = new_uv.name

        #iterates over selected objects, adding the node_group to them if they are a decal
        i = 0
        for obj in self.selected:
            #return if not a decal
            if not obj.DM.isdecal:
                continue
            #only run for simple decals and subset decals
            if obj.DM.decaltype != 'SIMPLE' and obj.DM.decaltype != 'SUBSET' and obj.DM.decaltype != 'PANEL':
                continue
            #iterate over possibly multiple materials
            for slot in obj.material_slots:
                #double check the decal actually has a material, continueing to the the next if not
                try:
                    decal_mat = slot.material
                except:
                    continue
                #kind of redundant, but I like it
                if not decal_mat.DM.isdecalmat:
                    continue
                
                bpy.context.view_layer.objects.active = self.active_object
                #add the group to the material and connect it
                self.apply_mat_to_decal(decal_mat, group_n, skip_list)
                
                
                #add the custom uv channel
                group = decal_mat.node_tree.nodes[group_n]
                self.add_custom_uv(obj, group, source_uv)
                #remove any left over unconnected nodes from previous runs
                self.remove_unconnected_nodes(decal_mat)
                i+=1

        #make original active again
        bpy.context.view_layer.objects.active = self.active_object
        ShowMessageBox('Applied Smudgr to {} decals'.format(i), 'Apply to decals', 'INFO') #specific to SMR
        return {'FINISHED'} 