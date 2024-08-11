import bpy
import os

from .. utils import addon


# class ARMORED_OT_Curve_Basher_Open_Preset_File(bpy.types.Operator):
#     '''Open the blend file that contains the default kitbash presets'''

#     bl_idname  = 'armored.open_kitbash_preset_file'
#     bl_label   = 'Open Kitbash Preset File'

#     def execute(self, context):
#         bpy.ops.wm.read_homefile(app_template='')
#         file_path = os.path.join(os.path.dirname(__file__), 'cable_packs/default_cables.blend')
#         bpy.ops.wm.open_mainfile(filepath=file_path)
#         return {'FINISHED'}


class CURVEBASH_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Curve Basher'
    bl_label = 'Curve Basher'

    def draw(self, context):
        layout = self.layout
        # layout.label(text='Tools:')
        # layout.operator('curvebash.kitbasher_modal', text='Curvebash Browser')
        # layout.operator('curvebash.raycast_curve', text='Curvecast')
        # layout.operator('object.curvebash_wire_generator', text='Wire Generator')
        # layout.operator('object.curvebash_draw_curve', text='Draw Curve')
        # layout.operator('curvebash.mesh_to_curvebash', text='Mesh to Curvebash')

        # layout.separator()
        layout.operator('curvebash.open_blend_file', text='Open Preset File')
        

class CURVEBASH_PT_SubPanel_Keymaps(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Curve Basher'
    bl_label = 'KEYMAPS:'
    bl_parent_id = 'CURVEBASH_PT_Panel'
    
    def draw(self, context):

        def keymap_block(self, context, category='Blank', factor=0.4):
            layout = self.layout
            box = layout.box()
            box.label(text=category)
            
            row       = box.row()
            split     = row.split(factor=factor)
            left_col  = split.column(align=True)
            right_col = split.column(align=True)

            left_col.alignment = 'RIGHT'
            right_col.alignment = 'LEFT'
            layout.separator()

            return left_col.label, right_col.label
        
        key, action =  keymap_block(self, context, category='Default Keymaps:')

        key(text='J');               action(text='- Curvebash Browser')
        key(text='C');               action(text='- Curvecast')
        key(text='Shift+A / Curve'); action(text='- Wire Generator')
        key(text='Shift+A / Curve'); action(text='- Draw Curve')
        key(text='RMB');             action(text='- Mesh to Curvebash')

        # key, action =  keymap_block(self, context, category='Kitbash Type:')

        # key(text='1');              action(text='- Basic')
        # key(text='2');              action(text='- Array')
        # key(text='3');              action(text='- Kitbash')
        # key(text='Scroll');         action(text='- Change Preset')
        # key(text='Shift + Scroll'); action(text='- Curve Resolution')

        # key, action =  keymap_block(self, context, category='Transform Mode:')

        # key(text='S');              action(text='- Scale')
        # key(text='R');              action(text='- Rotate')
        # key(text='T');              action(text='- Twisted Sister')

        # key, action =  keymap_block(self, context, category='Alternate Mode:')

        # key(text='ALT + Scale');    action(text='- Random Scale')
        # key(text='ALT + Twist');    action(text='- Reverse Twist')

        # key, action =  keymap_block(self, context, category='Reset Transform:')

        # key(text='Num 0');          action(text='- Reset ALL')
        # key(text='Alt + S');        action(text='- Reset Scale')
        # key(text='Alt + R');        action(text='- Reset Rotation')
        # key(text='Alt + T');        action(text='- Reset Twist')

        # key, action =  keymap_block(self, context, category='Viewport:')

        # key(text='W');              action(text='- Toggle Wireframe')
        # key(text='A');              action(text='- Toggle Smooth Shade')
        # key(text='TAB');            action(text='- Select Curve Points')
        # key(text='SPACE');          action(text='- Add Sub-D Modifier')


classes = (
    CURVEBASH_PT_Panel,
    CURVEBASH_PT_SubPanel_Keymaps,   # Not registering seems to be enough to disable it.
)

def register():
    if not addon.get_prefs().show_n_panel:
        return

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    try:
        for cls in classes:
            bpy.utils.unregister_class(cls)
    except Exception:
        pass