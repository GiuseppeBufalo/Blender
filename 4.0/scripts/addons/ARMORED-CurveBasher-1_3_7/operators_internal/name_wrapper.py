import bpy

from .. utils import addon

def wrapped_operator():
    return bpy.ops.curvebash.kitbasher_modal('INVOKE_DEFAULT')


class CURVEBASH_OT_modal_object_wrapper(bpy.types.Operator):
    bl_idname  = 'object.modal_kitbasher'
    bl_label = 'Modal Kitbasher (Object Mode)'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return wrapped_operator()
        # try:
        #     wrapped_operator()
        # except RuntimeError:
        #     self.report({'ERROR'}, 'Error in Core Modal')
        # return {'FINISHED'}

class CURVEBASH_OT_modal_mesh_wrapper(bpy.types.Operator):
    bl_idname  = 'mesh.modal_kitbasher'
    bl_label = 'Modal Kitbasher (Edit Mesh Mode)'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return wrapped_operator()
        # return {'FINISHED'}

class CURVEBASH_OT_modal_curve_wrapper(bpy.types.Operator):
    bl_idname  = 'curve.modal_kitbasher'
    bl_label = 'Modal Kitbasher (Edit Curve Mode)'
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return wrapped_operator()
        # return {'FINISHED'}

classes = (
    CURVEBASH_OT_modal_object_wrapper,
    CURVEBASH_OT_modal_mesh_wrapper,
    CURVEBASH_OT_modal_curve_wrapper,
)

def register():
    return
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    return
    for cls in classes:
        bpy.utils.unregister_class(cls)