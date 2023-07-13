#pylint: disable=import-error, relative-beyond-top-level
import bpy  

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    """
    shows a warning box
    """
    def draw(self, context):
        self.layout.label(text = message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class SMR_OT_RESET(bpy.types.Operator):
    bl_idname = "smr.reset"
    bl_label = "resetsmudgr"
    bl_description = "reset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.SMR.subscribed = False                  
        return {'FINISHED'}         