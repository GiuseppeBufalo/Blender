import bpy
from .. import bl_info
from .. utils.ui import get_icon


class PanelPUNCHit(bpy.types.Panel):
    bl_idname = "MACHIN3_PT_punchit"
    bl_label = "PUNCHit %s" % ('.'.join([str(v) for v in bl_info['version']]))
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MACHIN3"
    bl_order = 30

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator('machin3.punchit', text='Punch It', icon_value=get_icon('fist'))

        column.separator()

        column.operator('machin3.get_punchit_support', text='Get Support', icon='GREASEPENCIL')
        column.operator("wm.url_open", text='Documentation', icon='INFO').url = 'https://machin3.io/PUNCHit/docs'
