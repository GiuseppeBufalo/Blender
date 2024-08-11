#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . mat_functions import get_mat_data
from . influence_functions import stop_preview

class SMR_OT_AT(bpy.types.Operator):
    bl_idname = "smr.at"
    bl_label = "AT setup"
    bl_description = "Add AT setup"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    def execute(self, context):
        categ = self.categ
        add_AT_setup(categ)                
        return {'FINISHED'}              

class SMR_OT_ATREMOVE(bpy.types.Operator):
    bl_idname = "smr.atremove"
    bl_label = "remove AT setup"
    bl_description = "Remove AT setup"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    def execute(self, context):
        categ = self.categ
        remove_AT_setup(categ)                
        return {'FINISHED'} 


def add_AT_setup(categ):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()

    categ_texture_node = nodes["SMR_{}_Texture".format(categ)]
    categ_AT_node = nodes["SMR_AT_{}".format(categ)]
    categ_node = nodes["SMR_{}".format(categ)]
    

    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.name = 'SMR_{}_Texture_AT'.format(categ)


    node.projection = categ_texture_node.projection
    node.projection_blend = categ_texture_node.projection_blend
    node.image = categ_texture_node.image
    node.hide = True

    links.new(categ_AT_node.outputs[1], node.inputs[0])
    links.new(node.outputs[0], categ_node.inputs[1])
    links.new(categ_AT_node.outputs[2], categ_node.inputs[4])

    node.location = categ_texture_node.location[0], categ_texture_node.location[1] - 28
    if categ == 'Smudge':
        SMR_settings.smudge_at = True
    if categ == 'Scratch':
        SMR_settings.scratch_at = True    
    if categ == 'Dust':
        SMR_settings.dust_at = True     
     
def remove_AT_setup(categ):
    SMR_settings = bpy.context.scene.SMR
    mat, nodes, links = get_mat_data()

    categ_texture_node = nodes["SMR_{}_Texture".format(categ)]
    categ_AT_node = nodes["SMR_AT_{}".format(categ)]
    categ_node = nodes["SMR_{}".format(categ)]
    AT_texture_node = nodes["SMR_{}_Texture_AT".format(categ)]

    nodes.remove(AT_texture_node)

    AT_link = categ_AT_node.outputs[2].links[0]
    links.remove(AT_link)

    reset_setup = categ_AT_node.inputs[1].default_value
    categ_AT_node.inputs[1].default_value = reset_setup 

    stop_preview()

    if categ == 'Smudge':
        SMR_settings.smudge_at = False
    if categ == 'Scratch':
        SMR_settings.scratch_at = False   
    if categ == 'Dust':
        SMR_settings.dust_at = False   