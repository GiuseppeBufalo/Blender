#pylint: disable=import-error, relative-beyond-top-level
import bpy

class SMR_PREFERENCES(bpy.types.AddonPreferences):
    """
    user preferences for changing file path
    """   
    bl_idname = 'SMR_PRO'
        
    SMR_path2: bpy.props.StringProperty(
        name='smr_path',
        description="file path for smudgr",
        default= '',
        subtype = 'FILE_PATH'
        )
    SMR_bakepath: bpy.props.StringProperty(
        name='smr_bakepath',
        description="bake path for smudgr",
        default= '',
        subtype = 'FILE_PATH'
        )   
    show_info : bpy.props.BoolProperty(default = False, name = 'Show FAQ')
    small_ui : bpy.props.BoolProperty(default = False, name = 'Smaller UI')
    
    def draw(self, context):
        #file path box
        layout = self.layout
        box=layout.box()
        box.label(text='Select the path to the SMR_Files here, see the installation manual for instructions')
        row = box.row()
        row.prop(self, 'SMR_path2', text = '')

        #update button
        row.operator("smr.update", text="Update images")
        col = box.column()
        col.label(text = 'If the path starts with //.. instead of a normal path, uncheck "relative paths"', icon = 'INFO')

        box=layout.box()
        box.label(text='Baking Export Path: (When left empty, SMR_Files will be used for exporting')
        box.prop(self, 'SMR_bakepath', text = '')

        box = layout.box()
        col = box.column()
        col.scale_y = 2
        row = col.row()
        row.alignment = 'LEFT'
        row.prop(self, 'show_info',
            icon="TRIA_DOWN" if self.show_info else "TRIA_RIGHT",
            emboss=False,
            toggle=True)
        if self.show_info: 
            col.label(text = 'Frequently Asked Questions:')
            col.operator("smr.info", text =  'Are there tutorials?', icon = "QUESTION").info = 'info_tut'
            col.operator("smr.info", text =  'Why am I seeing lines and/or stretching in the effects?', icon = "QUESTION").info = 'info_lines'
            col.operator("smr.info", text =  "I've added cavity wear, but it's not visible?", icon = "QUESTION").info = 'info_nocavity'
            col.operator("smr.info", text =  'How to add my own textures?', icon = "QUESTION").info = 'info_files'
            col.operator("smr.info", text =  'How to report a bug?', icon = "QUESTION").info = 'info_bug'   
            col.operator("smr.info", text =  'Where can I post a review?', icon = "QUESTION").info = 'info_review'
        box = layout.box()
        col = box.column()
        col.scale_y = 2
        col.prop(self, 'small_ui')

class SMR_UPDATE_PATH(bpy.types.Operator):
    """
    updates the path
    """
    bl_idname = "smr.update"
    bl_label = "Update Path"
    bl_description = "Updates the path"
    
    def execute(self, context):   
        bpy.context.scene.SMR.SMR_path = bpy.context.preferences.addons['SMR_PRO'].preferences.SMR_path2
        return {'FINISHED'} 