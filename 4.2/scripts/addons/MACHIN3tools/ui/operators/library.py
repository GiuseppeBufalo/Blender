import bpy
from ... utils.draw import draw_fading_label

class ReloadLibraries(bpy.types.Operator):
    bl_idname = "machin3.reload_libraries"
    bl_label = "MACHIN3: Reload Libraries"
    bl_description = "Reload Libraries"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
           return bpy.data.libraries

    def execute(self, context):
        text = []

        for lib in bpy.data.libraries:
            lib.reload()
            msg = f"Reloaded libary {lib.name.replace('.blend', '')} from {lib.filepath}"
            text.append(msg)
            print("INFO:", msg)

        draw_fading_label(context, text=text, move_y=40, time=4)
        return {'FINISHED'}
