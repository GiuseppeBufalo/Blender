import bpy

from bpy.types import Operator

# add object W_Plane
class CSDF_OT_INSTALL_MODERNGL(Operator):
    """Installs ModernGL via PIP"""
    bl_idname = "mesh.csdf_installmoderngl"
    bl_label = "CSDF"

    @classmethod
    def poll(cls, context):
        try:  
            import moderngl
            return False
        except:
            return True

    def execute(self, context):

        from ..util.module_install import installModule

        installModule("moderngl")

        # import moderngl

        return {'FINISHED'}
