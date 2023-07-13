#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . mat_functions import get_mat_data, followLinks
from . SMR_CALLBACK import SMR_callback

class SMR_CDELETE(bpy.types.Operator):
    """
    deletes a category
    """
    bl_idname = "smr.cdelete"
    bl_label = "CDelete"
    bl_description = "Removes the nodes of this category from your material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):    
        SMR_settings = context.scene.SMR
        categ = SMR_settings.smr_ui_categ

        mat, nodes, links = get_mat_data()
        remove_list = []

        for node in nodes:
            if str(categ).lower() in node.name.lower() and 'SMR' in node.name:
                name = node.name
                remove_list.append(name)

        for node_name in remove_list:
            node=nodes[node_name]
            nodes.remove(node) 
        
        if categ == 'Scratch':
            smr_main = nodes['SMR']
            catcher = nodes['SMR_Catcher']
            links.new(catcher.outputs[2], smr_main.inputs[6])

        SMR_settings.del_confirmation = False
        SMR_callback(self)
        return {'FINISHED'} 

class SMR_ADELETE(bpy.types.Operator):
    """
    deletes a category
    """
    bl_idname = "smr.adelete"
    bl_label = "ADelete"
    bl_description = "Removes the SMUDGR nodes from your material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):    
        SMR_settings = context.scene.SMR
        mat, nodes, links = get_mat_data()

        try:
            catcher = nodes['SMR_Catcher']
        except: 
            self.report({'WARNING'}, "No Smudgr Catcher node found, automatic removal not possible")
            return {'FINISHED'} 

        for node in nodes:
            if node.name == 'SMR_Principled' or node.name == 'Extreme PBR BSDF':
                connect_to = node
                socket = [0, 7, 'Normal']
            if node.name == 'SMR Glass':
                connect_to = node
                socket = [0,1,3]

        if not connect_to:
            self.report({'WARNING'}, "No Principled or Glass node found, automatic removal not possible")            

        diffuse_n, dif_socket = followLinks(catcher,0)
        if diffuse_n:
            diffuse = nodes[diffuse_n]
            links.new(diffuse.outputs[dif_socket], connect_to.inputs[socket[0]])
        roughness_n, roughness_socket = followLinks(catcher,1)
        if roughness_n:
            roughness = nodes[roughness_n]
            links.new(roughness.outputs[roughness_socket], connect_to.inputs[socket[1]])
        normal_n, normal_socket = followLinks(catcher,2)
        if normal_n:
            normal = nodes[normal_n]
            links.new(normal.outputs[normal_socket], connect_to.inputs[socket[2]])

        remove_list = []
        for node in nodes:
            if 'SMR' in node.name and node.name != 'SMR_Principled':
                remove_list.append(node.name)

        for node_name in remove_list:
            node=nodes[node_name]
            nodes.remove(node)                    



        SMR_settings.del_confirmation = False
        SMR_callback(self)
        return {'FINISHED'} 