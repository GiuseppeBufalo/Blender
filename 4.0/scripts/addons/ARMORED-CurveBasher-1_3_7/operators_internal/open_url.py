# v1.0

import bpy


class CURVEBASH_OT_open_url(bpy.types.Operator):
    '''Youtube Video'''

    bl_idname  = 'curvebash.open_url'
    bl_label   = 'CURVEBASH Open URL'
    bl_options = {'REGISTER', 'INTERNAL'}

    url : bpy.props.StringProperty(default='https://gumroad.com/armoredcolony#xvVPd')

    def execute(self, context):
        bpy.ops.wm.url_open(url=self.url)
        return {'FINISHED'}

classes = (
    CURVEBASH_OT_open_url,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)    


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
