import bpy


class AddExtrudeMenuKeymap(bpy.types.Operator):
    bl_idname = "machin3.add_extrude_menu_keymap"
    bl_label = "MACHIN3: Add Extrude Menu Keymap"
    bl_description = "Add User Keymap Item for the Edit Mesh Extrude Menu, mapped to ALT + E"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps.get('Mesh')

        if km:
            kmi = km.keymap_items.new('wm.call_menu', 'E', 'PRESS', shift=False, ctrl=False, alt=True)
            setattr(kmi.properties, 'name', 'VIEW3D_MT_edit_mesh_extrude')

        return {'FINISHED'}
