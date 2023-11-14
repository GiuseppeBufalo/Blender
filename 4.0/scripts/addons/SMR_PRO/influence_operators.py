#pylint: disable=import-error, relative-beyond-top-level

import bpy
from . influence_functions import *
from . SMR_CALLBACK import SMR_callback

class SMR_OT_PREVIEW(bpy.types.Operator):
    bl_idname = "smr.preview"
    bl_label = "start previewing"
    bl_description = "Start preview"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    def execute(self, context):
        categ = self.categ
        SMR_preview(categ)               
        return {'FINISHED'} 


class SMR_OT_INFLUENCE(bpy.types.Operator):
    bl_idname = "smr.influence"
    bl_label = "add influence map"
    bl_description = "Add influence map"
    bl_options = {"REGISTER", "UNDO"}

    type : bpy.props.StringProperty()

    def execute(self, context):
        type = self.type
        add_influence(type)
        SMR_callback(self)              
        return {'FINISHED'}

class SMR_OT_TEXPAINT(bpy.types.Operator):
    bl_idname = "smr.texpaint"
    bl_label = "add texture paint map"
    bl_description = "Add texture paint map"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()

    def execute(self, context):
        categ = self.categ

        start_texture_paint(categ)            
        return {'FINISHED'}

class SMR_OT_REMOVEINFLUENCE(bpy.types.Operator):
    bl_idname = "smr.removeinfluence"
    bl_label = "remove influence map"
    bl_description = "Remove influence map"
    bl_options = {"REGISTER", "UNDO"}

    type : bpy.props.StringProperty()

    def execute(self, context):
        type = self.type
        remove_influence(type)              
        return {'FINISHED'}

class SMR_OT_STOPPREVIEW(bpy.types.Operator):
    bl_idname = "smr.stoppreview"
    bl_label = "stop previewing"
    bl_description = "Stop preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        stop_preview()               
        return {'FINISHED'}     





class SMR_OT_INFPRESET(bpy.types.Operator):
    bl_idname = "smr.infpreset"
    bl_label = "preset inf"
    bl_description = "Set this preset for your Influence Map"
    bl_options = {"REGISTER", "UNDO"}

    categ : bpy.props.StringProperty()
    
    def execute(self, context):
        categ = self.categ
        SMR_settings = bpy.context.scene.SMR
           
        presetno = categ [:1]
        categ = categ[1:]
        if presetno == '2':
            val1 = 70
            val2 = 70
            val4 = .9
        if presetno == '3':
            val1 = 100
            val2 = 70
            val4 = .6        
        if presetno == '1':
            val1 = 0
            val2 = 0
            val3 = 1
            val4 = 1    
        if presetno == '4':
            if categ == '1':       
                SMR_settings.inf1_mult = -1 * SMR_settings.inf1_mult
            elif categ == '2': 
                SMR_settings.inf2_mult = -1 * SMR_settings.inf2_mult   
            return {'FINISHED'}    
                                 
        if categ == '1':
            SMR_settings.inf1_black = val1
            SMR_settings.inf1_white = val2
            try:
                SMR_settings.inf1_mult = val3
            except:
                pass
            SMR_settings.inf1_inf = val4
        
        elif categ == '2':
            SMR_settings.inf2_black = val1
            SMR_settings.inf2_white = val2
            try:
                SMR_settings.inf2_mult = val3
            except:
                pass
            SMR_settings.inf2_inf = val4            
           
        return {'FINISHED'}   

class SMR_OT_PACK(bpy.types.Operator):
    bl_idname = "smr.pack"
    bl_label = "pack"
    bl_description = "Smudgr created an image for you. This will pack it in your file"
    bl_options = {"REGISTER", "UNDO"}

        
    def execute(self, context):
        obj = bpy.context.active_object.name
        SMR_settings = context.scene.SMR
        
        image_list = []
        
        for image in bpy.data.images:
            if 'SMR_Paint' in image.name:
                image_list.append(image)
            if 'SMR_Bake' in image.name:
                image_list.append(image)                
        
        for image in image_list:            
            image.pack()
            self.report({'INFO'}, "Image Packed: {}".format(image.name))
        
        bpy.context.scene.SMR.pack_confirmation = False
        SMR_settings.pack_ui = False
        return {'FINISHED'}    

class SMR_OT_NOPACK(bpy.types.Operator):
    bl_idname = "smr.nopack"
    bl_label = "don't pack"
    bl_description = "Don't pack the image, if you don't save it manually it will dissapear"
    bl_options = {"REGISTER", "UNDO"}

        
    def execute(self, context):
        bpy.context.scene.SMR.pack_confirmation = False
        bpy.context.scene.SMR.pack_ui = False
        return {'FINISHED'}    