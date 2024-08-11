#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . mat_functions import get_mat_data, check_node, followLinks
from . SMR_CALLBACK import SMR_callback

class SMR_OT_ADDPART(bpy.types.Operator):
    bl_idname = "smr.addpart"
    bl_label = "Addpart"
    bl_description = "Add a setup to this material"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    def execute(self, context):        
        if bpy.context.active_object.mode != 'OBJECT':
            self.report({'WARNING'}, 'You are not in object mode')
            return {'FINISHED'}

        categ = self.categ
        settings= context.scene.SMR
        if categ == 'Cavity' or categ == 'Edge':
            add_wear(categ)
            SMR_callback(self)
            return {'FINISHED'}
        elif categ == 'Droplets':
            add_droplets()
            normals_connect(self, 'droplets')
            SMR_callback(self)
            return {'FINISHED'}

        add_subsetup(categ)
        scale = define_mat_scale(context.active_object)
        SMR_callback(self)
        if categ == 'Scratch':
            normals_connect(self, 'scratch')
            settings.scratch_scale = scale * 2
        if categ == 'Dust':
            settings.dust_scale = scale
            settings.dust_genscale = scale      
        if categ == 'Smudge':
            settings.smudge_scale = scale        
        return {'FINISHED'}

def define_mat_scale(object):
    """
    uses a custom made mathematical formula to determine the best scale for this texture
    """
    dims = object.dimensions
    avg = sum(dims)/len(dims)
    tex_scale_fac = 3.7/(avg + 0.149)
    if tex_scale_fac > 20:
        tex_scale_fac  = 20
    return tex_scale_fac/2


def add_wear(categ):
    SMR_settings = bpy.context.scene.SMR
    if categ == 'Cavity':
        SMR_settings.wear_cavity = True
        mat, nodes, links = get_mat_data()
        
        check_node('SMR_Bake_Texture', 'ShaderNodeTexImage')
        texture_node = nodes['SMR_Bake_Texture']
        SMR_main_node = nodes['SMR']
            
        check_node('SMR_Influence_CWear', 'group')
        influence_node = nodes['SMR_Influence_CWear']
        
        links.new(texture_node.outputs[0], influence_node.inputs[0])
        links.new(influence_node.outputs[0], SMR_main_node.inputs[17])
        
        loc_dy = -270
    if categ == 'Edge':
        SMR_settings.wear_edge = True
        mat, nodes, links = get_mat_data()
        
        check_node('SMR_Bake2_Texture', 'ShaderNodeTexImage')
        texture_node = nodes['SMR_Bake2_Texture']
        SMR_main_node = nodes['SMR']
            
        check_node('SMR_Influence_EWear', 'group')
        influence_node = nodes['SMR_Influence_EWear']
        
        links.new(texture_node.outputs[0], influence_node.inputs[0])
        links.new(influence_node.outputs[0], SMR_main_node.inputs[15])
        
        loc_dy = -320
    
    loc_x = nodes['SMR'].location[0] 
    loc_y = nodes['SMR'].location[1] - 200
    texture_node.location = loc_x - 500, loc_y + loc_dy 
    influence_node.location = loc_x - 200, loc_y + loc_dy
                    
def add_subsetup(categ):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    
    check_node('SMR_{}'.format(categ), 'group')
    Categ_node = nodes['SMR_{}'.format(categ)]
    
    check_node('SMR_{}_Texture'.format(categ), 'ShaderNodeTexImage')   
    Texture_node = nodes['SMR_{}_Texture'.format(categ)]
    
    check_node('SMR_AT_{}'.format(categ), 'group')
    AT_node = nodes['SMR_AT_{}'.format(categ)]
    
    SMR_main_node = nodes['SMR']
    
    
    if categ == 'Smudge':
        SMR_settings.has_smudge = True
        main_socket = 2
        loc_dy = 50
    elif categ == 'Scratch':
        SMR_settings.has_scratch = True
        main_socket = 7
        loc_dy = -50
    elif categ == 'Dust':
        SMR_settings.has_dust = True
        main_socket = 12
        loc_dy = -150    

    
    links.new(AT_node.outputs[0], Texture_node.inputs[0])
    links.new(Texture_node.outputs[0], Categ_node.inputs[0])
    links.new(Categ_node.outputs[0], SMR_main_node.inputs[main_socket])
    if categ == 'Scratch':
        links.new(Categ_node.outputs[1], SMR_main_node.inputs[6])    

    loc_x = nodes['SMR'].location[0] 
    loc_y = nodes['SMR'].location[1] - 200
    
    Categ_node.location = loc_x - 200, loc_y + loc_dy
    Texture_node.location = loc_x - 500, loc_y + loc_dy + 30
    AT_node.location = loc_x - 700, loc_y + loc_dy 

def add_droplets():
    SMR_settings= bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()

    check_node('SMR_Droplets_Texture', 'ShaderNodeTexImage')   
    texture_node = nodes['SMR_Droplets_Texture']    

    check_node('SMR_Droplets_Coord', 'ShaderNodeTexCoord')
    coord_node =  nodes['SMR_Droplets_Coord']

    check_node('SMR_Droplets_Mapping', 'ShaderNodeMapping')
    mapping = nodes['SMR_Droplets_Mapping']


    SMR_main_node = nodes['SMR']
    
    links.new(coord_node.outputs[2], mapping.inputs[0])
    links.new(mapping.outputs[0], texture_node.inputs[0])
    links.new(texture_node.outputs[0], SMR_main_node.inputs[11])

    SMR_settings.has_droplets = True
    
    loc_x = nodes['SMR'].location[0] 
    loc_y = nodes['SMR'].location[1] - 200
    
    texture_node.location = loc_x - 275, loc_y -230
    mapping.location = loc_x - 500, loc_y -230
    coord_node.location = loc_x -700, loc_y - 230

def normals_connect(self, categ):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()
    SMR_catcher_node = nodes['SMR_Catcher']
    if categ == 'scratch':
        SMR_scratch_node = nodes['SMR_Scratch']
    else:
        SMR_scratch_node = nodes['SMR_Droplets_Texture']

    SMR_main_node = nodes['SMR']

    SMR_principled = None
    SMR_glass = None
    for node in nodes:
        if node.name == 'SMR_Principled' or node.name == "Extreme PBR BSDF":
            SMR_principled = node
        if node.name == 'SMR Glass':
            SMR_glass = node
    
    if 'SMR_Simple' in mat or 'SMR_Subset' in mat:
        normal_slot = 'Material Normal'
        for node in nodes:
            if node.label == 'Simple Decal Group':
                decal_group = node
                break
            if node.label == 'Subset Decal Group':
                decal_group = node
                break
            if node.label == 'Panel Decal Group':
                decal_group = node
                break
            if node.label == 'Info Decal Group':   
                decal_group = node
                normal_slot = 'Normal'
                break
        if 'SMR_Simple' in mat:
            source_normals_name, normals_socket = followLinks(decal_group, normal_slot)
            if source_normals_name != '' and source_normals_name != 'SMR':
                links.new(nodes[source_normals_name].outputs[normals_socket], SMR_catcher_node.inputs[2])
                if categ == 'scratch':
                    links.new(SMR_catcher_node.outputs[2], SMR_scratch_node.inputs[2])            
            links.new(SMR_main_node.outputs[2], decal_group.inputs[normal_slot])              
        if 'SMR_Subset' in mat:
            try:
                source_normals_name, normals_socket = followLinks(decal_group, 'Subset Normal')
                if source_normals_name != '' and source_normals_name != 'SMR':
                    links.new(nodes[source_normals_name].outputs[normals_socket], SMR_catcher_node.inputs[2])
                    if categ == 'scratch':
                        links.new(SMR_catcher_node.outputs[2], SMR_scratch_node.inputs[2])            
                links.new(SMR_main_node.outputs[2], decal_group.inputs['Subset Normal'])       
            except:
                pass
        return

    if SMR_principled != None:
        source_normals_name, normals_socket = followLinks(SMR_principled, 19 if (2, 91, 0) > bpy.app.version else 20)
        if source_normals_name != '' and source_normals_name != 'SMR':
            source_normals = nodes[source_normals_name]
            links.new(source_normals.outputs[normals_socket], SMR_catcher_node.inputs[2])
            if categ == 'scratch':
                links.new(SMR_catcher_node.outputs[2], SMR_scratch_node.inputs[2])
        links.new(SMR_main_node.outputs[2], SMR_principled.inputs['Normal'])
    elif SMR_glass != None:
        links.new(SMR_main_node.outputs[2], SMR_glass.inputs[3])  
    else:
        self.report({'WARNING'}, "SMUDGR couldn't automatically connect the normal map, please connect the node yourself")

