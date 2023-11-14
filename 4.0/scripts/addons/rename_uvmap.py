bl_info = {
    "name": "Rename UVmap",
    "author": "Giuseppe Bufalo",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Rename uv map1",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy


def main(context):

 for obj in bpy.context.selected_objects :
    for uvmap in  obj.data.uv_layers :
        uvmap.name = 'map1'


class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.rename_uvmap"
    bl_label = "Rename UVmap"


    def execute(self, context):
        main(context)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SimpleOperator.bl_idname, text=SimpleOperator.bl_label)

# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access)
def register():
    bpy.utils.register_class(SimpleOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SimpleOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    # bpy.ops.object.remove_custom_normals()
