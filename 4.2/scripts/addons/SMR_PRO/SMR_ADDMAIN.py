#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . smr_common import ShowMessageBox
from . mat_functions import get_mat_data, followLinks, add_smr_name, move_all_nodes, check_node
from . SMR_CALLBACK import SMR_callback

class SMR_OT_ADD(bpy.types.Operator):
    bl_idname = "smr.addmain"
    bl_label = "Addsmudgr"
    bl_description = "Add a SMUDGR setup to this material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):        
        if bpy.context.active_object.mode != 'OBJECT':
            self.report({'WARNING'}, 'You are not in object mode')
            return {'FINISHED'}

        SMR_callback(self)
        add_smr_base(self, 'Normal')                         
        return {'FINISHED'}


def smr_base_connect(type, simple, subset):
    """
    connects the smudgr node to a principled bsdf node
    """        
    mat, nodes, links = get_mat_data()
    smudgr_main_node = nodes['SMR']
    smudgr_catcher_node = nodes['SMR_Catcher']
    
    links.new(smudgr_catcher_node.outputs[0], smudgr_main_node.inputs[0])
    links.new(smudgr_catcher_node.outputs[1], smudgr_main_node.inputs[1])

    if type == 'manual':
        return

    elif type == 'principled':
        #find the principled bsdf
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                connection_node = node
        if connection_node.name == 'Extreme PBR BSDF':
            pass
        else:
            #renames the principled to SMUDGR terms
             connection_node.name = 'SMR_Principled'
        
        input_source_color, color_socket = followLinks(connection_node, 0)
        input_source_roughness, roughness_socket = followLinks(connection_node, 7)
        
        socket_roughness = 7
        socket_color = 0
        
    elif type == 'glass':
        for node in nodes:
            if node.type == 'BSDF_GLASS':
                connection_node = node
                connection_node.name = 'SMR Glass'
        input_source_roughness = ''
        input_source_color = ''
        socket_roughness = 1
        socket_color = 0

    else:
        for node in nodes:
            if node.name.lower().startswith(type):
                connection_node = node    
        input_source_color, color_socket = followLinks(connection_node, 0)
        input_source_roughness, roughness_socket = followLinks(connection_node, 7)

        socket_roughness = 7
        socket_color = 0
        if simple:
            mat['SMR_Simple'] = 1
        socket_sub_roughness = 'Subset Roughness'
        socket_sub_color = 'Subset Base Color'

        input_source_sub_color, color_sub_socket = followLinks(connection_node, socket_sub_color)
        input_source_sub_roughness, roughness_sub_socket = followLinks(connection_node, socket_sub_roughness)




    if subset:
        try:
            links.new(smudgr_main_node.outputs[0], connection_node.inputs[socket_sub_color])
            links.new(smudgr_main_node.outputs[1], connection_node.inputs[socket_sub_roughness])  
            if input_source_sub_color != '' and input_source_sub_color != 'SMR':
                input_source_node = nodes[input_source_sub_color]
                links.new(input_source_node.outputs[color_sub_socket], smudgr_catcher_node.inputs[0])
            else:
                base_color = connection_node.inputs[socket_sub_color].default_value
                smudgr_catcher_node.inputs[0].default_value= base_color 
                    
            if input_source_sub_roughness != '' and input_source_sub_roughness != 'SMR':
                input_source_node = nodes[input_source_sub_roughness]
                links.new(input_source_node.outputs[roughness_sub_socket], smudgr_catcher_node.inputs[1])
            else:
                base_roughness = connection_node.inputs[socket_sub_roughness].default_value
                smudgr_catcher_node.inputs[1].default_value=base_roughness 
            mat['SMR_Subset'] = 1
        except:
            pass

    if simple:
        links.new(smudgr_main_node.outputs[0], connection_node.inputs[socket_color])
        links.new(smudgr_main_node.outputs[1], connection_node.inputs[socket_roughness])
        #creates a new link to the smudgr node from the node that was connected to the principled bsdf before                
        if input_source_color != '' and input_source_color != 'SMR':
            input_source_node = nodes[input_source_color]
            links.new(input_source_node.outputs[color_socket], smudgr_catcher_node.inputs[0])
        else:
            base_color = connection_node.inputs[0].default_value
            smudgr_catcher_node.inputs[0].default_value= base_color 
                
        if input_source_roughness != '' and input_source_roughness != 'SMR':
            input_source_node = nodes[input_source_roughness]
            links.new(input_source_node.outputs[roughness_socket], smudgr_catcher_node.inputs[1])
        else:
            base_roughness = connection_node.inputs[socket_roughness].default_value
            smudgr_catcher_node.inputs[1].default_value=base_roughness      

def analyse_material(self, choice):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    
    glass_list = []
    principled_list = [] 
    
    forbidden_node = False
    shader_node_list = ['ADD_SHADER', 'BSDF_ANISOTROPIC', 'BSDF_DIFFUSE', 'BSDF_TRANSLUCENT', 'EMISSION', 'BSDF_GLOSSY' ]
    
    for mat_node in mat.node_tree.nodes:
        if mat_node.type == 'BSDF_PRINCIPLED':
            principled_list.append(mat_node)

        elif mat_node.type == 'BSDF_GLASS':
            glass_list.append(mat_node)


        elif mat_node.label == 'Simple Decal Group':
            return 'simple', mat_node.location
        elif mat_node.label == 'Panel Decal Group':
            return 'panel', mat_node.location
        elif mat_node.label == 'Subset Decal Group':
            return 'subset', mat_node.location
        elif mat_node.label == 'Info Decal Group':
            return 'info', mat_node.location
        elif mat_node.type in shader_node_list:    
            forbidden_node=True
        
    if len(principled_list) > 1:
        self.report({'WARNING'}, "There are more than 1 Principled BSDF shader nodes. Please connect the SMUDGR node yourself")
        ShowMessageBox("There are more than 1 Principled BSDF shader nodes. SMUDGR does not know what to smudge. Please connect the SMUDGR node yourself", "What the smudge!", 'ERROR')    
        return 'manual', None
    
    elif forbidden_node:
        if len(principled_list) == 1:
            if choice == 'Force':
                principled = principled_list[0]
                loc = principled.location
                return 'principled', loc
            elif choice == 'Manual':
                return 'manual', None        
            else:
                SMR_settings.forbidden_node_choice = True            
        elif len(glass_list) == 1:
            if choice == 'Force':
                glass = glass_list[0]
                loc = glass.location
                return 'glass', loc
            elif choice == 'Manual':
                return 'manual', None  
            SMR_settings.glass_node_choice = True
        else:
            self.report({'WARNING'}, "This is a complex material, please connect the SMUDGR node yourself")
            ShowMessageBox("This is a complex material, please connect the SMUDGR node yourself", "What the smudge!", 'ERROR')
            return 'manual', None
        return 'problem', None
    
    elif len(glass_list)== 0 and len(principled_list)== 0:
        self.report({'WARNING'}, "No principled or glass setup found, please connect the SMUDGR node yourself")
        ShowMessageBox("No principled or glass setup found, please connect the SMUDGR node yourself", "What the smudge!", 'ERROR')
        return 'manual', None
    
    elif len(principled_list)== 1:
        principled = principled_list[0]
        loc = principled.location
        return 'principled', loc
    
    elif len(glass_list) == 1:
        glass = glass_list[0]
        loc = glass.location
        return 'glass', loc

    else:
        self.report({'WARNING'}, "SMUDGR had some problems connecting, please connect the SMUDGR node yourself")
        ShowMessageBox("SMUDGR had some problems connecting, lease connect the SMUDGR node yourself", "What the smudge!", 'ERROR')    
        return 'manual', loc

def add_smr_base(self, choice):
    SMR_settings = bpy.context.scene.SMR
    if not bpy.context.active_object.active_material:
        self.report({'WARNING'}, "No material found")
        return False

    mat, nodes, links = get_mat_data()
    type, loc = analyse_material(self, choice)
    if type == 'problem':
        return
    
    add_smr_name()

    try:
        move_all_nodes(loc[0])
    except:
        pass
    
    check = check_node('SMR', 'group')
    if check == False:
        self.report({'WARNING'}, "Incorrect file path")
        return False
    check_node('SMR_Catcher', 'group')
    
    
    SMR_node = nodes['SMR']
    Catcher_node = nodes['SMR_Catcher']
    
    if loc:
        loc_x = loc[0] - 300
        loc_y = loc[1]
        SMR_node.location = loc_x, loc_y
    
    Catcher_node.location = SMR_node.location[0]-200, SMR_node.location[1]
    bool1 = True
    bool2 = False
    if type == 'simple' or type == 'panel' or type == 'subset' or type == 'info':
        bool1 = SMR_settings.decal_mat
        bool2 = SMR_settings.decal_sub
    smr_base_connect(type, bool1, bool2)
    SMR_settings.is_SMR_slot = True
    return True