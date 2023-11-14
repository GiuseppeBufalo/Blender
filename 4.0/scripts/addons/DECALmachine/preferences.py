import bpy
import os
from distutils.dir_util import copy_tree
from shutil import copyfile
import platform
from bpy.props import CollectionProperty, IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty
from . properties import DecalLibsCollection, AtlasesCollection
from . utils.registration import get_path, get_name, reload_decal_libraries, get_addon, reload_all_assets, get_version_filename_from_blender
from . utils.ui import get_icon, popup_message, draw_keymap_items, draw_pil_warning
from . utils.system import makedir, abspath, get_PIL_image_module_path
from . utils.library import get_lib, import_library, get_atlas, import_atlas, get_legacy_libs
from . items import prefs_tab_items, prefs_asset_loader_tab_items, prefs_newlibmode_items, prefs_decalmode_items
from . import bl_info


class DECALmachinePreferences(bpy.types.AddonPreferences):
    path = get_path()
    bl_idname = get_name()


    def update_assetspath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        newpath = makedir(abspath(self.assetspath)) + os.sep
        oldpath = abspath(self.oldpath)

        if os.path.normpath(newpath) != os.path.normpath(oldpath):

            srcmydecalspath = os.path.join(oldpath, 'Decals', 'MyDecals')
            dstmydecalspath = os.path.join(newpath, 'Decals', 'MyDecals')

            if os.path.exists(srcmydecalspath) and os.path.exists(dstmydecalspath):
                index = "001"

                while os.path.exists(os.path.join(newpath, 'Decals', f'MyDecals_{index}')):
                    index = str(int(index) + 1).zfill(3)

                print("WARNING: Preventing MyDecals library collision to avoid accidental user-created Decal loss")
                os.rename(srcmydecalspath, os.path.join(oldpath, 'Decals', f'MyDecals_{index}'))

            print("INFO: Copying all DECALmachine assets from %s to %s" % (oldpath, newpath))

            folders = sorted([f for f in os.listdir(oldpath) if f in ['Atlases', 'Create', 'Decals', 'Export', 'Trims'] and os.path.isdir(os.path.join(oldpath, f))])

            for f in folders:
                print("  •", f)
                copy_tree(os.path.join(oldpath, f), os.path.join(newpath, f))

            supplied_decallibs = [os.path.join(newpath, 'Decals', f) for f in os.listdir(os.path.join(newpath, 'Decals')) if f in ['Aircraft', 'Examples', 'Example Panels', 'MyDecals']]

            for path in supplied_decallibs:
                is20path = os.path.join(path, '.is20')
                is280path = os.path.join(path, '.is280')

                if os.path.exists(is20path):
                    print("INFO: removing legacy version file:", is20path)
                    os.unlink(is20path)

                elif os.path.exists(is280path):
                    print("INFO: removing legacy version file", is280path)
                    os.unlink(is280path)

            supplied_trimsheetlibs = [os.path.join(newpath, 'Trims', f) for f in os.listdir(os.path.join(newpath, 'Trims')) if f in ['Example Sheet']]

            for path in supplied_trimsheetlibs:
                is20path = os.path.join(path, '.is20')

                if os.path.exists(is20path):
                    print("INFO: removing legacy version file:", is20path)
                    os.unlink(is20path)

            presetspath = os.path.join(oldpath, 'presets.json')

            if os.path.exists(presetspath):
                print("INFO: copying library visibility presets")
                copyfile(presetspath, os.path.join(newpath, 'presets.json'))

            reload_all_assets()

            self.oldpath = newpath

            self.avoid_update = True
            self.assetspath = newpath

    def update_importdecallibpath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.importdecallibpath.strip():
            path = abspath(self.importdecallibpath)

            if path and os.path.exists(path):
                msg = import_library(path)

            else:
                msg = "Path does not exist: %s" % (path)

            if msg:
                popup_message(msg, title="Decal Library could not be imported")


        self.avoid_update = True
        self.importdecallibpath = ""

    def update_newdecallibraryname(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        assetspath = self.assetspath
        name = self.newdecallibraryname.strip()

        if name:
            if os.path.exists(os.path.join(assetspath, 'Decals', name)):
                popup_message("This library exists already, choose another name!", title="Failed to add library", icon="ERROR")
            else:
                libpath = makedir(os.path.join(assetspath, 'Decals', name))

                print(" • Created decal library folder '%s'" % (libpath))

                with open(os.path.join(libpath, get_version_filename_from_blender()), "w") as f:
                    f.write("")

                self.avoid_update = True
                self.newdecallibraryname = ""

                reload_decal_libraries()

    def update_importatlaspath(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.importatlaspath.strip():
            path = abspath(self.importatlaspath)

            if path and os.path.exists(path):
                msg = import_atlas(path)

            else:
                msg = "Path does not exist: %s" % (path)

            if msg:
                popup_message(msg, title="Atlas could not be imported")

        self.avoid_update = True
        self.importatlaspath = ""

    defaultpath = os.path.join(path, 'assets' + os.sep)
    assetspath: StringProperty(name="DECALmachine assets:\nDecal Libraries, Trim Sheet Libraries, Decal Atlases as well as\ntemporary locations for Decal/Trim Sheet/Atlas Creation and Export", subtype='DIR_PATH', default=defaultpath, update=update_assetspath)
    oldpath: StringProperty(name="Old Path", subtype='DIR_PATH', default=defaultpath)

    decallibsCOL: CollectionProperty(type=DecalLibsCollection)
    decallibsIDX: IntProperty(name="Registered Decal or Trim Sheet")

    atlasesCOL: CollectionProperty(type=AtlasesCollection)
    atlasesIDX: IntProperty(name="Registered Atlas")

    newlibmode: EnumProperty(name="New Library Mode", items=prefs_newlibmode_items, default="EMPTY")
    importdecallibpath: StringProperty(name="Import Path", description="Choose a Folder or .zip File to load a Library from", subtype='FILE_PATH', default="", update=update_importdecallibpath)
    newdecallibraryname: StringProperty(name="New Library Name", description="Enter a name to create a new empty Decal Library", update=update_newdecallibraryname)

    libs_corrupted: BoolProperty(name="Corrupted Decal Sheet Libraries in Assets Location", default=False)
    libs_invalid: BoolProperty(name="Invalid Decal Libraries in Assets Location", default=False)
    libs_incompatible: BoolProperty(name="Incompatible Decal Libraries in Assets Location", default=False)
    libs_ambiguous: BoolProperty(name="Ambiguous Decal Libraries in Assets Location", default=False)

    trim_libs_corrupted: BoolProperty(name="Corrupted Trim Sheet Libraries in Assets Location", default=False)
    trim_libs_invalid: BoolProperty(name="Invalid Trim Sheet Libraries in Assets Location", default=False)
    trim_libs_incompatible: BoolProperty(name="Incompatible Trim Sheet Libraries in Assets Location", default=False)
    trim_libs_ambiguous: BoolProperty(name="Ambiguous Trim Sheet Libraries in Assets Location", default=False)

    importatlaspath: StringProperty(name="Import Atlas", description="Choose a Folder or .zip File to load a Atlas from", subtype='FILE_PATH', default="", update=update_importatlaspath)

    reversedecalsorting: BoolProperty(name="Reverse Decal Sorting (requires library reload or Blender restart)", description="Sort Decals Newest First", default=False)
    libraryrows: IntProperty(name="Rows of libraries in the Pie Menu", default=2, min=1)
    libraryoffset: IntProperty(name="Offset libraries to the right or left side of the Pie Menu", default=0)
    libraryscale: IntProperty(name="Size of Decal Library Icons", default=4, min=1, max=20)
    decalsinlibraryscale: IntProperty(name="Size of Icons in Decal Libraries", default=4, min=1, max=20)
    showdecalcount: BoolProperty(description="Show Decal Count next to Library Name", default=False)
    showdecalnames: BoolProperty(description="Show Decal Names in Decal Libraries", default=False)
    showdecalbuttonname: BoolProperty(description="Show Decal Name on Insert Button", default=False)

    reversetrimsorting: BoolProperty(name="Reverse Trim Sorting (requires library reload or Blender restart)", description="Sort Trims Newest First", default=False)
    trimlibraryrows: IntProperty(name="Rows of libraries in the Pie Menu", default=1, min=1)
    trimlibraryoffset: IntProperty(name="Offset libraries to the right or left side of the Pie Menu", default=0)
    trimlibraryscale: IntProperty(name="Size of Decal Library Icons", default=4, min=1, max=20)
    trimsinlibraryscale: IntProperty(name="Size of Icons in Trimsheet Libraries", default=4, min=1, max=20)
    showtrimcount: BoolProperty(description="Show Trim Count next to Library Name", default=False)
    showtrimnames: BoolProperty(description="Show Trim Names in Trimsheet Libraries", default=False)
    showtrimbuttonname: BoolProperty(description="Show Trim Name on Insert Button", default=False)

    decalcreator: StringProperty(name="Decal Creator", description="Setting this property, will mark Decals created by you with your own details", default="MACHIN3 - machin3.io, @machin3io")
    use_decal_float_normals: BoolProperty(name="Use Decal Float Normals", description="Use 16-bit vs 8-bit Normal Maps, when creating Decals", default=False)



    show_join_in_pie: BoolProperty(description="Show Join and Split in Pie Menu\nThey can otherwise always be found in the Tools section of the main DECALmachine Panel in the 3D Views Sidebar", default=False)
    adjust_use_alt_height: BoolProperty(description="Require ALT Key when adjusting Decal Height", default=False)

    modal_hud_hints: BoolProperty(description="Show Hints", default=True)
    modal_hud_scale: FloatProperty(name="HUD Scale", default=1, min=0.5, max=10)
    modal_hud_color: FloatVectorProperty(name="HUD Font Color", subtype='COLOR', default=[1, 1, 1], size=3, min=0, max=1)



    use_legacy_line_smoothing: BoolProperty(name="Use Legacy Line Smoothing", description="Legacy Line Smoothing using the depreciated bgl module\nIf this is disabled, lines drawn by DECALmachine won't be anti aliased.", default=False)



    def update_trim_uv_layer(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.trim_uv_layer == self.second_uv_layer:
            self.avoid_update = True

            if self.second_uv_layer - 1 >= 0:
                self.second_uv_layer -= 1
            else:
                self.second_uv_layer += 1

    def update_second_uv_layer(self, context):
        if self.avoid_update:
            self.avoid_update = False
            return

        if self.second_uv_layer == self.trim_uv_layer:
            self.avoid_update = True

            if self.trim_uv_layer - 1 >= 0:
                self.trim_uv_layer -= 1
            else:
                self.trim_uv_layer += 1

    trim_uv_layer: IntProperty(name="UV Layer used for Trim Detail", default=0, min=0, update=update_trim_uv_layer)
    second_uv_layer: IntProperty(name="Secondary UV Layer used by Box Unwrap", default=1, min=0, update=update_second_uv_layer)



    update_available: BoolProperty(name="Update is available", default=False)



    def update_tabs(self, context):
        if self.tabs == "ABOUT":
            self.addons_MESHmachine = get_addon('MESHmachine')[0]
            self.addons_MACHIN3tools = get_addon('MACHIN3tools')[0]
            self.addons_GrouPro = get_addon('Group Pro')[0]
            self.addons_BatchOps = get_addon('Batch Operations™')[0]
            self.addons_HardOps = get_addon('Hard Ops 9')[0]
            self.addons_BoxCutter = get_addon('BoxCutter')[0]

    tabs: EnumProperty(name="Tabs", items=prefs_tab_items, default="GENERAL", update=update_tabs)
    asset_loader_tabs: EnumProperty(name="Asset Loader Tabs", items=prefs_asset_loader_tab_items, default="DECALS", update=update_tabs)

    def update_decalmode(self, context):
        if self.decalremovemode is True:
            self.decalmode = "REMOVE"
        else:
            self.decalmode = "INSERT"

    decalmode: EnumProperty(name="Decal Mode", items=prefs_decalmode_items, default="INSERT")
    decalremovemode: BoolProperty(name="Decal Removal Mode", description="Toggle Decal Removal Mode\nThis allows for permanent removal of specific Decals from the Hard Drive", default=False, update=update_decalmode)

    pil: BoolProperty(name="PIL", default=False)
    pilrestart: BoolProperty(name="PIL restart", default=False)
    showpildetails: BoolProperty(name="Show PIL details", default=False)

    addons_MESHmachine: BoolProperty(default=False)
    addons_MACHIN3tools: BoolProperty(default=False)

    avoid_update: BoolProperty(default=False)


    def draw(self, context):
        layout=self.layout

        column = layout.column()

        if bpy.app.version < (3, 3, 0):
            column.separator()
            column.separator()
            column.separator()
            column.separator()
            column.separator()
            column.separator()
            column.label(text=f"Official Support for Blender versions older than 3.3.0 LTS has ended. Please update Blender to ensure DECALmachine {'.'.join([str(i) for i in bl_info['version']])} works reliably.", icon_value=get_icon('error'))
            column.separator()
            column.separator()
            column.separator()
            column.separator()
            column.separator()
            column.separator()

        row = column.row()
        row.prop(self, "tabs", expand=True)

        box = column.box()

        if self.tabs == "GENERAL":
            self.draw_general_tab(box)

        elif self.tabs == "CREATEEXPORT":
            self.draw_create_export_tab(box)

        elif self.tabs == "ABOUT":
            self.draw_about_tab(box)

        self.draw_thank_you()



    def draw_general_tab(self, box):
        split = box.split()


        b = split.box()
        b.label(text="Assets")

        self.draw_assets_path(b)

        self.draw_decal_libraries(b)



        b = split.box()
        b.label(text="Settings")

        self.draw_keymaps(b)

        self.draw_UI(b)

        self.draw_UVs(b)

    def draw_create_export_tab(self, box):
        split = box.split()

        b = split.box()
        b.label(text="Create")

        self.draw_pil(b)

        self.draw_decal_creation(b)

        b = split.box()
        b.label(text="Export")

        self.draw_decal_export(b)

    def draw_about_tab(self, box):
        split = box.split()

        b = split.box()
        b.label(text="MACHIN3")

        self.draw_machin3(b)


        b = split.box()
        b.label(text="Get More Decals")
        self.draw_decal_resources(b)



    def draw_assets_path(self, layout):
        box = layout.box()
        column = box.column()

        row = column.row(align=True)
        row.prop(self, "assetspath", text="Location")
        row.operator("machin3.reset_decalmachine_assets_location", text="", icon="LOOP_BACK")

        if os.path.normpath(self.assetspath) == os.path.normpath(self.defaultpath):
            b = box.box()

            column = b.column()
            column.label(text="I highly recommend you change this path!", icon='INFO')
            column.label(text="Otherwise your Assets will remain in the DECALmachine folder,", icon='BLANK1')
            column.label(text="and you risk loosing any Decals/Trim Sheets/Atlases you have", icon='BLANK1')
            column.label(text="created yourself, when uninstalling or updating DECALmachine", icon='BLANK1')

        legacylibs = get_legacy_libs()

        if any(legacylibs) or any([self.libs_corrupted, self.libs_incompatible, self.libs_ambiguous, self.libs_invalid, self.trim_libs_corrupted, self.trim_libs_incompatible, self.trim_libs_ambiguous, self.trim_libs_invalid]):
            b = box.box()
            column = b.column()

            if self.libs_corrupted:
                column.label(text="There are corrupted Decal Libraries in your assets location!", icon_value=get_icon('error'))

            if self.libs_incompatible:
                column.label(text="There are incompatible Decal Libraries in your assets location!", icon_value=get_icon('error'))

            if self.libs_ambiguous:
                column.label(text="There are ambiguous Decal Libraries in your assets location!", icon_value=get_icon('error'))

            if self.libs_invalid:
                column.label(text="There are invalid Decal Libraries in your assets location!", icon_value=get_icon('error'))

            if self.trim_libs_corrupted:
                column.label(text="There are corrupted Trim Sheet Libraries in your assets location!", icon_value=get_icon('error'))

            if self.trim_libs_incompatible:
                column.label(text="There are incompatible Trim Sheet Libraries in your assets location!", icon_value=get_icon('error'))

            if self.trim_libs_ambiguous:
                column.label(text="There are ambiguous Trim Sheet Libraries in your assets location!", icon_value=get_icon('error'))

            if self.trim_libs_invalid:
                column.label(text="There are invalid Trim Sheet Libraries in your assets location!", icon_value=get_icon('error'))

            if any(legacylibs):

                count = sum([len(libs) for libs in legacylibs])

                if count == 1:
                    text = 'Legacy Decal or Trim Sheet library detected in your current Assets Path!'
                    optext = 'Update It!'

                else:
                    text = 'Legacy Decal or Trim Sheet libraries detected in your current Assets Path!'
                    optext = 'Update Them All!'

                column.label(text=text, icon='INFO')

                draw_pil_warning(column, needed="for library update")

                row = column.row()
                row.scale_y = 1.5
                row.operator("machin3.batch_update_decal_libraries", text=optext)

    def draw_decal_libraries(self, layout):
        box = layout.box()
        box.label(text="Decal + Trim Libraries")

        column = box.column()
        row = column.row()

        col = row.column(align=True)
        col.template_list("MACHIN3_UL_decal_libs", "", self, "decallibsCOL", self, "decallibsIDX", rows=max(len(self.decallibsCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_decal_or_trim_library", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_decal_or_trim_library", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()
        col.operator("machin3.rename_decal_or_trim_library", text="", icon="OUTLINER_DATA_FONT")
        col.separator()
        col.operator("machin3.clear_decal_and_trim_libraries", text="", icon="LOOP_BACK")
        col.operator("machin3.reload_decal_and_trim_libraries", text="", icon_value=get_icon("refresh"))

        _, _, active = get_lib()
        icon = "cancel" if active and not active.islocked else "cancel_grey"
        col.operator("machin3.remove_decal_or_trim_library", text="", icon_value=get_icon(icon))

        column = box.column()

        row = column.row()
        row.prop(self, "newlibmode", expand=True)

        if self.newlibmode == 'IMPORT':
            row.label(text="Library from Folder or .zip")
            row.prop(self, "importdecallibpath", text="")
        else:
            row.label(text="Library named")
            row.prop(self, "newdecallibraryname", text="")

    def draw_keymaps(self, layout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        from . registration import keys as keysdict

        box = layout.box()
        box.label(text="Keymaps")

        column = box.column()

        drawn = []
        for name, keylist in keysdict.items():
            drawn.extend(draw_keymap_items(kc, name, keylist, column))

        if not all(drawn):
            row = box.row()
            row.scale_y = 1.5
            row.operator('machin3.restore_decal_machine_user_keymap_items', text="Restore Keymaps")

    def draw_UI(self, layout):
        box = layout.box()
        box.label(text="UI")

        column = box.column()

        row = column.split(factor=0.1)
        row.prop(self, "show_join_in_pie", text="True" if self.show_join_in_pie else "False", toggle=True)
        row.label(text="Show Join and Split tools in Pie Menu")

        row = column.split(factor=0.1)
        row.prop(self, "adjust_use_alt_height", text="True" if self.adjust_use_alt_height else "False", toggle=True)

        r = row.split(factor=0.5)
        r.label(text="Require ALT key when adjusting decal height")
        r.label(text="Helpful to prevent accidental height changes", icon='INFO')



        box.label(text="HUDs")

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



        box.label(text="View 3D")

        column = box.column()
        row = column.row()

        rs = row.split(factor=0.1)
        rs.prop(self, "use_legacy_line_smoothing", text="True" if self.use_legacy_line_smoothing else "False", toggle=True)
        rs.label(text="Use Legacy Line Smoothing")



        box.label(text="Asset Loaders")

        row = box.row()
        row.prop(self, "asset_loader_tabs", expand=True)

        column = box.column()

        if self.asset_loader_tabs == 'DECALS':
            row = column.split(factor=0.1)
            row.prop(self, "libraryrows", text="")
            row.label(text="Rows of Decal Libraries in the Pie Menu")

            row = column.split(factor=0.1)
            row.prop(self, "libraryoffset", text="")
            row.label(text="Offset Decal Libraries to right or left side in the Pie Menu")

            row = column.split(factor=0.1)
            row.prop(self, "libraryscale", text="")
            row.label(text="Size of Decal Library Icons")

            row = column.split(factor=0.1)
            row.prop(self, "decalsinlibraryscale", text="")
            row.label(text="Size of Icons in Decal Libraries")

            row = column.split(factor=0.1)
            row.prop(self, "reversedecalsorting", text="True" if self.reversedecalsorting else "False", toggle=True)
            r = row.split(factor=0.3)
            r.label(text="Sort Decals Newest First")
            r.label(text="reqiures library reload or Blender restart", icon='INFO')

            row = column.split(factor=0.1)
            row.prop(self, "showdecalcount", text="True" if self.showdecalcount else "False", toggle=True)
            row.label(text="Show Decal Count next to Library Name")

            row = column.split(factor=0.1)
            row.prop(self, "showdecalnames", text="True" if self.showdecalnames else "False", toggle=True)
            row.label(text="Show Decal Names in Decal Libraries")

            row = column.split(factor=0.1)
            row.prop(self, "showdecalbuttonname", text="True" if self.showdecalbuttonname else "False", toggle=True)
            row.label(text="Show Decal Name on Insert Buttons")

        elif self.asset_loader_tabs == 'TRIMS':
            row = column.split(factor=0.1)
            row.prop(self, "trimlibraryrows", text="")
            row.label(text="Rows of Trim Libraries in the Pie Menu")

            row = column.split(factor=0.1)
            row.prop(self, "trimlibraryoffset", text="")
            row.label(text="Offset Trim Libraries to right or left side in the Pie Menu")

            row = column.split(factor=0.1)
            row.prop(self, "trimlibraryscale", text="")
            row.label(text="Size of Trim Library Icons")

            row = column.split(factor=0.1)
            row.prop(self, "trimsinlibraryscale", text="")
            row.label(text="Size of Icons in Trim Libraries")

            row = column.split(factor=0.1)
            row.prop(self, "reversetrimsorting", text="True" if self.reversetrimsorting else "False", toggle=True)
            r = row.split(factor=0.3)
            r.label(text="Sort Trims Newest First")
            r.label(text="reqiures library reload or Blender restart", icon='INFO')

            row = column.split(factor=0.1)
            row.prop(self, "showtrimcount", text="True" if self.showtrimcount else "False", toggle=True)
            row.label(text="Show Trim Count next to Library Name")

            row = column.split(factor=0.1)
            row.prop(self, "showtrimnames", text="True" if self.showtrimnames else "False", toggle=True)
            row.label(text="Show Trim Names in Decal Libraries")

            row = column.split(factor=0.1)
            row.prop(self, "showtrimbuttonname", text="True" if self.showtrimbuttonname else "False", toggle=True)
            row.label(text="Show Trim Name on Insert Buttons")

    def draw_UVs(self, layout):
        box = layout.box()
        box.label(text="UVs")

        column = box.column()

        row = column.split(factor=0.1)
        row.prop(self, "trim_uv_layer", text='')
        row.label(text="UV Layer used for Trim Detail")

        row = column.split(factor=0.1)
        row.prop(self, "second_uv_layer", text='')
        row.label(text="UV Layer used for Box Unwrap")



    def draw_pil(self, layout):
        box = layout.box()
        column = box.column()
        column.scale_y = 1.2

        if self.pil:
            row = column.row()
            row.label(text="PIL is installed.", icon_value=get_icon("save"))

            icon = 'TRIA_DOWN' if self.showpildetails else 'TRIA_LEFT'
            row.prop(self, "showpildetails", text="", icon=icon)

            if self.showpildetails:
                path = get_PIL_image_module_path()
                if path:
                    column.label(text=path, icon='MONKEY')

                row = column.row()
                row.operator("machin3.purge_pil", text="Purge PIL", icon_value=get_icon('cancel'))


        elif self.pilrestart:
            column.label(text="PIL has been installed. Please restart Blender now.", icon="INFO")

        else:
            row = column.split(factor=0.2)
            row.operator("machin3.install_pil", text="Install PIL", icon="PREFERENCES")
            col = row.column()
            col.label(text="PIL is needed for Decal and Trim Sheet Creation as wells as for Atlasing and Baking.")
            col.label(text="Internet connection required.", icon_value=get_icon('info'))


            column.separator()

            box = column.box()
            box.label(text="Alternative Installation Methods")

            col = box.column(align=True)
            col.label(text="If you've used the Install button above, but are not seeing a green checkmark,")
            col.label(text="even after a Blender restart, you can try the following alternative installation methods.")

            if platform.system() == "Windows":
                b = col.box()
                r = b.row()
                r.label(text="Windows users, purge PIL now.")
                r.operator("machin3.purge_pil", text="Purge PIL", icon_value=get_icon('cancel'))

            elif platform.system() == "Darwin" and "AppTranslocation" in bpy.app.binary_path:
                b = col.box()
                b.label(text="Warning", icon_value=get_icon("error"))
                c = b.column()

                c.label(text="Blender is not properly installed, AppTranslocation is enabled.")
                c.label(text="Please refer to Blender's 'Installing on macOS' instructions.")
                c.label(text="Note that, for dragging of files and folders, you need to hold down the command key.")

                r = c.row()
                r.operator("wm.url_open", text="Installing on macOS").url = "https://docs.blender.org/manual/en/dev/getting_started/installing/macos.html"
                r.operator("wm.url_open", text="additional Information").url = "https://machin3.io/DECALmachine/docs/installation/#macos"

            col.label(text="Make sure to either run Blender as Administrator or at least have write access to the Blender folder.")
            col.label(text="Restart Blender, if the green checkmark doesn't show, after pressing either button.")

            row = col.row()
            row.operator("machin3.install_pil_admin", text="Install PIL (Admin)", icon="PREFERENCES")
            row.operator("machin3.easy_install_pil_admin", text="Easy Install PIL (Admin)", icon="PREFERENCES")

    def draw_decal_creation(self, layout):
        box = layout.box()
        column = box.column()

        row = column.split(factor=0.25)
        row.label(text="Decal Creator")
        row.prop(self, "decalcreator", text="")

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Change this, so Decals created by you, are tagged with your info!", icon="INFO")

        column.separator()

        row = column.split(factor=0.25)
        row.label(text="Float Normals")

        r = row.split(factor=0.25)
        r.prop(self, "use_decal_float_normals", text='True' if self.use_decal_float_normals else 'False', toggle=True)

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Largely untested, use at your own risk", icon="INFO")

        row = column.split(factor=0.25)
        row.label()
        row.label(text="Atlasing will work, but will create 8-bit normal Atlas map", icon="INFO")


    def draw_decal_export(self, layout):
        box = layout.box()
        box.label(text="Decal Atlases")

        _, _, active = get_atlas()

        if active and active.istrimsheet:
            _, libs, _ = get_lib()

            for idx, lib in enumerate(libs):
                if lib.name == active.name:
                    self.decallibsIDX = idx
                    break

        column = box.column()

        row = column.row()

        col = row.column(align=True)
        col.template_list("MACHIN3_UL_atlases", "", self, "atlasesCOL", self, "atlasesIDX", rows=max(len(self.atlasesCOL), 6))

        col = row.column(align=True)
        col.operator("machin3.move_atlas", text="", icon="TRIA_UP").direction = "UP"
        col.operator("machin3.move_atlas", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.separator()

        if active and active.istrimsheet:
            col.operator("machin3.rename_decal_or_trim_library", text="", icon="OUTLINER_DATA_FONT")
        else:
            col.operator("machin3.rename_atlas", text="", icon="OUTLINER_DATA_FONT")

        col.separator()
        col.operator("machin3.reload_atlases", text="", icon_value=get_icon("refresh"))

        if active and active.istrimsheet:
            icon = "cancel" if lib and not lib.islocked else "cancel_grey"
            col.operator("machin3.remove_decal_or_trim_library", text="", icon_value=get_icon(icon))
        else:
            icon = "cancel" if active and not active.islocked else "cancel_grey"
            col.operator("machin3.remove_atlas", text="", icon_value=get_icon(icon))

        row = column.row()
        row.label(text="Import Existing Atlas from Folder or .zip")
        row.prop(self, "importatlaspath", text="")



    def draw_machin3(self, layout):
        installed = get_icon('save')
        missing = get_icon('cancel_grey')

        box = layout.box()
        box.label(text="Blender Addons")
        column = box.column()

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
        row.label(text="MESHmachine", icon_value=installed if self.addons_MESHmachine else missing)
        r = row.split(factor=0.2)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://mesh.machin3.io"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/l/MESHmachine"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://blendermarket.com/products/MESHmachine"


        row = column.split(factor=0.3)
        row.scale_y = 1.2
        row.label(text="MACHIN3tools", icon_value=installed if self.addons_MACHIN3tools else missing)
        r = row.split(factor=0.2)
        r.operator("wm.url_open", text="Web", icon='URL').url = "https://machin3.io/MACHIN3tools"
        rr = r.row(align=True)
        rr.operator("wm.url_open", text="Gumroad", icon='URL').url = "https://gumroad.com/l/MACHIN3tools"
        rr.operator("wm.url_open", text="Blender Market", icon='URL').url = "https://blendermarket.com/products/MACHIN3tools"


        box = layout.box()
        box.label(text="DECALmachine Documentation")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Docs", icon='INFO').url = "https://machin3.io/DECALmachine/docs"
        row.operator("wm.url_open", text="Youtube", icon='FILE_MOVIE').url = "https://www.youtube.com/playlist?list=PLcEiZ9GDvSdWiU2BPQp99HglGGg1OGiHs"
        row.operator("wm.url_open", text="FAQ", icon='QUESTION').url = "https://machin3.io/DECALmachine/docs/faq"
        row.operator("machin3.get_decalmachine_support", text="Get Support", icon='GREASEPENCIL')


        box = layout.box()
        box.label(text="DECALmachine Discussion")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Blender Artists", icon="COMMUNITY").url = "https://blenderartists.org/t/decalmachine/688181"
        row.operator("wm.url_open", text="polycount", icon="COMMUNITY").url = "https://polycount.com/discussion/210294/blender-decalmachine-surface-detailing-using-mesh-decals"

        box = layout.box()
        box.label(text="Follow my work")

        column = box.column()
        row = column.row(align=True)
        row.scale_y = 1.2
        row.operator("wm.url_open", text="Web").url = "https://machin3.io"
        row.operator("wm.url_open", text="Twitter @machin3io").url = "https://twitter.com/machin3io"
        row.operator("wm.url_open", text="Twitter #DECALmachine").url = "https://twitter.com/search?q=(%23DECALmachine)%20(from%3Amachin3io)&src=typed_query&f=live"
        row.operator("wm.url_open", text="Artstation").url = "https://artstation.com/machin3"

    def draw_decal_resources(self, layout):
        column = layout.column()

        row = column.row()
        row.scale_y = 16
        row.operator("wm.url_open", text="Get More Decals", icon='URL').url = "https://machin3.io/DECALmachine/docs/decal_resources"



    def draw_thank_you(self):
        thankypou_path = os.path.join(get_path(), 'thank_you')
        message = ["Thank you for purchasing DECALmachine!",
                   "",
                   "Your support allows me to keep developing this addon and future ones, keeps updates free for everyone, and most importantly enables me to provide for my family.",
                   "If you haven't purchased DECALmachine, please consider doing so."]

        if not os.path.exists(thankypou_path):
            with open(thankypou_path, mode='w') as f:
                f.write('\n'.join(m for m in message))

            popup_message(message)
