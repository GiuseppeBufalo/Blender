bl_info = {
    "name": "Set Center To Bottom",
    "author": "Giuseppe Bufalo",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Set the center to the bottom of an object",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy


def main(context):
    
 from mathutils import Matrix, Vector


 def origin_to_bottom(ob, matrix=Matrix()):
    me = ob.data
    mw = ob.matrix_world
    local_verts = [matrix @ Vector(v[:]) for v in ob.bound_box]
    o = sum(local_verts, Vector()) / 8
    o.z = min(v.z for v in local_verts)
    o = matrix.inverted() @ o
    me.transform(Matrix.Translation(-o))

    mw.translation = mw @ o

 for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        origin_to_bottom(o)
        #origin_to_bottom(o, matrix=o.matrix_world) # global


class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.set_center_to_bottom"
    bl_label = "Set Center To Bottom"


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
    # bpy.ops.object.set_center_to_bottom()
