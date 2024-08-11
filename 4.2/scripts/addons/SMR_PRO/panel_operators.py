#pylint: disable=import-error, relative-beyond-top-level
import bpy
from . SMR_CALLBACK import SMR_callback
from . SMR_ADDMAIN import add_smr_base

class SMR_UL_SLOTS_UI(bpy.types.UIList):
    """
    UI for selecting images from Blender Python API
    """   
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        ma = slot.material
               
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            if ma:
                if ma.name == bpy.context.scene.SMR.SMR_active_mat:               
                    layout.prop(ma, "name", text="", emboss=False,  icon='EVENT_S')
                else:
                    layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class SMR_PICK_SLOT(bpy.types.Operator):
    """
    activates the currently active slot as smudgr slot
    """
    bl_idname = "smr.slot"
    bl_label = "Slot"
    bl_description = "Pick this slot"

    def execute(self, context):    
        SMR_callback(self)
        return {'FINISHED'} 

class SMR_GETBACK(bpy.types.Operator):
    """
    activates the currently active slot as smudgr slot
    """
    bl_idname = "smr.getback"
    bl_label = "Get Back"
    bl_description = "Takes you back to your old scene"

    def execute(self, context):    
        bpy.data.scenes.remove(bpy.data.scenes['SMR_Bake'])
        return {'FINISHED'} 

class SMR_NOCHOISE(bpy.types.Operator):
    """
    activates the currently active slot as smudgr slot
    """
    bl_idname = "smr.nochoice"
    bl_label = "CancelChoice"
    bl_description = "Cancel adding Smudgr setup"

    def execute(self, context):    
        context.scene.SMR.forbidden_node_choice = False
        context.scene.SMR.glass_node_choice = False
        return {'FINISHED'} 

class SMR_MANUALCHOISE(bpy.types.Operator):
    """
    activates the currently active slot as smudgr slot
    """
    bl_idname = "smr.manualchoice"
    bl_label = "ManualChoice"
    bl_description = "The nodes will be added, but you have to connect them yourself"

    def execute(self, context):    
        add_smr_base(self, 'Manual')
        context.scene.SMR.forbidden_node_choice = False
        context.scene.SMR.glass_node_choice = False
        return {'FINISHED'} 

class SMR_FORCECHOISE(bpy.types.Operator):
    """
    activates the currently active slot as smudgr slot
    """
    bl_idname = "smr.forcechoice"
    bl_label = "ForceChoice"
    bl_description = "Tries to automatically connect Smudgr anyways"

    def execute(self, context):    
        add_smr_base(self, 'Force')
        context.scene.SMR.forbidden_node_choice = False
        context.scene.SMR.glass_node_choice = False
        return {'FINISHED'} 