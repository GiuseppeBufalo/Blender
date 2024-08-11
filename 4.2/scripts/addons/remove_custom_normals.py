bl_info = {
    "name": "Remove Custom Normals",
    "author": "Giuseppe Bufalo",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Remove custom normals from multiple objects",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy


def main(context):

 selection = bpy.context.selected_objects

 for o in selection:
    bpy.context.view_layer.objects.active = o
    bpy.ops.mesh.customdata_custom_splitnormals_clear()


class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.remove_custom_normals"
    bl_label = "Remove Custom Normals"


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
