import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty

class Procedural_Crowds_Preferences(AddonPreferences):
    bl_idname = __package__

    filepath : StringProperty(
        name = "Assets Folder",
        subtype = "DIR_PATH",
        description = "Select Folder that contains Procedural crowds assets"
    )
    ext_img_editor : StringProperty(
        name = "External Image Editor",
        description = "Select Image editor in which gif previews will be opened",
        subtype = "FILE_PATH",
    )
    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text="Select Assets Folder")
        row.prop(self,"filepath" , text = "")
        row = layout.row()
        row.label(text="External Image Editor")
        row.prop(self,"ext_img_editor" , text = "")

classes = [Procedural_Crowds_Preferences]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
