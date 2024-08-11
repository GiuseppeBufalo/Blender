import bpy

from bpy.props import PointerProperty

from ..util.addon import addon_name, get_prefs


from .primitives.main import CSDF_primitives, draw_primitives

class CSDF_Props(bpy.types.AddonPreferences):
    bl_idname = addon_name

    prims : PointerProperty(type=CSDF_primitives)

    def draw(self, context):

        prefs = get_prefs()

        layout = self.layout

        # General settings
        box = layout.box()
        row = box.row()

        draw_primitives(prefs, row)

        layout.separator()

        box = layout.box()
        row = box.row()
        row.operator('mesh.csdf_installmoderngl', text="Install ModernGL", icon='SCRIPTPLUGINS')

        mgl_installed = False
        try:  
            import moderngl
            mgl_installed = True
        except:
            pass

        if mgl_installed:
            row = box.row()
            row.label(text="ModernGL has already been installed")
