import bpy
from bpy.props import StringProperty
from bpy.types import Operator

class PHOTOGRAPHER_OT_ButtonStringClear(Operator):
    bl_idname = "photographer.button_string_clear"
    bl_label = "Clear string name search"

    prop : StringProperty()
    type : StringProperty()

    def execute(self, context):
        if self.type == 'light':
            settings = context.scene.lightmixer
        else:
            settings = context.scene.photographer
        if settings.get(self.prop,False):
            settings[self.prop] = ""
            return {'FINISHED'}
        else:
            return {'CANCELLED'}        

class PHOTOGRAPHER_OT_ButtonEnumClear(Operator):
    bl_idname = "photographer.button_enum_clear"
    bl_label = "Clear Enum"

    prop : StringProperty()

    def execute(self, context):
        settings = context.scene.photographer
        if settings.get(self.prop,False):
            settings[self.prop] = self.prop[0]
            return {'FINISHED'}
        else:
            return {'CANCELLED'}