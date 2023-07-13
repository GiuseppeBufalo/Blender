import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty
import os
from . properties import PlugLibsCollection
from . utils.registration import get_path, get_name, get_addon
from . utils.ui import draw_keymap_items, get_keymap_item, get_icon, popup_message
from . utils.library import get_lib
from . items import prefs_tab_items, prefs_plugmode_items


class MESHmachinePreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()



    def update_show_looptools_wrappers(self, context):

        if self.show_looptools_wrappers:
            looptools, name, _, _ = get_addon('LoopTools')

            if not looptools:
                bpy.ops.preferences.addon_enable(module=name)

    show_in_object_context_menu: BoolProperty(name="Show in Object Mode Context Menu", default=False)
    show_in_mesh_context_menu: BoolProperty(name="Show in Edit Mode Context Menu", default=False)

    show_looptools_wrappers: BoolProperty(name="Show LoopTools Wrappers", default=False, update=update_show_looptools_wrappers)

    show_mesh_split: BoolProperty(name="Show Mesh Split tool", default=False)
    show_delete: BoolProperty(name="Show Delete Menu", default=False)



    modal_hud_scale: FloatProperty(name="HUD Scale", default=1, min=0.5, max=10)
    modal_hud_color: FloatVectorProperty(name="HUD Font Color", subtype='COLOR', default=[1, 1, 1], size=3, min=0, max=1)
    modal_hud_hints: BoolProperty(name="Show Hints", default=True)
    modal_hud_follow_mouse: BoolProperty(name="Follow Mouse", default=True)
    modal_hud_timeout: FloatProperty(name="Timeout", description="Factor to speed up or slow down time based modal operators like Create Stash, Boolean, Symmetrize drawing, etc", default=1, min=0.5)

    stashes_hud_offset: IntProperty(name="Stashes HUD offset", default=0, min=0)
    symmetrize_flick_distance: IntProperty(name="Flick Distance", default=75, min=20, max=1000)



    def update_matcap(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        matcaps = [mc.name for mc in context.preferences.studio_lights if os.path.basename(os.path.dirname(mc.path)) == "matcap"]

        if self.matcap not in matcaps:
            self.avoid_update = True
            self.matcap = "NOT FOUND"

    matcap: StringProperty(name="Normal Transfer Matcap", default="toon.exr", update=update_matcap)
    experimental: BoolProperty(name="Experimental Features", default=False)



    assetspath: StringProperty(name="Plug Libraries", subtype='DIR_PATH', default=os.path.join(path, "assets", "Plugs"))

    pluglibsCOL: CollectionProperty(type=PlugLibsCollection)
    pluglibsIDX: IntProperty()

    newpluglibraryname: StringProperty(name="New Library Name")

    reverseplugsorting: BoolProperty(name="Reverse Plug Sorting (requires library reload or Blender restart)", default=False)

    libraryscale: IntProperty(name="Size of Plug Libary Icons", default=4, min=1, max=20)
    plugsinlibraryscale: IntProperty(name="Size of Icons in Plug Libaries", default=4, min=1, max=20)

    showplugcount: BoolProperty(name="Show Plug Count next to Library Name", default=True)
    showplugbutton: BoolProperty(name="Show Plug Buttons below Libraries", default=True)
    showplugbuttonname: BoolProperty(name="Show Plug Name on Insert Button", default=False)
    showplugnames: BoolProperty(name="Show Plug Names in Plug Libraries", default=False)

    plugxraypreview: BoolProperty(name="Auto-X-Ray the plug and its subsets, when inserting Plug into scene", default=True)
    plugfadingwire: BoolProperty(name="Fading wire frames (experimental)", default=False)

    plugcreator: StringProperty(name="Plug Creator", default="MACHIN3 - machin3.io, @machin3io")



    use_legacy_line_smoothing: BoolProperty(name="Use Legacy Line Smoothing", description="Legacy Line Smoothing using the depreciated bgl module\nIf this is disabled, lines drawn by MESHmachine won't be anti aliased.", default=False)



    def update_tabs(self, context):
        if self.tabs == "ABOUT":
            self.addons_MESHmachine = get_addon('MESHmachine')[0]
            self.addons_MACHIN3tools = get_addon('MACHIN3tools')[0]
            self.addons_GrouPro = get_addon('Group Pro')[0]
            self.addons_BatchOps = get_addon('Batch Operations™')[0]
            self.addons_HardOps = get_addon('Hard Ops 9')[0]
            self.addons_BoxCutter = get_addon('BoxCutter')[0]

    tabs: bpy.props.EnumProperty(name="Tabs", items=prefs_tab_items, default="GENERAL", update=update_tabs)

    def update_plugmode(self, context):
        if self.plugremovemode is True:
            self.plugmode = "REMOVE"
        else:
            self.plugmode = "INSERT"

    plugmode: EnumProperty(name="Plug Mode", items=prefs_plugmode_items, default="INSERT")
    plugremovemode: BoolProperty(name="Remove Plugs", default=False, update=update_plugmode)

    update_available: BoolProperty(name="Update is available", default=False)

    addons_MESHmachine: BoolProperty(default=False)
    addons_MACHIN3tools: BoolProperty(default=False)
    addons_GrouPro: BoolProperty(default=False)
    addons_BatchOps: BoolProperty(default=False)
    addons_HardOps: BoolProperty(default=False)
    addons_BoxCutter: BoolProperty(default=False)

    avoid_update: BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        row = column.row()
        row.prop(self, "tabs", expand=True)

        box = column.box()

        if self.tabs == "GENERAL":
            self.draw_general_tab(box)
        elif self.tabs == "PLUGS":
            self.draw_plugs_tab(box)
        elif self.tabs == "ABOUT":
            self.draw_about_tab(box)

        self.draw_thank_you()



    def draw_general_tab(self, box):
        split = box.split()


        b = split.box()

        self.draw_menu(b)

        self.draw_tools(b)

        self.draw_HUD(b)

        self.draw_view3d(b)

        self.draw_experimental(b)




        b = split.box()

        self.draw_keymaps(b)

    def draw_plugs_tab(self, box):
        split = box.split()


        b = split.box()
        b.label(text="Plug Libraries")

        self.draw_assets_path(b)

        self.draw_plug_libraries(b)



        b = split.box()
        b.label(text="Plug Settings")

        self.draw_asset_loaders(b)

        self.draw_plug_creation(b)

    def draw_about_tab(self, box):
        split = box.split()

        b = split.box()
        b.label(text="MACHIN3")

        self.draw_machin3(b)


        b = split.box()
        b.label(text="Get More Plugs")
        self.draw_plug_resources(b)



    def draw_menu(self, layout):
        box = layout.box()
        box.label(text="Menu")

        column = box.column()

        row = column.row()
        row.label(text="show in Context Menus")
        r = row.split(factor=0.3)
        r.prop(self, "show_in_mesh_context_menu", text="in Edit Mode")
        r.prop(self, "show_in_object_context_menu", text="in Object Mode")

        column.separator()

        column.prop(self, "show_looptools_wrappers")

        if get_keymap_item('Mesh', 'machin3.call_mesh_machine_menu', 'X') or get_keymap_item('Object Mode', 'machin3.call_mesh_machine_menu', 'X'):
            column.prop(self, "show_delete")

        if get_keymap_item('Mesh', 'machin3.call_mesh_machine_menu', 'Y'):
            column.prop(self, "show_mesh_split")

    def draw_tools(self, layout):
        box = layout.box()
        box.label(text="Tools")

        b = box.box()
        b.label(text="Normal Transfer")

        column = b.column()

        row = column.split(factor=0.3)
        row.prop(self, "matcap", text="")
        row.label(text="Matcap used for Surface Check.")
        row.label(text="Leave empty, to disable", icon="INFO")

    def draw_HUD(self, layout):
        box = layout.box()
        box.label(text="HUD")

        column = box.column()

        row = column.row()

        rs = row.split(factor=0.35)
        rs.prop(self, "modal_hud_hints", text="True" if self.modal_hud_hints else "False", toggle=True)
        rs.label(text="Show Hints")

        rs = row.split(factor=0.35)
        rs.prop(self, "modal_hud_scale", text="")
        rs.label(text="HUD Scale")

        rs = row.split(factor=0.35)
        rs.prop(self, "modal_hud_color", text="")
        rs.label(text="HUD Color")

        row = column.row()

        rs = row.split(factor=0.35)
        rs.prop(self, "modal_hud_follow_mouse", text="True" if self.modal_hud_follow_mouse else "False", toggle=True)
        rs.label(text="Follow Mouse")

        rs = row.split(factor=0.35)
        rs.prop(self, "modal_hud_timeout", text='')
        rs.label(text="Timeout")

        rs = row.split(factor=0.35)
        rs.prop(self, "stashes_hud_offset", text='')
        rs.label(text="Stashes HUD Offset")


        column.separator()
        column.label(text="Symmetrize")

        row = column.split(factor=0.11)
        row.prop(self, 'symmetrize_flick_distance', text='')
        row.label(text="Flick Distance")

    def draw_view3d(self, layout):
        box = layout.box()
        box.label(text="View 3D")

        column = box.column()
        row = column.split(factor=0.11)
        row.prop(self, "use_legacy_line_smoothing", text='True' if self.use_legacy_line_smoothing else 'False', toggle=True)
        row.label(text="Use Legacy Line Smoothing")

    def draw_experimental(self, layout):
        box = layout.box()
        box.label(text="Experimental")

        column = box.column()
        row = column.split(factor=0.11)
        row.prop(self, "experimental", text='True' if self.experimental else 'False', toggle=True)
        row.label(text="Use Experimental Features, at your own risk")

        row.label(text="Not covered by Product Support!", icon_value=get_icon('error'))


    def draw_keymaps(self, layout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        from . registration import keys as keysdict

        box = layout.box()
        box.label(text="Keymaps")

        column = box.column()

        for name, keylist in keysdict.items():
            draw_keymap_items(kc, name, keylist, column)



    def draw_assets_path(self, layout):
        box = layout.box()
        column = box.column()

        column.prop(self, "assetspath", text="Location")

    def draw_plug_libraries(self, layout):
        box = layout.box()
        box.label(text="Libraries")

        column = box.column()

        row = column.row()
        row.template_list("MACHIN3_UL_plug_libs", "", self, "pluglibsCOL", self, "pluglibsIDX", rows=max(len(self.pluglibsCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_plug_library", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_plug_library", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()
        col.operator("machin3.clear_plug_libraries", text="", icon="LOOP_BACK")
        col.operator("machin3.reload_plug_libraries", text="", icon_value=get_icon("refresh"))
        col.separator()
        col.operator("machin3.open_plug_library", text="", icon="FILE_FOLDER")
        col.operator("machin3.rename_plug_library", text="", icon="OUTLINER_DATA_FONT")

        _, _, active = get_lib()
        icon = get_icon("cancel") if active and not active.islocked else get_icon("cancel_grey")
        col.operator("machin3.remove_plug_library", text="", icon_value=icon)

        row = column.row()
        row.prop(self, "newpluglibraryname")
        row.operator("machin3.add_plug_library", text="", icon_value=get_icon("plus"))

    def draw_asset_loaders(self, layout):
        box = layout.box()
        box.label(text="Asset Loaders")

        column = box.column()

        row = column.split(factor=0.1)
        row.prop(self, "libraryscale", text="")
        row.label(text="Size of Plug Library Icons")

        row = column.split(factor=0.1)
        row.prop(self, "plugsinlibraryscale", text="")
        row.label(text="Size of Icons in Plug Libraries")

        row = column.split(factor=0.1)
        row.prop(self, "reverseplugsorting", text="True" if self.reverseplugsorting else "False", toggle=True)
        r = row.split(factor=0.3)
        r.label(text="Reverse Plug Sorting")
        r.label(text="reqiures library reload or Blender restart", icon='INFO')

        row = column.split(factor=0.1)
        row.prop(self, "showplugcount", text="True" if self.showplugcount else "False", toggle=True)
        row.label(text="Show Plug Count next to Library Name")

        row = column.split(factor=0.1)
        row.prop(self, "showplugnames", text="True" if self.showplugnames else "False", toggle=True)
        row.label(text="Show Plug Names in Decal Libraries")

        row = column.split(factor=0.1)
        row.prop(self, "showplugbuttonname", text="True" if self.showplugbuttonname else "False", toggle=True)
        row.label(text="Show Plug Name on Insert Buttons")

        row = column.split(factor=0.1)
        row.prop(self, "plugxraypreview", text="True" if self.plugxraypreview else "False", toggle=True)
        row.label(text="Show Plugs 'In Front' when bringing them into the scene")

    def draw_plug_creation(self, layout):
        box = layout.box()
        column = box.column()

        row = column.split(factor=0.3)
        row.label(text="Plug Creator")
        row.prop(self, "plugcreator", text="")

        row = column.split(factor=0.3)
        row.label()
        row.label(text="Change this, so Plugs created by you, are tagged with your info!", icon="INFO")



    def draw_machin3(self, layout):
        installed = get_icon('save')
        missing = get_icon('cancel_grey')

        box = layout.box()
        box.label(text="Blender Addons")
        column = box.column()

        row = column.split(factor=0.3)
        row.scale_y = 1.2
        row.label(text="MESHmachine", icon_value=installed if self.addons_MESHmachine else missing)
        r = row.split(factor=0.2)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://mesh.machin3.io"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/l/MESHmachine"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://blendermarket.com/products/MESHmachine"

        row = column.split(factor=0.3)
        row.scale_y = 1.2
        row.label(text="DECALmachine", icon_value=installed)
        r = row.split(factor=0.2)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://decal.machin3.io"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/l/DECALmachine"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://blendermarket.com/products/DECALmachine"

        row = column.split(factor=0.3)
        row.scale_y = 1.2
        row.label(text="MACHIN3tools", icon_value=installed if self.addons_MACHIN3tools else missing)
        r = row.split(factor=0.2)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://machin3.io/MACHIN3tools"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/l/MACHIN3tools"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://blendermarket.com/products/MACHIN3tools"


        box = layout.box()
        box.label(text="MESHmachine Documentation")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Docs", icon='INFO').url = "https://machin3.io/MESHmachine/docs"
        row.operator("wm.url_open", text="Youtube", icon='FILE_MOVIE').url = "https://www.youtube.com/watch?v=i68jOGMEUV8&list=PLcEiZ9GDvSdXR9kd4O6cdQN_6i0LOe5lw"
        row.operator("wm.url_open", text="FAQ", icon='QUESTION').url = "https://machin3.io/MESHmachine/docs/faq"
        row.operator("machin3.get_meshmachine_support", text="Get Support", icon='GREASEPENCIL')


        box = layout.box()
        box.label(text="MESHmachine Discussion")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Blender Artists", icon="COMMUNITY").url = "https://blenderartists.org/t/meshmachine/1102529"
        row.operator("wm.url_open", text="polycount", icon="COMMUNITY").url = "https://polycount.com/discussion/205933/blender-meshmachine-hard-surface-focused-mesh-modeling"

        box = layout.box()
        box.label(text="Follow my work")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Web").url = "https://machin3.io"
        row.operator("wm.url_open", text="Twitter @machin3io").url = "https://twitter.com/machin3io"
        row.operator("wm.url_open", text="Twitter #MESHmachine").url = "https://twitter.com/search?q=(%23MESHmachine)%20(from%3Amachin3io)&src=typed_query&f=live"
        row.operator("wm.url_open", text="Artstation").url = "https://artstation.com/machin3"

    def draw_plug_resources(self, layout):
        column = layout.column()

        row = column.row()
        row.scale_y = 16
        row.operator("wm.url_open", text="Get More Plugs", icon='URL').url = "https://machin3.io/MESHmachine/docs/plug_resources"



    def draw_thank_you(self):
        thankypou_path = os.path.join(get_path(), 'thank_you')
        message = ["Thank you for purchasing MESHmachine!",
                   "",
                   "Your support allows me to keep developing this addon and future ones, keeps updates free for everyone, and most importantly enables me to provide for my family.",
                   "If you haven't purchased MESHmachine, please consider doing so."]

        if not os.path.exists(thankypou_path):
            with open(thankypou_path, mode='w') as f:
                f.write('\n'.join(m for m in message))

            popup_message(message)
