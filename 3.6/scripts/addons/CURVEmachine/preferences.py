import bpy
from bpy.props import  BoolProperty, FloatProperty, IntProperty
import os
from . utils.registration import get_path, get_name, get_addon
from . utils.ui import get_keymap_item, draw_keymap_items, get_icon, popup_message
from . registration import keys as keysdict


decalmachine = None
meshmachine = None
machin3tools = None
punchit = None


class CURVEmachinePreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()



    show_curve_split: BoolProperty(name="Show Curve Split tool", default=True)
    show_delete: BoolProperty(name="Show Delete Menu", default=True)




    modal_hud_scale: FloatProperty(name="HUD Scale", default=1, min=0.5, max=10)



    show_sidebar_panel: BoolProperty(name="Show Sidebar Panel", default=True)



    blendulate_segment_count: IntProperty(name="Blendulate default Segment Count", description="Use this many Segments, when invoking Blendulate with a single Point selection", default=6, min=0)



    update_available: BoolProperty()

    def draw(self, context):
        self.draw_thank_you()

        global decalmachine, meshmachine, machin3tools, punchit

        if decalmachine is None:
            decalmachine = get_addon('DECALmachine')[0]

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        if machin3tools is None:
            machin3tools = get_addon('MACHIN3tools')[0]

        if punchit is None:
            punchit = get_addon('PUNCHit')[0]

        menu_keymap = get_keymap_item('Curve', 'wm.call_menu', properties=[('name', 'MACHIN3_MT_curve_machine')], iterate=True)

        layout = self.layout

        column = layout.column(align=True)
        box = column.box()

        split = box.split()



        b = split.box()

        if menu_keymap.type in ['Y', 'X']:
            bb = b.box()
            bb.label(text="Menu")

            column = bb.column()
            row = column.row()
            rs = row.split(factor=0.2)

            if menu_keymap.type == 'Y':
                rs.prop(self, "show_curve_split", text=str(self.show_curve_split), toggle=True)
                rss = rs.split(factor=0.3)
                rss.label(text="Show Curve Split tool")
                rss.label(text="Because the Y key is used for the Menu", icon='INFO')

            else:
                rs.prop(self, "show_delete", text=str(self.show_delete), toggle=True)
                rss = rs.split(factor=0.3)
                rss.label(text="Show Delete tool")
                rss.label(text="Because the X key is used for the Menu", icon='INFO')

        bb = b.box()
        bb.label(text="HUD")

        column = bb.column()
        row = column.row()
        rs = row.split(factor=0.2)
        rs.prop(self, "modal_hud_scale", text="")
        rs.label(text="HUD Scale")


        bb = b.box()
        bb.label(text="3D View")

        column = bb.column(align=True)

        row = column.row()
        rs = row.split(factor=0.2)
        rs.prop(self, "show_sidebar_panel", text=str(self.show_sidebar_panel), toggle=True)
        rs.label(text="Show Sidebar Panel")


        bb = b.box()
        bb.label(text="Tools")

        column = bb.column(align=True)

        row = column.row()
        rs = row.split(factor=0.2)
        rs.prop(self, "blendulate_segment_count", text='')
        rs.label(text="Blendulate Default Segment Count")



        b = split.box()

        b.label(text="Keymaps")

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        draw_keymap_items(kc, 'Curve', keysdict['MENU'], b)
        draw_keymap_items(kc, 'Curve', keysdict['BLEND'], b)
        draw_keymap_items(kc, 'Curve', keysdict['MERGE'], b, skip_box_label=True)




        column = layout.column(align=True)
        box = column.box()
        box.label(text="Support")

        column = box.column()
        row = column.row()
        row.scale_y = 1.5
        row.operator('machin3.get_curvemachine_support', text='Get Support', icon='GREASEPENCIL')

        column = layout.column(align=True)
        box = column.box()
        box.label(text="About")

        column = box.column(align=True)
        row = column.row(align=True)

        row.scale_y = 1.5
        row.operator("wm.url_open", text='CURVEmachine', icon='CURVE_DATA').url = 'https://machin3.io/CURVEmachine/'
        row.operator("wm.url_open", text='Documentation', icon='INFO').url = 'https://machin3.io/CURVEmachine/docs'
        row.operator("wm.url_open", text='MACHINƎ.io', icon='WORLD').url = 'https://machin3.io'
        row.operator("wm.url_open", text='blenderartists', icon_value=get_icon('blenderartists')).url = 'https://blenderartists.org/t/curvemachine/1467375'

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator("wm.url_open", text='Patreon', icon_value=get_icon('patreon')).url = 'https://patreon.com/machin3'
        row.operator("wm.url_open", text='Twitter', icon_value=get_icon('twitter')).url = 'https://twitter.com/machin3io'
        row.operator("wm.url_open", text='Youtube', icon_value=get_icon('youtube')).url = 'https://www.youtube.com/c/MACHIN3/'
        row.operator("wm.url_open", text='Artstation', icon_value=get_icon('artstation')).url = 'https://www.artstation.com/machin3'

        column.separator()

        row = column.row(align=True)
        row.scale_y = 1.5
        row.operator("wm.url_open", text='DECALmachine', icon_value=get_icon('save' if decalmachine else 'cancel_grey')).url = 'https://decal.machin3.io'
        row.operator("wm.url_open", text='MESHmachine', icon_value=get_icon('save' if meshmachine else 'cancel_grey')).url = 'https://mesh.machin3.io'
        row.operator("wm.url_open", text='MACHIN3tools', icon_value=get_icon('save' if machin3tools else 'cancel_grey')).url = 'https://machin3.io/MACHIN3tools'
        row.operator("wm.url_open", text='PUNCHit', icon_value=get_icon('save' if punchit else 'cancel_grey')).url = 'https://machin3.io/PUNCHit'



    def draw_thank_you(self):
        thankypou_path = os.path.join(get_path(), 'thank_you')

        message = ["Thank you for purchasing CURVEmachine!",
                   "",
                   "Your support allows me to keep developing this addon and future ones, keeps updates free for everyone, and most importantly enables me to provide for my family.",
                   "If you haven't purchased CURVEmachine, please consider doing so."]

        if not os.path.exists(thankypou_path):
            with open(thankypou_path, mode='w') as f:
                f.write('\n'.join(m for m in message))

            popup_message(message)
