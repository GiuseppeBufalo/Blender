import bpy

from .. utils import addon


class CURVEBASH_OT_open_blend_file(bpy.types.Operator):
    '''Open the blend file that contains the default kitbash presets'''

    bl_idname  = 'curvebash.open_blend_file'
    bl_label   = 'Open Blend File'
    bl_options = {'REGISTER', 'INTERNAL'}

    filepath : bpy.props.StringProperty(name='File Path')

    def execute(self, context):
        import os
        from .. utils import addon

        # bpy.ops.wm.read_homefile(app_template='')
        file_path = os.path.join(addon.get_path(), 'resources', 'default_cables.blend')
        bpy.ops.wm.open_mainfile(filepath=file_path)

        return {'FINISHED'}

classes = (
    CURVEBASH_OT_open_blend_file,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)