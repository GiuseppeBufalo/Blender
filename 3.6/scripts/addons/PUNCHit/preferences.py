import bpy
from bpy.props import FloatProperty, BoolProperty, IntProperty
from . utils.registration import get_path, get_name, get_addon
from . utils.ui import draw_keymap_items, get_keymap_item, get_icon
from . registration import keys as keysdict


decalmachine = None
meshmachine = None
machin3tools = None
curvemachine = None


class PUNCHitPreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()


    push_default: IntProperty(name="Push Default Value", description="Pushing means widening the Extrusion a tiny bit. \nThis helps with Precision Issues in Polygonal Meshes\nSet to 0 to attempt Extrusions without changing the Shape at all.", default=1, min=0)
    pull_default: IntProperty(name="Push Default Value", description="Pulling means receding the initially selected faces a tiny bit. \nThis helps with Precision Issues in Polygonal Meshes", default=1, min=0)

    non_manifold_extrude: BoolProperty(name="Support non-manifold meshes", description="Allow Extruding on non-manifold meshes", default=False)



    modal_hud_scale: FloatProperty(name="HUD Scale", description="Scale of HUD elements", default=1, min=0.1)
    modal_hud_timeout: FloatProperty(name="HUD Timeout", description="Modulate duration of fading HUD elements", default=1, min=0.1, max=10)

    def draw(self, context):
        global decalmachine, meshmachine, curvemachine, machin3tools

        if decalmachine is None:
            decalmachine = get_addon('DECALmachine')[0]

        if meshmachine is None:
            meshmachine = get_addon('MESHmachine')[0]

        if curvemachine is None:
            curvemachine = get_addon('CURVEmachine')[0]

        if machin3tools is None:
            machin3tools = get_addon('MACHIN3tools')[0]

        layout = self.layout

        column = layout.column(align=True)
        box = column.box()

        split = box.split()



        b = split.box()

        bb = b.box()
        bb.label(text="General")

        column = bb.column(align=True)
        row = column.row(align=True)
        rs = row.split(factor=0.2, align=True)
        rs.prop(self, "push_default", text="")
        rs.label(text="Push Default Value")

        row = column.row(align=True)
        rs = row.split(factor=0.2, align=True)
        rs.prop(self, "pull_default", text="")
        rs.label(text="Pull Default Value")

        column = bb.column()
        row = column.row()
        rs = row.split(factor=0.2)
        rs.prop(self, "non_manifold_extrude", text=str(self.non_manifold_extrude), toggle=True)

        if self.non_manifold_extrude:
            rss = rs.split(factor=0.34)
            rss.label(text="Support non-manifold meshes")
            rss.label(text="Experimental! Tends to require higher Push values!", icon='ERROR')
        else:
            rs.label(text="Support non-manifold meshes")

        bb = b.box()
        bb.label(text="HUD")

        column = bb.column(align=True)
        row = column.row(align=True)
        rs = row.split(factor=0.2, align=True)
        rs.prop(self, "modal_hud_scale", text="")
        rs.label(text="Scale")

        row = column.split(factor=0.2, align=True)
        row.prop(self, "modal_hud_timeout", text='')
        rs = row.split(factor=0.2, align=True)
        rs.label(text="Timeout")
        rs.label(text="Modulate Duration of Fading HUDs", icon='INFO')



        b = split.box()
        b.label(text="Keymaps")

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user


        keymap = 'Mesh'
        idname = 'wm.call_menu'
        properties=[('name', 'VIEW3D_MT_edit_mesh_extrude')]

        extrude_menu_kmi = get_keymap_item(keymap, idname, properties=properties, iterate=True)

        if extrude_menu_kmi:
            draw_keymap_items(kc, 'Extrude Menu', [{'keymap': keymap, 'idname': idname, 'properties': properties}], b)
        else:
            column = b.column()
            column.label(text="Your current keyconfig does not include a keymap item for the edit mesh Extrude Menu.", icon="ERROR")
            column.label(text="While you don't need this, it can be convenient to have.", icon="BLANK1")

            row = column.row()
            row.scale_y = 1.2
            row.label(text='', icon='BLANK1')
            row.operator('machin3.add_extrude_menu_keymap', text="Add Extrude Menu Keymap")
            row.label(text='', icon='BLANK1')

            column.separator()
            column.label(text="In any case, you can still use Punch It using the adjustable keymap item shown below.", icon="BLANK1")



        draw_keymap_items(kc, 'Mesh', keysdict['EXTRUDE'], b)



        column = layout.column(align=True)
        box = column.box()
        box.label(text="Support")

        column = box.column()
        row = column.row()
        row.scale_y = 1.5
        row.operator('machin3.get_punchit_support', text='Get Support', icon='GREASEPENCIL')

        column = layout.column(align=True)
        box = column.box()
        box.label(text="About")

        column = box.column(align=True)
        row = column.row(align=True)

        row.scale_y = 1.5
        row.operator("wm.url_open", text='PUNCHit', icon_value=get_icon('fist')).url = 'https://machin3.io/PUNCHit/'
        row.operator("wm.url_open", text='Documentation', icon='INFO').url = 'https://machin3.io/PUNCHit/docs'
        row.operator("wm.url_open", text='MACHINƎ.io', icon='WORLD').url = 'https://machin3.io'
        row.operator("wm.url_open", text='blenderartists', icon_value=get_icon('blenderartists')).url = 'https://blenderartists.org/t/punchit/1352729'

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
        row.operator("wm.url_open", text='CURVEmachine', icon_value=get_icon('save' if curvemachine else 'cancel_grey')).url = 'https://curve.machin3.io/'
        row.operator("wm.url_open", text='MACHIN3tools', icon_value=get_icon('save' if machin3tools else 'cancel_grey')).url = 'https://machin3.io/MACHIN3tools'
