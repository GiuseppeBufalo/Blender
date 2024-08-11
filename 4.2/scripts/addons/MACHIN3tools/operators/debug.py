import bpy

class Debug(bpy.types.Operator):
    bl_idname = "machin3.m3_debug"
    bl_label = "MACHIN3: M3 Debug"
    bl_description = "M3 Debug"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        return {'FINISHED'}
