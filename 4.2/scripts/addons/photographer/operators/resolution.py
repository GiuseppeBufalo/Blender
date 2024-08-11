import bpy
from bpy.props import BoolProperty

class PHOTOGRAPHER_OT_FlipImage(bpy.types.Operator):
    bl_idname = "photographer.flip_image"
    bl_label = "Flip Image"
    bl_description = ("Flip image horizontally or vertically. \n "
                    "Can be useful to get a fresh look at the current composition")
    bl_options = {'UNDO'}

    use_scene_camera : BoolProperty(default=False)
    x : BoolProperty(default=False)
    y : BoolProperty(default=False)

    def execute(self,context,):
        if self.use_scene_camera:
            obj = context.scene.camera
        else:
            obj = [o for o in bpy.data.objects if o.type == 'CAMERA' and o.data is context.camera][0]

        if self.x:
         obj.scale[0] *= -1.0
        
        if self.y:
         obj.scale[1] *= -1.0
        
        return {'FINISHED'}
